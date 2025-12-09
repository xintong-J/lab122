"""Replaces the PII text entity with gen-z slang."""

import random
from typing import Dict, List

from presidio_anonymizer.operators import Operator, OperatorType


class GenZ(Operator):
    """Replaces the PII text entity with gen-z slang."""

    # Mapping from entity type → list of slang terms
    GENZ_MAP: Dict[str, List[str]] = {
        "PERSON": [
            "bestie", "pookie", "queen", "GOAT", "baddie", "mc",
            "slay", "based", "gagged", "snatched"
        ],
        "EMAIL_ADDRESS": [
            "brainrot", "touch grass", "iykyk", "no cap", "bet"
        ],
        "PHONE_NUMBER": [
            "fr fr", "bruh", "oop—", "big yikes", "vibe check"
        ],
        "CREDIT_CARD": [
            "this ain't it", "sheesh", "mid", "L", "bro???"
        ],
        "IP_ADDRESS": [
            "skibidi", "out of pocket", "sus", "rizzless", "delulu"
        ],
        "DATE_TIME": [
            "it's giving… time?", "Gucci hour", "dead 💀", "locked in"
        ],
        "URL": [
            "slaps", "fire", "bussin'", "gas", "drip"
        ],
        "LOCATION": [
            "Ohio", "vibe zone", "the lore", "the timeline", "the trenches"
        ],
        # fallback for other PII types
        "DEFAULT": [
            "slay", "mid", "big yikes", "skibidi", "based",
            "gigachad", "oop", "touch grass", "sus", "W"
        ]
    }

    ENTITY_TYPE = "entity_type"

    def operate(self, text: str = None, params: Dict = None) -> str:
        """Replace the entity text with a random Gen-Z slang term."""
        if not params:
            params = {}

        entity_type = params.get(self.ENTITY_TYPE, "DEFAULT")
        slang_options = self.GENZ_MAP.get(entity_type, self.GENZ_MAP["DEFAULT"])

        return random.choice(slang_options)

    def validate(self, params: Dict = None) -> None:
        """Params are optional."""
        pass

    def operator_name(self) -> str:
        """Return operator name."""
        return "genz"

    def operator_type(self) -> OperatorType:
        """Return operator type."""
        return OperatorType.Anonymize
