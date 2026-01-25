"""
Mapper for legacy state names to new state names.

This module provides a function to map old community and raion names
from states_legacy.json to new names in states.json.
"""

from typing import Optional, Tuple


# Mapping of renamed raions: (oblast, old_raion) -> new_raion
_RAION_RENAMES = {
    ("Дніпропетровська область", "Новомосковський район"): "Самарівський район",
    ("Житомирська область", "Новоград-Волинський район"): "Звягельський район",
}

# Mapping of renamed communities: (oblast, raion, old_community) -> new_community
_COMMUNITY_RENAMES = {
    ("Сумська область", "Сумський район", "Миколаївська сільська територіальна громада"): "Миколаївська територіальна громада",
}


def get_new_name(
    oblast: str,
    raion: str,
    community: Optional[str] = None
) -> Optional[Tuple[str, Optional[str]]]:
    """
    Map old raion and community names to their new names.

    Args:
        oblast: The oblast (state) name.
        raion: The raion (district) name.
        community: The community name (optional).

    Returns:
        A tuple (new_raion, new_community) if either raion or community has been renamed.
        Returns None if no renaming is needed.

        If only raion was renamed, new_community will be the same as input community.
        If only community was renamed, new_raion will be the same as input raion.
    """
    new_raion = _RAION_RENAMES.get((oblast, raion))

    new_community = None
    if community is not None:
        # Use the new raion name if it exists, otherwise use original
        lookup_raion = new_raion if new_raion else raion
        new_community = _COMMUNITY_RENAMES.get((oblast, lookup_raion, community))

        # Also try with the original raion name in case community rename was recorded with old raion
        if new_community is None:
            new_community = _COMMUNITY_RENAMES.get((oblast, raion, community))

    # Return tuple if any renaming occurred
    if new_raion is not None or new_community is not None:
        return (
            new_raion if new_raion else raion,
            new_community if new_community else community
        )

    return None
