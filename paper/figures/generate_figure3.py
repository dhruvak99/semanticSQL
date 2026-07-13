from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

cache_root = Path(tempfile.gettempdir()) / "semanticsql_figure_cache"
cache_root.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(cache_root / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(cache_root / "xdg"))

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


BLUE = "#4E79A7"
GREEN = "#59A14F"
RED = "#E15759"
GRID = "#E8E8E8"
TEXT = "#2F2F2F"
MUTED = "#666666"
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
            "xtick.labelsize": 7.2,
            "ytick.labelsize": 7.5,
            "axes.linewidth": 0.5,
            "savefig.dpi": 600,
            "patch.antialiased": True,
            "lines.antialiased": True,
        }
    )


def load_category_accuracy() -> list[tuple[str, float, int, int]]:
    root = Path(__file__).resolve().parents[2]
    with (root / "results" / "evaluation_summary.json").open("r", encoding="utf-8") as handle:
        summary = json.load(handle)

    category_accuracy = summary.get("overall", summary).get("accuracy_by_category", {})
    rows = [
        (
            category.replace("_", " "),
            float(values["accuracy"]),
            int(values["passed"]),
            int(values["total"]),
        )
        for category, values in category_accuracy.items()
    ]
    return sorted(rows, key=lambda item: item[1], reverse=True)


def add_rounded_barh(ax: plt.Axes, y_center: float, width: float, height: float, color: str) -> None:
    radius = height / 2
    bar = FancyBboxPatch(
        (0, y_center - height / 2),
        width,
        height,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        linewidth=0,
        facecolor=color,
        antialiased=True,
        mutation_aspect=1,
    )
    ax.add_patch(bar)


def style_axes(ax: plt.Axes) -> None:
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_linewidth(0.5)
        ax.spines[spine].set_color(AXIS)
    ax.tick_params(axis="both", length=3.4, width=0.5, color=AXIS, pad=4)
    ax.xaxis.grid(True, color=GRID, linewidth=0.5)
    ax.set_axisbelow(True)


def main() -> None:
    configure_style()
    rows = load_category_accuracy()
    accuracies = [row[1] for row in rows]
    y_positions = list(range(len(rows)))

    colors = []
    for index in range(len(rows)):
        if index < 3:
            colors.append(GREEN)
        elif index >= len(rows) - 3:
            colors.append(RED)
        else:
            colors.append(BLUE)

    fig_height = max(3.4, 0.29 * len(rows) + 0.6)
    fig, ax = plt.subplots(figsize=(3.55, fig_height), constrained_layout=True)
    bar_height = 0.74

    for y_position, (_, accuracy, _, _), color in zip(y_positions, rows, colors):
        add_rounded_barh(ax, y_position, accuracy, bar_height, color)

    ax.set_yticks(y_positions)
    ax.set_yticklabels([row[0] for row in rows])
    ax.invert_yaxis()
    ax.set_xlabel("Accuracy (%)", labelpad=8)
    ax.set_xlim(0, max(100, max(accuracies) + 18))
    ax.set_ylim(len(rows) - 0.35, -0.65)
    style_axes(ax)

    for y_position, (_, accuracy, passed, total) in zip(y_positions, rows):
        label_x = accuracy + 1.65
        ax.text(
            label_x,
            y_position - 0.11,
            f"{accuracy:.2f}%",
            va="center",
            ha="left",
            fontsize=7.6,
            fontweight="bold",
            color=TEXT,
        )
        ax.text(
            label_x,
            y_position + 0.16,
            f"({passed}/{total})",
            va="center",
            ha="left",
            fontsize=6.1,
            color=MUTED,
        )

    output_base = Path(__file__).resolve().parent / "figure3_sql_category_accuracy"
    fig.savefig(output_base.with_suffix(".png"), dpi=600, bbox_inches="tight", facecolor="white")
    fig.savefig(output_base.with_suffix(".svg"), bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
