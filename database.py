"""
database.py
===========
Handles all SQLite database operations for SukhaOS.
"""

import sqlite3
import json
import os
import shutil
from datetime import datetime, date, timedelta


class Database:
    def __init__(self, db_name="sukhaos.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    # -------------------------------------------------------------------------
    # TABLE CREATION & SEEDING
    # -------------------------------------------------------------------------

    def create_tables(self):
        """Create all tables and seed defaults on first run."""
        cursor = self.conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player (
                id INTEGER PRIMARY KEY,
                oxp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                gold INTEGER DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skill (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1
            )
        ''')
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
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_reward (
                task_id INTEGER,
                skill_name TEXT,
                sxp INTEGER DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quest (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT UNIQUE,
                description TEXT,
                category TEXT DEFAULT 'general',
                difficulty TEXT DEFAULT 'medium',
                quest_type TEXT DEFAULT 'standard',
                branch_a_name TEXT DEFAULT '',
                branch_a_style TEXT DEFAULT '',
                branch_b_name TEXT DEFAULT '',
                branch_b_style TEXT DEFAULT '',
                selected_branch TEXT DEFAULT '',
                progress_mode TEXT DEFAULT 'all_tasks',
                target_count INTEGER DEFAULT 0,
                oxp_reward INTEGER DEFAULT 0,
                gold_reward INTEGER DEFAULT 0,
                attack_reward INTEGER DEFAULT 0,
                status TEXT DEFAULT 'Active',
                created_at TEXT,
                completed_at TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quest_task (
                quest_id INTEGER,
                task_id INTEGER,
                UNIQUE(quest_id, task_id)
            )
        ''')

        # Achievement table — title is UNIQUE to prevent duplicates
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievement (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT UNIQUE,
                description TEXT,
                category TEXT DEFAULT "general",
                unlocked INTEGER DEFAULT 0
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                title TEXT,
                difficulty TEXT,
                date_completed TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS boss (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                tier TEXT,
                hp INTEGER,
                max_hp INTEGER,
                attack_damage INTEGER,
                level_trigger INTEGER,
                defeated INTEGER DEFAULT 0,
                spawned INTEGER DEFAULT 0,
                date_spawned TEXT,
                taunt TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_focus (
                focus_date TEXT PRIMARY KEY,
                streak INTEGER DEFAULT 0,
                completed INTEGER DEFAULT 0,
                claimed INTEGER DEFAULT 0,
                completed_at TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_focus_item (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                focus_date TEXT,
                slot_name TEXT,
                category TEXT,
                task_id INTEGER,
                task_title TEXT,
                task_period TEXT,
                task_difficulty TEXT,
                status TEXT DEFAULT 'Pending',
                UNIQUE(focus_date, slot_name)
            )
        ''')

        # --- Safely add new columns to existing databases ---
        new_columns =[
            "ALTER TABLE player ADD COLUMN last_login TEXT",
            "ALTER TABLE player ADD COLUMN login_streak INTEGER DEFAULT 0",
            "ALTER TABLE player ADD COLUMN name TEXT DEFAULT 'Hero'",
            "ALTER TABLE player ADD COLUMN current_hp INTEGER DEFAULT 100",
            "ALTER TABLE player ADD COLUMN max_hp INTEGER DEFAULT 100",
            "ALTER TABLE player ADD COLUMN attack_points INTEGER DEFAULT 0",
            "ALTER TABLE player ADD COLUMN total_gold_earned INTEGER DEFAULT 0",
            "ALTER TABLE player ADD COLUMN gold_spent INTEGER DEFAULT 0",
            "ALTER TABLE player ADD COLUMN bosses_defeated INTEGER DEFAULT 0",
            "ALTER TABLE player ADD COLUMN armor_name TEXT DEFAULT 'Cloth Armor'",
            "ALTER TABLE player ADD COLUMN armor_bonus_hp INTEGER DEFAULT 0",
            "ALTER TABLE player ADD COLUMN sword_name TEXT DEFAULT 'Training Sword'",
            "ALTER TABLE player ADD COLUMN sword_bonus_damage INTEGER DEFAULT 0",
            "ALTER TABLE player ADD COLUMN onboarding_seen INTEGER DEFAULT 0",
            "ALTER TABLE skill ADD COLUMN is_core INTEGER DEFAULT 0",
            "ALTER TABLE achievement ADD COLUMN category TEXT DEFAULT 'general'",
            "ALTER TABLE quest ADD COLUMN quest_type TEXT DEFAULT 'standard'",
            "ALTER TABLE quest ADD COLUMN branch_a_name TEXT DEFAULT ''",
            "ALTER TABLE quest ADD COLUMN branch_a_style TEXT DEFAULT ''",
            "ALTER TABLE quest ADD COLUMN branch_b_name TEXT DEFAULT ''",
            "ALTER TABLE quest ADD COLUMN branch_b_style TEXT DEFAULT ''",
            "ALTER TABLE quest ADD COLUMN selected_branch TEXT DEFAULT ''",
        ]
        for sql in new_columns:
            try:
                cursor.execute(sql)
            except:
                pass

        # --- Seed default player ---
        cursor.execute("SELECT COUNT(*) FROM player")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO player (id, oxp, level, gold, current_hp, max_hp, attack_points)
                VALUES (1, 0, 1, 0, 100, 100, 0)
            """)

        # --- Seed default skills ---
        CORE_SKILLS    = {"Mind", "Health", "Strength"}
        default_skills = ["Mind", "Health", "Strength", "IQ", "Programming", "Editing"]
        for skill in default_skills:
            is_core = 1 if skill in CORE_SKILLS else 0
            cursor.execute(
                "INSERT OR IGNORE INTO skill (name, xp, level, is_core) VALUES (?, 0, 1, ?)",
                (skill, is_core)
            )
        for skill in CORE_SKILLS:
            cursor.execute("UPDATE skill SET is_core=1 WHERE name=?", (skill,))

        # --- Seed all 24 achievements ---
        # INSERT OR IGNORE means if title already exists it is skipped entirely
        # This is the ONLY place achievements are inserted — no UPDATE statements
        # that could cause issues
        all_achievements = [
            # Tasks
            ("First Task",       "Complete your first task",             "tasks"),
            ("Getting Started",  "Complete 10 tasks total",              "tasks"),
            ("Halfway There",    "Complete 50 tasks total",              "tasks"),
            ("Century",          "Complete 100 tasks total",             "tasks"),
            ("Hard Worker",      "Complete a Hard difficulty task",       "tasks"),
            ("Triple Threat",    "Complete 3 tasks in a single day",     "tasks"),
            # Streaks
            ("Consistent",       "Reach a 3-day login streak",           "streaks"),
            ("7 Day Discipline", "Reach a 7-day streak on a daily task", "streaks"),
            ("Two Weeks Strong", "Reach a 14-day streak on a daily task","streaks"),
            ("Dedicated",        "Reach a 30-day login streak",          "streaks"),
            # Levels
            ("Rising",           "Reach character level 5",              "levels"),
            ("Veteran",          "Reach character level 10",             "levels"),
            ("Elite",            "Reach character level 25",             "levels"),
            # Gold
            ("Gold Collector",   "Earn 500 total gold",                  "gold"),
            ("Rich",             "Earn 1000 total gold",                 "gold"),
            ("Big Spender",      "Spend 500 gold in the shop",           "gold"),
            # Skills
            ("Mind Level 5",     "Reach Mind skill level 5",             "skills"),
            ("Master",           "Max any skill to level 10",            "skills"),
            ("Well Rounded",     "Have 3 skills at level 5 or higher",   "skills"),
            ("Creator",          "Add a custom skill",                   "skills"),
            # Bosses
            ("Boss Slayer",      "Defeat your first boss",               "bosses"),
            ("Giant Killer",     "Defeat a Hard boss",                   "bosses"),
            ("Boss Hunter",      "Defeat 3 bosses total",                "bosses"),
            ("Near Death",       "Survive a boss fight at 1 HP",         "bosses"),
        ]

        for title, desc, category in all_achievements:
            cursor.execute("""
                INSERT OR IGNORE INTO achievement(title, description, category)
                VALUES (?, ?, ?)
            """, (title, desc, category))

        # Fix category on any existing rows that had no category set
        # Safe to run every launch — only updates rows where category is null/empty
        cursor.execute("""
            UPDATE achievement SET category='tasks'
            WHERE category IS NULL OR category=''
            AND title IN ('First Task','Getting Started','Halfway There',
                          'Century','Hard Worker','Triple Threat')
        """)

        self.conn.commit()

    # -------------------------------------------------------------------------
    # PLAYER
    # -------------------------------------------------------------------------

    def get_player(self):
        """Fetch the player record."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM player LIMIT 1")
        row = cursor.fetchone()
        if row is None:
            cursor.execute("""
                INSERT INTO player (id, oxp, level, gold, current_hp, max_hp, attack_points)
                VALUES (1, 0, 1, 0, 100, 100, 0)
            """)
            self.conn.commit()
            cursor.execute("SELECT * FROM player LIMIT 1")
            row = cursor.fetchone()

        return {
            "id":                row[0],
            "oxp":               row[1],
            "level":             row[2],
            "gold":              row[3],
            "last_login":        row[4]  if len(row) > 4  else None,
            "login_streak":      row[5]  if len(row) > 5  else 0,
            "name":              row[6]  if len(row) > 6  else "Hero",
            "current_hp":        row[7]  if len(row) > 7  else 100,
            "max_hp":            row[8]  if len(row) > 8  else 100,
            "attack_points":     row[9]  if len(row) > 9  else 0,
            "total_gold_earned": row[10] if len(row) > 10 else 0,
            "gold_spent":        row[11] if len(row) > 11 else 0,
            "bosses_defeated":   row[12] if len(row) > 12 else 0,
            "armor_name":        row[13] if len(row) > 13 and row[13] else "Cloth Armor",
            "armor_bonus_hp":    row[14] if len(row) > 14 and row[14] is not None else 0,
            "sword_name":        row[15] if len(row) > 15 and row[15] else "Training Sword",
            "sword_bonus_damage": row[16] if len(row) > 16 and row[16] is not None else 0,
            "onboarding_seen":   bool(row[17]) if len(row) > 17 else False,
        }

    def update_player(self, player):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE player
            SET oxp=?, level=?, gold=?, current_hp=?, max_hp=?,
                attack_points=?, total_gold_earned=?, gold_spent=?, bosses_defeated=?,
                armor_name=?, armor_bonus_hp=?, sword_name=?, sword_bonus_damage=?
            WHERE id=?
        """, (
            player["oxp"], player["level"], player["gold"],
            player["current_hp"], player["max_hp"], player["attack_points"],
            player.get("total_gold_earned", 0),
            player.get("gold_spent", 0),
            player.get("bosses_defeated", 0),
            player.get("armor_name", "Cloth Armor"),
            player.get("armor_bonus_hp", 0),
            player.get("sword_name", "Training Sword"),
            player.get("sword_bonus_damage", 0),
            player["id"]
        ))
        self.conn.commit()

    def set_player_name(self, name):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE player SET name=? WHERE id=1", (name,))
        self.conn.commit()

    def set_onboarding_seen(self, seen=True):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE player SET onboarding_seen=? WHERE id=1", (1 if seen else 0,))
        self.conn.commit()

    def update_hp(self, current_hp, max_hp):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE player SET current_hp=?, max_hp=? WHERE id=1",
            (current_hp, max_hp)
        )
        self.conn.commit()

    def update_login(self, last_login, login_streak):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE player SET last_login=?, login_streak=? WHERE id=1",
            (last_login, login_streak)
        )
        self.conn.commit()

    # -------------------------------------------------------------------------
    # BOSS
    # -------------------------------------------------------------------------

    def get_active_boss(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, name, tier, hp, max_hp, attack_damage,
                   level_trigger, defeated, spawned, date_spawned, taunt
            FROM boss WHERE spawned=1 AND defeated=0 LIMIT 1
        """)
        row = cursor.fetchone()
        if row is None:
            return None
        return {
            "id": row[0], "name": row[1], "tier": row[2],
            "hp": row[3], "max_hp": row[4], "attack_damage": row[5],
            "level_trigger": row[6], "defeated": row[7],
            "spawned": row[8], "date_spawned": row[9], "taunt": row[10],
        }

    def spawn_boss(self, name, tier, hp, attack_damage, level_trigger, taunt):
        from datetime import date
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO boss (name, tier, hp, max_hp, attack_damage,
                              level_trigger, defeated, spawned, date_spawned, taunt)
            VALUES (?, ?, ?, ?, ?, ?, 0, 1, ?, ?)
        """, (name, tier, hp, hp, attack_damage, level_trigger,
              date.today().isoformat(), taunt))
        self.conn.commit()

    def update_boss_hp(self, boss_id, hp):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE boss SET hp=? WHERE id=?", (hp, boss_id))
        self.conn.commit()

    def defeat_boss(self, boss_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE boss SET defeated=1, spawned=0 WHERE id=?", (boss_id,)
        )
        self.conn.commit()

    def boss_already_spawned_for_level(self, level_trigger):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM boss WHERE level_trigger=?", (level_trigger,)
        )
        return cursor.fetchone()[0] > 0

    def get_bosses_defeated_count(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM boss WHERE defeated=1")
        return cursor.fetchone()[0]

    # -------------------------------------------------------------------------
    # TASKS
    # -------------------------------------------------------------------------

    def get_task(self, task_id):
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
            "id": row[0], "title": row[1], "description": row[2],
            "period": row[3], "oxp": row[4], "gold": row[5],
            "status": row[6], "last_completed": row[7],
            "streak": row[8], "difficulty": row[9]
        }

    def get_tasks_by_period(self, period):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, title, description, status, streak, difficulty
            FROM task WHERE period=?
        """, (period,))
        return [{
            "id": r[0], "title": r[1], "description": r[2],
            "period": period, "status": r[3], "streak": r[4], "difficulty": r[5]
        } for r in cursor.fetchall()]

    def add_task(self, title, description, period, difficulty, oxp, gold):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO task(title, description, period, difficulty, oxp, gold, status)
            VALUES(?, ?, ?, ?, ?, ?, 'Pending')
        """, (title, description, period, difficulty, oxp, gold))
        self.conn.commit()
        return cursor.lastrowid

    def update_task(self, task_id, title, description, period):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE task SET title=?, description=?, period=? WHERE id=?",
            (title, description, period, task_id)
        )
        self.conn.commit()

    def delete_task(self, task_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM task_reward WHERE task_id=?", (task_id,))
        cursor.execute("DELETE FROM quest_task WHERE task_id=?", (task_id,))
        cursor.execute("DELETE FROM task WHERE id=?", (task_id,))
        self.conn.commit()
        self.delete_daily_focus_task(task_id)

    def mark_task_completed(self, task_id):
        from datetime import date
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE task SET status='Completed', last_completed=? WHERE id=?",
            (date.today().isoformat(), task_id)
        )
        self.conn.commit()

    def update_task_streak(self, task_id, streak):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE task SET streak=? WHERE id=?", (streak, task_id))
        self.conn.commit()

    def reset_tasks(self):
        from datetime import date, datetime
        today = date.today()
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, period, last_completed FROM task")
        for task_id, period, last_completed in cursor.fetchall():
            if not last_completed:
                continue
            last_date = datetime.strptime(last_completed, "%Y-%m-%d").date()
            reset = False
            if period == "daily":
                reset = last_date != today
            elif period == "weekly":
                reset = (last_date.isocalendar()[1] != today.isocalendar()[1]
                         or last_date.year != today.year)
            elif period == "monthly":
                reset = last_date.month != today.month or last_date.year != today.year
            elif period == "yearly":
                reset = last_date.year != today.year
            if reset:
                cursor.execute("UPDATE task SET status='Pending' WHERE id=?", (task_id,))
        self.conn.commit()

    def get_total_tasks_completed(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM task_history")
        return cursor.fetchone()[0]

    def get_tasks_completed_today(self):
        from datetime import date
        today = date.today().isoformat()
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM task_history WHERE date_completed=?", (today,)
        )
        return cursor.fetchone()[0]

    def get_max_task_streak(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(streak) FROM task")
        result = cursor.fetchone()[0]
        return result or 0

    # -------------------------------------------------------------------------
    # DAILY FOCUS
    # -------------------------------------------------------------------------

    def get_daily_focus(self, focus_date=None):
        focus_date = focus_date or date.today().isoformat()
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT focus_date, streak, completed, claimed, completed_at
            FROM daily_focus
            WHERE focus_date=?
        """, (focus_date,))
        focus_row = cursor.fetchone()
        if focus_row is None:
            return None

        cursor.execute("""
            SELECT slot_name, category, task_id, task_title, task_period,
                   task_difficulty, status
            FROM daily_focus_item
            WHERE focus_date=?
            ORDER BY
                CASE slot_name
                    WHEN 'mind' THEN 1
                    WHEN 'body' THEN 2
                    WHEN 'life' THEN 3
                    ELSE 4
                END
        """, (focus_date,))
        items = [{
            "slot_name": row[0],
            "category": row[1],
            "task_id": row[2],
            "task_title": row[3],
            "task_period": row[4],
            "task_difficulty": row[5],
            "status": row[6],
        } for row in cursor.fetchall()]

        completed_count = sum(1 for item in items if item["status"] == "Completed")
        return {
            "focus_date": focus_row[0],
            "streak": focus_row[1] or 0,
            "completed": bool(focus_row[2]),
            "claimed": bool(focus_row[3]),
            "completed_at": focus_row[4],
            "items": items,
            "completed_count": completed_count,
            "total_count": len(items),
        }

    def save_daily_focus(self, focus_date, items, streak=0):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO daily_focus(focus_date, streak, completed, claimed, completed_at)
            VALUES (?, ?, 0, 0, NULL)
        """, (focus_date, streak))
        cursor.execute("DELETE FROM daily_focus_item WHERE focus_date=?", (focus_date,))
        for item in items:
            cursor.execute("""
                INSERT INTO daily_focus_item(
                    focus_date, slot_name, category, task_id, task_title,
                    task_period, task_difficulty, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                focus_date,
                item["slot_name"],
                item["category"],
                item["task_id"],
                item["task_title"],
                item["task_period"],
                item["task_difficulty"],
                item.get("status", "Pending"),
            ))
        self.conn.commit()

    def get_last_completed_daily_focus(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT focus_date, streak
            FROM daily_focus
            WHERE completed=1
            ORDER BY focus_date DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        if row is None:
            return None
        return {"focus_date": row[0], "streak": row[1] or 0}

    def get_latest_daily_focus(self, before_date=None):
        cursor = self.conn.cursor()
        if before_date:
            cursor.execute("""
                SELECT focus_date, streak, completed, claimed, completed_at
                FROM daily_focus
                WHERE focus_date < ?
                ORDER BY focus_date DESC
                LIMIT 1
            """, (before_date,))
        else:
            cursor.execute("""
                SELECT focus_date, streak, completed, claimed, completed_at
                FROM daily_focus
                ORDER BY focus_date DESC
                LIMIT 1
            """)
        row = cursor.fetchone()
        if row is None:
            return None
        return {
            "focus_date": row[0],
            "streak": row[1] or 0,
            "completed": bool(row[2]),
            "claimed": bool(row[3]),
            "completed_at": row[4],
        }

    def get_best_daily_focus_streak(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(streak) FROM daily_focus WHERE completed=1")
        result = cursor.fetchone()[0]
        return result or 0

    def mark_daily_focus_task_completed(self, task_id, focus_date=None):
        focus_date = focus_date or date.today().isoformat()
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE daily_focus_item
            SET status='Completed'
            WHERE focus_date=? AND task_id=?
        """, (focus_date, task_id))
        changed = cursor.rowcount > 0
        self.conn.commit()
        return changed

    def complete_daily_focus(self, focus_date=None, streak=1):
        focus_date = focus_date or date.today().isoformat()
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE daily_focus
            SET completed=1, streak=?, completed_at=?
            WHERE focus_date=?
        """, (streak, focus_date, focus_date))
        self.conn.commit()

    def claim_daily_focus(self, focus_date=None):
        focus_date = focus_date or date.today().isoformat()
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE daily_focus SET claimed=1 WHERE focus_date=?",
            (focus_date,)
        )
        self.conn.commit()

    def delete_daily_focus_task(self, task_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM daily_focus_item WHERE task_id=?", (task_id,))
        self.conn.commit()

    # -------------------------------------------------------------------------
    # TASK REWARDS
    # -------------------------------------------------------------------------

    def get_task_rewards(self, task_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT skill_name, sxp FROM task_reward WHERE task_id=?", (task_id,)
        )
        return [{"skill_name": r[0], "sxp": r[1]} for r in cursor.fetchall()]

    def add_task_reward(self, task_id, skill_name, sxp):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO task_reward(task_id, skill_name, sxp) VALUES(?, ?, ?)",
            (task_id, skill_name, sxp)
        )
        self.conn.commit()

    # -------------------------------------------------------------------------
    # SKILLS
    # -------------------------------------------------------------------------

    def get_all_skills(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, xp, level, is_core FROM skill")
        return [{"name": r[0], "xp": r[1], "level": r[2], "is_core": r[3]}
                for r in cursor.fetchall()]

    def get_skill(self, skill_name):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM skill WHERE name=?", (skill_name,))
        row = cursor.fetchone()
        if row is None:
            cursor.execute(
                "INSERT INTO skill (name, xp, level, is_core) VALUES (?, 0, 1, 0)",
                (skill_name,)
            )
            self.conn.commit()
            return {"name": skill_name, "xp": 0, "level": 1, "is_core": 0}
        return {
            "id": row[0], "name": row[1], "xp": row[2],
            "level": row[3], "is_core": row[4] if len(row) > 4 else 0
        }

    def update_skill(self, skill):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE skill SET xp=?, level=? WHERE name=?",
            (skill["xp"], skill["level"], skill["name"])
        )
        self.conn.commit()

    def add_skill(self, skill_name):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM skill WHERE name=?", (skill_name,))
        if cursor.fetchone():
            return False
        cursor.execute(
            "INSERT INTO skill(name, xp, level, is_core) VALUES (?, 0, 1, 0)",
            (skill_name,)
        )
        self.conn.commit()
        return True

    def delete_skill(self, skill_name):
        cursor = self.conn.cursor()
        cursor.execute("SELECT is_core FROM skill WHERE name=?", (skill_name,))
        row = cursor.fetchone()
        if row and row[0] == 1:
            return False
        cursor.execute("DELETE FROM skill WHERE name=?", (skill_name,))
        self.conn.commit()
        return True

    def get_skills_above_level(self, min_level):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM skill WHERE level >= ?", (min_level,))
        return cursor.fetchone()[0]

    def get_max_skill_level(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(level) FROM skill")
        result = cursor.fetchone()[0]
        return result or 0

    def get_custom_skill_count(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM skill WHERE is_core=0")
        return cursor.fetchone()[0]

    # -------------------------------------------------------------------------
    # ACHIEVEMENTS
    # -------------------------------------------------------------------------

    def unlock_achievement(self, title):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE achievement SET unlocked=1 WHERE title=?", (title,)
        )
        self.conn.commit()

    def get_achievement(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT title, description, unlocked, category
            FROM achievement
            ORDER BY category, unlocked DESC, title
        """)
        return [{
            "title":       r[0],
            "description": r[1],
            "unlocked":    r[2],
            "category":    r[3]
        } for r in cursor.fetchall()]

    def get_achievement_count(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM achievement WHERE unlocked=1")
        unlocked = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM achievement")
        total = cursor.fetchone()[0]
        return unlocked, total

    # -------------------------------------------------------------------------
    # TASK HISTORY
    # -------------------------------------------------------------------------

    def get_task_history(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT title, difficulty, date_completed
            FROM task_history ORDER BY date_completed DESC
        """)
        return cursor.fetchall()

    def get_weekly_review_summary(self):
        start_date = date.today() - timedelta(days=6)
        start_str = start_date.isoformat()
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM task_history
            WHERE date_completed >= ?
        """, (start_str,))
        tasks_completed = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT th.date_completed, COUNT(*)
            FROM task_history th
            WHERE th.date_completed >= ?
            GROUP BY th.date_completed
            ORDER BY th.date_completed
        """, (start_str,))
        daily_breakdown = [
            {"date": row[0], "count": row[1]}
            for row in cursor.fetchall()
        ]

        cursor.execute("""
            SELECT
                COALESCE(SUM(t.oxp), 0),
                COALESCE(SUM(t.gold), 0),
                COALESCE(SUM(CASE
                    WHEN LOWER(COALESCE(t.difficulty, 'medium')) = 'easy' THEN 5
                    WHEN LOWER(COALESCE(t.difficulty, 'medium')) = 'hard' THEN 15
                    ELSE 10
                END), 0)
            FROM task_history th
            JOIN task t ON t.id = th.task_id
            WHERE th.date_completed >= ?
        """, (start_str,))
        totals = cursor.fetchone() or (0, 0, 0)
        oxp_gained, gold_gained, attack_gained = totals

        cursor.execute("""
            SELECT t.period, COUNT(*)
            FROM task_history th
            JOIN task t ON t.id = th.task_id
            WHERE th.date_completed >= ?
            GROUP BY t.period
            ORDER BY COUNT(*) DESC, t.period
        """, (start_str,))
        period_rows = cursor.fetchall()
        period_breakdown = [{"period": row[0], "count": row[1]} for row in period_rows]
        strongest_period = period_rows[0][0] if period_rows else None

        cursor.execute("""
            SELECT tr.skill_name, COALESCE(SUM(tr.sxp), 0)
            FROM task_history th
            JOIN task_reward tr ON tr.task_id = th.task_id
            WHERE th.date_completed >= ?
            GROUP BY tr.skill_name
            ORDER BY SUM(tr.sxp) DESC, tr.skill_name
        """, (start_str,))
        skill_rows = cursor.fetchall()
        skill_breakdown = [{"skill": row[0], "xp": row[1]} for row in skill_rows]
        top_skill = (
            {"name": skill_rows[0][0], "xp": skill_rows[0][1]}
            if skill_rows else None
        )

        cursor.execute("""
            SELECT COUNT(*)
            FROM quest
            WHERE completed_at >= ?
        """, (start_str,))
        quests_completed = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT category, COUNT(*)
            FROM quest
            WHERE completed_at >= ?
            GROUP BY category
            ORDER BY COUNT(*) DESC, category
        """, (start_str,))
        quest_category_rows = cursor.fetchall()
        quest_category_breakdown = [
            {"category": row[0], "count": row[1]}
            for row in quest_category_rows
        ]
        top_category = quest_category_rows[0][0] if quest_category_rows else None

        return {
            "start_date": start_str,
            "end_date": date.today().isoformat(),
            "tasks_completed": tasks_completed,
            "quests_completed": quests_completed,
            "oxp_gained": oxp_gained,
            "gold_gained": gold_gained,
            "attack_gained": attack_gained,
            "daily_breakdown": daily_breakdown,
            "period_breakdown": period_breakdown,
            "skill_breakdown": skill_breakdown,
            "quest_category_breakdown": quest_category_breakdown,
            "top_skill": top_skill,
            "strongest_period": strongest_period,
            "top_category": top_category,
        }

    def get_progression_insights_summary(self):
        cursor = self.conn.cursor()
        player = self.get_player()

        cursor.execute("""
            SELECT
                COUNT(*),
                COALESCE(SUM(CASE WHEN status='Completed' THEN 1 ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN status!='Completed' THEN 1 ELSE 0 END), 0)
            FROM task
        """)
        task_totals = cursor.fetchone() or (0, 0, 0)
        total_tasks, completed_tasks, pending_tasks = task_totals

        cursor.execute("""
            SELECT LOWER(COALESCE(difficulty, 'medium')), COUNT(*)
            FROM task
            GROUP BY LOWER(COALESCE(difficulty, 'medium'))
            ORDER BY COUNT(*) DESC
        """)
        task_mix = [
            {"difficulty": row[0], "count": row[1]}
            for row in cursor.fetchall()
        ]

        cursor.execute("""
            SELECT LOWER(COALESCE(difficulty, 'medium')), COUNT(*)
            FROM task_history
            GROUP BY LOWER(COALESCE(difficulty, 'medium'))
            ORDER BY COUNT(*) DESC
        """)
        completed_difficulty_breakdown = [
            {"difficulty": row[0], "count": row[1]}
            for row in cursor.fetchall()
        ]

        cursor.execute("""
            SELECT
                COALESCE(SUM(t.oxp), 0),
                COALESCE(SUM(t.gold), 0),
                COALESCE(SUM(CASE
                    WHEN LOWER(COALESCE(t.difficulty, 'medium')) = 'easy' THEN 3
                    WHEN LOWER(COALESCE(t.difficulty, 'medium')) = 'hard' THEN 9
                    ELSE 6
                END), 0)
            FROM task_history th
            JOIN task t ON t.id = th.task_id
        """)
        task_reward_totals = cursor.fetchone() or (0, 0, 0)
        task_oxp_total, task_gold_total, task_attack_total = task_reward_totals

        cursor.execute("""
            SELECT
                COALESCE(SUM(oxp_reward), 0),
                COALESCE(SUM(gold_reward), 0),
                COALESCE(SUM(attack_reward), 0),
                COUNT(*)
            FROM quest
            WHERE status='Completed'
        """)
        quest_reward_totals = cursor.fetchone() or (0, 0, 0, 0)
        quest_oxp_total, quest_gold_total, quest_attack_total, completed_quests = quest_reward_totals

        cursor.execute("""
            SELECT COUNT(*)
            FROM quest
            WHERE status='Active'
        """)
        active_quests = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT
                COUNT(*),
                COALESCE(AVG(task_count), 0)
            FROM (
                SELECT qt.quest_id, COUNT(*) AS task_count
                FROM quest_task qt
                GROUP BY qt.quest_id
            )
        """)
        quest_structure = cursor.fetchone() or (0, 0)
        total_quest_paths = quest_structure[0] or 0
        avg_linked_tasks = round(quest_structure[1] or 0, 1)

        cursor.execute("""
            SELECT name, level, xp
            FROM skill
            ORDER BY level DESC, xp DESC, name ASC
            LIMIT 1
        """)
        top_skill_row = cursor.fetchone()
        top_skill = (
            {"name": top_skill_row[0], "level": top_skill_row[1], "xp": top_skill_row[2]}
            if top_skill_row else None
        )

        cursor.execute("SELECT COUNT(*) FROM skill")
        total_skills = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM skill WHERE level >= 5")
        skills_above_five = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM boss WHERE defeated=1")
        bosses_defeated = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM achievement WHERE unlocked=1")
        achievements_unlocked = cursor.fetchone()[0] or 0

        total_oxp_earned = task_oxp_total + quest_oxp_total
        total_gold_earned = player.get("total_gold_earned", 0)
        total_attack_earned = task_attack_total + quest_attack_total
        quest_share = round((quest_oxp_total / total_oxp_earned) * 100, 1) if total_oxp_earned > 0 else 0
        completion_rate = round((completed_tasks / total_tasks) * 100, 1) if total_tasks > 0 else 0
        net_gold = total_gold_earned - player.get("gold_spent", 0)

        balance_notes = []
        if total_tasks == 0:
            balance_notes.append("No tasks exist yet, so progression data is still waiting for your first loop.")
        if total_tasks > 0 and completion_rate < 40:
            balance_notes.append("Completion rate is low, which can mean the task list is growing faster than it is being cleared.")
        if total_tasks > 0 and completion_rate >= 75:
            balance_notes.append("Completion rate is strong, so the current pacing is supporting consistency well.")
        if total_gold_earned > 0 and player.get("gold_spent", 0) < total_gold_earned * 0.25:
            balance_notes.append("Gold spending is light compared to gold earned, so the shop economy may still have room for more sinks.")
        if completed_quests == 0 and active_quests > 0:
            balance_notes.append("Quests are active but none are finished yet, which may mean quest goals are still a bit long-term.")
        if bosses_defeated == 0 and player["level"] >= 10:
            balance_notes.append("The player has reached boss levels but has not defeated one yet, so combat pressure may be higher than payoff.")
        if not balance_notes:
            balance_notes.append("Progression looks fairly healthy right now, with no obvious economy warning signs.")

        return {
            "player_level": player["level"],
            "player_oxp": player["oxp"],
            "player_gold": player["gold"],
            "attack_points": player["attack_points"],
            "current_hp": player["current_hp"],
            "max_hp": player["max_hp"],
            "total_gold_earned": total_gold_earned,
            "gold_spent": player.get("gold_spent", 0),
            "net_gold": net_gold,
            "task_oxp_total": task_oxp_total,
            "task_gold_total": task_gold_total,
            "task_attack_total": task_attack_total,
            "quest_oxp_total": quest_oxp_total,
            "quest_gold_total": quest_gold_total,
            "quest_attack_total": quest_attack_total,
            "total_oxp_earned": total_oxp_earned,
            "total_attack_earned": total_attack_earned,
            "quest_share_percent": quest_share,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "completion_rate": completion_rate,
            "task_mix": task_mix,
            "completed_difficulty_breakdown": completed_difficulty_breakdown,
            "active_quests": active_quests,
            "completed_quests": completed_quests,
            "total_quest_paths": total_quest_paths,
            "avg_linked_tasks": avg_linked_tasks,
            "bosses_defeated": bosses_defeated,
            "achievements_unlocked": achievements_unlocked,
            "top_skill": top_skill,
            "total_skills": total_skills,
            "skills_above_five": skills_above_five,
            "balance_notes": balance_notes,
        }

    def get_all_tasks(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, title, description, period, status, streak, difficulty
            FROM task
            ORDER BY period, title
        """)
        return [{
            "id": r[0], "title": r[1], "description": r[2], "period": r[3],
            "status": r[4], "streak": r[5], "difficulty": r[6]
        } for r in cursor.fetchall()]

    # -------------------------------------------------------------------------
    # QUESTS
    # -------------------------------------------------------------------------

    def add_quest(self, title, description, category, difficulty, progress_mode,
                  target_count, oxp_reward, gold_reward, attack_reward,
                  quest_type="standard", branch_a_name="", branch_a_style="",
                  branch_b_name="", branch_b_style="", selected_branch=""):
        from datetime import date
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO quest(
                title, description, category, difficulty, quest_type,
                branch_a_name, branch_a_style, branch_b_name, branch_b_style,
                selected_branch, progress_mode, target_count, oxp_reward,
                gold_reward, attack_reward, status, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Active', ?)
        """, (
            title, description, category, difficulty, quest_type,
            branch_a_name, branch_a_style, branch_b_name, branch_b_style,
            selected_branch, progress_mode, target_count, oxp_reward,
            gold_reward, attack_reward, date.today().isoformat()
        ))
        self.conn.commit()
        return cursor.lastrowid

    def update_quest(self, quest_id, title, description, category, difficulty,
                     progress_mode, target_count, oxp_reward, gold_reward, attack_reward,
                     quest_type="standard", branch_a_name="", branch_a_style="",
                     branch_b_name="", branch_b_style="", selected_branch=""):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE quest
            SET title=?, description=?, category=?, difficulty=?, quest_type=?,
                branch_a_name=?, branch_a_style=?, branch_b_name=?, branch_b_style=?,
                selected_branch=?, progress_mode=?, target_count=?, oxp_reward=?,
                gold_reward=?, attack_reward=?
            WHERE id=?
        """, (
            title, description, category, difficulty, quest_type,
            branch_a_name, branch_a_style, branch_b_name, branch_b_style,
            selected_branch, progress_mode, target_count, oxp_reward,
            gold_reward, attack_reward, quest_id
        ))
        self.conn.commit()

    def delete_quest(self, quest_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM quest_task WHERE quest_id=?", (quest_id,))
        cursor.execute("DELETE FROM quest WHERE id=?", (quest_id,))
        self.conn.commit()

    def get_quest(self, quest_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, title, description, category, difficulty, quest_type,
                   branch_a_name, branch_a_style, branch_b_name, branch_b_style,
                   selected_branch, progress_mode, target_count, oxp_reward,
                   gold_reward, attack_reward, status, created_at, completed_at
            FROM quest WHERE id=?
        """, (quest_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return {
            "id": row[0], "title": row[1], "description": row[2],
            "category": row[3], "difficulty": row[4], "quest_type": row[5],
            "branch_a_name": row[6], "branch_a_style": row[7],
            "branch_b_name": row[8], "branch_b_style": row[9],
            "selected_branch": row[10], "progress_mode": row[11],
            "target_count": row[12], "oxp_reward": row[13], "gold_reward": row[14],
            "attack_reward": row[15], "status": row[16], "created_at": row[17],
            "completed_at": row[18],
        }

    def get_all_quests(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, title, description, category, difficulty, quest_type,
                   branch_a_name, branch_a_style, branch_b_name, branch_b_style,
                   selected_branch, progress_mode, target_count, oxp_reward,
                   gold_reward, attack_reward, status, created_at, completed_at
            FROM quest
            ORDER BY
                CASE WHEN status='Active' THEN 0 ELSE 1 END,
                category, title
        """)
        return [{
            "id": r[0], "title": r[1], "description": r[2],
            "category": r[3], "difficulty": r[4], "quest_type": r[5],
            "branch_a_name": r[6], "branch_a_style": r[7],
            "branch_b_name": r[8], "branch_b_style": r[9],
            "selected_branch": r[10], "progress_mode": r[11],
            "target_count": r[12], "oxp_reward": r[13], "gold_reward": r[14],
            "attack_reward": r[15], "status": r[16], "created_at": r[17],
            "completed_at": r[18],
        } for r in cursor.fetchall()]

    def set_quest_tasks(self, quest_id, task_ids):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM quest_task WHERE quest_id=?", (quest_id,))
        for task_id in task_ids:
            cursor.execute(
                "INSERT OR IGNORE INTO quest_task(quest_id, task_id) VALUES(?, ?)",
                (quest_id, task_id)
            )
        self.conn.commit()

    def get_quest_tasks(self, quest_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT t.id, t.title, t.description, t.period, t.status, t.streak, t.difficulty
            FROM quest_task qt
            JOIN task t ON t.id = qt.task_id
            WHERE qt.quest_id=?
            ORDER BY t.period, t.title
        """, (quest_id,))
        return [{
            "id": r[0], "title": r[1], "description": r[2], "period": r[3],
            "status": r[4], "streak": r[5], "difficulty": r[6]
        } for r in cursor.fetchall()]

    def get_task_quests(self, task_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT q.id, q.title, q.description, q.category, q.difficulty, q.quest_type,
                   q.branch_a_name, q.branch_a_style, q.branch_b_name, q.branch_b_style,
                   q.selected_branch, q.progress_mode, q.target_count, q.oxp_reward,
                   q.gold_reward, q.attack_reward, q.status, q.created_at, q.completed_at
            FROM quest_task qt
            JOIN quest q ON q.id = qt.quest_id
            WHERE qt.task_id=?
            ORDER BY q.title
        """, (task_id,))
        return [{
            "id": r[0], "title": r[1], "description": r[2], "category": r[3],
            "difficulty": r[4], "quest_type": r[5], "branch_a_name": r[6],
            "branch_a_style": r[7], "branch_b_name": r[8], "branch_b_style": r[9],
            "selected_branch": r[10], "progress_mode": r[11], "target_count": r[12],
            "oxp_reward": r[13], "gold_reward": r[14], "attack_reward": r[15],
            "status": r[16], "created_at": r[17], "completed_at": r[18],
        } for r in cursor.fetchall()]

    def get_quest_progress(self, quest_id):
        quest = self.get_quest(quest_id)
        if quest is None:
            return None

        tasks = self.get_quest_tasks(quest_id)
        linked_tasks = len(tasks)

        if quest["progress_mode"] == "completion_count":
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT COUNT(*)
                FROM task_history th
                JOIN quest_task qt ON qt.task_id = th.task_id
                WHERE qt.quest_id=? AND th.date_completed >= ?
            """, (quest_id, quest["created_at"] or "0000-00-00"))
            progress_value = cursor.fetchone()[0]
            target_value = max(1, quest["target_count"])
        else:
            progress_value = sum(1 for task in tasks if task["status"] == "Completed")
            target_value = linked_tasks

        is_complete = linked_tasks > 0 and target_value > 0 and progress_value >= target_value

        return {
            "quest_id": quest_id,
            "linked_tasks": linked_tasks,
            "progress_value": progress_value,
            "target_value": target_value,
            "is_complete": is_complete,
            "ratio": min(1, progress_value / target_value) if target_value > 0 else 0,
        }

    def get_quests_with_progress(self):
        quests = []
        for quest in self.get_all_quests():
            quest["tasks"] = self.get_quest_tasks(quest["id"])
            quest["progress"] = self.get_quest_progress(quest["id"])
            quests.append(quest)
        return quests

    def complete_quest(self, quest_id):
        from datetime import date
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE quest SET status='Completed', completed_at=? WHERE id=?",
            (date.today().isoformat(), quest_id)
        )
        self.conn.commit()

    # -------------------------------------------------------------------------
    # UTILITY
    # -------------------------------------------------------------------------

    def commit(self):
        self.conn.commit()

    def backup_database(self, backup_dir="backups"):
        self.conn.commit()
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"sukhaos_backup_{timestamp}.db"
        backup_path = os.path.abspath(os.path.join(backup_dir, backup_name))
        shutil.copy2(self.db_name, backup_path)
        return backup_path

    def list_backups(self, backup_dir="backups"):
        os.makedirs(backup_dir, exist_ok=True)
        backups = []
        for name in os.listdir(backup_dir):
            if not name.lower().endswith(".db"):
                continue
            full_path = os.path.abspath(os.path.join(backup_dir, name))
            if os.path.isfile(full_path):
                backups.append(full_path)
        backups.sort(key=os.path.getmtime, reverse=True)
        return backups

    def restore_database(self, backup_path):
        if not backup_path or not os.path.exists(backup_path):
            raise FileNotFoundError("Backup file not found.")
        if os.path.abspath(backup_path) == os.path.abspath(self.db_name):
            raise ValueError("Backup path cannot be the active database file.")

        self.conn.commit()
        self.conn.close()
        try:
            shutil.copy2(backup_path, self.db_name)
            self.conn = sqlite3.connect(self.db_name)
            self.create_tables()
        except Exception:
            # Always reopen the current database connection so the app does not
            # stay stuck with a closed connection if restore fails midway.
            self.conn = sqlite3.connect(self.db_name)
            raise
        return os.path.abspath(backup_path)

    def export_progress_summary(self, export_dir="exports"):
        os.makedirs(export_dir, exist_ok=True)

        player = self.get_player()
        unlocked, total = self.get_achievement_count()
        quests = self.get_quests_with_progress()
        active_boss = self.get_active_boss()

        summary = {
            "exported_at": datetime.now().isoformat(timespec="seconds"),
            "player": player,
            "achievements": {"unlocked": unlocked, "total": total},
            "skills": self.get_all_skills(),
            "tasks": self.get_all_tasks(),
            "quests": quests,
            "boss": active_boss,
            "daily_focus": self.get_daily_focus(),
            "task_history": self.get_task_history(),
        }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_name = f"sukhaos_progress_{timestamp}.json"
        export_path = os.path.abspath(os.path.join(export_dir, export_name))
        with open(export_path, "w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2)
        return export_path

    def reset_all_progress(self):
        cursor = self.conn.cursor()
        tables = [
            "daily_focus_item", "daily_focus",
            "task_reward", "task_history", "quest_task", "quest",
            "boss", "task", "skill", "achievement", "player"
        ]
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
        cursor.execute("DELETE FROM sqlite_sequence")
        self.conn.commit()
        self.create_tables()

    def clean_duplicate_achievements(self):
        """
        One-time cleanup to remove duplicate achievements.
        Keeps the row with the lowest id for each title.
        Safe to call multiple times — does nothing if no duplicates exist.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            DELETE FROM achievement
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM achievement
                GROUP BY title
            )
        """)
        self.conn.commit()
        return cursor.rowcount  # returns number of duplicates removed
