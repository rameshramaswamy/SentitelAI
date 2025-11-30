# Keyword/Regex Matching Logic# sentinel_speech/src/core/nlp_router.py
import re
import time
from typing import List, Optional, Dict
from functools import lru_cache

class NLPRouter:
    def __init__(self, use_vector: bool = True):
        # In a real app, load this from Database/Redis
        self.rules = [
            {
                "keywords": ["budget", "price", "expensive", "cost"],
                "trigger": {
                    "title": "Pricing Objection",
                    "message": "Focus on Value (ROI), not cost.",
                    "color_hex": "#FFA500" # Orange
                }
            },
            {
                "keywords": ["competitor", "other solution", "using jira"],
                "trigger": {
                    "title": "Competitor Detected",
                    "message": "We offer 24/7 support, they don't.",
                    "color_hex": "#FF0000" # Red
                }
            },
            {
                "keywords": ["timeline", "start date", "implementation"],
                "trigger": {
                    "title": "Closing Signal",
                    "message": "Propose a start date next week.",
                    "color_hex": "#00FF00" # Green
                }
            }
        ]
        for rule in self.rules:
            # Create a regex like: \b(budget|cost|price)\b
            pattern_str = r"\b(" + "|".join([re.escape(k) for k in rule["keywords"]]) + r")\b"
            rule["_compiled"] = re.compile(pattern_str, re.IGNORECASE)
        self.cooldowns = {} 
        self.COOLDOWN_SECONDS = 10
        if self.use_vector:
            # OPTIMIZATION: prefer_grpc=True uses Port 6334
            self.qdrant = QdrantClient(
                url="http://localhost:6333", 
                prefer_grpc=True 
            )
            
    # OPTIMIZATION: Cache the last 1000 phrases. 
    # This prevents running the model for repeated short commands.
    @lru_cache(maxsize=1000)
    def _get_embedding(self, text: str):
        # SentenceTransformer isn't thread-safe, ensure single thread access if needed
        # or just rely on the GIL for simple calls.
        return self.embedder.encode(text).tolist()
    
    def process(self, text: str) -> Optional[Dict]:
        current_time = time.time()
        
        for rule in self.rules:
            if rule["_compiled"].search(text):
                trigger_name = rule["trigger"]["title"]
                
                # OPTIMIZATION: Cooldown Check
                last_time = self.cooldowns.get(trigger_name, 0)
                if current_time - last_time < self.COOLDOWN_SECONDS:
                    # Too soon, ignore this trigger
                    continue
                
                # Update timestamp and return
                self.cooldowns[trigger_name] = current_time
                return rule["trigger"]
                
        return None