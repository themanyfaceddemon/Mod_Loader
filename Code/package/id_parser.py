import logging
from dataclasses import dataclass
from typing import List, Optional, Set, Tuple

from Code.xml_object import XMLElement

logger = logging.getLogger("XMLIDParser")


@dataclass
class IDParserUnit:
    add_id: Set[str]
    override_id: Set[str]

    @staticmethod
    def create_empty() -> "IDParserUnit":
        return IDParserUnit(set(), set())


def get_ids(obj: Optional[XMLElement]) -> IDParserUnit:
    return_obj = IDParserUnit.create_empty()

    if not obj or obj.name.lower() in ["infotext", "infotexts"]:
        return return_obj

    _pars(obj, return_obj)

    return return_obj


def _contecst_rule(con_type: str):
    def _rule(
        obj: XMLElement,
        stack: List[Tuple[XMLElement, bool, Optional[str]]],
        is_override: bool,
        id_p_u: IDParserUnit,
    ):
        for ch in obj.iter_non_comment_childrens():
            if obj.name.lower() == "override":
                stack.append((ch, True, con_type))
                continue

            stack.append((ch, is_override, con_type))

    return _rule


def _id_rule(prefix: str, id_fild: str = "identifier"):
    def _rule(
        obj: XMLElement,
        stack: List[Tuple[XMLElement, bool, Optional[str]]],
        is_override: bool,
        id_p_u: IDParserUnit,
    ):
        if is_override:
            id_p_u.override_id.add(f"{prefix}.{obj.attributes.get(id_fild, obj.name)}")
        else:
            id_p_u.add_id.add(f"{prefix}.{obj.attributes.get(id_fild, obj.name)}")

    return _rule


def _is_animation(obj: XMLElement) -> Optional[str]:
    anim_type = obj.get_attribute_ignore_case("animationtype")
    if not anim_type:
        return None

    if anim_type in ["SwimSlow", "SwimFast"]:
        return f"WaterAnimation.{obj.name}"

    if anim_type in ["Walk", "Run", "Crouch"]:
        return f"GroungAnimation.{obj.name}"

    return None


def _ignore(*args, **kwargs):
    return


_RULES = {"items": _contecst_rule("item"), "item": _id_rule("item")}


def _pars(
    obj: XMLElement,
    id_p_u: IDParserUnit,
):
    cur_stack: List[Tuple[XMLElement, bool, Optional[str]]] = [(obj, False, None)]

    while cur_stack:
        cur_obj = cur_stack.pop()
        obj_el = cur_obj[0]
        obj_name = cur_obj[0].name.lower()
        is_override = cur_obj[1]
        cur_contecst = cur_obj[2]

        if obj_name == "override":
            for ch in obj_el.iter_non_comment_childrens():
                cur_stack.append((ch, True, cur_contecst))

            continue

        name_rule = _RULES.get(obj_name)
        if name_rule:
            name_rule(obj_el, cur_stack, is_override, id_p_u)

        elif cur_contecst:
            con_rule = _RULES.get(cur_contecst)
            if con_rule:
                con_rule(obj_el, cur_stack, is_override, id_p_u)

            else:
                anim_id = _is_animation(obj_el)
                if anim_id:
                    if is_override:
                        id_p_u.override_id.add(anim_id)
                    else:
                        id_p_u.add_id.add(anim_id)
                else:
                    logger.warning(f"Rule not set for: {obj_name}")

        else:
            anim_id = _is_animation(obj_el)
            if anim_id:
                if is_override:
                    id_p_u.override_id.add(anim_id)
                else:
                    id_p_u.add_id.add(anim_id)
            else:
                logger.warning(f"Rule not set for: {obj_name}")
