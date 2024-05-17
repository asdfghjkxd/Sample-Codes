"""
Contains verification functions for fields used in the demo app
"""

import re


def verify_uen(uen: str) -> bool:
    """Verifies if the UEN provided is preliminarily valid"""

    if len(uen) != 9 and len(uen) != 10:
        return False

    if len(uen) == 9:
        return True if re.compile(r"[0-9]{8}[A-Z]{1}").match(uen) else False

    if len(uen) == 10:
        match1 = re.compile(r"[0-9]{9}[A-Z]{1}").match(uen)
        match2 = re.compile(r"T[0-9]{2}[A-Z]{2}[0-9]{4}[A-Z]{1}").match(uen)
        found_match = match1 or match2

        return True if found_match else False