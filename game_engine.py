"""
game_engine.py
==============
Core game logic for SukhaOS.
Handles task completion, XP/leveling, HP, attack points,
login rewards, shop, and boss system.
"""

from datetime import date, datetime
import random


class GameEngine:
    """Manages all game mechanics for SukhaOS."""

    HP_PER_LEVEL         = 10
    HP_PER_HEALTH_LEVEL  = 15
    ATTACK_PER_DIFFICULTY = {"easy": 5, "medium": 10, "hard": 15}
    ATTACK_PER_LEVEL_UP  = 20

    # Boss definitions — name, tier, hp, attack_damage_per_day, taunt
    # Multiple bosses per tier so variety increases over time
    BOSS_ROSTER = {
        "easy": [
            ("The Slacker",    80,  5,  "You haven't worked in days... I'm barely trying."),
            ("Brain Fog",      90,  5,  "Can't think clearly? Neither can you."),
            ("The Distraction",100, 5,  "Look at this shiny thing instead of your tasks!"),
        ],
        "medium": [
            ("The Procrastinator", 200, 15, "You'll defeat me tomorrow, right? Maybe next week."),
            ("Doubt",              220, 15, "Are you sure you're good enough for this?"),
            ("Entropy",            250, 15, "Everything falls apart eventually. Including you."),
        ],
        "hard": [
            ("Lord Chaos",         500, 30, "Your discipline means nothing. I am inevitable."),
            ("The Void",           600, 30, "You cannot defeat what you cannot see."),
            ("The Final Exam",     700, 30, "Let's see what you're really made of."),
        ]
    }

    # Victory rewards per tier
    BOSS_REWARDS = {
        "easy":   {"gold": 100, "oxp": 80,  "attack": 30},
        "medium": {"gold": 250, "oxp": 200, "attack": 75},
        "hard":   {"gold": 600, "oxp": 500, "attack": 200},
    }

    def __init__(self, database):
        self.db = database

    # -------------------------------------------------------------------------
    # ATTACK DAMAGE
    # -------------------------------------------------------------------------

    def get_attack_damage(self):
        """
        Calculate player's attack damage per hit.
        Base: 10. Each Strength level beyond 1 adds +2.
        """
        base      = 10
        strength  = self.db.get_skill("Strength")
        bonus     = (strength["level"] - 1) * 2
        return base + bonus

    # -------------------------------------------------------------------------
    # BOSS SYSTEM
    # -------------------------------------------------------------------------

    def check_boss_spawn(self, player_level):
        """
        Check if a new boss should spawn based on the player's current level.
        Called after every level up.

        Spawn rules:
            - Easy boss every 10 levels (10, 20, 30...)
            - Medium boss every 25 levels (25, 50, 75...) — takes priority over easy
            - Hard boss every 50 levels (50, 100, 150...) — takes priority over all

        Only one boss can be active at a time. If a boss is already active,
        no new boss spawns until the current one is defeated.

        Args:
            player_level (int): The player's current level after leveling up.

        Returns:
            dict with boss data if spawned, None otherwise.
        """
        # Don't spawn if another boss is already active
        if self.db.get_active_boss():
            return None

        # Don't spawn if we've already spawned a boss for this level
        if self.db.boss_already_spawned_for_level(player_level):
            return None

        # Determine tier — hard takes priority over medium over easy
        tier = None
        if player_level % 50 == 0:
            tier = "hard"
        elif player_level % 25 == 0:
            tier = "medium"
        elif player_level % 10 == 0:
            tier = "easy"

        if tier is None:
            return None

        # Pick a random boss from the roster for this tier
        roster       = self.BOSS_ROSTER[tier]
        name, hp, atk_damage, taunt = random.choice(roster)

        self.db.spawn_boss(name, tier, hp, atk_damage, player_level, taunt)

        return self.db.get_active_boss()

    def apply_passive_boss_damage(self):
        """
        Apply daily passive damage from an undefeated active boss.
        Called on app launch alongside reset_tasks().

        An active boss that was spawned on a previous day deals damage
        to the player's HP for every day it has been ignored.

        Returns:
            dict with damage info if damage was dealt, None otherwise.
        """
        boss = self.db.get_active_boss()
        if not boss:
            return None

        if not boss["date_spawned"]:
            return None

        today        = date.today()
        spawned_date = datetime.strptime(boss["date_spawned"], "%Y-%m-%d").date()
        days_ignored = (today - spawned_date).days

        # Only deal damage if boss has been active for at least 1 day
        if days_ignored < 1:
            return None

        player     = self.db.get_player()
        damage     = boss["attack_damage"] * days_ignored

        # Apply damage — floor at 1 HP (never kill the player passively)
        new_hp = max(1, player["current_hp"] - damage)
        player["current_hp"] = new_hp
        self.db.update_player(player)

        return {
            "boss_name":   boss["name"],
            "damage":      damage,
            "days":        days_ignored,
            "remaining_hp": new_hp
        }

    def attack_boss(self, boss_id):
        """
        Player attacks the active boss.
        Player deals get_attack_damage() to boss.
        Boss strikes back with its attack_damage.

        Args:
            boss_id (int): ID of the boss being attacked.

        Returns:
            dict with combat result:
                - player_damage: damage dealt to boss
                - boss_damage: damage dealt to player
                - boss_hp: boss HP remaining
                - player_hp: player HP remaining
                - boss_defeated: True if boss was killed
                - player_near_death: True if player HP hit 0 (now at 1)
                - rewards: dict if boss was defeated, else None
        """
        boss   = self.db.get_active_boss()
        player = self.db.get_player()

        if not boss or boss["id"] != boss_id:
            return None

        # --- Player attacks boss ---
        player_damage = self.get_attack_damage()
        new_boss_hp   = max(0, boss["hp"] - player_damage)
        self.db.update_boss_hp(boss_id, new_boss_hp)

        # --- Boss strikes back ---
        boss_damage   = boss["attack_damage"]
        new_player_hp = player["current_hp"] - boss_damage

        near_death    = False
        rewards       = None

        if new_player_hp <= 0:
            # Player near death — HP stays at 1, lose gold penalty
            new_player_hp = 1
            near_death    = True
            penalty       = min(player["gold"], 50)   # lose up to 50 gold
            player["gold"] = max(0, player["gold"] - penalty)

        player["current_hp"] = new_player_hp

        # --- Check if boss is defeated ---
        boss_defeated = new_boss_hp <= 0
        if boss_defeated:
            self.db.defeat_boss(boss_id)
            self.db.unlock_achievement("Boss Slayer")

            if boss["tier"] == "hard":
                self.db.unlock_achievement("Giant Killer")

            # Victory rewards
            tier_rewards         = self.BOSS_REWARDS[boss["tier"]]
            player["gold"]       += tier_rewards["gold"]
            player["oxp"]        += tier_rewards["oxp"]
            player["attack_points"] += tier_rewards["attack"]
            self.check_player_level_up(player)

            rewards = tier_rewards

        self.db.update_player(player)

        return {
            "player_damage":   player_damage,
            "boss_damage":     boss_damage,
            "boss_hp":         new_boss_hp,
            "player_hp":       new_player_hp,
            "boss_defeated":   boss_defeated,
            "player_near_death": near_death,
            "rewards":         rewards,
        }

    # -------------------------------------------------------------------------
    # TASK COMPLETION
    # -------------------------------------------------------------------------

    def complete_task(self, task_id):
        """
        Process a task completion.
        Awards gold, OXP, skill XP, attack points.
        Checks for level up and boss spawn.

        Returns:
            True if completed, False if already completed.
        """
        task   = self.db.get_task(task_id)
        player = self.db.get_player()

        if task["status"] == "Completed":
            return False

        player["gold"] += task["gold"]
        player["oxp"]  += task["oxp"]

        difficulty = task.get("difficulty", "Medium").lower()
        player["attack_points"] += self.ATTACK_PER_DIFFICULTY.get(difficulty, 10)

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

            if skill["name"] == "Mind" and skill["level"] >= 5:
                self.db.unlock_achievement("Mind Level 5")

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

        if new_streak >= 7:
            self.db.unlock_achievement("7 Day Discipline")
        if new_streak % 7 == 0:
            player["oxp"] += 50

        old_level = player["level"]
        self.check_player_level_up(player)
        new_level = player["level"]

        self.db.unlock_achievement("First Task")
        if player["gold"] >= 500:
            self.db.unlock_achievement("Gold Collector")

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

        # Check boss spawn for each new level gained
        spawned_boss = None
        if new_level > old_level:
            for lvl in range(old_level + 1, new_level + 1):
                spawned_boss = self.check_boss_spawn(lvl)
                if spawned_boss:
                    break

        return {"leveled_up": new_level > old_level,
                "new_level":  new_level,
                "boss":       spawned_boss}

    # -------------------------------------------------------------------------
    # LOGIN REWARD
    # -------------------------------------------------------------------------

    def check_login_reward(self):
        """
        Check and award daily login reward.
        Returns dict with reward info, or None if already claimed today.
        """
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

        self.check_player_level_up(player)
        self.db.update_player(player)
        self.db.update_login(today_str, login_streak)

        return {
            "gold": gold, "oxp": oxp, "streak": login_streak,
            "message": bonus_msg, "hp_restored": hp_restored, "bonus_atk": bonus_atk
        }

    # -------------------------------------------------------------------------
    # SHOP
    # -------------------------------------------------------------------------

    def buy_skill_boost(self, skill_name):
        """Buy +20 XP boost for 100 gold. Returns True if successful."""
        player = self.db.get_player()
        skill  = self.db.get_skill(skill_name)

        if player["gold"] < 100:
            return False

        player["gold"] -= 100
        skill["xp"]    += 20

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
        return True

    # -------------------------------------------------------------------------
    # LEVEL UP
    # -------------------------------------------------------------------------

    def check_player_level_up(self, player):
        """
        Level up player while OXP is sufficient.
        Each level: +HP_PER_LEVEL max HP, full heal, +ATTACK_PER_LEVEL_UP attack.
        Formula: required = 100 + (level-1) * 50
        """
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
        """
        Level up skill while XP is sufficient.
        Formula: required = 50 + (level-1) * 25
        """
        while True:
            required = 50 + (skill["level"] - 1) * 25
            if skill["xp"] >= required:
                skill["xp"]    -= required
                skill["level"] += 1
            else:
                break