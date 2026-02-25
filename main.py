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
        self.root.geometry("1000x550")
        
        self.db = Database()
        self.db.reset_tasks()  # Reset daily tasks on startup
        
        self.engine = GameEngine(self.db)
        self.skill_ui = SkillUI(self.root, self.db, self.engine)
        

        

        
        
        
        
if __name__ == "__main__":
    root = tk.Tk()
    app = SukhaOS(root)
    root.mainloop()
