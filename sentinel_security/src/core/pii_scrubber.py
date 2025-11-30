# sentinel_security/src/core/pii_scrubber.py
import re
from typing import List, Pattern
from src.config import settings

class PIIScrubber:
    def __init__(self):
        self.patterns: List[dict] = []
        
        # 1. Email Regex (Standard RFC 5322 simplified)
        if settings.SCRUB_EMAIL:
            self.patterns.append({
                "type": "EMAIL",
                "regex": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
            })

        # 2. US Social Security Number (SSN) - Format: 000-00-0000
        if settings.SCRUB_SSN:
            self.patterns.append({
                "type": "SSN",
                "regex": re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
            })

        # 3. US Phone Number (Formats: 123-456-7890, (123) 456-7890, 123 456 7890)
        if settings.SCRUB_PHONE:
            self.patterns.append({
                "type": "PHONE",
                "regex": re.compile(r'(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b')
            })

        # 4. Credit Card (13-19 digits, optional spaces/dashes)
        # Note: This uses a simple digit counters. 
        # For stricter checks, we would implement the Luhn algorithm, 
        # but that is slow for regex. This catches the shape of a CC.
        if settings.SCRUB_CREDIT_CARDS:
            self.patterns.append({
                "type": "CC",
                "regex": re.compile(r'\b(?:\d[ -]*?){13,16}\b')
            })

    def scrub(self, text: str) -> str:
        """
        Input: "Call me at 555-0199 about VISA 4111 1111 1111 1111"
        Output: "Call me at [REDACTED_PHONE] about VISA [REDACTED_CC]"
        """
        if not text:
            return ""

        scrubbed_text = text
        
        for p in self.patterns:
            # We use a lambda to insert the specific type into the mask
            replacement = settings.REDACTION_MASK.format(type=p["type"])
            scrubbed_text = p["regex"].sub(replacement, scrubbed_text)
            
        return scrubbed_text

# Singleton instance for easy import
scrubber = PIIScrubber()