"""
main.py
=======
Entry point for SukhaOS — a gamified productivity desktop app.

Initialises the database, game engine, and UI in the correct order,
then checks for the daily login reward after the UI has fully loaded.

Run this file to launch the application:
    python main.py
"""

import tkinter as tk
from database import Database
from game_engine import GameEngine
from layout import SkillUI


class SukhaOS:
    """
    Root application class for SukhaOS.
    Wires together the three core components:
        - Database  → persistent storage (SQLite)
        - GameEngine → game logic (XP, levels, rewards)
        - SkillUI   → user interface (tkinter)
    """

    def __init__(self, root):
        """
        Initialise the application window and all core components.

        Args:
            root (tk.Tk): The main tkinter window.
        """
        self.root = root
        self.root.title("SukhaOS")
        self.root.state("zoomed")   # launch maximised on Windows

        # --- Initialise core components in dependency order ---
        self.db = Database()            # database first — others depend on it
        self.db.reset_tasks()           # reset expired tasks on every launch

        self.engine = GameEngine(self.db)           # engine needs database
        self.skill_ui = SkillUI(self.root, self.db, self.engine)  # UI needs both

        # --- Check login reward after UI is ready ---
        # 500ms delay ensures the main window is fully rendered before popup appears
        self.root.after(500, self.check_login_reward)

    def check_login_reward(self):
        """
        Ask the game engine if a daily login reward is due.
        If so, display the reward popup via the UI.
        Called once automatically 500ms after launch.
        """
        reward = self.engine.check_login_reward()
        if reward:
            self.skill_ui.show_login_reward(reward)


# --- Application entry point ---
if __name__ == "__main__":
    root = tk.Tk()
    app = SukhaOS(root)
    root.mainloop()