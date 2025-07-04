from asyncio import run
from datetime import datetime
from typing import Dict
from urllib.parse import quote

from humanize import intword, naturalsize, intcomma

from manager_debug import init_debug_manager, DebugManager as DBM
from manager_github import init_github_manager, GitHubManager as GHM
from manager_download import init_download_manager, DownloadManager as DM
from manager_environment import EnvironmentManager as EM

from graphics_chart_drawer import create_loc_graph, GRAPH_PATH
from yearly_commit_calculater import calculate_commit_data
from graphics_list_formatter import make_list, make_commit_day_time_list, make_language_per_repo_list


async def get_waka_time_stats(repositories: Dict, commit_dates: Dict) -> str:
    DBM.i("Adding Short WakaTime Stats...")
    stats = ""

    data = await DM.get_remote_json("waka_latest")
    if not data:
        DBM.p("WakaTime Data Unavailable!")
        return stats

    if EM.SHOW_COMMIT or EM.SHOW_DAYS_OF_WEEK:
        DBM.i("Adding User Commit Day/Time Info...")
        stats += f"{await make_commit_day_time_list(data['data']['timezone'], repositories, commit_dates)}\n\n"

    if EM.SHOW_TIMEZONE or EM.SHOW_LANGUAGE or EM.SHOW_EDITORS or EM.SHOW_PROJECTS or EM.SHOW_OS:
        no_activity = "No Activity Tracked This Week"
        stats += "📊 **This Week The Team Spent Time On** \n\n```text\n"

        if EM.SHOW_TIMEZONE:
            stats += f"🕑︎ Timezone: {data['data']['timezone']}\n\n"
        if EM.SHOW_LANGUAGE:
            stats += f"💬 Languages:\n{make_list(data['data']['languages']) or no_activity}\n\n"
        if EM.SHOW_EDITORS:
            stats += f"🔥 Editors:\n{make_list(data['data']['editors']) or no_activity}\n\n"
        if EM.SHOW_PROJECTS:
            stats += f"🐱‍💻 Projects:\n{make_list(data['data']['projects']) or no_activity}\n\n"
        if EM.SHOW_OS:
            stats += f"💻 Operating System:\n{make_list(data['data']['operating_systems']) or no_activity}\n\n"

        stats = stats.rstrip() + "\n```\n\n"

    DBM.g("WakaTime Stats Added!")
    return stats


async def get_short_github_info() -> str:
    DBM.i("Adding Short GitHub Info...")
    stats = "**🐱 Durgaai Solutions GitHub Data** \n\n"

    if GHM.USER.disk_usage is None:
        stats += "> 📦 Used In GitHub's Storage: ? \n > \n"
        DBM.p("Missing GitHub PAT With User Scope.")
    else:
        stats += f"> 📦 Used In GitHub's Storage: {naturalsize(GHM.USER.disk_usage)} \n > \n"

    data = await DM.get_remote_json("github_stats")
    if data and data["years"]:
        year_info = data["years"][0]
        stats += f"> 🏆 Contributions Made In The Year: {intcomma(year_info['total'])} in {year_info['year']} \n > \n"

    hire_status = "Durgaai Solutions Is Open to Hire" if GHM.USER.hireable else "Durgaai Solutions Is Not Open to Hire"
    stats += f"> {'💼' if GHM.USER.hireable else '🚫'} {hire_status} \n > \n"
    stats += f"> 📜 Public Repositories: {GHM.USER.public_repos} \n > \n"
    private = GHM.USER.owned_private_repos or 0
    stats += f"> 🔑 Private Repositories: {private} \n > \n"

    DBM.g("Short GitHub Info Added!")
    return stats


async def collect_user_repositories() -> Dict:
    DBM.i("Getting User Repositories List...")
    repos = await DM.get_remote_graphql("user_repository_list", username=GHM.USER.login, id=GHM.USER.node_id)
    repo_names = [repo["name"] for repo in repos]
    contributed = await DM.get_remote_graphql("repos_contributed_to", username=GHM.USER.login)
    contributed_clean = [repo for repo in contributed if repo and repo["name"] not in repo_names and not repo["isFork"]]
    DBM.g("Collected All User And Contributed Repositories.")
    return repos + contributed_clean


async def get_stats() -> str:
    DBM.i("Collecting Stats For README...")
    stats = ""
    repositories = await collect_user_repositories()

    if EM.SHOW_LINES_OF_CODE or EM.SHOW_LOC_CHART or EM.SHOW_COMMIT or EM.SHOW_DAYS_OF_WEEK:
        yearly_data, commit_data = await calculate_commit_data(repositories)
    else:
        yearly_data, commit_data = {}, {}
        DBM.w("Skipped Yearly Data Calculation.")

    if EM.SHOW_TOTAL_CODE_TIME:
        data = await DM.get_remote_json("waka_all")
        if data:
            stats += f"![Code Time](http://img.shields.io/badge/{quote('Code Time (Team)')}-{quote(data['data']['text'])}-blue)\n\n"

    if EM.SHOW_PROFILE_VIEWS:
        views = GHM.REMOTE.get_views_traffic(per="week").count
        stats += f"![Profile Views](http://img.shields.io/badge/Profile%20Views%20(Team)-{views}-blue)\n\n"

    if EM.SHOW_LINES_OF_CODE:
        total_loc = sum(yearly_data[y][q][d]["add"] for y in yearly_data for q in yearly_data[y] for d in yearly_data[y][q])
        data_str = f"{intword(total_loc)} Lines of code"
        stats += f"![Lines of code](https://img.shields.io/badge/From%20Hello%20World%20the%20Team%20Has%20Written-{quote(data_str)}-blue)\n\n"

    if EM.SHOW_SHORT_INFO:
        stats += await get_short_github_info()

    stats += await get_waka_time_stats(repositories, commit_data)

    if EM.SHOW_LANGUAGE_PER_REPO:
        stats += f"{make_language_per_repo_list(repositories)}\n\n"

    if EM.SHOW_LOC_CHART:
        await create_loc_graph(yearly_data, GRAPH_PATH)
        stats += f"**Timeline**\n\n{GHM.update_chart('Lines of Code', GRAPH_PATH)}"

    if EM.SHOW_UPDATED_DATE:
        stats += f"\n Last Updated On {datetime.now().strftime(EM.UPDATED_DATE_FORMAT)} UTC"

    DBM.g("Stats collected.")
    return stats


async def main():
    init_github_manager()
    await init_download_manager(GHM.USER.login)
    DBM.i("Managers Initialized.")
    stats = await get_stats()

    if not EM.DEBUG_RUN:
        GHM.update_readme(stats)
        GHM.commit_update()
    else:
        GHM.set_github_output(stats)

    await DM.close_remote_resources()


if __name__ == "__main__":
    init_debug_manager()
    start_time = datetime.now()
    DBM.g("Program Execution Started At $date.", date=start_time)
    run(main())
    end_time = datetime.now()
    DBM.g("Program Execution Finished At $date.", date=end_time)
    DBM.p("Program Finished In $time.", time=end_time - start_time)
