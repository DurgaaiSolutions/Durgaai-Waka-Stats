from asyncio import sleep
from json import dumps
from re import search
from datetime import datetime
from typing import Dict, Tuple

from manager_download import DownloadManager as DM
from manager_environment import EnvironmentManager as EM
from manager_github import GitHubManager as GHM
from manager_debug import DebugManager as DBM


async def calculate_commit_data(repositories: Dict) -> Tuple[Dict, Dict]:
    DBM.i("Calculating Commit Data...")
    yearly_data = {}
    date_data = {}

    for idx, repo in enumerate(repositories):
        if repo["name"] not in EM.IGNORED_REPOS:
            repo_name = "[private]" if repo["isPrivate"] else f"{repo['owner']['login']}/{repo['name']}"
            DBM.i(f"\t{idx + 1}/{len(repositories)} Processing Repository: {repo_name}")
            await update_data_with_commit_stats(repo, yearly_data, date_data)

    DBM.g("Commit Data Computation Complete.")

    if EM.DEBUG_RUN:
        from pickle import dump

        with open("./assets/commits_data.pick", "wb") as f:
            dump([yearly_data, date_data], f)
        with open("./assets/commits_data.json", "w") as f:
            f.write(dumps([yearly_data, date_data], indent=2))
        DBM.g("Commit Data Saved To Cache.")

    return yearly_data, date_data


async def update_data_with_commit_stats(repo_details: Dict, yearly_data: Dict, date_data: Dict):
    owner = repo_details["owner"]["login"]
    branch_data = await DM.get_remote_graphql("repo_branch_list", owner=owner, name=repo_details["name"])

    if not branch_data:
        DBM.w("\t\tNo Branches Found. Skipping Repository.")
        return

    for branch in branch_data:
        commits = await DM.get_remote_graphql("repo_commit_list", owner=owner, name=repo_details["name"], branch=branch["name"], id=GHM.USER.node_id)

        for commit in commits:
            commit_date = search(r"\d+-\d+-\d+", commit["committedDate"]).group()
            parsed_date = datetime.fromisoformat(commit_date)
            year = parsed_date.year
            quarter = (parsed_date.month - 1) // 3 + 1

            # Commit timestamp indexing
            date_data.setdefault(repo_details["name"], {}).setdefault(branch["name"], {})[commit["oid"]] = commit["committedDate"]

            if repo_details["primaryLanguage"]:
                lang = repo_details["primaryLanguage"]["name"]
                yearly_data.setdefault(year, {}).setdefault(quarter, {}).setdefault(lang, {"add": 0, "del": 0})
                yearly_data[year][quarter][lang]["add"] += commit["additions"]
                yearly_data[year][quarter][lang]["del"] += commit["deletions"]

        if not EM.DEBUG_RUN:
            await sleep(0.4)
