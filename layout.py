"""
layout.py
=========
Defines the SkillUI class — the entire user interface for SukhaOS.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from heatmap import show_heatmap

PERIOD_REWARDS = {
    "daily":   {"gold": 20,  "oxp": 20,  "sxp": 10},
    "weekly":  {"gold": 50,  "oxp": 60,  "sxp": 25},
    "monthly": {"gold": 120, "oxp": 150, "sxp": 60},
    "yearly":  {"gold": 500, "oxp": 500, "sxp": 200}
}


class SkillUI:
    def __init__(self, root, db, engine):
        self.root = root
        self.db = db
        self.engine = engine
        self.current_period = "daily"
        self.build_ui()

    # -------------------------------------------------------------------------
    # UI CONSTRUCTION
    # -------------------------------------------------------------------------

    def build_ui(self):
        """Build the full application layout — skills panel, player info, task area."""

        self.root.rowconfigure(0, weight=3, minsize=200)
        self.root.rowconfigure(1, weight=1, minsize=150)
        self.root.columnconfigure(0, weight=3)
        self.root.columnconfigure(1, weight=7)

        # ── TOP LEFT: Skills Panel ────────────────────────────────────────────
        chrctr_frame = tk.Frame(self.root, bg="#00254d", bd=2, relief="ridge")
        chrctr_frame.grid(row=0, column=0, sticky="nsew")

        tk.Label(chrctr_frame,
                 text="Skills",
                 bg="#00254d", fg="#E0E0E0",
                 font=("Arial", 14, "bold")
                 ).grid(row=0, column=0, columnspan=2, pady=(15, 5))

        # --- HP display (bar + label) ---
        # HP sits at the top of the skills panel so it's always visible
        hp_frame = tk.Frame(chrctr_frame, bg="#00254d")
        hp_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 8))
        hp_frame.columnconfigure(0, weight=1)

        self.hp_label = tk.Label(hp_frame,
                                 text="HP: 100 / 100",
                                 bg="#00254d", fg="#ff6666",
                                 font=("Arial", 9, "bold"))
        self.hp_label.grid(row=0, column=0, sticky="w")

        # HP bar — red colour to distinguish from XP bar
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("HP.Horizontal.TProgressbar",
                        troughcolor="#001833",
                        background="#ff4444",
                        thickness=12,
                        bordercolor="#001833",
                        lightcolor="#ff4444",
                        darkcolor="#ff4444")

        self.hp_bar = ttk.Progressbar(hp_frame,
                                      orient="horizontal",
                                      mode="determinate",
                                      style="HP.Horizontal.TProgressbar")
        self.hp_bar.grid(row=1, column=0, sticky="ew", pady=(2, 0))

        # Divider line between HP and skills list
        tk.Frame(chrctr_frame, bg="#003366", height=1
                 ).grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 5))

        # --- Scrollable skill list ---
        self.skills_canvas = tk.Canvas(chrctr_frame, bg="#00254d", highlightthickness=0)
        self.skills_canvas.grid(row=3, column=0, sticky="nsew", padx=(10, 0))

        skills_scrollbar = ttk.Scrollbar(chrctr_frame, orient="vertical",
                                         command=self.skills_canvas.yview)
        skills_scrollbar.grid(row=3, column=1, sticky="ns")
        self.skills_canvas.configure(yscrollcommand=skills_scrollbar.set)

        self.skills_container = tk.Frame(self.skills_canvas, bg="#00254d")
        self.skills_canvas_window = self.skills_canvas.create_window(
            (0, 0), window=self.skills_container, anchor="nw"
        )

        self.skills_container.bind("<Configure>", lambda e: self.skills_canvas.configure(
            scrollregion=self.skills_canvas.bbox("all")
        ))
        self.skills_canvas.bind("<Configure>", lambda e: self.skills_canvas.itemconfig(
            self.skills_canvas_window, width=e.width
        ))
        self.skills_canvas.bind("<MouseWheel>", lambda e: self.skills_canvas.yview_scroll(
            int(-1 * (e.delta / 120)), "units"
        ))

        tk.Button(chrctr_frame,
                  text="+ Add Skill",
                  bg="#003366", fg="#E0E0E0",
                  font=("Arial", 9, "bold"),
                  command=self.open_add_skill_popup
                  ).grid(row=4, column=0, columnspan=2, pady=(0, 10))

        chrctr_frame.rowconfigure(3, weight=1)
        chrctr_frame.columnconfigure(0, weight=1)
        chrctr_frame.columnconfigure(1, weight=0)

        # ── TOP RIGHT: Player Info ────────────────────────────────────────────
        info_frame = tk.Frame(self.root, bg="#00254d", bd=2, relief="ridge")
        info_frame.grid(row=0, column=1, sticky="nsew")

        for i in range(6):
            info_frame.rowconfigure(i, weight=0)
        info_frame.rowconfigure(6, weight=1)   # spacer
        info_frame.columnconfigure(0, weight=1)

        # Character name label — updated after name is set
        self.level_label = tk.Label(info_frame,
                                    text="Hero  |  lvl 1",
                                    bg="#00254d", fg="#E0E0E0",
                                    font=("Arial", 16, "bold"))
        self.level_label.grid(row=0, column=0, pady=20)

        self.gold_label = tk.Label(info_frame,
                                   text="Gold: 0",
                                   bg="#00254d", fg="gold",
                                   font=("Arial", 12))
        self.gold_label.grid(row=1, column=0, pady=(0, 15))

        tk.Button(info_frame,
                  text="Add Task",
                  bg="#003366", fg="#E0E0E0",
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
                  bg="#003366", fg="white",
                  font=("Arial", 11, "bold"),
                  command=self.show_stats
                  ).grid(row=4, column=0, pady=15)

        tk.Button(info_frame,
                  text="Habit Map",
                  bg="#003366", fg="white",
                  font=("Arial", 11, "bold"),
                  command=self.show_heatmap
                  ).grid(row=5, column=0, pady=(0, 15))

        # ── BOTTOM: Task Area ─────────────────────────────────────────────────
        tasks_frame = tk.Frame(self.root, bg="#001833", bd=2, relief="ridge")
        tasks_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        tasks_frame.rowconfigure(0, weight=1)
        tasks_frame.columnconfigure(0, weight=0)
        tasks_frame.columnconfigure(1, weight=1)

        side_bar = tk.Frame(tasks_frame, bg="#003366")
        side_bar.grid(row=0, column=0, sticky="ns", padx=15)

        self.bottons = {}
        for i, (name, label) in enumerate(zip(
            ["daily", "weekly", "monthly", "yearly"], ["D", "W", "M", "Y"]
        )):
            btn = tk.Button(side_bar, text=label,
                            bg="#003366", fg="#E0E0E0",
                            font=("Arial", 10, "bold"),
                            command=lambda n=name: self.switch_menu(n))
            btn.grid(row=i, column=0, pady=10)
            self.bottons[name] = btn

        tk.Button(side_bar, text="Log",
                  bg="#003366", fg="white",
                  font=("Arial", 10, "bold"),
                  command=self.show_history
                  ).grid(row=4, column=0, pady=10)

        tk.Button(side_bar, text="Shop",
                  bg="#003366", fg="white",
                  font=("Arial", 10, "bold"),
                  command=self.show_shop
                  ).grid(row=5, column=0, pady=10)

        self.task_container = tk.Frame(tasks_frame, bg="#001833")
        self.task_container.grid(row=0, column=1, sticky="nsew", padx=20)

        for i in range(2):
            self.task_container.grid_rowconfigure(i, weight=1)
            self.task_container.grid_columnconfigure(i, weight=1)

        self.xp_label = tk.Label(tasks_frame,
                                 text="0 / 100 OXP",
                                 bg="#001833",
                                 font=("Arial", 9, "bold"),
                                 fg="#aaaaaa")
        self.xp_label.grid(row=3, column=0)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TProgressbar",
                        troughcolor="#001833", background="#00ccff",
                        thickness=18, bordercolor="#001833",
                        lightcolor="#00ccff", darkcolor="#00ccff")

        self.switch_menu("daily")
        self.refresh_player_ui()
        self.refresh_skill_ui()

    # -------------------------------------------------------------------------
    # SKILL PANEL
    # -------------------------------------------------------------------------

    def refresh_skill_ui(self):
        """Clear and redraw the skills list. Called after any skill change."""
        for widget in self.skills_container.winfo_children():
            widget.destroy()

        skills = self.db.get_all_skills()

        if not skills:
            tk.Label(self.skills_container,
                     text="No skills yet",
                     bg="#00254d", fg="#E0E0E0",
                     font=("Arial", 10)
                     ).grid(row=0, column=0)
            return

        for index, skill in enumerate(skills):
            required = self.get_required_sxp(skill["level"])
            skill_text = f"{skill['name']} | Lv {skill['level']}  {skill['xp']} / {required}"

            tk.Label(self.skills_container,
                     text=skill_text,
                     bg="#00254d", fg="#E0E0E0",
                     anchor="w", font=("Arial", 10)
                     ).grid(row=index, column=0, sticky="ew", pady=3)

            tk.Button(self.skills_container,
                      text="x",
                      bg="#00254d", fg="#ff4444",
                      font=("Arial", 8, "bold"),
                      bd=0, cursor="hand2",
                      command=lambda n=skill["name"]: self.delete_skill(n)
                      ).grid(row=index, column=1, padx=(5, 0), pady=3)

        self.skills_container.columnconfigure(0, weight=1)
        self.skills_container.columnconfigure(1, weight=0)

    def delete_skill(self, skill_name):
        """Ask for confirmation then delete a skill."""
        if messagebox.askyesno("Delete Skill",
                               f"Delete '{skill_name}'? This won't affect existing tasks."):
            self.db.delete_skill(skill_name)
            self.refresh_skill_ui()

    # -------------------------------------------------------------------------
    # TASK CARDS
    # -------------------------------------------------------------------------

    def create_task_card(self, row, col, task_id, title, description, status, streak, difficulty):
        """Render a single task card. Clicking status label completes the task."""
        card = tk.Frame(self.task_container, bg="#003366", bd=0)
        card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")

        tk.Label(card, text=title, bg="#003366", fg="#E0E0E0",
                 font=("Arial", 12, "bold")
                 ).grid(row=0, column=1, sticky="w", padx=10, pady=(10, 0))

        tk.Label(card, text=description, bg="#003366", fg="#E0E0E0",
                 font=("Arial", 10)
                 ).grid(row=1, column=1, sticky="w", padx=10)

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
        """Render task cards for the selected period."""
        for widget in self.task_container.winfo_children():
            widget.destroy()

        for i in range(10):
            self.task_container.grid_rowconfigure(i, weight=0)
            self.task_container.grid_columnconfigure(i, weight=0)

        self.task_container.grid_rowconfigure(0, weight=0)
        self.task_container.grid_rowconfigure(1, weight=0)
        self.task_container.grid_rowconfigure(2, weight=1)
        self.task_container.grid_rowconfigure(3, weight=1)
        self.task_container.grid_columnconfigure(0, weight=1)
        self.task_container.grid_columnconfigure(1, weight=1)

        tasks = self.db.get_tasks_by_period(period)
        completed = sum(1 for t in tasks if t["status"] == "Completed")
        total = len(tasks)

        tk.Label(self.task_container,
                 text=f"{completed} / {total} tasks completed",
                 bg="#001833", fg="white", font=("Arial", 11, "bold")
                 ).grid(row=0, column=0, columnspan=2, pady=5)

        ttk.Progressbar(self.task_container,
                        length=250,
                        maximum=total if total > 0 else 1,
                        value=completed
                        ).grid(row=1, column=0, columnspan=2, pady=5)

        positions = [(2, 0), (2, 1), (3, 0), (3, 1)]
        for task, pos in zip(tasks, positions):
            self.create_task_card(
                pos[0], pos[1],
                task["id"], task["title"], task["description"],
                task["status"], task["streak"], task["difficulty"]
            )

        tk.Button(self.task_container,
                  text="Show Graph", bg="#001833", fg="white",
                  command=self.show_task_graph
                  ).grid(row=4, column=1, pady=10)

    def show_stats(self):
        """Render the Stats screen with character info, skills, and achievements."""
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

        tk.Label(self.task_container,
                 text=f"Name: {player['name']}",
                 bg="#001833", fg="white"
                 ).grid(row=1, column=0, sticky="w", padx=20)

        tk.Label(self.task_container,
                 text=f"Level: {player['level']}",
                 bg="#001833", fg="white"
                 ).grid(row=2, column=0, sticky="w", padx=20)

        tk.Label(self.task_container,
                 text=f"HP: {player['current_hp']} / {player['max_hp']}",
                 bg="#001833", fg="#ff6666"
                 ).grid(row=3, column=0, sticky="w", padx=20)

        tk.Label(self.task_container,
                 text=f"OXP: {player['oxp']}",
                 bg="#001833", fg="white"
                 ).grid(row=4, column=0, sticky="w", padx=20)

        tk.Label(self.task_container,
                 text=f"Gold: {player['gold']}",
                 bg="#001833", fg="white"
                 ).grid(row=5, column=0, sticky="w", padx=20)

        self.show_skill_stats()

        achievement = self.db.get_achievement()
        start_row = 16

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
        """Render skill progress bars inside the stats screen. Starts at row 7."""
        skills = self.db.get_all_skills()
        start_row = 7

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
        """Render the Skill Boost Shop."""
        self.clear_content()

        tk.Label(self.task_container, text="Skill Boost Shop",
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
        """Render the Task History Log screen."""
        self.clear_content()

        for i in range(10):
            self.task_container.grid_rowconfigure(i, weight=0)
            self.task_container.grid_columnconfigure(i, weight=0)

        self.task_container.grid_rowconfigure(0, weight=0)
        self.task_container.grid_rowconfigure(1, weight=1)
        self.task_container.grid_columnconfigure(0, weight=1)
        self.task_container.grid_columnconfigure(1, weight=1)
        self.task_container.grid_columnconfigure(2, weight=0)

        tk.Label(self.task_container, text="Task History",
                 bg="#001833", fg="white", font=("Arial", 16, "bold")
                 ).grid(row=0, column=0, pady=10)

        tk.Button(self.task_container,
                  text="<- Back", bg="#003366", fg="white",
                  command=lambda: self.switch_menu(self.current_period)
                  ).grid(row=0, column=1, sticky="e", padx=20)

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

        for col, header in enumerate(["Date", "Task", "Difficulty"]):
            tk.Label(history_frame, text=header,
                     bg="#001833", fg="#aaaaaa", font=("Arial", 10, "bold")
                     ).grid(row=0, column=col, padx=20, pady=(10, 5), sticky="w")

        difficulty_colors = {"easy": "#00cc66", "medium": "#ffcc00", "hard": "#ff4444"}

        for index, (title, difficulty, date_str) in enumerate(history):
            row = index + 1
            diff_color = difficulty_colors.get((difficulty or "medium").lower(), "#aaaaaa")

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

        tk.Label(history_frame,
                 text=f"Total completions: {len(history)}",
                 bg="#001833", fg="#aaaaaa", font=("Arial", 10, "italic")
                 ).grid(row=len(history) + 1, column=0, columnspan=3, pady=15)

    # -------------------------------------------------------------------------
    # POPUPS
    # -------------------------------------------------------------------------

    def open_name_setup_popup(self, on_complete=None):
        """
        First launch popup — asks the player to name their character.
        Blocks the main window until a name is entered.
        Calls on_complete() after name is saved.

        Args:
            on_complete (callable): Function to call after name is set.
        """
        popup = tk.Toplevel(self.root)
        popup.title("Welcome to SukhaOS")
        popup.geometry("380x250")
        popup.config(bg="#00254d")
        popup.grab_set()    # block main window until done
        popup.resizable(False, False)

        tk.Label(popup,
                 text="Welcome to SukhaOS!",
                 bg="#00254d", fg="#ffcc00",
                 font=("Arial", 15, "bold")
                 ).pack(pady=(25, 5))

        tk.Label(popup,
                 text="Enter your character name to begin:",
                 bg="#00254d", fg="#E0E0E0",
                 font=("Arial", 10)
                 ).pack(pady=5)

        name_entry = tk.Entry(popup,
                              font=("Arial", 13),
                              justify="center",
                              width=20)
        name_entry.pack(pady=15)
        name_entry.focus()

        def save_name():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter a name", parent=popup)
                return
            if len(name) > 20:
                messagebox.showerror("Error", "Name too long (max 20 chars)", parent=popup)
                return

            self.db.set_player_name(name)
            self.refresh_player_ui()    # update the level label with new name
            popup.destroy()

            if on_complete:
                on_complete()           # trigger login reward check

        name_entry.bind("<Return>", lambda e: save_name())

        tk.Button(popup,
                  text="Start Game!",
                  bg="#003366", fg="#ffcc00",
                  font=("Arial", 12, "bold"),
                  command=save_name
                  ).pack(pady=5)

    def open_add_task_popup(self):
        """Open a popup to create a new task."""
        popup = tk.Toplevel(self.root)
        popup.title("Add New Task")
        popup.geometry("400x400")

        tk.Label(popup, text="Title:", bg="#00254d", fg="#E0E0E0").grid(row=0, column=0, pady=5)
        title_entry = tk.Entry(popup)
        title_entry.grid(row=0, column=1)

        tk.Label(popup, text="Description:", bg="#00254d", fg="#E0E0E0").grid(row=1, column=0, pady=5)
        desc_entry = tk.Entry(popup)
        desc_entry.grid(row=1, column=1)

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
        skill1_entry = ttk.Combobox(popup, values=skills,
                                    textvariable=skill1_var, state="readonly")
        skill1_entry.grid(row=4, column=1)

        tk.Label(popup, text="Skill 2 (OPTIONAL)", bg="#00254d", fg="#E0E0E0").grid(row=5, column=0)
        skill2_var = tk.StringVar()
        skill2_entry = ttk.Combobox(popup, values=skills,
                                    textvariable=skill2_var, state="readonly")
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

            DIFFICULTY_MULTIPLIER = {"Easy": 0.8, "Medium": 1.0, "Hard": 1.5}
            rewards = PERIOD_REWARDS[period]
            mult    = DIFFICULTY_MULTIPLIER[difficulty]

            task_id = self.db.add_task(
                title, description, period, difficulty,
                int(rewards["oxp"] * mult),
                int(rewards["gold"] * mult)
            )
            self.db.add_task_reward(task_id, skill1, int(rewards["sxp"] * mult))
            if skill2:
                self.db.add_task_reward(task_id, skill2, int(rewards["sxp"] * mult))

            popup.destroy()
            self.show_tasks(self.current_period)

        tk.Button(popup, text="Save Task", command=save_task
                  ).grid(row=6, column=0, columnspan=2, pady=20)

    def open_edit_task_popup(self, task_id):
        """Open a popup to edit an existing task."""
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
            self.db.update_task(task_id, title_entry.get(),
                                desc_entry.get(), period_var.get())
            popup.destroy()
            self.show_tasks(self.current_period)

        tk.Button(popup, text="Save Changes", command=save_changes
                  ).grid(row=3, column=0, columnspan=2, pady=20)

    def open_add_skill_popup(self):
        """Open a popup to add a new custom skill."""
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
        """Handle a task completion click."""
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
        """Ask for confirmation then delete a task."""
        if messagebox.askyesno("Confirm Deletion",
                               "This task will be permanently deleted.\n\nContinue?"):
            self.db.delete_task(task_id)
            self.show_tasks(self.current_period)

    def buy_skill(self, skill_name):
        """Attempt to purchase a skill XP boost."""
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
        """Switch the active period tab."""
        self.current_period = period
        self.highlight_button(period)
        self.show_tasks(period)

    def highlight_button(self, period):
        """Highlight the active sidebar button."""
        for name, btn in self.bottons.items():
            btn.config(bg="#0059b3" if name == period else "#003366")

    def clear_content(self):
        """Destroy all widgets in the task container."""
        for widget in self.task_container.winfo_children():
            widget.destroy()

    # -------------------------------------------------------------------------
    # PLAYER UI REFRESH
    # -------------------------------------------------------------------------

    def refresh_player_ui(self):
        """
        Update level label, gold, XP bar, and HP bar.
        Called after any action that changes player state.
        """
        player   = self.db.get_player()
        required = self.get_required_oxp(player["level"])
        current  = player["oxp"]

        # Show character name + level in header
        name = player.get("name") or "Hero"
        self.level_label.config(text=f"{name}  |  lvl {player['level']}")
        self.gold_label.config(text=f"Gold: {player['gold']}")
        self.xp_label.config(text=f"{current} / {required} OXP")

        # XP bar
        self.xp_bar["maximum"] = required
        self.animate_bar(current)

        # XP bar colour changes with level
        if player["level"] >= 10:
            xp_color = "#00ff88"
        elif player["level"] >= 5:
            xp_color = "#00ccff"
        else:
            xp_color = "#ffcc00"

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("XP.Horizontal.TProgressbar",
                        background=xp_color,
                        lightcolor=xp_color,
                        darkcolor=xp_color)

        # HP bar + label
        current_hp = player.get("current_hp", 100)
        max_hp     = player.get("max_hp", 100)

        self.hp_label.config(text=f"HP: {current_hp} / {max_hp}")
        self.hp_bar["maximum"] = max_hp
        self.hp_bar["value"]   = current_hp

        # HP bar colour changes based on health percentage
        hp_pct = current_hp / max_hp if max_hp > 0 else 1
        if hp_pct > 0.6:
            hp_color = "#ff4444"    # healthy — red
        elif hp_pct > 0.3:
            hp_color = "#ff8800"    # low — orange
        else:
            hp_color = "#ffcc00"    # critical — yellow warning

        style.configure("HP.Horizontal.TProgressbar",
                        background=hp_color,
                        lightcolor=hp_color,
                        darkcolor=hp_color)

    def animate_bar(self, target):
        """Smoothly animate the XP bar to the target value."""
        current = self.xp_bar["value"]
        if current < target:
            self.xp_bar["value"] = current + 1
            self.root.after(5, lambda: self.animate_bar(target))

    # -------------------------------------------------------------------------
    # GRAPHS & VISUALISATIONS
    # -------------------------------------------------------------------------

    def show_heatmap(self):
        """Open the habit heatmap."""
        show_heatmap(self.db)

    def show_task_graph(self):
        """Show a bar chart of tasks by difficulty."""
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
        """Show a small auto-closing popup. Disappears after 2 seconds."""
        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.geometry("250x120")

        tk.Label(popup, text=title, font=("Arial", 12, "bold")).pack(pady=5)
        tk.Label(popup, text=message, font=("Arial", 10)).pack(pady=5)

        popup.after(2000, popup.destroy)

    def show_login_reward(self, reward):
        """
        Show the daily login reward popup.
        Now also shows HP restored amount.
        """
        popup = tk.Toplevel(self.root)
        popup.title("Daily Reward")
        popup.geometry("320x250")
        popup.config(bg="#00254d")
        popup.grab_set()

        tk.Label(popup, text="Daily Login Reward!",
                 bg="#00254d", fg="#ffcc00",
                 font=("Arial", 14, "bold")
                 ).pack(pady=(20, 5))

        tk.Label(popup, text=reward["message"],
                 bg="#00254d", fg="#E0E0E0",
                 font=("Arial", 10)
                 ).pack(pady=5)

        tk.Label(popup,
                 text=f"+ {reward['gold']} Gold     + {reward['oxp']} OXP",
                 bg="#00254d", fg="#00ccff",
                 font=("Arial", 12, "bold")
                 ).pack(pady=5)

        # Show HP restored if any was restored
        if reward.get("hp_restored", 0) > 0:
            tk.Label(popup,
                     text=f"+ {reward['hp_restored']} HP restored",
                     bg="#00254d", fg="#ff6666",
                     font=("Arial", 10)
                     ).pack(pady=2)

        tk.Label(popup,
                 text=f"Login Streak: {reward['streak']} days 🔥",
                 bg="#00254d", fg="orange",
                 font=("Arial", 11)
                 ).pack(pady=5)

        tk.Button(popup,
                  text="Claim!",
                  bg="#003366", fg="white",
                  font=("Arial", 11, "bold"),
                  command=lambda: [popup.destroy(), self.refresh_player_ui()]
                  ).pack(pady=10)

    # -------------------------------------------------------------------------
    # HELPER FORMULAS
    # -------------------------------------------------------------------------

    def get_required_oxp(self, level):
        """OXP required for next level. Formula: 100 + (level-1) * 50"""
        return 100 + (level - 1) * 50

    def get_required_sxp(self, level):
        """SXP required for next skill level. Formula: 50 + (level-1) * 25"""
        return 50 + (level - 1) * 25