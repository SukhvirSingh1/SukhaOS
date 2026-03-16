# main.py
# Entry point for SukhaOS application


from database import Database
from layout import SkillUI
from game_engine import GameEngine
import tkinter as tk
from tkinter import ttk


class SukhaOS:
    def __init__(self, root):
        self.root = root
        self.root.title("SukhaOS")
        self.root.geometry("1280x720")
        
        self.db = Database()
        self.db.reset_tasks()  # Reset daily tasks on startup
        
        self.engine = GameEngine(self.db)
        self.skill_ui = SkillUI(self.root, self.db, self.engine)
        
        self.root.after(500, self.check_login_reward)
        
    def check_login_reward(self):
        reward = self.engine.check_login_reward()
        if reward:
            self.skill_ui.show_login_reward(reward)
        

        

        
        
        
        
if __name__ == "__main__":
    root = tk.Tk()
    app = SukhaOS(root)
    root.mainloop()
