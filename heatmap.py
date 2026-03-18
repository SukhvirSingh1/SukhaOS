"""
heatmap.py
==========
Renders a GitHub-style habit heatmap for SukhaOS.
Shows task completion frequency over the past 365 days
as a colour-coded grid — darker green = more completions.

Called from layout.py via the Habit Map button.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from datetime import date, timedelta


def show_heatmap(db):
    """
    Fetch task history from the database and render a
    52-week contribution heatmap using matplotlib.

    The grid is structured as:
        - 7 rows  → days of the week (Monday at top, Sunday at bottom)
        - 53 cols → weeks over the past year

    Cell colour intensity is based on how many tasks were completed that day:
        0 completions → dark background
        1             → dark green
        2             → medium green
        3             → bright green
        4+            → brightest green

    Args:
        db: An instance of the Database class from database.py.
    """

    # --- Step 1: Fetch and count completions per day ---
    history = db.get_task_history()  # returns [(title, difficulty, date_str), ...]

    completion_counts = {}
    for title, difficulty, date_str in history:
        if date_str:
            # Increment count for this date
            completion_counts[date_str] = completion_counts.get(date_str, 0) + 1

    # --- Step 2: Build the 7x53 grid ---
    today = date.today()
    start = today - timedelta(days=364)

    # Align start to Monday so columns are clean calendar weeks
    start = start - timedelta(days=start.weekday())

    num_weeks = 53
    grid = np.zeros((7, num_weeks))  # 7 rows (days), 53 cols (weeks)
    month_positions = {}             # {week_index: "Jan"} for month labels

    current = start
    for week in range(num_weeks):

        # Check month label once per week (on Monday, the first day of the week)
        if current.day <= 7:
            month_positions[week] = current.strftime("%b")

        for day in range(7):
            date_str = current.isoformat()
            count = completion_counts.get(date_str, 0)

            if start <= current <= today:
                grid[day][week] = count   # real data
            else:
                grid[day][week] = -1      # out of range — rendered invisible

            current += timedelta(days=1)

    # --- Step 3: Set up the plot ---
    fig, ax = plt.subplots(figsize=(18, 4))
    fig.patch.set_facecolor("#0d1117")   # GitHub dark background
    ax.set_facecolor("#0d1117")

    # Five shades from empty → 4+ completions
    colors = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
    cell_size = 0.9  # slightly smaller than 1 to leave a small gap between cells

    # --- Step 4: Draw each cell as a rounded rectangle ---
    for week in range(num_weeks):
        for day in range(7):
            val = grid[day][week]

            if val < 0:
                color = "#0d1117"    # invisible — out of date range
            elif val == 0:
                color = colors[0]   # empty day
            elif val == 1:
                color = colors[1]
            elif val == 2:
                color = colors[2]
            elif val == 3:
                color = colors[3]
            else:
                color = colors[4]   # 4+ completions

            # 6 - day flips the grid so Monday is at the top
            rect = mpatches.FancyBboxPatch(
                (week, 6 - day),
                cell_size, cell_size,
                boxstyle="round,pad=0.05",
                linewidth=0,
                facecolor=color
            )
            ax.add_patch(rect)

    # --- Step 5: Month labels above each new month ---
    for week, month in month_positions.items():
        ax.text(week + 0.4, 7.6, month,
                color="#8b949e", fontsize=8,
                ha="center", va="center",
                fontfamily="monospace")

    # --- Step 6: Day labels on the left (Mon, Wed, Fri only to avoid crowding) ---
    day_labels = ["Mon", "", "Wed", "", "Fri", "", "Sun"]
    for i, label in enumerate(day_labels):
        if label:
            ax.text(-1, 6.5 - i, label,
                    color="#8b949e", fontsize=8,
                    ha="right", va="center",
                    fontfamily="monospace")

    # --- Step 7: Title showing total completions ---
    total = sum(completion_counts.values())
    ax.set_title(
        f"Habit Tracker — {total} task completions in the last year",
        color="#e6edf3",
        fontsize=13,
        fontfamily="monospace",
        pad=20
    )

    # --- Step 8: Colour legend (Less → More) ---
    legend_x = num_weeks - 6
    ax.text(legend_x - 1, -0.8, "Less",
            color="#8b949e", fontsize=8,
            va="center", fontfamily="monospace")

    for i, color in enumerate(colors):
        rect = mpatches.FancyBboxPatch(
            (legend_x + i, -1),
            cell_size, cell_size,
            boxstyle="round,pad=0.05",
            linewidth=0,
            facecolor=color
        )
        ax.add_patch(rect)

    ax.text(legend_x + len(colors) + 0.2, -0.8, "More",
            color="#8b949e", fontsize=8,
            va="center", fontfamily="monospace")

    # --- Step 9: Clean up axes and show ---
    ax.set_xlim(-2, num_weeks + 1)
    ax.set_ylim(-2, 9)
    ax.axis("off")   # hide default axes, ticks, and borders

    plt.tight_layout()
    plt.show()