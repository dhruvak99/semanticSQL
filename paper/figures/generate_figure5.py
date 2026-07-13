from __future__ import annotations

import json
import os
import tempfile
from itertools import accumulate
from pathlib import Path

cache_root = Path(tempfile.gettempdir()) / "semanticsql_figure_cache"
cache_root.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(cache_root / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(cache_root / "xdg"))

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


BLUE = "#4E79A7"
RED = "#E15759"
GRAY = "#B7B7B7"
GRID = "#E8E8E8"
TEXT = "#2F2F2F"
AXIS = "#7A7A7A"


def configure_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "font.family": "DejaVu Sans",
            "font.size": 8.5,
            "axes.labelsize": 8.5,
            "axes.labelweight": "medium",
            "xtick.labelsize": 6.7,
            "ytick.labelsize": 7.3,
            "axes.linewidth": 0.5,
            "savefig.dpi": 600,
            "patch.antialiased": True,
            "lines.antialiased": True,
        }
    )


def load_root_causes() -> list[tuple[str, int]]:
    root = Path(__file__).resolve().parents[2]
    failure_summary_path = root / "results" / "analysis" / "failure_summary.json"
    failure_breakdown_path = root / "results" / "analysis" / "failure_breakdown.json"

    with failure_summary_path.open("r", encoding="utf-8") as handle:
        summary = json.load(handle)
    root_causes = summary.get("root_cause_counts")

    if not root_causes:
        with failure_breakdown_path.open("r", encoding="utf-8") as handle:
            breakdown = json.load(handle)
        root_causes = breakdown.get("by_root_cause", {})

    rows = [(cause, int(count)) for cause, count in root_causes.items()]
    return sorted(rows, key=lambda item: item[1], reverse=True)


def top_ten_with_others(rows: list[tuple[str, int]]) -> list[tuple[str, int]]:
    top_ten = rows[:10]
    other_count = sum(count for _, count in rows[10:])
    if other_count:
        return [*top_ten, ("Others", other_count)]
    return top_ten


LABEL_OVERRIDES = {
    "Aggregate result alias mismatch in evaluator comparison": "Aggregate Alias",
    "Wrong or invented column": "Invented Column",
    "Aggregate result mismatch": "Aggregate Result",
    "Wrong aggregate function": "Wrong Aggregate",
    "LIMIT clause mismatch": "LIMIT Clause",
    "WHERE clause error": "WHERE Clause",
    "ORDER BY mismatch": "ORDER BY",
    "DISTINCT/projection mismatch": "DISTINCT",
    "JOIN result mismatch": "JOIN Result",
    "Others": "Others",
}


def concise_label(label: str) -> str:
    return LABEL_OVERRIDES.get(label, label)


def add_rounded_bar(ax: plt.Axes, x_center: float, height: float, width: float, color: str) -> None:
    bar = FancyBboxPatch(
        (x_center - width / 2, 0),
        width,
        height,
        boxstyle=f"round,pad=0,rounding_size={width * 0.18}",
        linewidth=0,
        facecolor=color,
        antialiased=True,
    )
    ax.add_patch(bar)


def style_axes(ax: plt.Axes) -> None:
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_linewidth(0.5)
        ax.spines[spine].set_color(AXIS)
    ax.tick_params(axis="both", length=3.4, width=0.5, color=AXIS, pad=4)
    ax.yaxis.grid(True, color=GRID, linewidth=0.5)
    ax.set_axisbelow(True)


def main() -> None:
    configure_style()
    all_rows = load_root_causes()
    rows = top_ten_with_others(all_rows)
    causes = [row[0] for row in rows]
    counts = [row[1] for row in rows]
    total_failures = sum(count for _, count in all_rows)
    cumulative_percentages = [count / total_failures * 100 for count in accumulate(counts)]

    x_positions = list(range(len(rows)))
    colors = [RED if index < 3 else GRAY for index in x_positions]

    fig, ax = plt.subplots(figsize=(6.65, 3.15), constrained_layout=True)
    bar_width = 0.66
    for x_position, count, color in zip(x_positions, counts, colors):
        add_rounded_bar(ax, x_position, count, bar_width, color)

    ax.set_ylabel("Failure count", labelpad=8)
    ax.set_xticks(x_positions)
    ax.set_xticklabels([concise_label(cause) for cause in causes], rotation=28, ha="right")
    ax.set_xlim(-0.65, len(rows) - 0.35)
    ax.set_ylim(0, max(counts) * 1.18)
    style_axes(ax)

    ax_cumulative = ax.twinx()
    ax_cumulative.plot(
        x_positions,
        cumulative_percentages,
        color=BLUE,
        linewidth=1.45,
        marker="o",
        markersize=3.2,
        markeredgewidth=0,
    )
    ax_cumulative.set_ylabel("Cumulative failures (%)", labelpad=8)
    ax_cumulative.set_ylim(0, 105)
    ax_cumulative.spines["top"].set_visible(False)
    ax_cumulative.spines["left"].set_visible(False)
    ax_cumulative.spines["right"].set_visible(False)
    ax_cumulative.tick_params(axis="y", length=3.4, width=0.5, color=AXIS, pad=4)

    for index, percentage in enumerate(cumulative_percentages):
        ax_cumulative.text(
            index,
            min(percentage + 2.3, 103),
            f"{percentage:.1f}%",
            ha="center",
            va="bottom",
            fontsize=6.1,
            fontweight="bold" if index < 3 or index == len(rows) - 1 else "normal",
            color=TEXT,
        )

    output_base = Path(__file__).resolve().parent / "figure5_failure_pareto"
    fig.savefig(output_base.with_suffix(".png"), dpi=600, bbox_inches="tight", facecolor="white")
    fig.savefig(output_base.with_suffix(".svg"), bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
