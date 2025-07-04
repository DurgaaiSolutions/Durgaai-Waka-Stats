from base64 import b64encode
from os import environ, makedirs
from os.path import dirname, join
from random import choice
from re import sub
from shutil import copy, rmtree
from string import ascii_letters

from git import Repo, Actor
from github import Github, AuthenticatedUser, Repository

from manager_environment import EnvironmentManager as EM
from manager_debug import DebugManager as DBM


def init_github_manager():
    GitHubManager.prepare_github_env()
    DBM.i(f"Current User : {GitHubManager.USER.login}.")


class GitHubManager:
    USER: AuthenticatedUser
    REPO: Repo
    REMOTE: Repository

    _REMOTE_NAME: str
    _REPO_PATH: str
    _SINGLE_COMMIT_BRANCH = "latest_branch"

    _START_COMMENT = f"<!--START_SECTION:{EM.SECTION_NAME}-->"
    _END_COMMENT = f"<!--END_SECTION:{EM.SECTION_NAME}-->"
    _README_REGEX = f"{_START_COMMENT}[\\s\\S]+{_END_COMMENT}"

    @staticmethod
    def prepare_github_env():
        github = Github(EM.GH_TOKEN)
        clone_path = "repo"
        GitHubManager.USER = github.get_user()
        rmtree(clone_path, ignore_errors=True)

        GitHubManager._REMOTE_NAME = environ.get("GITHUB_REPOSITORY", f"{GitHubManager.USER.login}/Durgaai-Waka-Stats")
        GitHubManager._REPO_PATH = f"https://{EM.GH_TOKEN}@github.com/{GitHubManager._REMOTE_NAME}.git"

        GitHubManager.REMOTE = github.get_repo(GitHubManager._REMOTE_NAME)
        GitHubManager.REPO = Repo.clone_from(GitHubManager._REPO_PATH, to_path=clone_path)

        if EM.COMMIT_SINGLE:
            GitHubManager.REPO.git.checkout(GitHubManager.branch(EM.PULL_BRANCH_NAME))
            GitHubManager.REPO.git.checkout("--orphan", GitHubManager._SINGLE_COMMIT_BRANCH)
        else:
            GitHubManager.REPO.git.checkout(GitHubManager.branch(EM.PUSH_BRANCH_NAME))

    @staticmethod
    def _get_author() -> Actor:
        if EM.COMMIT_BY_ME:
            return Actor(EM.COMMIT_USERNAME or GitHubManager.USER.login, EM.COMMIT_EMAIL or GitHubManager.USER.email)
        return Actor(EM.COMMIT_USERNAME or "readme-bot", EM.COMMIT_EMAIL or "41898282+github-actions[bot]@users.noreply.github.com")

    @staticmethod
    def branch(requested_branch: str) -> str:
        return GitHubManager.REMOTE.default_branch if requested_branch == "" else requested_branch

    @staticmethod
    def _copy_file_and_add_to_repo(src_path: str):
        dst_path = join(GitHubManager.REPO.working_tree_dir, src_path)
        makedirs(dirname(dst_path), exist_ok=True)
        copy(src_path, dst_path)
        GitHubManager.REPO.git.add(dst_path)

    @staticmethod
    def update_readme(stats: str):
        DBM.i("Updating README...")
        readme_path = join(GitHubManager.REPO.working_tree_dir, GitHubManager.REMOTE.get_readme().path)
        with open(readme_path, "r") as readme_file:
            readme_contents = readme_file.read()
        readme_stats = f"{GitHubManager._START_COMMENT}\n{stats}\n{GitHubManager._END_COMMENT}"
        new_readme = sub(GitHubManager._README_REGEX, readme_stats, readme_contents)
        with open(readme_path, "w") as readme_file:
            readme_file.write(new_readme)
        GitHubManager.REPO.git.add(readme_path)
        DBM.g("README Updated!")

    @staticmethod
    def update_chart(name: str, path: str) -> str:
        output = str()
        DBM.i(f"Updating {name} Chart...")
        if not EM.DEBUG_RUN:
            DBM.i("\tAdding Chart To Repo...")
            GitHubManager._copy_file_and_add_to_repo(path)
            chart_path = f"https://raw.githubusercontent.com/{GitHubManager._REMOTE_NAME}/{GitHubManager.branch(EM.PUSH_BRANCH_NAME)}/{path}"
            output += f"![{name} chart]({chart_path})\n\n"
        else:
            DBM.i("\tInlining Chart...")
            hint = "Use [this website](https://codebeautify.org/base64-to-image-converter) to view the image."
            with open(path, "rb") as input_file:
                output += f"{hint}\n```\ndata:image/png;base64,{b64encode(input_file.read()).decode('utf-8')}\n```\n\n"
        return output

    @staticmethod
    def commit_update():
        actor = GitHubManager._get_author()
        DBM.i("Committing Files To Repo...")
        GitHubManager.REPO.index.commit(EM.COMMIT_MESSAGE, author=actor, committer=actor)
        if EM.COMMIT_SINGLE:
            DBM.i("Pushing Files To Repo As A Single Commit...")
            refspec = f"{GitHubManager._SINGLE_COMMIT_BRANCH}:{GitHubManager.branch(EM.PUSH_BRANCH_NAME)}"
            headers = GitHubManager.REPO.remotes.origin.push(force=True, refspec=refspec)
        else:
            DBM.i("Pushing Files To Repo...")
            headers = GitHubManager.REPO.remotes.origin.push()
        if len(headers) == 0:
            DBM.i(f"Repository Push Error : {headers}!")
        else:
            DBM.i("Repository Synchronized!")

    @staticmethod
    def set_github_output(stats: str):
        DBM.i("Setting README Contents As Action Output...")
        if "GITHUB_OUTPUT" not in environ:
            DBM.p("Not In GitHub Environment, Not Setting Action Output!")
            return
        DBM.i("Outputting Readme Contents, Check The Latest Comment For The Generated Stats.")
        prefix = "README Stats Current Output : "
        eol = "".join(choice(ascii_letters) for _ in range(10))
        with open(environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"README_CONTENT<<{eol}\n{prefix}\n\n{stats}\n{eol}\n")
        DBM.g("Action Output Set!")
