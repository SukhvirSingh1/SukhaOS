# Entry point for SukhaOS application

from database import Database
from layout import SkillUI
import tkinter as tk
from tkinter import ttk

class SukhaOS:
    def __init__(self, root):
        self.root = root
        self.root.title("SukhaOS")
        self.root.geometry("1000x550")
        
        self.db = Database()
        
        self.skill_ui = SkillUI(self.root, self.db)
        
        
        
        
if __name__ == "__main__":
    root = tk.Tk()
    app = SukhaOS(root)
    root.mainloop()
