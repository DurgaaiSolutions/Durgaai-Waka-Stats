from typing import Dict

from numpy import arange, array, add, amax, zeros
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from manager_download import DownloadManager as DM

MAX_LANGUAGES = 5
GRAPH_PATH = "./assets/bar_graph.png"  # hardcoded path


async def create_loc_graph(yearly_data: Dict, save_path: str):
    colors = await DM.get_remote_yaml("linguist") or {}
    years = len(yearly_data)
    year_indexes = arange(years)

    languages_all_loc = dict()
    for i, year in enumerate(sorted(yearly_data.keys())):
        for quarter in yearly_data[year]:
            top_languages = sorted(
                yearly_data[year][quarter],
                key=lambda lang: yearly_data[year][quarter][lang]["add"] + yearly_data[year][quarter][lang]["del"],
                reverse=True,
            )[:MAX_LANGUAGES]

            for lang in top_languages:
                if lang not in languages_all_loc:
                    languages_all_loc[lang] = zeros((years, 4, 2), dtype=int)
                languages_all_loc[lang][i][quarter - 1] = array([yearly_data[year][quarter][lang]["add"], yearly_data[year][quarter][lang]["del"]])

    fig = plt.figure()
    ax = fig.add_axes([0, 0, 1.5, 1])
    cumulative = zeros((years, 4, 2), dtype=int)
    language_handles = []

    for language, values in languages_all_loc.items():
        color = colors.get(language, {}).get("color", "tab:gray")
        language_handles.append(mpatches.Patch(color=color, label=language))

        for q in range(4):
            ax.bar(year_indexes + q * 0.21, values[:, q][:, 0], 0.2, bottom=cumulative[:, q][:, 0], color=color)
            ax.bar(year_indexes + q * 0.21, -values[:, q][:, 1], 0.2, bottom=-cumulative[:, q][:, 1], color=color)
            cumulative[:, q] = add(cumulative[:, q], values[:, q])

    ax.axhline(y=0.5, lw=0.5, color="k", snap=True)
    ax.set_ylabel("Lines of Code (LOC)", fontdict={"weight": "bold"})
    ax.set_xticks(array([arange(i, i + 0.84, 0.21) for i in year_indexes]).flatten(), labels=["Q1", "Q2", "Q3", "Q4"] * years)

    sax = ax.secondary_xaxis("top")
    sax.set_xticks(year_indexes + 0.42, labels=sorted(yearly_data.keys()))
    sax.spines["top"].set_visible(False)

    ax.legend(title="Language", handles=language_handles, loc="upper left", bbox_to_anchor=(1, 1), framealpha=0, title_fontproperties={"weight": "bold"})
    sax.tick_params(axis="both", length=0)
    sax.spines["top"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    max_offset = 0.05 * amax(cumulative)
    flat = cumulative.reshape(-1, 2)
    plt.ylim(top=amax(flat[:, 0]) + max_offset, bottom=-amax(flat[:, 1]) - max_offset)

    plt.savefig(save_path, bbox_inches="tight")
    plt.close(fig)
