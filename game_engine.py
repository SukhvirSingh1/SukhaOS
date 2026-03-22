"""
game_engine.py
==============
Core game logic for SukhaOS.
"""

from datetime import date, datetime
import random


class GameEngine:
    HP_PER_LEVEL          = 10
    HP_PER_HEALTH_LEVEL   = 15
    ATTACK_PER_DIFFICULTY = {"easy": 5, "medium": 10, "hard": 15}
    ATTACK_PER_LEVEL_UP   = 20

    BOSS_ROSTER = {
        "easy": [
            ("The Slacker",     80,  5,  "You haven't worked in days... I'm barely trying."),
            ("Brain Fog",       90,  5,  "Can't think clearly? Neither can you."),
            ("The Distraction", 100, 5,  "Look at this shiny thing instead of your tasks!"),
        ],
        "medium": [
            ("The Procrastinator", 200, 15, "You'll defeat me tomorrow, right? Maybe next week."),
            ("Doubt",              220, 15, "Are you sure you're good enough for this?"),
            ("Entropy",            250, 15, "Everything falls apart eventually. Including you."),
        ],
        "hard": [
            ("Lord Chaos",      500, 30, "Your discipline means nothing. I am inevitable."),
            ("The Void",        600, 30, "You cannot defeat what you cannot see."),
            ("The Final Exam",  700, 30, "Let's see what you're really made of."),
        ]
    }

    BOSS_REWARDS = {
        "easy":   {"gold": 100, "oxp": 80,  "attack": 30},
        "medium": {"gold": 250, "oxp": 200, "attack": 75},
        "hard":   {"gold": 600, "oxp": 500, "attack": 200},
    }

    def __init__(self, database):
        self.db = database

    # -------------------------------------------------------------------------
    # ACHIEVEMENT CHECKING
    # -------------------------------------------------------------------------

    def check_all_achievements(self, player=None, new_streak=None, task_difficulty=None):
        """
        Central achievement checker — called after any meaningful game event.
        Checks all conditions and unlocks any that are newly met.

        Args:
            player (dict): Current player data. Fetched fresh if not provided.
            new_streak (int): Streak value from the just-completed task.
            task_difficulty (str): Difficulty of the just-completed task.

        Returns:
            list: Titles of newly unlocked achievements (for notification).
        """
        if player is None:
            player = self.db.get_player()

        newly_unlocked = []

        def check(title, condition):
            if condition:
                cursor = self.db.conn.cursor()
                cursor.execute(
                    "SELECT unlocked FROM achievement WHERE title=?", (title,)
                )
                row = cursor.fetchone()
                if row and row[0] == 0:
                    self.db.unlock_achievement(title)
                    newly_unlocked.append(title)

        # --- Task achievements ---
        total_completed = self.db.get_total_tasks_completed()
        check("First Task",    total_completed >= 1)
        check("Getting Started", total_completed >= 10)
        check("Halfway There", total_completed >= 50)
        check("Century",       total_completed >= 100)
        check("Hard Worker",   task_difficulty and task_difficulty.lower() == "hard")
        check("Triple Threat", self.db.get_tasks_completed_today() >= 3)

        # --- Streak achievements ---
        login_streak = player.get("login_streak", 0)
        max_task_streak = self.db.get_max_task_streak()
        check("Consistent",       login_streak >= 3)
        check("Dedicated",        login_streak >= 30)
        check("7 Day Discipline", new_streak is not None and new_streak >= 7)
        check("Two Weeks Strong", max_task_streak >= 14)

        # --- Level achievements ---
        check("Rising",   player["level"] >= 5)
        check("Veteran",  player["level"] >= 10)
        check("Elite",    player["level"] >= 25)

        # --- Gold achievements ---
        check("Gold Collector", player.get("total_gold_earned", 0) >= 500)
        check("Rich",           player.get("total_gold_earned", 0) >= 1000)
        check("Big Spender",    player.get("gold_spent", 0) >= 500)

        # --- Skill achievements ---
        check("Mind Level 5",  self.db.get_skill("Mind")["level"] >= 5)
        check("Master",        self.db.get_max_skill_level() >= 10)
        check("Well Rounded",  self.db.get_skills_above_level(5) >= 3)
        check("Creator",       self.db.get_custom_skill_count() >= 1)

        # --- Boss achievements ---
        bosses_defeated = self.db.get_bosses_defeated_count()
        check("Boss Slayer",  bosses_defeated >= 1)
        check("Boss Hunter",  bosses_defeated >= 3)
        # Giant Killer and Near Death are unlocked directly in attack_boss()

        return newly_unlocked

    # -------------------------------------------------------------------------
    # ATTACK DAMAGE
    # -------------------------------------------------------------------------

    def get_attack_damage(self):
        strength = self.db.get_skill("Strength")
        return 10 + (strength["level"] - 1) * 2

    # -------------------------------------------------------------------------
    # BOSS SYSTEM
    # -------------------------------------------------------------------------

    def check_boss_spawn(self, player_level):
        if self.db.get_active_boss():
            return None
        if self.db.boss_already_spawned_for_level(player_level):
            return None

        tier = None
        if player_level % 50 == 0:
            tier = "hard"
        elif player_level % 25 == 0:
            tier = "medium"
        elif player_level % 10 == 0:
            tier = "easy"

        if tier is None:
            return None

        name, hp, atk_damage, taunt = random.choice(self.BOSS_ROSTER[tier])
        self.db.spawn_boss(name, tier, hp, atk_damage, player_level, taunt)
        return self.db.get_active_boss()

    def apply_passive_boss_damage(self):
        boss = self.db.get_active_boss()
        if not boss or not boss["date_spawned"]:
            return None

        today        = date.today()
        spawned_date = datetime.strptime(boss["date_spawned"], "%Y-%m-%d").date()
        days_ignored = (today - spawned_date).days

        if days_ignored < 1:
            return None

        player = self.db.get_player()
        damage = boss["attack_damage"] * days_ignored
        new_hp = max(1, player["current_hp"] - damage)

        player["current_hp"] = new_hp
        self.db.update_player(player)

        return {
            "boss_name":    boss["name"],
            "damage":       damage,
            "days":         days_ignored,
            "remaining_hp": new_hp
        }

    def attack_boss(self, boss_id):
        """
        One round of combat.
        Spends 1 attack point, deals damage to boss, boss strikes back.
        Near death: HP=1, lose 50 gold + 20 attack points.
        Victory: rewards applied, achievements checked.
        """
        boss   = self.db.get_active_boss()
        player = self.db.get_player()

        if not boss or boss["id"] != boss_id:
            return None
        if player["attack_points"] <= 0:
            return None

        player["attack_points"] -= 1

        # Player hits boss
        player_damage = self.get_attack_damage()
        new_boss_hp   = max(0, boss["hp"] - player_damage)
        self.db.update_boss_hp(boss_id, new_boss_hp)

        # Boss hits back
        boss_damage   = boss["attack_damage"]
        new_player_hp = player["current_hp"] - boss_damage

        near_death = False
        rewards    = None

        if new_player_hp <= 0:
            new_player_hp          = 1
            near_death             = True
            gold_penalty           = min(player["gold"], 50)
            atk_penalty            = min(player["attack_points"], 20)
            player["gold"]         = max(0, player["gold"] - gold_penalty)
            player["attack_points"] = max(0, player["attack_points"] - atk_penalty)
            self.db.unlock_achievement("Near Death")

        player["current_hp"] = new_player_hp

        boss_defeated = new_boss_hp <= 0
        if boss_defeated:
            self.db.defeat_boss(boss_id)
            player["bosses_defeated"] = player.get("bosses_defeated", 0) + 1

            if boss["tier"] == "hard":
                self.db.unlock_achievement("Giant Killer")

            tier_rewards             = self.BOSS_REWARDS[boss["tier"]]
            player["gold"]          += tier_rewards["gold"]
            player["oxp"]           += tier_rewards["oxp"]
            player["attack_points"] += tier_rewards["attack"]
            player["total_gold_earned"] = player.get("total_gold_earned", 0) + tier_rewards["gold"]

            self.check_player_level_up(player)
            self.db.update_player(player)

            # Check boss achievements after saving
            self.check_all_achievements(player=self.db.get_player())
            rewards = tier_rewards
        else:
            self.db.update_player(player)

        return {
            "player_damage":     player_damage,
            "boss_damage":       boss_damage,
            "boss_hp":           new_boss_hp,
            "player_hp":         new_player_hp,
            "boss_defeated":     boss_defeated,
            "player_near_death": near_death,
            "rewards":           rewards,
            "attack_points":     player["attack_points"],
        }

    # -------------------------------------------------------------------------
    # TASK COMPLETION
    # -------------------------------------------------------------------------

    def complete_task(self, task_id):
        """
        Process task completion. Returns dict with level/boss info, or False.
        """
        task   = self.db.get_task(task_id)
        player = self.db.get_player()

        if task["status"] == "Completed":
            return False

        # Base rewards
        gold_earned             = task["gold"]
        player["gold"]         += gold_earned
        player["oxp"]          += task["oxp"]
        player["total_gold_earned"] = player.get("total_gold_earned", 0) + gold_earned

        difficulty = task.get("difficulty", "Medium").lower()
        player["attack_points"] += self.ATTACK_PER_DIFFICULTY.get(difficulty, 10)

        # Skill XP
        rewards = self.db.get_task_rewards(task_id)
        for reward in rewards:
            skill     = self.db.get_skill(reward["skill_name"])
            skill["xp"] += reward["sxp"]
            old_level = skill["level"]
            self.check_skill_level_up(skill)

            if skill["name"] == "Health" and skill["level"] > old_level:
                levels_gained        = skill["level"] - old_level
                player["max_hp"]    += self.HP_PER_HEALTH_LEVEL * levels_gained
                player["current_hp"] = min(
                    player["current_hp"] + self.HP_PER_HEALTH_LEVEL * levels_gained,
                    player["max_hp"]
                )

            self.db.update_skill(skill)

        # Streak logic
        today          = date.today()
        last_completed = task.get("last_completed")
        new_streak     = 1

        if last_completed:
            last_date = datetime.strptime(last_completed, "%Y-%m-%d").date()
            if task["period"] == "daily":
                new_streak = task["streak"] + 1 if (today - last_date).days == 1 else 1
            elif task["period"] == "weekly":
                this_week = today.isocalendar()[1]
                last_week = last_date.isocalendar()[1]
                new_streak = task["streak"] + 1 if this_week - last_week == 1 else task["streak"]
            else:
                new_streak = task["streak"]

        if new_streak % 7 == 0:
            player["oxp"] += 50

        old_level = player["level"]
        self.check_player_level_up(player)
        new_level = player["level"]

        self.db.mark_task_completed(task_id)
        self.db.update_task_streak(task_id, new_streak)
        self.db.update_player(player)

        # Log to history
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO task_history(task_id, title, difficulty, date_completed)
            VALUES (?, ?, ?, ?)
        """, (task["id"], task["title"],
              task.get("difficulty", "Medium"), date.today().isoformat()))
        self.db.conn.commit()

        # Check all achievements
        newly_unlocked = self.check_all_achievements(
            player=self.db.get_player(),
            new_streak=new_streak,
            task_difficulty=task.get("difficulty")
        )

        # Boss spawn check
        spawned_boss = None
        if new_level > old_level:
            for lvl in range(old_level + 1, new_level + 1):
                spawned_boss = self.check_boss_spawn(lvl)
                if spawned_boss:
                    break

        return {
            "leveled_up":      new_level > old_level,
            "new_level":       new_level,
            "boss":            spawned_boss,
            "newly_unlocked":  newly_unlocked,
        }

    # -------------------------------------------------------------------------
    # LOGIN REWARD
    # -------------------------------------------------------------------------

    def check_login_reward(self):
        player       = self.db.get_player()
        today        = date.today()
        today_str    = today.isoformat()
        last_login   = player.get("last_login")
        login_streak = player.get("login_streak", 0)

        if last_login == today_str:
            return None

        if last_login:
            last_date    = datetime.strptime(last_login, "%Y-%m-%d").date()
            diff         = (today - last_date).days
            login_streak = login_streak + 1 if diff == 1 else 1
        else:
            login_streak = 1

        gold, oxp = 10, 10
        bonus_atk = 5

        if login_streak >= 7:
            gold, oxp = 50, 50
            bonus_atk = 20
            bonus_msg = "7 Day Login Streak! MEGA reward!"
        elif login_streak >= 3:
            gold, oxp = 25, 25
            bonus_atk = 10
            bonus_msg = f"{login_streak} Day Streak! Bonus reward!"
        else:
            bonus_msg = f"Day {login_streak} streak. Keep it up!"

        hp_restored          = min(5, player["max_hp"] - player["current_hp"])
        player["current_hp"] += hp_restored
        player["gold"]       += gold
        player["oxp"]        += oxp
        player["attack_points"] += bonus_atk
        player["total_gold_earned"] = player.get("total_gold_earned", 0) + gold

        self.check_player_level_up(player)
        self.db.update_player(player)
        self.db.update_login(today_str, login_streak)

        # Check login streak achievements
        self.check_all_achievements(
            player=self.db.get_player()
        )

        return {
            "gold": gold, "oxp": oxp, "streak": login_streak,
            "message": bonus_msg, "hp_restored": hp_restored, "bonus_atk": bonus_atk
        }

    # -------------------------------------------------------------------------
    # SHOP
    # -------------------------------------------------------------------------

    def buy_skill_boost(self, skill_name):
        player = self.db.get_player()
        skill  = self.db.get_skill(skill_name)

        if player["gold"] < 100:
            return False

        player["gold"]      -= 100
        player["gold_spent"] = player.get("gold_spent", 0) + 100
        skill["xp"]         += 20

        old_level = skill["level"]
        self.check_skill_level_up(skill)

        if skill["name"] == "Health" and skill["level"] > old_level:
            levels_gained        = skill["level"] - old_level
            player["max_hp"]    += self.HP_PER_HEALTH_LEVEL * levels_gained
            player["current_hp"] = min(
                player["current_hp"] + self.HP_PER_HEALTH_LEVEL * levels_gained,
                player["max_hp"]
            )

        self.db.update_skill(skill)
        self.db.update_player(player)
        self.db.commit()

        # Check Big Spender achievement
        self.check_all_achievements(player=self.db.get_player())
        return True

    # -------------------------------------------------------------------------
    # LEVEL UP
    # -------------------------------------------------------------------------

    def check_player_level_up(self, player):
        while True:
            required = 100 + (player["level"] - 1) * 50
            if player["oxp"] >= required:
                player["oxp"]           -= required
                player["level"]         += 1
                player["max_hp"]        += self.HP_PER_LEVEL
                player["current_hp"]     = player["max_hp"]
                player["attack_points"] += self.ATTACK_PER_LEVEL_UP
            else:
                break

    def check_skill_level_up(self, skill):
        while True:
            required = 50 + (skill["level"] - 1) * 25
            if skill["xp"] >= required:
                skill["xp"]    -= required
                skill["level"] += 1
            else:
                break