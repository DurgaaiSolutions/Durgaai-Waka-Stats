from asyncio import Task
from hashlib import md5
from json import dumps
from string import Template
from typing import Awaitable, Dict, Callable, Optional, List, Tuple, Union

from httpx import AsyncClient, Response
from yaml import safe_load

from manager_environment import EnvironmentManager as EM
from manager_debug import DebugManager as DBM

# GitHub GraphQL API query templates
GITHUB_API_QUERIES = {
    "repos_contributed_to": """
    {
        user(login: "$username") {
            repositoriesContributedTo(orderBy: {field: CREATED_AT, direction: DESC}, $pagination, includeUserRepositories: true) {
                nodes {
                    primaryLanguage { name }
                    name
                    owner { login }
                    isPrivate
                    isFork
                }
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }
    """,
    "user_repository_list": """
    {
        user(login: "$username") {
            repositories(orderBy: {field: CREATED_AT, direction: DESC}, $pagination, affiliations: [OWNER, COLLABORATOR], isFork: false) {
                nodes {
                    primaryLanguage { name }
                    name
                    owner { login }
                    isPrivate
                }
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }
    """,
    "repo_branch_list": """
    {
        repository(owner: "$owner", name: "$name") {
            refs(refPrefix: "refs/heads/", orderBy: {direction: DESC, field: TAG_COMMIT_DATE}, $pagination) {
                nodes { name }
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }
    """,
    "repo_commit_list": """
    {
        repository(owner: "$owner", name: "$name") {
            ref(qualifiedName: "refs/heads/$branch") {
                target {
                    ... on Commit {
                        history(author: { id: "$id" }, $pagination) {
                            nodes {
                                additions
                                deletions
                                committedDate
                                oid
                            }
                            pageInfo {
                                endCursor
                                hasNextPage
                            }
                        }
                    }
                }
            }
        }
    }
    """,
    "hide_outdated_comment": """
    mutation {
        minimizeComment(input: {classifier: OUTDATED, subjectId: "$id"}) {
            clientMutationId
        }
    }
    """,
}


async def init_download_manager(user_login: str):
    await DownloadManager.load_remote_resources(
        linguist="https://cdn.jsdelivr.net/gh/github/linguist@master/lib/linguist/languages.yml",
        waka_latest=f"https://wakatime.com/api/v1/users/current/stats/last_7_days?api_key={EM.WAKATIME_API_KEY}",
        waka_all=f"https://wakatime.com/api/v1/users/current/all_time_since_today?api_key={EM.WAKATIME_API_KEY}",
        github_stats=f"https://github-contributions.vercel.app/api/v1/{user_login}",
    )


class DownloadManager:
    _client = AsyncClient(timeout=60.0)
    _REMOTE_RESOURCES_CACHE: Dict[str, Union[Awaitable, Response]] = {}

    @staticmethod
    async def load_remote_resources(**resources: str):
        for key, url in resources.items():
            DownloadManager._REMOTE_RESOURCES_CACHE[key] = await DownloadManager._client.get(url)

    @staticmethod
    async def close_remote_resources():
        for resource in DownloadManager._REMOTE_RESOURCES_CACHE.values():
            if isinstance(resource, Task):
                resource.cancel()
            elif isinstance(resource, Awaitable):
                await resource
        await DownloadManager._client.aclose()

    @staticmethod
    async def _get_remote_resource(resource: str, convertor: Optional[Callable[[bytes], Dict]]) -> Optional[Dict]:
        DBM.i(f"\tRequesting Static Resource '{resource}'...")
        entry = DownloadManager._REMOTE_RESOURCES_CACHE[resource]

        if isinstance(entry, Awaitable):
            res = await entry
            DownloadManager._REMOTE_RESOURCES_CACHE[resource] = res
            DBM.g(f"\tStatic Resource '{resource}' Downloaded And Cached.")
        else:
            res = entry
            DBM.g(f"\tStatic Resource '{resource}' Loaded From Cache.")

        if res.status_code == 200:
            return res.json() if convertor is None else convertor(res.content)
        elif res.status_code in {201, 202}:
            DBM.w(f"\tStatic Resource '{resource}' Returned Status {res.status_code}.")
            return None
        raise Exception(f"Static Request To '{res.url}' Failed With Code {res.status_code}: {res.json()}")

    @staticmethod
    async def get_remote_json(resource: str) -> Optional[Dict]:
        return await DownloadManager._get_remote_resource(resource, None)

    @staticmethod
    async def get_remote_yaml(resource: str) -> Optional[Dict]:
        return await DownloadManager._get_remote_resource(resource, safe_load)

    @staticmethod
    async def _fetch_graphql_query(query: str, retries_count: int = 10, **kwargs) -> Dict:
        headers = {"Authorization": f"Bearer {EM.GH_TOKEN}"}
        query_template = Template(GITHUB_API_QUERIES[query])
        res = await DownloadManager._client.post(
            "https://api.github.com/graphql",
            json={"query": query_template.substitute(kwargs)},
            headers=headers,
        )

        if res.status_code == 200:
            return res.json()
        elif res.status_code == 502 and retries_count > 0:
            return await DownloadManager._fetch_graphql_query(query, retries_count - 1, **kwargs)
        raise Exception(f"GraphQL Query '{query}' Failed With Code {res.status_code}: {res.json()}")

    @staticmethod
    def _find_pagination_and_data_list(response: Dict) -> Tuple[List, Dict]:
        if "nodes" in response and "pageInfo" in response:
            return response["nodes"], response["pageInfo"]
        if len(response) == 1 and isinstance(next(iter(response.values())), Dict):
            return DownloadManager._find_pagination_and_data_list(next(iter(response.values())))
        return [], {"hasNextPage": False}

    @staticmethod
    async def _fetch_graphql_paginated(query: str, **kwargs) -> List:
        results = []
        pagination = "first: 100"
        while True:
            response = await DownloadManager._fetch_graphql_query(query, **kwargs, pagination=pagination)
            page, info = DownloadManager._find_pagination_and_data_list(response)
            results.extend(page)
            if not info.get("hasNextPage"):
                break
            pagination = f'first: 100, after: "{info["endCursor"]}"'
        return results

    @staticmethod
    async def get_remote_graphql(query: str, **kwargs) -> Dict:
        key = f"{query}_{md5(dumps(kwargs, sort_keys=True).encode('utf-8')).digest()}"
        if key not in DownloadManager._REMOTE_RESOURCES_CACHE:
            requires_pagination = "$pagination" in GITHUB_API_QUERIES[query]
            result = (
                await DownloadManager._fetch_graphql_paginated(query, **kwargs)
                if requires_pagination
                else await DownloadManager._fetch_graphql_query(query, **kwargs)
            )
            DownloadManager._REMOTE_RESOURCES_CACHE[key] = result
        return DownloadManager._REMOTE_RESOURCES_CACHE[key]
