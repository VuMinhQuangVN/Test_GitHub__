import json
import os

class PromptBuilder:
    def __init__(self, json_path="database/prompts/scenarios.json"):
        self.json_path = json_path
        self.products_path = "database/products.json"
        self.db = {"scenarios": {}}
        self.products = {}
        self._load_config()

    def _load_config(self):
        if os.path.exists(self.json_path):
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.db = json.load(f)
        if os.path.exists(self.products_path):
            with open(self.products_path, 'r', encoding='utf-8') as f:
                self.products = json.load(f)

    def get_scenarios(self):
        return {k: v.get("display_name", k) for k, v in self.db.get("scenarios", {}).items()}

    def get_products(self):
        return self.products
    
    def get_image_tasks(self, scenario_key, product_type):
        scenario = self.db.get("scenarios", {}).get(scenario_key)
        if not scenario: return []

        tasks = []
        template = scenario.get("image_prompt_template", "")
        shots_dict = scenario.get("shots", {})

        for shot_name, shot_data in shots_dict.items():
            shot_def = shot_data.get("prompt", "") if isinstance(shot_data, dict) else shot_data
            t_count = shot_data.get("target_count", 2) if isinstance(shot_data, dict) else 2
            
            # --- NHẶT CÂU LỆNH ĐỔI DÁNG TẠI ĐÂY ---
            pose_req = shot_data.get("pose_change_request", "") if isinstance(shot_data, dict) else ""

            final_prompt = template.replace("{shot_definition}", shot_def)\
                                   .replace("{product_type}", str(product_type))
            
            tasks.append({
                "type": shot_name,
                "prompt": final_prompt,
                "target_count": t_count,
                "pose_change_request": pose_req # Gửi sang cho Worker
            })
        return tasks
    
    def get_shot_config(self, scenario_key, shot_type):
        scenario = self.db.get("scenarios", {}).get(scenario_key, {})
        shot_data = scenario.get("shots", {}).get(shot_type, {})
        if isinstance(shot_data, str):
            return {"prompt": shot_data, "target_count": 2, "variants": 1}
        return shot_data

    def build_video_instruction(self, scenario_key, shot_type, product_type, num_variants=1):
        scenario = self.db.get("scenarios", {}).get(scenario_key)
        if not scenario: return ""
        template = scenario.get("chatgpt_video_prompt", "")
        return template.replace("{product_type}", product_type).replace("{shot_type}", shot_type).replace("{num_variants}", str(num_variants))
    
    def save_all(self):
        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self.db, f, indent=4, ensure_ascii=False)
            with open(self.products_path, 'w', encoding='utf-8') as f:
                json.dump(self.products, f, indent=4, ensure_ascii=False)
            return True
        except: return False