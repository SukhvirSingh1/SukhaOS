"""
main.py
=======
Entry point for SukhaOS.
Run with: python main.py
"""

import tkinter as tk
from database import Database
from game_engine import GameEngine
from layout import SkillUI


class SukhaOS:
    def __init__(self, root):
        self.root = root
        self.root.title("SukhaOS")
        self.root.state("zoomed")

        self.db       = Database()
        self.db.reset_tasks()

        self.engine   = GameEngine(self.db)
        self.skill_ui = SkillUI(self.root, self.db, self.engine)

        # Check first launch, then login reward, then boss damage — in sequence
        self.root.after(300, self.check_first_launch)

    def check_first_launch(self):
        """Show name setup on first launch, else go straight to login check."""
        player = self.db.get_player()
        if player["name"] == "Hero" or not player["name"]:
            self.skill_ui.open_name_setup_popup(on_complete=self.check_login)
        else:
            self.check_login()

    def check_login(self):
        """Check login reward then check boss passive damage."""
        reward = self.engine.check_login_reward()
        if reward:
            self.skill_ui.show_login_reward(
                reward, on_close=self.check_boss_damage
            )
        else:
            self.check_boss_damage()

    def check_boss_damage(self):
        """
        Apply passive boss damage if an active boss has been ignored.
        Shows a warning popup if damage was dealt.
        Then check if an active boss exists and show the boss alert.
        """
        damage_info = self.engine.apply_passive_boss_damage()
        if damage_info:
            self.skill_ui.show_boss_damage_warning(
                damage_info, on_close=self.check_active_boss
            )
        else:
            self.check_active_boss()

    def check_active_boss(self):
        """If an active boss exists, show the boss alert banner."""
        boss = self.db.get_active_boss()
        if boss:
            self.skill_ui.show_boss_alert(boss)
            self.skill_ui.refresh_player_ui()


if __name__ == "__main__":
    root = tk.Tk()
    app = SukhaOS(root)
    root.mainloop()