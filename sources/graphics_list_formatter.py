from enum import Enum
from typing import Dict, Tuple, List
from datetime import datetime

from pytz import timezone, utc
from manager_environment import EnvironmentManager as EM

DAY_TIME_EMOJI = ["🌞", "🌆", "🌃", "🌙"]
DAY_TIME_NAMES = ["Morning", "Daytime", "Evening", "Night"]
WEEK_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class Symbol(Enum):
    VERSION_1 = "▰", "▱"
    VERSION_2 = "🞔", "🞎"
    VERSION_3 = "⬛", "⬜"

    @staticmethod
    def get_symbols(version: int) -> Tuple[str, str]:
        return Symbol[f"VERSION_{version}"].value


def make_graph(percent: float) -> str:
    done_block, empty_block = Symbol.get_symbols(EM.SYMBOL_VERSION)
    percent_quart = round(percent / 4)
    return f"{done_block * percent_quart}{empty_block * (25 - percent_quart)}"


def make_list(
    data: List = None,
    names: List[str] = None,
    texts: List[str] = None,
    percents: List[float] = None,
    top_num: int = 5,
    sort: bool = True,
) -> str:
    MAX_NAME_WIDTH = 22
    MAX_TEXT_WIDTH = 18

    if data is not None:
        if names is None:
            names = [item["name"] for item in data if "name" in item]
        if texts is None:
            texts = [item["text"] for item in data if "text" in item]
        if percents is None:
            percents = [item["percent"] for item in data if "percent" in item]

    def truncate(text: str, max_len: int) -> str:
        return text if len(text) <= max_len else text[: max_len - 3] + "..."

    data = list(zip(names, texts, percents))
    top_data = sorted(data[:top_num], key=lambda record: record[2], reverse=True) if sort else data[:top_num]

    data_list = [
        f"{truncate(n.title(), MAX_NAME_WIDTH):{MAX_NAME_WIDTH}}" f"{truncate(t.title(), MAX_TEXT_WIDTH):{MAX_TEXT_WIDTH}}" f"{make_graph(p)}   {p:05.2f} %"
        for n, t, p in top_data
    ]
    return "\n".join(data_list)


async def make_commit_day_time_list(time_zone: str, repositories: Dict, commit_dates: Dict) -> str:
    stats = ""
    day_times = [0] * 4
    week_days = [0] * 7

    for repo in repositories:
        repo_name = repo["name"]
        if repo_name not in commit_dates:
            continue
        for committed_date in [d for branch in commit_dates[repo_name].values() for d in branch.values()]:
            local_date = datetime.strptime(committed_date, "%Y-%m-%dT%H:%M:%SZ")
            date = local_date.replace(tzinfo=utc).astimezone(timezone(time_zone))
            day_times[date.hour // 6] += 1
            week_days[date.isoweekday() - 1] += 1

    sum_day = sum(day_times)
    sum_week = sum(week_days)
    day_times = day_times[1:] + day_times[:1]

    if EM.SHOW_COMMIT:
        dt_names = [f"{DAY_TIME_EMOJI[i]} {DAY_TIME_NAMES[i]}" for i in range(len(day_times))]
        dt_texts = [f"{count} Commits" for count in day_times]
        dt_percents = [0 if sum_day == 0 else round((count / sum_day) * 100, 2) for count in day_times]
        is_early_bird = sum(day_times[0:2]) >= sum(day_times[2:4])
        title = "We Are Early Birds" if is_early_bird else "We Are Night Owls"

        stats += f"**{title}** \n\n```text\n{make_list(names=dt_names, texts=dt_texts, percents=dt_percents, top_num=7, sort=False)}\n```\n"

    if EM.SHOW_DAYS_OF_WEEK:
        wd_names = WEEK_DAY_NAMES
        wd_texts = [f"{count} Commits" for count in week_days]
        wd_percents = [0 if sum_week == 0 else round((count / sum_week) * 100, 2) for count in week_days]
        most_productive_day = wd_names[wd_percents.index(max(wd_percents))]
        title = f"We Are Most Productive On {most_productive_day}"

        stats += f"📅 **{title}** \n\n```text\n{make_list(names=wd_names, texts=wd_texts, percents=wd_percents, top_num=7, sort=False)}\n```\n"

    return stats


def make_language_per_repo_list(repositories: Dict) -> str:
    language_count = {}

    repos_with_lang = [repo for repo in repositories if repo["primaryLanguage"] is not None]
    for repo in repos_with_lang:
        lang = repo["primaryLanguage"]["name"]
        if lang not in language_count:
            language_count[lang] = {"count": 0}
        language_count[lang]["count"] += 1

    names = [lang.title() for lang in language_count]
    texts = [
        f"{language_count[lang]['count']} Repo" if language_count[lang]["count"] == 1 else f"{language_count[lang]['count']} Repos" for lang in language_count
    ]
    percents = [round(language_count[lang]["count"] / len(repos_with_lang) * 100, 2) for lang in language_count]

    top_lang = max(language_count, key=lambda x: language_count[x]["count"]).title()
    title = f"**We Mostly Code In {top_lang}** \n\n" if repos_with_lang else ""

    return f"{title}```text\n{make_list(names=names, texts=texts, percents=percents)}\n```\n\n"
