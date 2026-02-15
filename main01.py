from database import Database
from skill import SkillUI
import tkinter as tk

class SukhaOS:
    def __init__(self, root):
        self.root = root
        self.root.title("SukhaOS")
        self.root.geometry("800x850")
        
        self.db = Database()
        
        self.skill_ui = SkillUI(self.root, self.db)
        
        
        
        
if __name__ == "__main__":
    root = tk.Tk()
    app = SukhaOS(root)
    root.mainloop()
