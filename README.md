# SukhaOS 🎮

> A gamified productivity desktop app that turns your daily habits and tasks into an RPG experience.

Built with **Python**, **tkinter**, and **SQLite** — no frameworks, no dependencies beyond the standard library and matplotlib.

---

## What is SukhaOS?

SukhaOS is a personal productivity system disguised as a video game. Instead of a boring to-do list, you level up a character, earn gold, build skills, and track streaks — all tied to real tasks you set for yourself.

The more consistent you are, the stronger your character gets.

---

## Features

| Feature | Description |
|---|---|
| 🗂 **Task Management** | Add daily, weekly, monthly, and yearly tasks with difficulty levels |
| ⚔️ **RPG Progression** | Earn OXP and gold on task completion, level up your character |
| 🧠 **Skill System** | Track custom skills (Programming, Mind, Strength, etc.) with XP and levels |
| 🔥 **Streaks** | Daily task streaks with bonus rewards at 7-day milestones |
| 🏆 **Achievements** | Unlock achievements for milestones like First Task, Gold Collector, 7 Day Discipline |
| 📅 **Daily Login Reward** | Consecutive login streaks give increasing gold and OXP bonuses |
| 🗺 **Habit Heatmap** | GitHub-style contribution graph showing task completion over the past year |
| 📜 **Task History Log** | Full scrollable log of every completed task with date and difficulty |
| 🛒 **Skill Boost Shop** | Spend gold to instantly boost skill XP |
| 📊 **Stats Screen** | View character level, skill progress bars, and achievements |
| 📈 **Difficulty Graph** | Bar chart breakdown of tasks by difficulty |

---

## Tech Stack

- **Python 3** — core language
- **tkinter** — desktop UI (built-in, no install needed)
- **SQLite** — local database via `sqlite3` (built-in)
- **matplotlib** — heatmap and graphs
- **numpy** — heatmap grid calculations

---

## Project Structure

```
SukhaOS/
│
├── main.py          # Entry point, app initialization
├── layout.py        # All UI — frames, buttons, popups, screens
├── game_engine.py   # XP, leveling, rewards, streak logic
├── database.py      # All SQLite operations
├── heatmap.py       # GitHub-style habit heatmap
└── sukhaos.db       # Auto-generated SQLite database
```

---

## How to Run

**Requirements:**
- Python 3.8+
- matplotlib (`pip install matplotlib`)
- numpy (`pip install numpy`)

**Steps:**
```bash
# Clone the repo
git clone https://github.com/yourusername/SukhaOS.git
cd SukhaOS

# Install dependencies
pip install matplotlib numpy

# Run the app
python main.py
```

The database (`sukhaos.db`) is created automatically on first launch with default skills and achievements.

---

## How It Works

### Task Completion Flow
1. You click **Pending** on a task card → `complete_task()` in `layout.py` fires
2. `game_engine.py` validates the task, adds OXP + gold to the player, updates skill XP
3. Streak logic checks `last_completed` date — consecutive days increment the streak
4. Level up check runs — if OXP threshold is crossed, character levels up
5. Task logged to `task_history`, UI refreshes

### Reward Scaling
Tasks are scaled by period and difficulty:

| Period | Gold | OXP | Skill XP |
|---|---|---|---|
| Daily | 20 | 20 | 10 |
| Weekly | 50 | 60 | 25 |
| Monthly | 120 | 150 | 60 |
| Yearly | 500 | 500 | 200 |

Difficulty multipliers: Easy ×0.8 / Medium ×1.0 / Hard ×1.5

### Leveling Formula
- **Character level up:** `required OXP = 100 + (level - 1) × 50`
- **Skill level up:** `required SXP = 50 + (level - 1) × 25`

---


## About

Built by a self-taught developer as a personal productivity tool and portfolio project. Started from scratch with no prior CS background — every feature was researched, debugged, and shipped one day at a time.

> *"Discipline is doing what needs to be done even when you don't want to."*

---

## License

MIT License — free to use, modify, and distribute.
