"""
main.py
=======
Entry point for SukhaOS — a gamified productivity desktop app.
Run this file to launch the application:
    python main.py
"""

import tkinter as tk
from database import Database
from game_engine import GameEngine
from layout import SkillUI


class SukhaOS:
    """
    Root application class. Wires together Database, GameEngine, and SkillUI.
    """

    def __init__(self, root):
        """
        Initialise the app window and all core components.

        Args:
            root (tk.Tk): The main tkinter window.
        """
        self.root = root
        self.root.title("SukhaOS")
        self.root.state("zoomed")

        # Initialise in dependency order
        self.db     = Database()
        self.db.reset_tasks()

        self.engine   = GameEngine(self.db)
        self.skill_ui = SkillUI(self.root, self.db, self.engine)

        # Check for first launch (no name set) — show name popup first
        # then check login reward after name is set
        self.root.after(300, self.check_first_launch)

    def check_first_launch(self):
        """
        On first launch, player name is 'Hero' (default).
        Show the name setup popup so the player can personalise their character.
        Login reward is checked after name setup is complete.
        """
        player = self.db.get_player()

        if player["name"] == "Hero" or not player["name"]:
            # First launch — show name setup, login reward comes after
            self.skill_ui.open_name_setup_popup(on_complete=self.check_login)
        else:
            # Returning player — go straight to login reward
            self.check_login()

    def check_login(self):
        """
        Check and display the daily login reward popup if due.
        Called after name setup on first launch, or directly on returning launches.
        """
        reward = self.engine.check_login_reward()
        if reward:
            self.skill_ui.show_login_reward(reward)


if __name__ == "__main__":
    root = tk.Tk()
    app = SukhaOS(root)
    root.mainloop()