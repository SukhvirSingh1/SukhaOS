"""
layout.py
=========
Defines the SkillUI class — the entire user interface for SukhaOS.
Responsible for building all frames, rendering task cards,
handling popups, and refreshing the UI after game state changes.

UI is built with tkinter and organised into three main zones:
    - Top Left  : Skills panel (scrollable, with add/delete)
    - Top Right : Player info (level, gold, XP bar, action buttons)
    - Bottom    : Task area (sidebar navigation + main content container)

The content container (task_container) is reused across all screens —
show_tasks(), show_stats(), show_shop(), show_history() all clear and
redraw it. This avoids creating multiple frames that fight for space.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from heatmap import show_heatmap


# Reward values per task period — used when calculating task rewards on creation
PERIOD_REWARDS = {
    "daily":   {"gold": 20,  "oxp": 20,  "sxp": 10},
    "weekly":  {"gold": 50,  "oxp": 60,  "sxp": 25},
    "monthly": {"gold": 120, "oxp": 150, "sxp": 60},
    "yearly":  {"gold": 500, "oxp": 500, "sxp": 200}
}


class SkillUI:
    """
    Main UI class for SukhaOS.
    All tkinter widgets are created and managed here.
    Communicates with the database and game engine via self.db and self.engine.
    """

    def __init__(self, root, db, engine):
        """
        Initialise the UI with references to the database and game engine.

        Args:
            root (tk.Tk): The main application window.
            db: Database instance from database.py.
            engine: GameEngine instance from game_engine.py.
        """
        self.root = root
        self.db = db
        self.engine = engine
        self.current_period = "daily"   # tracks which period tab is active
        self.build_ui()

    # -------------------------------------------------------------------------
    # UI CONSTRUCTION
    # -------------------------------------------------------------------------

    def build_ui(self):
        """
        Build the full application layout.
        Called once during __init__. Creates all three main zones:
        skills panel (top left), player info (top right), task area (bottom).
        """

        # Root grid: 2 rows (top/bottom), 2 cols (left/right)
        self.root.rowconfigure(0, weight=3, minsize=200)   # top zone — larger
        self.root.rowconfigure(1, weight=1, minsize=150)   # bottom zone — smaller
        self.root.columnconfigure(0, weight=3)   # left column — 30%
        self.root.columnconfigure(1, weight=7)   # right column — 70%

        # ── TOP LEFT: Skills Panel ────────────────────────────────────────────
        chrctr_frame = tk.Frame(self.root, bg="#00254d", bd=2, relief="ridge")
        chrctr_frame.grid(row=0, column=0, sticky="nsew")

        tk.Label(chrctr_frame,
                 text="Skills",
                 bg="#00254d",
                 fg="#E0E0E0",
                 font=("Arial", 14, "bold")
                 ).grid(row=0, column=0, pady=(20, 10))

        # Canvas + scrollbar for scrollable skill list
        # Canvas is the visible viewport; skills_container is the full-height frame inside it
        self.skills_canvas = tk.Canvas(chrctr_frame, bg="#00254d", highlightthickness=0)
        self.skills_canvas.grid(row=1, column=0, sticky="nsew", padx=(10, 0))

        skills_scrollbar = ttk.Scrollbar(chrctr_frame, orient="vertical",
                                         command=self.skills_canvas.yview)
        skills_scrollbar.grid(row=1, column=1, sticky="ns")
        self.skills_canvas.configure(yscrollcommand=skills_scrollbar.set)

        self.skills_container = tk.Frame(self.skills_canvas, bg="#00254d")
        self.skills_canvas_window = self.skills_canvas.create_window(
            (0, 0), window=self.skills_container, anchor="nw"
        )

        # Keep scroll region in sync with content height
        self.skills_container.bind("<Configure>", lambda e: self.skills_canvas.configure(
            scrollregion=self.skills_canvas.bbox("all")
        ))
        # Keep content width in sync with canvas width
        self.skills_canvas.bind("<Configure>", lambda e: self.skills_canvas.itemconfig(
            self.skills_canvas_window, width=e.width
        ))
        # Mouse wheel scrolling
        self.skills_canvas.bind("<MouseWheel>", lambda e: self.skills_canvas.yview_scroll(
            int(-1 * (e.delta / 120)), "units"
        ))

        tk.Button(chrctr_frame,
                  text="+ Add Skill",
                  bg="#003366",
                  fg="#E0E0E0",
                  font=("Arial", 9, "bold"),
                  command=self.open_add_skill_popup
                  ).grid(row=2, column=0, columnspan=2, pady=(0, 10))

        chrctr_frame.rowconfigure(1, weight=1)
        chrctr_frame.rowconfigure(2, weight=0)
        chrctr_frame.columnconfigure(0, weight=1)
        chrctr_frame.columnconfigure(1, weight=0)

        # ── TOP RIGHT: Player Info ────────────────────────────────────────────
        info_frame = tk.Frame(self.root, bg="#00254d", bd=2, relief="ridge")
        info_frame.grid(row=0, column=1, sticky="nsew")

        # Row layout for info_frame:
        # 0 - character level label
        # 1 - gold label
        # 2 - add task button
        # 3 - XP progress bar
        # 4 - stats button
        # 5 - habit map button
        # 6 - empty spacer (weight=1 pushes all content upward)
        for i in range(6):
            info_frame.rowconfigure(i, weight=0)
        info_frame.rowconfigure(6, weight=1)    # spacer
        info_frame.columnconfigure(0, weight=1)

        self.level_label = tk.Label(info_frame,
                                    text="Character lvl 1",
                                    bg="#00254d",
                                    fg="#E0E0E0",
                                    font=("Arial", 16, "bold"))
        self.level_label.grid(row=0, column=0, pady=20)

        self.gold_label = tk.Label(info_frame,
                                   text="Gold: 0",
                                   bg="#00254d",
                                   fg="gold",
                                   font=("Arial", 12))
        self.gold_label.grid(row=1, column=0, pady=(0, 15))

        tk.Button(info_frame,
                  text="Add Task",
                  bg="#003366",
                  fg="#E0E0E0",
                  font=("Arial", 12, "bold"),
                  command=self.open_add_task_popup
                  ).grid(row=2, column=0, pady=(0, 15))

        self.xp_bar = ttk.Progressbar(info_frame,
                                      orient="horizontal",
                                      mode="determinate",
                                      style="XP.Horizontal.TProgressbar")
        self.xp_bar.grid(row=3, column=0, padx=40, sticky="ew", pady=(10, 2))

        tk.Button(info_frame,
                  text="Stats",
                  bg="#003366",
                  fg="white",
                  font=("Arial", 11, "bold"),
                  command=self.show_stats
                  ).grid(row=4, column=0, pady=15)

        tk.Button(info_frame,
                  text="Habit Map",
                  bg="#003366",
                  fg="white",
                  font=("Arial", 11, "bold"),
                  command=self.show_heatmap
                  ).grid(row=5, column=0, pady=(0, 15))

        # ── BOTTOM: Task Area ─────────────────────────────────────────────────
        tasks_frame = tk.Frame(self.root, bg="#001833", bd=2, relief="ridge")
        tasks_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        tasks_frame.rowconfigure(0, weight=1)
        tasks_frame.columnconfigure(0, weight=0)   # sidebar — fixed width
        tasks_frame.columnconfigure(1, weight=1)   # content — expands

        # Sidebar navigation buttons
        side_bar = tk.Frame(tasks_frame, bg="#003366")
        side_bar.grid(row=0, column=0, sticky="ns", padx=15)

        # Period buttons (D/W/M/Y) — rows 0-3
        self.bottons = {}
        btn_names  = ["daily", "weekly", "monthly", "yearly"]
        btn_labels = ["D", "W", "M", "Y"]

        for i, (name, label) in enumerate(zip(btn_names, btn_labels)):
            btn = tk.Button(side_bar,
                            text=label,
                            bg="#003366",
                            fg="#E0E0E0",
                            font=("Arial", 10, "bold"),
                            command=lambda n=name: self.switch_menu(n))
            btn.grid(row=i, column=0, pady=10)
            self.bottons[name] = btn

        # Log button — row 4
        tk.Button(side_bar,
                  text="Log",
                  bg="#003366",
                  fg="white",
                  font=("Arial", 10, "bold"),
                  command=self.show_history
                  ).grid(row=4, column=0, pady=10)

        # Shop button — row 5
        tk.Button(side_bar,
                  text="Shop",
                  bg="#003366",
                  fg="white",
                  font=("Arial", 10, "bold"),
                  command=self.show_shop
                  ).grid(row=5, column=0, pady=10)

        # Main content area — all screens render inside this frame
        self.task_container = tk.Frame(tasks_frame, bg="#001833")
        self.task_container.grid(row=0, column=1, sticky="nsew", padx=20)

        for i in range(2):
            self.task_container.grid_rowconfigure(i, weight=1)
            self.task_container.grid_columnconfigure(i, weight=1)

        # XP label (shows "current / required OXP")
        self.xp_label = tk.Label(tasks_frame,
                                 text="0 / 100 OXP",
                                 bg="#001833",
                                 font=("Arial", 9, "bold"),
                                 fg="#aaaaaa")
        self.xp_label.grid(row=3, column=0)

        # Progress bar style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TProgressbar",
                        troughcolor="#001833",
                        background="#00ccff",
                        thickness=18,
                        bordercolor="#001833",
                        lightcolor="#00ccff",
                        darkcolor="#00ccff")

        # Initial render
        self.switch_menu("daily")
        self.refresh_player_ui()
        self.refresh_skill_ui()

    # -------------------------------------------------------------------------
    # SKILL PANEL
    # -------------------------------------------------------------------------

    def refresh_skill_ui(self):
        """
        Clear and redraw the skills panel.
        Called after any skill change (add, delete, level up, XP gain).
        Each skill gets a label showing name, level, XP progress,
        and a small red 'x' delete button.
        """
        for widget in self.skills_container.winfo_children():
            widget.destroy()

        skills = self.db.get_all_skills()

        if not skills:
            tk.Label(self.skills_container,
                     text="No skills yet",
                     bg="#00254d",
                     fg="#E0E0E0",
                     font=("Arial", 10)
                     ).grid(row=0, column=0)
            return

        for index, skill in enumerate(skills):
            required = self.get_required_sxp(skill["level"])
            skill_text = f"{skill['name']} | Lv {skill['level']}  {skill['xp']} / {required}"

            tk.Label(self.skills_container,
                     text=skill_text,
                     bg="#00254d",
                     fg="#E0E0E0",
                     anchor="w",
                     font=("Arial", 10)
                     ).grid(row=index, column=0, sticky="ew", pady=3)

            # Delete button — small red x, no border, hand cursor
            tk.Button(self.skills_container,
                      text="x",
                      bg="#00254d",
                      fg="#ff4444",
                      font=("Arial", 8, "bold"),
                      bd=0,
                      cursor="hand2",
                      command=lambda n=skill["name"]: self.delete_skill(n)
                      ).grid(row=index, column=1, padx=(5, 0), pady=3)

        self.skills_container.columnconfigure(0, weight=1)
        self.skills_container.columnconfigure(1, weight=0)

    def delete_skill(self, skill_name):
        """
        Ask for confirmation then delete a skill.
        Existing task rewards linked to the skill are not removed.

        Args:
            skill_name (str): Name of the skill to delete.
        """
        confirm = messagebox.askyesno(
            "Delete Skill",
            f"Delete '{skill_name}'? This won't affect existing tasks."
        )
        if confirm:
            self.db.delete_skill(skill_name)
            self.refresh_skill_ui()

    # -------------------------------------------------------------------------
    # TASK CARDS
    # -------------------------------------------------------------------------

    def create_task_card(self, row, col, task_id, title, description, status, streak, difficulty):
        """
        Render a single task card in the task container grid.
        Each card shows: title, description, status (clickable), streak, difficulty,
        and Edit / Delete buttons.

        Clicking the status label triggers task completion.

        Args:
            row (int): Grid row in task_container.
            col (int): Grid column in task_container.
            task_id (int): Task's database ID.
            title (str): Task title.
            description (str): Task description.
            status (str): 'Pending' or 'Completed'.
            streak (int): Current streak count.
            difficulty (str): 'Easy', 'Medium', or 'Hard'.
        """
        card = tk.Frame(self.task_container, bg="#003366", bd=0)
        card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")

        tk.Label(card, text=title, bg="#003366", fg="#E0E0E0",
                 font=("Arial", 12, "bold")
                 ).grid(row=0, column=1, sticky="w", padx=10, pady=(10, 0))

        tk.Label(card, text=description, bg="#003366", fg="#E0E0E0",
                 font=("Arial", 10)
                 ).grid(row=1, column=1, sticky="w", padx=10)

        # Status label — green if completed, orange if pending, clickable to complete
        status_color = "green" if status == "Completed" else "orange"
        status_label = tk.Label(card, text=status, bg="#003366", fg=status_color,
                                font=("Arial", 9, "italic"), cursor="hand2")
        status_label.grid(row=2, column=1, sticky="e", padx=10, pady=(5, 10))
        status_label.bind("<Button-1>", lambda e, tid=task_id: self.complete_task(tid))

        tk.Label(card, text=f"Streak: {streak}", bg="#003366", fg="orange",
                 font=("Arial", 9, "italic")
                 ).grid(row=0, column=2, padx=10)

        tk.Label(card, text=f"Difficulty: {difficulty}", bg="#003366", fg="#cccccc",
                 font=("Arial", 9)
                 ).grid(row=1, column=2)

        tk.Button(card, text="Edit", bg="#004080", fg="white", font=("Arial", 8),
                  command=lambda tid=task_id: self.open_edit_task_popup(tid)
                  ).grid(row=2, column=0, padx=10)

        tk.Button(card, text="Delete", bg="#800000", fg="white", font=("Arial", 8),
                  command=lambda tid=task_id: self.delete_task(tid)
                  ).grid(row=2, column=2, padx=10, pady=5)

    # -------------------------------------------------------------------------
    # MAIN SCREENS
    # -------------------------------------------------------------------------

    def show_tasks(self, period):
        """
        Render the task cards for the selected period.
        Clears the content container first, then draws:
        completion counter, progress bar, up to 4 task cards, and a graph button.

        Args:
            period (str): 'daily', 'weekly', 'monthly', or 'yearly'.
        """
        for widget in self.task_container.winfo_children():
            widget.destroy()

        # Reset all row/col weights before configuring for this screen
        for i in range(10):
            self.task_container.grid_rowconfigure(i, weight=0)
            self.task_container.grid_columnconfigure(i, weight=0)

        self.task_container.grid_rowconfigure(0, weight=0)
        self.task_container.grid_rowconfigure(1, weight=0)
        self.task_container.grid_rowconfigure(2, weight=1)   # task card rows expand
        self.task_container.grid_rowconfigure(3, weight=1)
        self.task_container.grid_columnconfigure(0, weight=1)
        self.task_container.grid_columnconfigure(1, weight=1)

        tasks = self.db.get_tasks_by_period(period)
        completed = sum(1 for t in tasks if t["status"] == "Completed")
        total = len(tasks)

        # Completion summary
        tk.Label(self.task_container,
                 text=f"{completed} / {total} tasks completed",
                 bg="#001833", fg="white", font=("Arial", 11, "bold")
                 ).grid(row=0, column=0, columnspan=2, pady=5)

        # Overall completion progress bar
        ttk.Progressbar(self.task_container,
                        length=250,
                        maximum=total if total > 0 else 1,
                        value=completed
                        ).grid(row=1, column=0, columnspan=2, pady=5)

        # Render up to 4 task cards in a 2x2 grid
        positions = [(2, 0), (2, 1), (3, 0), (3, 1)]
        for task, pos in zip(tasks, positions):
            self.create_task_card(
                pos[0], pos[1],
                task["id"], task["title"], task["description"],
                task["status"], task["streak"], task["difficulty"]
            )

        tk.Button(self.task_container,
                  text="Show Graph",
                  bg="#001833", fg="white",
                  command=self.show_task_graph
                  ).grid(row=4, column=1, pady=10)

    def show_stats(self):
        """
        Render the Stats screen showing character level, OXP, gold,
        skill progress bars, and achievement list.
        Replaces the task cards in the content container.
        """
        self.clear_content()

        for i in range(10):
            self.task_container.grid_rowconfigure(i, weight=0)
            self.task_container.grid_columnconfigure(i, weight=0)

        self.task_container.grid_rowconfigure(0, weight=0)
        self.task_container.grid_rowconfigure(1, weight=1)
        self.task_container.grid_columnconfigure(0, weight=1)
        self.task_container.grid_columnconfigure(1, weight=1)

        tk.Button(self.task_container,
                  text="<- Back", bg="#003366", fg="white",
                  command=lambda: self.switch_menu(self.current_period)
                  ).grid(row=0, column=0, sticky="w", pady=5)

        player = self.db.get_player()

        tk.Label(self.task_container, text="Character Stats",
                 bg="#001833", fg="white", font=("Arial", 16, "bold")
                 ).grid(row=0, column=0, columnspan=2, pady=10)

        tk.Label(self.task_container, text=f"Level: {player['level']}",
                 bg="#001833", fg="white"
                 ).grid(row=1, column=0, sticky="w", padx=20)

        tk.Label(self.task_container, text=f"OXP: {player['oxp']}",
                 bg="#001833", fg="white"
                 ).grid(row=2, column=0, sticky="w", padx=20)

        tk.Label(self.task_container, text=f"Gold: {player['gold']}",
                 bg="#001833", fg="white"
                 ).grid(row=3, column=0, sticky="w", padx=20)

        self.show_skill_stats()

        # Achievements section
        achievement = self.db.get_achievement()
        start_row = 15

        tk.Label(self.task_container, text="Achievements",
                 bg="#001833", fg="white", font=("Arial", 14, "bold")
                 ).grid(row=start_row, column=1, sticky="w", padx=20)

        row = start_row + 1
        for ach in achievement:
            color = "gold" if ach["unlocked"] else "#555555"
            tk.Label(self.task_container,
                     text=f"{ach['title']} - {ach['description']}",
                     bg="#001833", fg=color
                     ).grid(row=row, column=0, sticky="w", padx=20)
            row += 1

    def show_skill_stats(self):
        """
        Render skill name, level, and XP progress bars inside the stats screen.
        Called by show_stats() — uses task_container directly.
        Starts at row 5 to leave space for player stats above.
        """
        skills = self.db.get_all_skills()
        start_row = 5

        for index, skill in enumerate(skills):
            required = 50 + (skill["level"] - 1) * 25

            tk.Label(self.task_container,
                     text=f"{skill['name']} - Lv {skill['level']}",
                     bg="#001833", fg="white", font=("Arial", 11, "bold")
                     ).grid(row=start_row + index * 2, column=0, sticky="w", padx=20)

            ttk.Progressbar(self.task_container,
                            length=250, maximum=required, value=skill["xp"],
                            style="TProgressbar"
                            ).grid(row=start_row + index * 2 + 1, column=0,
                                   sticky="w", padx=20, pady=5)

    def show_shop(self):
        """
        Render the Skill Boost Shop screen.
        Lists all skills with a buy button for each.
        Costs 100 gold for +20 XP to the selected skill.
        """
        self.clear_content()

        tk.Label(self.task_container,
                 text="Skill Boost Shop",
                 bg="#001833", fg="white", font=("Arial", 16, "bold")
                 ).grid(row=0, column=0, pady=10)

        skills = self.db.get_all_skills()
        row = 1

        for skill in skills:
            tk.Label(self.task_container,
                     text=f"{skill['name']} (Lvl {skill['level']})",
                     bg="#001833", fg="white"
                     ).grid(row=row, column=0, sticky="w")

            tk.Button(self.task_container,
                      text="Buy +20 XP (100 GOLD)",
                      command=lambda s=skill["name"]: self.buy_skill(s)
                      ).grid(row=row, column=1, padx=10)
            row += 1

        tk.Button(self.task_container,
                  text="<- Back",
                  command=lambda: self.switch_menu(self.current_period)
                  ).grid(row=row + 1, column=0, pady=20)

    def show_history(self):
        """
        Render the Task History Log screen.
        Shows a scrollable table of all completed tasks with date,
        title, and colour-coded difficulty.
        Pulls data from the task_history table via db.get_task_history().
        """
        self.clear_content()

        for i in range(10):
            self.task_container.grid_rowconfigure(i, weight=0)
            self.task_container.grid_columnconfigure(i, weight=0)

        self.task_container.grid_rowconfigure(0, weight=0)
        self.task_container.grid_rowconfigure(1, weight=1)
        self.task_container.grid_columnconfigure(0, weight=1)
        self.task_container.grid_columnconfigure(1, weight=1)
        self.task_container.grid_columnconfigure(2, weight=0)   # scrollbar column

        tk.Label(self.task_container,
                 text="Task History",
                 bg="#001833", fg="white", font=("Arial", 16, "bold")
                 ).grid(row=0, column=0, pady=10)

        tk.Button(self.task_container,
                  text="<- Back", bg="#003366", fg="white",
                  command=lambda: self.switch_menu(self.current_period)
                  ).grid(row=0, column=1, sticky="e", padx=20)

        # Scrollable canvas for history rows
        canvas = tk.Canvas(self.task_container, bg="#001833", highlightthickness=0)
        canvas.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10)

        scrollbar = ttk.Scrollbar(self.task_container, orient="vertical",
                                  command=canvas.yview)
        scrollbar.grid(row=1, column=2, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)

        history_frame = tk.Frame(canvas, bg="#001833")
        canvas_window = canvas.create_window((0, 0), window=history_frame, anchor="nw")

        history_frame.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        ))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(
            canvas_window, width=e.width
        ))
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(
            int(-1 * (e.delta / 120)), "units"
        ))

        history = self.db.get_task_history()

        if not history:
            tk.Label(history_frame,
                     text="No completed tasks yet. Get to work!",
                     bg="#001833", fg="#aaaaaa", font=("Arial", 11)
                     ).pack(pady=20)
            return

        # Column headers
        for col, header in enumerate(["Date", "Task", "Difficulty"]):
            tk.Label(history_frame, text=header,
                     bg="#001833", fg="#aaaaaa", font=("Arial", 10, "bold")
                     ).grid(row=0, column=col, padx=20, pady=(10, 5), sticky="w")

        difficulty_colors = {
            "easy":   "#00cc66",
            "medium": "#ffcc00",
            "hard":   "#ff4444"
        }

        for index, (title, difficulty, date_str) in enumerate(history):
            row = index + 1
            diff_lower = (difficulty or "medium").lower()
            diff_color = difficulty_colors.get(diff_lower, "#aaaaaa")

            tk.Label(history_frame, text=date_str or "—",
                     bg="#001833", fg="#aaaaaa", font=("Arial", 10)
                     ).grid(row=row, column=0, padx=20, pady=3, sticky="w")

            tk.Label(history_frame, text=title,
                     bg="#001833", fg="#E0E0E0", font=("Arial", 10)
                     ).grid(row=row, column=1, padx=20, pady=3, sticky="w")

            tk.Label(history_frame,
                     text=(difficulty or "Medium").capitalize(),
                     bg="#001833", fg=diff_color, font=("Arial", 10, "bold")
                     ).grid(row=row, column=2, padx=20, pady=3, sticky="w")

        # Total count footer
        tk.Label(history_frame,
                 text=f"Total completions: {len(history)}",
                 bg="#001833", fg="#aaaaaa", font=("Arial", 10, "italic")
                 ).grid(row=len(history) + 1, column=0, columnspan=3, pady=15)

    # -------------------------------------------------------------------------
    # POPUPS
    # -------------------------------------------------------------------------

    def open_add_task_popup(self):
        """
        Open a popup window to create a new task.
        Collects: title, description, period, difficulty, skill 1, skill 2 (optional).
        Calculates OXP/gold/SXP rewards based on period and difficulty multiplier.
        Saves to database and refreshes the task view.
        """
        popup = tk.Toplevel(self.root)
        popup.title("Add New Task")
        popup.geometry("400x400")

        fields = [
            ("Title:",           0),
            ("Description:",     1),
        ]
        entries = {}
        for label, row in fields:
            tk.Label(popup, text=label, bg="#00254d", fg="#E0E0E0").grid(row=row, column=0, pady=5)
            entry = tk.Entry(popup)
            entry.grid(row=row, column=1)
            entries[label] = entry

        title_entry = entries["Title:"]
        desc_entry  = entries["Description:"]

        tk.Label(popup, text="Period:", bg="#00254d", fg="#E0E0E0").grid(row=2, column=0, pady=5)
        period_var = tk.StringVar(value="daily")
        ttk.Combobox(popup, textvariable=period_var,
                     values=["daily", "weekly", "monthly", "yearly"],
                     state="readonly").grid(row=2, column=1)

        tk.Label(popup, text="Difficulty:", bg="#00254d", fg="#E0E0E0").grid(row=3, column=0)
        difficulty_var = tk.StringVar(value="Medium")
        ttk.Combobox(popup, textvariable=difficulty_var,
                     values=["Easy", "Medium", "Hard"],
                     state="readonly").grid(row=3, column=1)

        skills = [skill["name"] for skill in self.db.get_all_skills()]

        tk.Label(popup, text="Skill 1", bg="#00254d", fg="#E0E0E0").grid(row=4, column=0)
        skill1_var = tk.StringVar()
        skill1_entry = ttk.Combobox(popup, values=skills, textvariable=skill1_var, state="readonly")
        skill1_entry.grid(row=4, column=1)

        tk.Label(popup, text="Skill 2 (OPTIONAL)", bg="#00254d", fg="#E0E0E0").grid(row=5, column=0)
        skill2_var = tk.StringVar()
        skill2_entry = ttk.Combobox(popup, values=skills, textvariable=skill2_var, state="readonly")
        skill2_entry.grid(row=5, column=1)

        def save_task():
            title      = title_entry.get().strip()
            description = desc_entry.get().strip()
            period     = period_var.get()
            skill1     = skill1_entry.get()
            skill2     = skill2_entry.get()
            difficulty = difficulty_var.get()

            if not title:
                messagebox.showerror("Error", "Title is required")
                return
            if not description:
                messagebox.showerror("Error", "Description is required")
                return
            if not skill1:
                messagebox.showerror("Error", "At least one skill must be selected")
                return

            # Calculate rewards with difficulty multiplier
            DIFFICULTY_MULTIPLIER = {"Easy": 0.8, "Medium": 1.0, "Hard": 1.5}
            rewards = PERIOD_REWARDS[period]
            mult    = DIFFICULTY_MULTIPLIER[difficulty]
            oxp     = int(rewards["oxp"] * mult)
            gold    = int(rewards["gold"] * mult)
            sxp     = int(rewards["sxp"] * mult)

            task_id = self.db.add_task(title, description, period, difficulty, oxp, gold)
            self.db.add_task_reward(task_id, skill1, sxp)
            if skill2:
                self.db.add_task_reward(task_id, skill2, sxp)

            popup.destroy()
            self.show_tasks(self.current_period)

        tk.Button(popup, text="Save Task", command=save_task
                  ).grid(row=6, column=0, columnspan=2, pady=20)

    def open_edit_task_popup(self, task_id):
        """
        Open a popup to edit an existing task's title, description, and period.

        Args:
            task_id (int): ID of the task to edit.
        """
        task = self.db.get_task(task_id)

        popup = tk.Toplevel(self.root)
        popup.title("Edit Task")
        popup.geometry("400x300")

        tk.Label(popup, text="Title").grid(row=0, column=0, pady=10)
        title_entry = tk.Entry(popup)
        title_entry.insert(0, task["title"])
        title_entry.grid(row=0, column=1)

        tk.Label(popup, text="Description").grid(row=1, column=0, pady=10)
        desc_entry = tk.Entry(popup)
        desc_entry.insert(0, task["description"])
        desc_entry.grid(row=1, column=1)

        tk.Label(popup, text="Period").grid(row=2, column=0, pady=10)
        period_var = tk.StringVar(value=task["period"])
        ttk.Combobox(popup, textvariable=period_var,
                     values=["daily", "weekly", "monthly", "yearly"],
                     state="readonly").grid(row=2, column=1)

        def save_changes():
            self.db.update_task(task_id, title_entry.get(), desc_entry.get(), period_var.get())
            popup.destroy()
            self.show_tasks(self.current_period)

        tk.Button(popup, text="Save Changes", command=save_changes
                  ).grid(row=3, column=0, columnspan=2, pady=20)

    def open_add_skill_popup(self):
        """
        Open a popup to add a new custom skill.
        Validates: not empty, max 20 characters, no duplicates.
        Refreshes the skills panel on success.
        """
        popup = tk.Toplevel(self.root)
        popup.title("Add New Skill")
        popup.geometry("300x150")
        popup.config(bg="#00254d")

        tk.Label(popup, text="Skill Name:",
                 bg="#00254d", fg="#E0E0E0", font=("Arial", 11)
                 ).grid(row=0, column=0, padx=20, pady=20)

        name_entry = tk.Entry(popup, font=("Arial", 11))
        name_entry.grid(row=0, column=1, padx=10, pady=20)
        name_entry.focus()

        def save_skill():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Skill name cannot be empty")
                return
            if len(name) > 20:
                messagebox.showerror("Error", "Skill name too long (max 20 chars)")
                return
            if not self.db.add_skill(name):
                messagebox.showerror("Error", f"'{name}' already exists")
                return
            popup.destroy()
            self.refresh_skill_ui()
            self.show_notification("Skill Added", f"{name} is now tracking!")

        name_entry.bind("<Return>", lambda e: save_skill())
        tk.Button(popup, text="Add Skill",
                  bg="#003366", fg="#E0E0E0", font=("Arial", 11, "bold"),
                  command=save_skill
                  ).grid(row=1, column=0, columnspan=2, pady=10)

    # -------------------------------------------------------------------------
    # TASK ACTIONS
    # -------------------------------------------------------------------------

    def complete_task(self, task_id):
        """
        Handle a task completion click.
        Calls the game engine to process rewards, then refreshes the UI.
        Shows a level-up message if the player leveled up from this completion.

        Args:
            task_id (int): ID of the task being completed.
        """
        old_level = self.db.get_player()["level"]

        result = self.engine.complete_task(task_id)

        if result is False:
            messagebox.showinfo("Task", "Task already completed")
            return

        new_level = self.db.get_player()["level"]
        if new_level > old_level:
            messagebox.showinfo("Level Up!", f"You reached level {new_level}!")

        self.refresh_player_ui()
        self.refresh_skill_ui()
        self.show_tasks(self.current_period)
        self.show_notification("Task Completed", "Great work! Rewards added.")

    def delete_task(self, task_id):
        """
        Ask for confirmation then permanently delete a task and its rewards.

        Args:
            task_id (int): ID of the task to delete.
        """
        if messagebox.askyesno("Confirm Deletion",
                               "This task will be permanently deleted.\n\nContinue?"):
            self.db.delete_task(task_id)
            self.show_tasks(self.current_period)

    def buy_skill(self, skill_name):
        """
        Attempt to purchase a skill XP boost from the shop.
        Shows an error if the player can't afford it.

        Args:
            skill_name (str): Name of the skill to boost.
        """
        if self.engine.buy_skill_boost(skill_name):
            self.refresh_player_ui()
            self.refresh_skill_ui()
            self.show_shop()
        else:
            messagebox.showerror("Error", "Not enough Gold")

    # -------------------------------------------------------------------------
    # NAVIGATION
    # -------------------------------------------------------------------------

    def switch_menu(self, period):
        """
        Switch the active period tab and redraw the task list.

        Args:
            period (str): 'daily', 'weekly', 'monthly', or 'yearly'.
        """
        self.current_period = period
        self.highlight_button(period)
        self.show_tasks(period)

    def highlight_button(self, period):
        """
        Visually highlight the active period button in the sidebar.
        Active button is a brighter blue; inactive buttons are dark blue.

        Args:
            period (str): The currently active period.
        """
        for name, btn in self.bottons.items():
            btn.config(bg="#0059b3" if name == period else "#003366")

    def clear_content(self):
        """Destroy all widgets inside the task_container to prepare for a new screen."""
        for widget in self.task_container.winfo_children():
            widget.destroy()

    # -------------------------------------------------------------------------
    # PLAYER UI REFRESH
    # -------------------------------------------------------------------------

    def refresh_player_ui(self):
        """
        Update all player-related UI elements:
        level label, gold label, XP label, XP bar, and XP bar colour.
        Called after any action that changes player state.
        """
        player   = self.db.get_player()
        required = self.get_required_oxp(player["level"])
        current  = player["oxp"]

        self.level_label.config(text=f"Character lvl {player['level']}")
        self.gold_label.config(text=f"Gold: {player['gold']}")
        self.xp_label.config(text=f"{current} / {required} OXP")

        self.xp_bar["maximum"] = required
        self.animate_bar(current)

        # Bar colour changes with level — yellow → cyan → green
        if player["level"] >= 10:
            color = "#00ff88"
        elif player["level"] >= 5:
            color = "#00ccff"
        else:
            color = "#ffcc00"

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("XP.Horizontal.TProgressbar",
                        background=color, lightcolor=color, darkcolor=color)

    def animate_bar(self, target):
        """
        Smoothly animate the XP bar from its current value to the target.
        Increments by 1 every 5ms until the target is reached.

        Args:
            target (int): The target XP value to animate to.
        """
        current = self.xp_bar["value"]
        if current < target:
            self.xp_bar["value"] = current + 1
            self.root.after(5, lambda: self.animate_bar(target))

    # -------------------------------------------------------------------------
    # GRAPHS & VISUALISATIONS
    # -------------------------------------------------------------------------

    def show_heatmap(self):
        """Open the GitHub-style habit heatmap in a matplotlib window."""
        show_heatmap(self.db)

    def show_task_graph(self):
        """
        Show a bar chart of current period tasks broken down by difficulty.
        Uses matplotlib. Counts Easy/Medium/Hard tasks and renders a simple bar chart.
        """
        tasks = self.db.get_tasks_by_period(self.current_period)
        difficulty_count = {"Easy": 0, "Medium": 0, "Hard": 0}

        for task in tasks:
            diff = task["difficulty"].capitalize()
            if diff in difficulty_count:
                difficulty_count[diff] += 1

        plt.figure()
        plt.bar(list(difficulty_count.keys()), list(difficulty_count.values()))
        plt.title("Tasks by Difficulty")
        plt.xlabel("Difficulty")
        plt.ylabel("Number of tasks")
        plt.show()

    # -------------------------------------------------------------------------
    # NOTIFICATIONS
    # -------------------------------------------------------------------------

    def show_notification(self, title, message):
        """
        Show a small auto-closing popup notification.
        Disappears after 2 seconds automatically.

        Args:
            title (str): Popup window title and bold header text.
            message (str): Body message shown below the title.
        """
        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.geometry("250x120")

        tk.Label(popup, text=title, font=("Arial", 12, "bold")).pack(pady=5)
        tk.Label(popup, text=message, font=("Arial", 10)).pack(pady=5)

        popup.after(2000, popup.destroy)    # auto-close after 2 seconds

    def show_login_reward(self, reward):
        """
        Show the daily login reward popup with gold, OXP, and streak info.
        Uses grab_set() to force the user to interact with it before the main window.
        Claim button closes the popup and refreshes the player UI.

        Args:
            reward (dict): Contains 'gold', 'oxp', 'streak', 'message' keys.
                           Returned by game_engine.check_login_reward().
        """
        popup = tk.Toplevel(self.root)
        popup.title("Daily Reward")
        popup.geometry("320x220")
        popup.config(bg="#00254d")
        popup.grab_set()    # block interaction with main window until claimed

        tk.Label(popup, text="Daily Login Reward!",
                 bg="#00254d", fg="#ffcc00", font=("Arial", 14, "bold")
                 ).pack(pady=(20, 5))

        tk.Label(popup, text=reward["message"],
                 bg="#00254d", fg="#E0E0E0", font=("Arial", 10)
                 ).pack(pady=5)

        tk.Label(popup, text=f"+ {reward['gold']} Gold     + {reward['oxp']} OXP",
                 bg="#00254d", fg="#00ccff", font=("Arial", 12, "bold")
                 ).pack(pady=10)

        tk.Label(popup, text=f"Login Streak: {reward['streak']} days 🔥",
                 bg="#00254d", fg="orange", font=("Arial", 11)
                 ).pack(pady=5)

        tk.Button(popup, text="Claim!",
                  bg="#003366", fg="white", font=("Arial", 11, "bold"),
                  command=lambda: [popup.destroy(), self.refresh_player_ui()]
                  ).pack(pady=15)

    # -------------------------------------------------------------------------
    # HELPER FORMULAS
    # -------------------------------------------------------------------------

    def get_required_oxp(self, level):
        """
        Calculate OXP required to reach the next character level.
        Formula: 100 + (level - 1) * 50

        Args:
            level (int): Current character level.

        Returns:
            int: OXP needed to level up.
        """
        return 100 + (level - 1) * 50

    def get_required_sxp(self, level):
        """
        Calculate SXP required to reach the next skill level.
        Formula: 50 + (level - 1) * 25

        Args:
            level (int): Current skill level.

        Returns:
            int: SXP needed to level up the skill.
        """
        return 50 + (level - 1) * 25