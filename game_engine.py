"""
game_engine.py
==============
Core game logic for SukhaOS.
Handles task completion rewards, XP/level progression,
skill leveling, login streaks, and shop purchases.
All methods operate on data fetched from the database
and write results back through database methods.
"""

from datetime import date, datetime


class GameEngine:
    """
    Manages all game mechanics for SukhaOS.
    Acts as the bridge between the UI (layout.py) and the database (database.py).
    The UI calls engine methods, the engine processes logic, the database persists data.
    """

    def __init__(self, database):
        """
        Initialise the game engine with a database connection.

        Args:
            database: An instance of the Database class from database.py
        """
        self.db = database

    # -------------------------------------------------------------------------
    # TASK COMPLETION
    # -------------------------------------------------------------------------

    def complete_task(self, task_id):
        """
        Process a task completion — award gold, OXP, skill XP, update streaks,
        log to task history, and check for level ups and achievements.

        Args:
            task_id (int): The ID of the task being completed.

        Returns:
            True if the task was successfully completed.
            False if the task was already completed (no double rewards).
        """
        task = self.db.get_task(task_id)
        player = self.db.get_player()

        # Guard: prevent completing an already completed task
        if task["status"] == "Completed":
            return False

        # --- Award base rewards ---
        player["gold"] += task["gold"]
        player["oxp"] += task["oxp"]

        # --- Award skill XP for each linked skill ---
        rewards = self.db.get_task_rewards(task_id)
        for reward in rewards:
            skill = self.db.get_skill(reward["skill_name"])
            skill["xp"] += reward["sxp"]
            self.check_skill_level_up(skill)
            self.db.update_skill(skill)

            # Achievement: Mind skill reaches level 5
            if skill["name"] == "Mind" and skill["level"] >= 5:
                self.db.unlock_achievement("Mind Level 5")

        # --- Streak logic ---
        today = date.today()
        last_completed = task.get("last_completed")
        new_streak = 1  # default: start or reset streak

        if last_completed:
            last_date = datetime.strptime(last_completed, "%Y-%m-%d").date()

            if task["period"] == "daily":
                # Streak continues only if completed exactly yesterday
                if (today - last_date).days == 1:
                    new_streak = task["streak"] + 1
                else:
                    new_streak = 1  # gap in days — reset

            elif task["period"] == "weekly":
                # Streak continues if completed in the previous calendar week
                this_week = today.isocalendar()[1]
                last_week = last_date.isocalendar()[1]
                if this_week - last_week == 1:
                    new_streak = task["streak"] + 1
                else:
                    new_streak = task["streak"]  # weekly streaks don't reset on miss

            else:
                # Monthly/yearly tasks: preserve current streak
                new_streak = task["streak"]

        # --- Streak milestone rewards ---
        if new_streak >= 7:
            self.db.unlock_achievement("7 Day Discipline")

        if new_streak % 7 == 0:
            # Bonus OXP every 7-day streak milestone
            player["oxp"] += 50
            print(f"Streak bonus! +50 OXP for {new_streak}-day streak.")

        # --- Check for character level up ---
        self.check_player_level_up(player)

        # --- Unlock standard achievements ---
        self.db.unlock_achievement("First Task")
        if player["gold"] >= 500:
            self.db.unlock_achievement("Gold Collector")

        # --- Persist all changes ---
        self.db.mark_task_completed(task_id)
        self.db.update_task_streak(task_id, new_streak)
        self.db.update_player(player)

        # --- Log completion to task history ---
        today_str = date.today().isoformat()
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO task_history(task_id, title, difficulty, date_completed)
            VALUES (?, ?, ?, ?)
        """, (
            task["id"],
            task["title"],
            task.get("difficulty", "Medium"),
            today_str
        ))
        self.db.conn.commit()

        return True

    # -------------------------------------------------------------------------
    # LOGIN REWARD
    # -------------------------------------------------------------------------

    def check_login_reward(self):
        """
        Check if the player is eligible for a daily login reward.
        Called once on app launch. Gives gold and OXP with streak bonuses
        for consecutive daily logins.

        Returns:
            dict with keys: gold, oxp, streak, message — if reward was given.
            None — if the player already logged in today.
        """
        player = self.db.get_player()
        today = date.today()
        today_str = today.isoformat()

        last_login = player.get("last_login")
        login_streak = player.get("login_streak", 0)

        # Already claimed today's reward
        if last_login == today_str:
            return None

        # --- Calculate login streak ---
        if last_login:
            last_date = datetime.strptime(last_login, "%Y-%m-%d").date()
            diff = (today - last_date).days
            if diff == 1:
                login_streak += 1   # consecutive day — extend streak
            else:
                login_streak = 1    # missed a day — reset streak
        else:
            login_streak = 1        # first ever login

        # --- Determine reward based on streak ---
        gold = 10
        oxp = 10

        if login_streak >= 7:
            gold, oxp = 50, 50
            bonus_msg = "7 Day Login Streak! MEGA reward!"
        elif login_streak >= 3:
            gold, oxp = 25, 25
            bonus_msg = f"{login_streak} Day Streak! Bonus reward!"
        else:
            bonus_msg = f"Day {login_streak} streak. Keep it up!"

        # --- Apply rewards ---
        player["gold"] += gold
        player["oxp"] += oxp
        self.check_player_level_up(player)
        self.db.update_player(player)
        self.db.update_login(today_str, login_streak)

        return {
            "gold": gold,
            "oxp": oxp,
            "streak": login_streak,
            "message": bonus_msg
        }

    # -------------------------------------------------------------------------
    # SHOP
    # -------------------------------------------------------------------------

    def buy_skill_boost(self, skill_name):
        """
        Purchase a skill XP boost from the shop.
        Deducts gold from the player and adds XP to the specified skill.

        Args:
            skill_name (str): The name of the skill to boost.

        Returns:
            True if purchase was successful.
            False if the player doesn't have enough gold.
        """
        player = self.db.get_player()
        skill = self.db.get_skill(skill_name)

        COST = 100          # gold cost per boost
        BOOST_AMOUNT = 20   # XP added per boost

        if player["gold"] < COST:
            return False

        player["gold"] -= COST
        skill["xp"] += BOOST_AMOUNT

        self.check_skill_level_up(skill)
        self.db.update_skill(skill)
        self.db.update_player(player)
        self.db.commit()

        return True

    # -------------------------------------------------------------------------
    # LEVEL UP LOGIC
    # -------------------------------------------------------------------------

    def check_player_level_up(self, player):
        """
        Check if the player has enough OXP to level up.
        Loops until OXP is below the threshold for the next level.
        Modifies the player dict in place — caller must save with db.update_player().

        Formula: required OXP = 100 + (level - 1) * 50

        Args:
            player (dict): The player data dictionary with 'oxp' and 'level' keys.
        """
        while True:
            required = 100 + (player["level"] - 1) * 50
            if player["oxp"] >= required:
                player["oxp"] -= required   # carry over excess OXP
                player["level"] += 1
                print(f"Level up! New level: {player['level']}, OXP remaining: {player['oxp']}")
            else:
                break   # not enough OXP for next level

    def check_skill_level_up(self, skill):
        """
        Check if a skill has enough XP to level up.
        Loops until XP is below the threshold for the next skill level.
        Modifies the skill dict in place — caller must save with db.update_skill().

        Formula: required SXP = 50 + (level - 1) * 25

        Args:
            skill (dict): The skill data dictionary with 'xp' and 'level' keys.
        """
        while True:
            required = 50 + (skill["level"] - 1) * 25
            if skill["xp"] >= required:
                skill["xp"] -= required     # carry over excess XP
                skill["level"] += 1
                print(f"Skill '{skill['name']}' leveled up! Level: {skill['level']}, XP remaining: {skill['xp']}")
            else:
                break   # not enough XP for next level