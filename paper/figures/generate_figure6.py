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
ORANGE = "#F28E2B"
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
            "xtick.labelsize": 7.8,
            "ytick.labelsize": 7.3,
            "axes.linewidth": 0.5,
            "savefig.dpi": 600,
            "patch.antialiased": True,
            "lines.antialiased": True,
        }
    )


def load_difficulty_accuracy() -> dict[str, dict[str, float]]:
    root = Path(__file__).resolve().parents[2]
    with (root / "results" / "evaluation_summary.json").open("r", encoding="utf-8") as handle:
        summary = json.load(handle)
    return summary.get("overall", summary).get("accuracy_by_difficulty", {})


def add_rounded_bar(ax: plt.Axes, x_center: float, height: float, width: float, color: str) -> None:
    bar = FancyBboxPatch(
        (x_center - width / 2, 0),
        width,
        height,
        boxstyle=f"round,pad=0,rounding_size={width * 0.2}",
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
    difficulty_accuracy = load_difficulty_accuracy()
    difficulties = ["easy", "medium", "hard"]
    labels = ["Easy", "Medium", "Hard"]
    values = [float(difficulty_accuracy[difficulty]["accuracy"]) for difficulty in difficulties]
    colors = [BLUE, GREEN, ORANGE]
    x_positions = list(range(len(labels)))

    fig, ax = plt.subplots(figsize=(3.55, 2.55), constrained_layout=True)
    bar_width = 0.68
    for x_position, value, color in zip(x_positions, values, colors):
        add_rounded_bar(ax, x_position, value, bar_width, color)

    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Accuracy (%)", labelpad=8)
    ax.set_xlim(-0.6, len(labels) - 0.4)
    ax.set_ylim(0, 70)
    style_axes(ax)

    for x_position, value in zip(x_positions, values):
        ax.text(
            x_position,
            value + 1.7,
            f"{value:.2f}%",
            ha="center",
            va="bottom",
            fontsize=8,
            fontweight="bold",
            color=TEXT,
        )

    output_base = Path(__file__).resolve().parent / "figure6_difficulty_accuracy"
    fig.savefig(output_base.with_suffix(".png"), dpi=600, bbox_inches="tight", facecolor="white")
    fig.savefig(output_base.with_suffix(".svg"), bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
