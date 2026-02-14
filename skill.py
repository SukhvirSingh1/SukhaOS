import tkinter as tk
from datetime import date
from models import Skill

class skillUI:
    def __init__(self, parent, database):
        self.parent = parent
        self.db = database
        self.current_type = "main"