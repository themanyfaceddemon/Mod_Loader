from typing import Set


def evaluate_condition(condition: str, active_mod_ids: Set[str]) -> bool:
    condition = condition.strip()
    if condition.startswith("ifhas(") and condition.endswith(")"):
        mod_id = condition[6:-1].strip().strip("'\"")
        return mod_id in active_mod_ids

    return True
