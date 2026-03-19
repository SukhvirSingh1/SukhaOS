"""
database.py
===========
Handles all SQLite database operations for SukhaOS.
Responsible for creating tables, seeding default data,
and providing read/write methods for all entities:
player, tasks, skills, achievements, and task history.

The database file (sukhaos.db) is created automatically
on first run in the same directory as this file.
"""

import sqlite3


class Database:
    """
    SQLite database interface for SukhaOS.
    All UI and game engine interactions with persistent data
    go through this class.
    """

    def __init__(self, db_name="sukhaos.db"):
        """
        Connect to the SQLite database and initialise all tables.

        Args:
            db_name (str): Filename for the SQLite database. Defaults to 'sukhaos.db'.
        """
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    # -------------------------------------------------------------------------
    # TABLE CREATION & SEEDING
    # -------------------------------------------------------------------------

    def create_tables(self):
        """
        Create all required tables if they don't already exist.
        Also seeds default player record, skills, and achievements on first run.
        Uses ALTER TABLE to safely add new columns to existing databases
        without breaking older installs.
        """
        cursor = self.conn.cursor()

        # Player table — single row, always id=1
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player (
                id INTEGER PRIMARY KEY,
                oxp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                gold INTEGER DEFAULT 0
            )
        ''')

        # Skills table — one row per skill, name must be unique
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skill (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1
            )
        ''')

        # Tasks table — stores all user-created tasks
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task (
                id INTEGER PRIMARY KEY,
                title TEXT,
                description TEXT,
                period TEXT,
                difficulty TEXT DEFAULT "medium",
                oxp INTEGER DEFAULT 0,
                gold INTEGER DEFAULT 0,
                status TEXT DEFAULT "Pending",
                last_completed TEXT,
                Streak INTEGER DEFAULT 0
            )
        ''')

        # Task rewards — links tasks to skills with SXP amounts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_reward (
                task_id INTEGER,
                skill_name TEXT,
                sxp INTEGER DEFAULT 0
            )
        ''')

        # Achievements table — predefined, unlocked via gameplay
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievement (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                unlocked INTEGER DEFAULT 0
            )
        ''')

        # Task history — log of every completed task
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                title TEXT,
                difficulty TEXT,
                date_completed TEXT
            )
        ''')

        # --- Safely add new columns to existing databases ---
        new_columns = [
            ("ALTER TABLE player ADD COLUMN last_login TEXT",),
            ("ALTER TABLE player ADD COLUMN login_streak INTEGER DEFAULT 0",),
            ("ALTER TABLE player ADD COLUMN name TEXT DEFAULT 'Hero'",),
            ("ALTER TABLE player ADD COLUMN current_hp INTEGER DEFAULT 100",),
            ("ALTER TABLE player ADD COLUMN max_hp INTEGER DEFAULT 100",),
        ]
        for (sql,) in new_columns:
            try:
                cursor.execute(sql)
            except:
                pass  # column already exists — skip silently

        # --- Seed default player if none exists ---
        cursor.execute("SELECT COUNT(*) FROM player")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO player (id, oxp, level, gold, current_hp, max_hp)
                VALUES (1, 0, 1, 0, 100, 100)
            """)

        # --- Seed default skills ---
        default_skills = ["Mind", "Health", "Strength", "IQ", "Programming", "Editing"]
        for skill in default_skills:
            cursor.execute(
                "INSERT OR IGNORE INTO skill (name, xp, level) VALUES (?, 0, 1)", (skill,)
            )

        # --- Seed default achievements if none exist ---
        cursor.execute("SELECT COUNT(*) FROM achievement")
        if cursor.fetchone()[0] == 0:
            achievements = [
                ("First Task",       "Complete your first task"),
                ("7 Day Discipline", "Reach a 7-day streak on a daily task"),
                ("Gold Collector",   "Earn 500 total gold"),
                ("Mind Level 5",     "Reach Mind skill level 5"),
            ]
            for title, desc in achievements:
                cursor.execute(
                    "INSERT INTO achievement(title, description) VALUES (?, ?)", (title, desc)
                )

        self.conn.commit()

    # -------------------------------------------------------------------------
    # PLAYER
    # -------------------------------------------------------------------------

    def get_player(self):
        """
        Fetch the single player record from the database.

        Returns:
            dict: Player data with all keys including name, current_hp, max_hp.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM player LIMIT 1")
        row = cursor.fetchone()

        if row is None:
            cursor.execute("""
                INSERT INTO player (id, oxp, level, gold, current_hp, max_hp)
                VALUES (1, 0, 1, 0, 100, 100)
            """)
            self.conn.commit()
            cursor.execute("SELECT * FROM player LIMIT 1")
            row = cursor.fetchone()

        return {
            "id":           row[0],
            "oxp":          row[1],
            "level":        row[2],
            "gold":         row[3],
            "last_login":   row[4] if len(row) > 4 else None,
            "login_streak": row[5] if len(row) > 5 else 0,
            "name":         row[6] if len(row) > 6 else "Hero",
            "current_hp":   row[7] if len(row) > 7 else 100,
            "max_hp":       row[8] if len(row) > 8 else 100,
        }

    def update_player(self, player):
        """
        Save updated player data back to the database.

        Args:
            player (dict): Player dict with all keys.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE player
            SET oxp=?, level=?, gold=?, current_hp=?, max_hp=?
            WHERE id=?
        """, (
            player["oxp"],
            player["level"],
            player["gold"],
            player["current_hp"],
            player["max_hp"],
            player["id"]
        ))
        self.conn.commit()

    def set_player_name(self, name):
        """
        Set the player's character name.
        Called once on first launch from the name setup popup.

        Args:
            name (str): The chosen character name.
        """
        cursor = self.conn.cursor()
        cursor.execute("UPDATE player SET name=? WHERE id=1", (name,))
        self.conn.commit()

    def update_hp(self, current_hp, max_hp):
        """
        Update the player's current and max HP directly.
        Used when HP changes outside of a full player update.

        Args:
            current_hp (int): New current HP value.
            max_hp (int): New max HP value.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE player SET current_hp=?, max_hp=? WHERE id=1",
            (current_hp, max_hp)
        )
        self.conn.commit()

    def update_login(self, last_login, login_streak):
        """
        Update the player's last login date and login streak count.

        Args:
            last_login (str): Today's date in 'YYYY-MM-DD' format.
            login_streak (int): Current consecutive login day count.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE player SET last_login=?, login_streak=? WHERE id=1",
            (last_login, login_streak)
        )
        self.conn.commit()

    # -------------------------------------------------------------------------
    # TASKS
    # -------------------------------------------------------------------------

    def get_task(self, task_id):
        """
        Fetch a single task by ID.

        Args:
            task_id (int): The task's primary key.

        Returns:
            dict: Task data, or None if not found.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, title, description, period, oxp, gold,
                   status, last_completed, streak, difficulty
            FROM task WHERE id=?
        """, (task_id,))
        row = cursor.fetchone()

        if row is None:
            return None

        return {
            "id":             row[0],
            "title":          row[1],
            "description":    row[2],
            "period":         row[3],
            "oxp":            row[4],
            "gold":           row[5],
            "status":         row[6],
            "last_completed": row[7],
            "streak":         row[8],
            "difficulty":     row[9]
        }

    def get_tasks_by_period(self, period):
        """
        Fetch all tasks for a given time period.

        Args:
            period (str): One of 'daily', 'weekly', 'monthly', 'yearly'.

        Returns:
            list of dicts: Each dict contains task data for display in the UI.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, title, description, status, streak, difficulty
            FROM task WHERE period=?
        """, (period,))
        rows = cursor.fetchall()

        return [{
            "id":          row[0],
            "title":       row[1],
            "description": row[2],
            "period":      period,
            "status":      row[3],
            "streak":      row[4],
            "difficulty":  row[5]
        } for row in rows]

    def add_task(self, title, description, period, difficulty, oxp, gold):
        """
        Insert a new task into the database.

        Args:
            title (str): Task title.
            description (str): Short description of the task.
            period (str): 'daily', 'weekly', 'monthly', or 'yearly'.
            difficulty (str): 'Easy', 'Medium', or 'Hard'.
            oxp (int): OXP reward amount.
            gold (int): Gold reward amount.

        Returns:
            int: The new task's ID.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO task(title, description, period, difficulty, oxp, gold, status)
            VALUES(?, ?, ?, ?, ?, ?, 'Pending')
        """, (title, description, period, difficulty, oxp, gold))
        self.conn.commit()
        return cursor.lastrowid

    def update_task(self, task_id, title, description, period):
        """
        Update an existing task's title, description, and period.

        Args:
            task_id (int): ID of the task to update.
            title (str): New title.
            description (str): New description.
            period (str): New period.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE task SET title=?, description=?, period=?
            WHERE id=?
        """, (title, description, period, task_id))
        self.conn.commit()

    def delete_task(self, task_id):
        """
        Permanently delete a task and its associated rewards.

        Args:
            task_id (int): ID of the task to delete.
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM task_reward WHERE task_id=?", (task_id,))
        cursor.execute("DELETE FROM task WHERE id=?", (task_id,))
        self.conn.commit()

    def mark_task_completed(self, task_id):
        """
        Set a task's status to 'Completed' and record today's date.

        Args:
            task_id (int): ID of the task to mark complete.
        """
        from datetime import date
        today = date.today().isoformat()
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE task SET status='Completed', last_completed=? WHERE id=?",
            (today, task_id)
        )
        self.conn.commit()

    def update_task_streak(self, task_id, streak):
        """
        Update the streak count for a task.

        Args:
            task_id (int): ID of the task.
            streak (int): New streak value.
        """
        cursor = self.conn.cursor()
        cursor.execute("UPDATE task SET streak=? WHERE id=?", (streak, task_id))
        self.conn.commit()

    def reset_tasks(self):
        """
        Reset tasks to 'Pending' if their period has elapsed since last completion.
        Called once on app startup.
        """
        from datetime import date, datetime
        today = date.today()
        cursor = self.conn.cursor()

        cursor.execute("SELECT id, period, last_completed FROM task")
        tasks = cursor.fetchall()

        for task_id, period, last_completed in tasks:
            if last_completed is None:
                continue

            last_date = datetime.strptime(last_completed, "%Y-%m-%d").date()
            reset = False

            if period == "daily":
                reset = last_date != today
            elif period == "weekly":
                reset = (last_date.isocalendar()[1] != today.isocalendar()[1]
                         or last_date.year != today.year)
            elif period == "monthly":
                reset = (last_date.month != today.month
                         or last_date.year != today.year)
            elif period == "yearly":
                reset = last_date.year != today.year

            if reset:
                cursor.execute("UPDATE task SET status='Pending' WHERE id=?", (task_id,))

        self.conn.commit()

    # -------------------------------------------------------------------------
    # TASK REWARDS
    # -------------------------------------------------------------------------

    def get_task_rewards(self, task_id):
        """
        Fetch all skill rewards linked to a task.

        Args:
            task_id (int): ID of the task.

        Returns:
            list of dicts: Each with 'skill_name' and 'sxp' keys.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT skill_name, sxp FROM task_reward WHERE task_id=?", (task_id,)
        )
        return [{"skill_name": r[0], "sxp": r[1]} for r in cursor.fetchall()]

    def add_task_reward(self, task_id, skill_name, sxp):
        """
        Link a skill reward to a task.

        Args:
            task_id (int): ID of the task.
            skill_name (str): Name of the skill to reward.
            sxp (int): Amount of skill XP to award on completion.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO task_reward(task_id, skill_name, sxp)
            VALUES(?, ?, ?)
        """, (task_id, skill_name, sxp))
        self.conn.commit()

    # -------------------------------------------------------------------------
    # SKILLS
    # -------------------------------------------------------------------------

    def get_all_skills(self):
        """
        Fetch all skills from the database.

        Returns:
            list of dicts: Each with 'name', 'xp', and 'level' keys.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, xp, level FROM skill")
        return [{"name": r[0], "xp": r[1], "level": r[2]} for r in cursor.fetchall()]

    def get_skill(self, skill_name):
        """
        Fetch a single skill by name. Creates the skill if it doesn't exist.

        Args:
            skill_name (str): The skill's name.

        Returns:
            dict: Skill data with 'id', 'name', 'xp', 'level' keys.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM skill WHERE name=?", (skill_name,))
        row = cursor.fetchone()

        if row is None:
            cursor.execute(
                "INSERT INTO skill (name, xp, level) VALUES (?, 0, 1)", (skill_name,)
            )
            self.conn.commit()
            return {"name": skill_name, "xp": 0, "level": 1}

        return {"id": row[0], "name": row[1], "xp": row[2], "level": row[3]}

    def update_skill(self, skill):
        """
        Save updated skill XP and level to the database.

        Args:
            skill (dict): Skill dict with 'xp', 'level', and 'name' keys.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE skill SET xp=?, level=? WHERE name=?",
            (skill["xp"], skill["level"], skill["name"])
        )
        self.conn.commit()

    def add_skill(self, skill_name):
        """
        Add a new custom skill. Prevents duplicates.

        Args:
            skill_name (str): Name of the new skill.

        Returns:
            True if added, False if duplicate.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM skill WHERE name=?", (skill_name,))
        if cursor.fetchone():
            return False

        cursor.execute(
            "INSERT INTO skill(name, xp, level) VALUES (?, 0, 1)", (skill_name,)
        )
        self.conn.commit()
        return True

    def delete_skill(self, skill_name):
        """
        Delete a skill from the database.

        Args:
            skill_name (str): Name of the skill to delete.
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM skill WHERE name=?", (skill_name,))
        self.conn.commit()

    # -------------------------------------------------------------------------
    # ACHIEVEMENTS
    # -------------------------------------------------------------------------

    def unlock_achievement(self, title):
        """
        Mark an achievement as unlocked.

        Args:
            title (str): The achievement title to unlock.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE achievement SET unlocked=1 WHERE title=?", (title,)
        )
        self.conn.commit()

    def get_achievement(self):
        """
        Fetch all achievements with their unlock status.

        Returns:
            list of dicts: Each with 'title', 'description', 'unlocked' keys.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT title, description, unlocked FROM achievement")
        return [{"title": r[0], "description": r[1], "unlocked": r[2]}
                for r in cursor.fetchall()]

    # -------------------------------------------------------------------------
    # TASK HISTORY
    # -------------------------------------------------------------------------

    def get_task_history(self):
        """
        Fetch all completed task history entries, most recent first.

        Returns:
            list of tuples: Each tuple is (title, difficulty, date_completed).
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT title, difficulty, date_completed
            FROM task_history
            ORDER BY date_completed DESC
        """)
        return cursor.fetchall()

    # -------------------------------------------------------------------------
    # UTILITY
    # -------------------------------------------------------------------------

    def commit(self):
        """Manually commit any pending database transactions."""
        self.conn.commit()