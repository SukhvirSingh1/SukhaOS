"""
main.py
=======
Entry point for SukhaOS.
Run with: python main.py
"""

import customtkinter as ctk
from database import Database
from game_engine import GameEngine
from layout import SkillUI

# --- CustomTkinter global appearance settings ---
# Must be set before any CTK widgets are created
ctk.set_appearance_mode("dark")       # dark mode
ctk.set_default_color_theme("dark-blue")  # dark-blue accent colours


class SukhaOS:
    def __init__(self, root):
        self.root = root
        self.root.title("SukhaOS")
        self.root.after(0, lambda:self.root.state("zoomed"))
        self.root.minsize(1100, 600)

        self.db       = Database()
        self.db.reset_tasks()

        self.engine   = GameEngine(self.db)
        self.skill_ui = SkillUI(self.root, self.db, self.engine)

        # Startup sequence: name → login reward → boss damage → boss alert
        self.root.after(300, self.check_first_launch)

    def check_first_launch(self):
        """Show name setup on first launch."""
        player = self.db.get_player()
        if player["name"] == "Hero" or not player["name"]:
            self.skill_ui.open_name_setup_popup(on_complete=self.check_login)
        else:
            self.check_login()

    def check_login(self):
        """Check login reward then boss damage."""
        reward = self.engine.check_login_reward()
        if reward:
            self.skill_ui.show_login_reward(reward, on_close=self.check_boss_damage)
        else:
            self.check_boss_damage()

    def check_boss_damage(self):
        """Apply passive boss damage if applicable."""
        damage_info = self.engine.apply_passive_boss_damage()
        if damage_info:
            self.skill_ui.show_boss_damage_warning(
                damage_info, on_close=self.check_active_boss
            )
        else:
            self.check_active_boss()

    def check_active_boss(self):
        """Show boss alert if an active boss exists."""
        boss = self.db.get_active_boss()
        if boss:
            self.skill_ui.show_boss_alert(boss)
            self.skill_ui.refresh_player_ui()


if __name__ == "__main__":
    root = ctk.CTk()   # CTk instead of tk.Tk
    app = SukhaOS(root)
    root.mainloop()