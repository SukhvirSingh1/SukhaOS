import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from datetime import date, timedelta

def show_heatmap(db):
    # Get competion data
    history = db.get_task_history()
    
    # Count completion per day
    completion_counts = {}
    for title, difficulty, date_str in history:
        if date_str:
            completion_counts[date_str] = completion_counts.get(date_str, 0) + 1
            
            
    #  Build 365-day grid
    today = date.today()
    start = today - timedelta(days=364)
    
    start = start - timedelta(days=start.weekday())
    
    nums_weeks = 53
    grid = np.zeros((7, nums_weeks))
    week_labels = []
    month_positions = {}
    
    current = start
    for week in range(nums_weeks):
        if current.day <= 7:
            month_positions[week] = current.strftime("%b")
            
        for day in range(7):
            date_str = current.isoformat()
            count = completion_counts.get(date_str, 0)
            
            if start <= current <= today:
                grid[day][week] = count
            else:
                grid[day][week] = -1
                
            
            current += timedelta(days=1)
    week_start = current - timedelta(days=7)
    if week_start.day <= 7:
        month_positions[week] = week_start.strftime("%b")
    
    # Plot
    fig, ax = plt.subplots(figsize = (18, 4))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")
    
    colors = ["#161b22","#0e4429","#006d32","#26a641","#39d353"]
    
    cell_size = 0.9
    for week in range(nums_weeks):
        for day in range(7):
            val = grid[day][week]
            
            if val < 0:
                color = "#0d1117"
            elif val == 0:
                color = colors[0]
            elif val == 1:
                color = colors[1]
            elif val == 2:
                color = colors[2]
            elif val == 3:
                color = colors[3]
            else:
                color = colors[4]
                
            rect = mpatches.FancyBboxPatch(
                (week, 6 - day),
                cell_size, cell_size,
                boxstyle="round,pad=0.05",
                linewidth =0,
                facecolor=color
            )
            ax.add_patch(rect)
            
            
            
        # Month Labels
        
    for week, month in month_positions.items():
        ax.text(week + 0.4, 7.6, month,
                color="#8b949e", fontsize=8,
                ha="center", va="center",
                fontfamily="monospace")
        
        
    day_labels = ["Mon", "", "Wed", "", "fri", "", "Sun"]
    for i, label in enumerate(day_labels):
        if label:
            ax.text(-1, 6.5 - i, label,
                    color="#8b949e", fontsize=8,
                    ha="right", va="center",
                    fontfamily="monospace")
            
    total = sum(completion_counts.values())
    ax.set_title(
        f"Habil Tracker - {total} task comletions in the last year",
        color="#e6edf3",
        fontsize=13,
        fontfamily="monospace",
        pad=20
    )   
                
    legend_x = nums_weeks - 6
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
            color="#8b949e", fontsize=8, va="center", fontfamily="monospace")
    
    # axes cleanup
    ax.set_xlim(-2, nums_weeks + 1)
    ax.set_ylim(-2, 9)
    ax.axis("off")
    
    plt.tight_layout()
    plt.show()