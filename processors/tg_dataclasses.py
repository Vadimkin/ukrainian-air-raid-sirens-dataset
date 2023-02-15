from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Literal, Optional

from translitua import translit

PLACE_LEVEL = Literal['oblast', 'raion', 'hromada']


@dataclass
class OfficialAirRaidAlertChannelAlert:
    """Class for keeping track of an item in inventory."""
    oblast: str
    raion: str
    hromada: str
    level: PLACE_LEVEL
    started_at: datetime
    finished_at: Optional[datetime] = None
    source: Literal['official', 'volunteer'] = "official"

    def dict(self, lang: str = 'uk'):
        if lang == 'uk':
            return {k: str(v) for k, v in asdict(self).items()}

        transliterated = {}

        keys_to_transliterate = ['oblast', 'raion', 'hromada']
        special_rules = {
            # Official:
            "м. Київ": "Kyiv City",
            # Volunteer naming:
            "Київ": "Kyiv City",
        }

        for k, v in asdict(self).items():
            if k in keys_to_transliterate:
                if v in special_rules:
                    transliterated[k] = special_rules[v]
                    continue

                transliterated[k] = translit(v)
                continue

            transliterated[k] = str(v)

        return transliterated
