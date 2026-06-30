"""Server-rendered report images for the chat fast layer (TZ §11).

Premium light style, no emoji. A donut chart is present in EVERY report.
"""
from __future__ import annotations

import io
from datetime import date

import matplotlib

matplotlib.use("Agg")
import matplotlib.font_manager as fm  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle  # noqa: E402

from app.core.currencies import fmt_amount  # noqa: E402

BG = "#FFFFFF"
INK = "#1A1A1A"
SUB = "#8A8F98"
GOLD = "#C9A227"
GREEN = "#34C759"
RED = "#FF3B30"
PALETTE = ["#C9A227", "#34C759", "#5AC8FA", "#AF52DE", "#FF9500", "#FF2D55",
           "#30B0C7", "#007AFF", "#8E8E93", "#FFCC00"]

TITLES = {
    "today": {"ru": "Сегодня", "en": "Today"},
    "now": {"ru": "Сегодня", "en": "Today"},
    "week": {"ru": "Эта неделя", "en": "This week"},
    "month": {"ru": "Этот месяц", "en": "This month"},
}
LBL = {
    "income": {"ru": "Доход", "en": "Income"},
    "expense": {"ru": "Расход", "en": "Expense"},
    "net": {"ru": "Итог", "en": "Net"},
    "nodata": {"ru": "За этот период операций нет", "en": "No entries for this period"},
}


def _font():
    for name in ("SF Pro Display", "Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"):
        try:
            fm.findfont(name, fallback_to_default=False)
            return name
        except Exception:
            continue
    return "DejaVu Sans"


def render_report(
    *, period: str, lang: str, currency: str,
    income: float, expense: float, categories: list[dict],
) -> bytes:
    plt.rcParams["font.family"] = _font()
    fig = plt.figure(figsize=(6.4, 5.0), dpi=200)
    fig.patch.set_facecolor(BG)

    title = TITLES.get(period, {"ru": "Отчёт", "en": "Report"})[("ru" if lang == "ru" else "en")]
    fig.text(0.08, 0.92, "N E B A N K", fontsize=13, color=GOLD, weight="bold")
    fig.text(0.08, 0.86, title, fontsize=20, color=INK, weight="bold")

    # figures row
    net = income - expense
    cols = [
        (LBL["expense"][("ru" if lang == "ru" else "en")], fmt_amount(expense, currency), RED),
        (LBL["income"][("ru" if lang == "ru" else "en")], fmt_amount(income, currency), GREEN),
        (LBL["net"][("ru" if lang == "ru" else "en")], fmt_amount(net, currency), INK),
    ]
    for i, (label, value, color) in enumerate(cols):
        x = 0.08 + i * 0.30
        fig.text(x, 0.76, label, fontsize=10.5, color=SUB)
        fig.text(x, 0.71, value, fontsize=13.5, color=color, weight="bold")

    ax = fig.add_axes([0.06, 0.06, 0.52, 0.56])
    ax.set_facecolor(BG)
    if categories and expense > 0:
        sizes = [c["total"] for c in categories[:8]]
        colors = [c.get("color") or PALETTE[i % len(PALETTE)] for i, c in enumerate(categories[:8])]
        ax.pie(sizes, colors=colors, startangle=90, counterclock=False,
               wedgeprops={"width": 0.36, "edgecolor": BG, "linewidth": 2})
        ax.add_artist(Circle((0, 0), 0.64, color=BG))
        ax.text(0, 0.06, fmt_amount(expense, currency), ha="center", va="center",
                fontsize=13, color=INK, weight="bold")
        ax.text(0, -0.12, LBL["expense"][("ru" if lang == "ru" else "en")], ha="center", va="center",
                fontsize=10, color=SUB)
    else:
        ax.text(0, 0, LBL["nodata"][("ru" if lang == "ru" else "en")], ha="center", va="center",
                fontsize=12, color=SUB)
        ax.axis("off")
    ax.set_aspect("equal")
    ax.axis("off")

    # legend / top categories
    ly = 0.56
    for i, c in enumerate(categories[:6]):
        color = c.get("color") or PALETTE[i % len(PALETTE)]
        name = c["name"] if len(c["name"]) <= 13 else c["name"][:12] + "…"
        fig.text(0.63, ly, "●", fontsize=11, color=color)
        fig.text(0.655, ly, name, fontsize=10, color=INK)
        fig.text(0.995, ly, fmt_amount(c["total"], currency), fontsize=10, color=SUB, ha="right")
        ly -= 0.075

    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=BG, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    buf.seek(0)
    return buf.read()
