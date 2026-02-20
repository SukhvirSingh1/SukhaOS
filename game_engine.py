# xp, levels, rewards logic for SukhaOS application

class GameEngine:
    def __init__(self, database):
        self.db = database
    def complete_task(self, task_id):   
        task = self.db.get_task(task_id)
        player = self.db.get_player()
        
        if task["status"] == "Completed":
            return  # Task already completed
        
        self.db.mark_task_completed(task_id)
    
        
        player["gold"] += task["gold"]
        player["oxp"] += task["oxp"]
        
        rewards = self.db.get_task_rewards(task_id) 
        for reward in rewards:
            skill = self.db.get_skill(reward["skill_name"])
            skill["xp"] += reward["sxp"]
            self.check_skill_level_up(skill)
            
            
        self.check_player_level_up(player)
        self.db.update_player(player)
        self.db.commit()
        
    def check_player_level_up(self, player):
        required = player["level"] * 100
        while player["oxp"] >= required:
            player["oxp"] -= required
            player["level"] += 1
            required = player["level"] * 100
    
    def check_skill_level_up(self, skill):
        required = skill["level"] * 50
        while skill["xp"] >= required:
            skill["xp"] -= required
            skill["level"] += 1
            required = skill["level"] * 50