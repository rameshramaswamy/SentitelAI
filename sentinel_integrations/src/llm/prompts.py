# sentinel_integrations/src/llm/prompts.py
import os
from jinja2 import Environment, FileSystemLoader
from src.config import settings

class PromptManager:
    def __init__(self):
        # Resolve absolute path to templates
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        template_dir = os.path.join(base_dir, settings.TEMPLATE_DIR)
        
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def render_summary_prompt(self, transcript: str) -> str:
        template = self.env.get_template("summary_prompt.j2")
        return template.render(transcript=transcript)