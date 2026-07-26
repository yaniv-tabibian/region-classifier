"""Optional live visualisation (requires the ``viz`` extra: matplotlib).

Draws the pasture, the two regions, and the moving sensor coloured by the
classifier's live decision. The classifier still consumes only the two getters;
the true position is used solely to place the dot on screen.
"""

from __future__ import annotations

from pathlib import Path

from .config import SimConfig
from .geometry import Circle, Polygon, Rectangle
from .simulator import build

_COLOR = {"In A": "#1565C0", "In B": "#2E7D32", "Outside": "#9E9E9E"}


def _add_shape(ax, shape, face):
    import matplotlib.patches as mp

    if isinstance(shape, Circle):
        ax.add_patch(
            mp.Circle(
                (shape.cx, shape.cy),
                shape.r,
                facecolor=face,
                edgecolor="black",
                alpha=0.35,
            )
        )
    elif isinstance(shape, Rectangle):
        ax.add_patch(
            mp.Rectangle(
                (shape.cx - shape.w / 2, shape.cy - shape.h / 2),
                shape.w,
                shape.h,
                facecolor=face,
                edgecolor="black",
                alpha=0.35,
            )
        )
    elif isinstance(shape, Polygon):
        ax.add_patch(
            mp.Polygon(
                shape.vertices,
                closed=True,
                facecolor=face,
                edgecolor="black",
                alpha=0.35,
            )
        )


def _figure(config: SimConfig):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 7))
    xmin, ymin, xmax, ymax = config.pasture
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_aspect("equal")
    _add_shape(ax, config.region_a, "#90CAF9")
    _add_shape(ax, config.region_b, "#A5D6A7")
    ax.text(*config.region_a.centroid, "A", ha="center", fontsize=14, weight="bold")
    ax.text(*config.region_b.centroid, "B", ha="center", fontsize=14, weight="bold")
    (dot,) = ax.plot([], [], marker="o", markersize=12, color="#9E9E9E")
    title = ax.set_title("")
    return fig, ax, dot, title


def _frames(config: SimConfig, n_steps: int):
    _field, sensor, clf = build(config)
    for _ in range(n_steps):
        sensor.step(config.dt)
        label = clf.update(sensor.get_dist_a(), sensor.get_dist_b())
        x, y = sensor.position()
        yield x, y, label


def run_live(config: SimConfig, save_gif: str | Path | None = None) -> None:
    import matplotlib

    if save_gif is not None:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, PillowWriter

    fig, ax, dot, title = _figure(config)
    n_steps = int(round(config.duration_s / config.dt))
    gen = _frames(config, n_steps)

    def update(_):
        try:
            x, y, label = next(gen)
        except StopIteration:
            return dot, title
        dot.set_data([x], [y])
        dot.set_color(_COLOR[label])
        title.set_text(f"live classification:  {label}")
        return dot, title

    interval = max(1, int(config.dt * 1000))
    anim = FuncAnimation(
        fig, update, frames=n_steps, interval=interval, blit=False, repeat=False
    )
    if save_gif is not None:
        anim.save(str(save_gif), writer=PillowWriter(fps=int(1 / config.dt)))
        plt.close(fig)
    else:
        plt.show()
