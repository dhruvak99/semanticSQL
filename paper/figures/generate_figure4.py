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
from matplotlib.patches import FancyBboxPatch, Patch


BLUE = "#4E79A7"
GREEN = "#59A14F"
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
            "xtick.labelsize": 7.3,
            "ytick.labelsize": 7.3,
            "legend.fontsize": 7.4,
            "axes.linewidth": 0.5,
            "savefig.dpi": 600,
            "patch.antialiased": True,
            "lines.antialiased": True,
        }
    )


def load_cache_comparison() -> dict[str, float]:
    root = Path(__file__).resolve().parents[2]
    with (root / "results" / "cache_comparison.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def add_rounded_bar(ax: plt.Axes, x_center: float, height: float, width: float, color: str) -> None:
    bar = FancyBboxPatch(
        (x_center - width / 2, 0),
        width,
        height,
        boxstyle=f"round,pad=0,rounding_size={width * 0.22}",
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


def annotate_pair(ax: plt.Axes, x_positions: list[float], values: list[float], y_pad: float, decimals: int = 2) -> None:
    for x_position, value in zip(x_positions, values):
        ax.text(
            x_position,
            value + y_pad,
            f"{value:.{decimals}f}",
            ha="center",
            va="bottom",
            fontsize=7.2,
            fontweight="bold",
            color=TEXT,
        )


def draw_grouped_bars(
    ax: plt.Axes,
    labels: list[str],
    cold_values: list[float],
    warm_values: list[float],
    ylabel: str,
    ylim: float,
    decimals: int,
) -> None:
    group_positions = list(range(len(labels)))
    width = 0.28
    cold_positions = [position - width / 1.75 for position in group_positions]
    warm_positions = [position + width / 1.75 for position in group_positions]

    for x_position, value in zip(cold_positions, cold_values):
        add_rounded_bar(ax, x_position, value, width, BLUE)
    for x_position, value in zip(warm_positions, warm_values):
        add_rounded_bar(ax, x_position, value, width, GREEN)

    ax.set_xticks(group_positions)
    ax.set_xticklabels(labels)
    ax.set_ylabel(ylabel, labelpad=8)
    ax.set_xlim(-0.55, len(labels) - 0.45)
    ax.set_ylim(0, ylim)
    style_axes(ax)
    annotate_pair(ax, cold_positions, cold_values, ylim * 0.025, decimals)
    annotate_pair(ax, warm_positions, warm_values, ylim * 0.025, decimals)


def main() -> None:
    configure_style()
    comparison = load_cache_comparison()

    fig, (ax_top, ax_bottom) = plt.subplots(
        2,
        1,
        figsize=(3.55, 3.85),
        constrained_layout=True,
        gridspec_kw={"height_ratios": [1, 1]},
    )

    draw_grouped_bars(
        ax_top,
        ["Accuracy", "Cache hit rate"],
        [float(comparison["cold_cache_accuracy"]), float(comparison["cold_cache_hit_rate"])],
        [float(comparison["warm_cache_accuracy"]), float(comparison["warm_cache_hit_rate"])],
        "Percent (%)",
        112,
        2,
    )
    draw_grouped_bars(
        ax_bottom,
        ["Average Latency"],
        [float(comparison["cold_cache_average_latency_ms"])],
        [float(comparison["warm_cache_average_latency_ms"])],
        "Latency (ms)",
        max(float(comparison["cold_cache_average_latency_ms"]), float(comparison["warm_cache_average_latency_ms"])) * 1.22,
        1,
    )

    legend_handles = [
        Patch(facecolor=BLUE, edgecolor="none", label="Cold Cache"),
        Patch(facecolor=GREEN, edgecolor="none", label="Warm Cache"),
    ]
    fig.legend(
        handles=legend_handles,
        loc="upper center",
        ncols=2,
        frameon=False,
        bbox_to_anchor=(0.5, 1.035),
        handlelength=1.4,
        columnspacing=1.6,
    )

    output_base = Path(__file__).resolve().parent / "figure4_cache_performance"
    fig.savefig(output_base.with_suffix(".png"), dpi=600, bbox_inches="tight", facecolor="white")
    fig.savefig(output_base.with_suffix(".svg"), bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
