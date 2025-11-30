# sentinel_data/scripts/seed_knowledge.py
import sys
import os
from pathlib import Path

# Add project root to path so we can import src
sys.path.append(str(Path(__file__).parent.parent))

from sentence_transformers import SentenceTransformer
from src.vector.qdrant_service import QdrantService

# 1. Defined The Sales Playbook
PLAYBOOK_DATA = [
    {
        "text": "The price is too high, it is very expensive, cost is an issue.",
        "trigger": {
            "title": "Pricing Objection",
            "message": "Pivot to ROI: 'If we could save you 20 hours a week, is the price justified?'",
            "color_hex": "#FFA500"
        }
    },
    {
        "text": "We are using a competitor, we use Jira, we use Salesforce.",
        "trigger": {
            "title": "Competitor Mention",
            "message": "Highlight our AI features: 'Does your current tool offer real-time coaching?'",
            "color_hex": "#FF0000"
        }
    },
    {
        "text": "I need to ask my manager, I need approval, send me a proposal.",
        "trigger": {
            "title": "Decision Maker Gate",
            "message": "Secure the next step: 'When will you meet your manager? Can I join?'",
            "color_hex": "#0000FF"
        }
    },
    {
        "text": "When can we start? How long is implementation? What is the timeline?",
        "trigger": {
            "title": "Buying Signal",
            "message": "Close now: 'We can deploy within 24 hours. Shall I send the contract?'",
            "color_hex": "#00FF00"
        }
    }
]

def seed():
    print("Loading Embedding Model (all-MiniLM-L6-v2)...")
    # This downloads the model to local cache (~80MB)
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    qdrant = QdrantService()
    qdrant.create_collection_if_not_exists()
    
    print("Generating Embeddings...")
    texts = [item["text"] for item in PLAYBOOK_DATA]
    embeddings = model.encode(texts).tolist()
    
    print("Uploading to Qdrant...")
    qdrant.upsert_knowledge(PLAYBOOK_DATA, embeddings)
    print("✅ Knowledge Base Seeded Successfully.")

if __name__ == "__main__":
    seed()