import re
from typing import Callable, Dict, List, Optional

condition_handlers: Dict[str, Callable[..., bool]] = {}


def register_condition_handler(prefix: str):
    def decorator(func: Callable[..., bool]):
        condition_handlers[prefix] = func
        return func

    return decorator


def process_condition(condition: Optional[str], **kwargs) -> bool:
    if not condition:
        return False

    def eval_single(cond: str) -> bool:
        cond = cond.strip()
        for prefix, handler in condition_handlers.items():
            if cond.startswith(prefix) and cond.endswith(")"):
                inner_context = cond[len(prefix) : -1].strip()
                return handler(inner_context, **kwargs)

        raise ValueError(f"Unknown condition format: {cond}")

    def precedence(op: str) -> int:
        return {"&": 2, "|": 1}.get(op, 0)

    def apply_operator(
        op: str, left: Callable[[], bool], right: Callable[[], bool]
    ) -> bool:
        if op == "&":
            return left() and right()

        if op == "|":
            return left() or right()

        raise ValueError(f"Unsupported operator: {op}")

    def process_expression(tokens: List[str]) -> bool:
        values: List[Callable[[], bool]] = []
        operators: List[str] = []

        for token in tokens:
            token = token.strip()
            if not token:
                continue

            if token == "(":
                operators.append(token)

            elif token == ")":
                while operators and operators[-1] != "(":
                    op = operators.pop()
                    right = values.pop()
                    left = values.pop()
                    values.append(lambda l=left, r=right, o=op: apply_operator(o, l, r))  # noqa: E741

                operators.pop()

            elif token in ("&", "|"):
                while (
                    operators
                    and operators[-1] != "("
                    and precedence(operators[-1]) >= precedence(token)
                ):
                    op = operators.pop()
                    right = values.pop()
                    left = values.pop()
                    values.append(lambda l=left, r=right, o=op: apply_operator(o, l, r))  # noqa: E741

                operators.append(token)

            else:
                values.append(lambda t=token: eval_single(t))

        while operators:
            op = operators.pop()
            right = values.pop()
            left = values.pop()
            values.append(lambda l=left, r=right, o=op: apply_operator(o, l, r))  # noqa: E741

        return values[0]()

    tokens = re.findall(r"\(|\)|\w+\(.*?\)|&|\|", condition.replace(" ", ""))
    return process_expression(tokens)


@register_condition_handler("ifhas(")
def handle_ifhas(inner_context: str, **kwargs) -> bool:
    """True if has mod"""
    mod_id = inner_context.strip("'\"")
    active_mod_ids = kwargs.get("active_mod_ids", set())
    return mod_id in active_mod_ids
