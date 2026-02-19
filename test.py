#  test
from  game_engine import GameEngine
from database import Database

db = Database()
engine = GameEngine(db)
# Simulate completing a task with ID 1
engine.complete_task(1)
