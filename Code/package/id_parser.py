import logging
from dataclasses import dataclass
from typing import List, Optional, Set

from Code.xml_object import XMLComment, XMLElement

logger = logging.getLogger("XMLIDParser")


@dataclass
class IDParserUnit:
    add_id: Set[str]
    override_id: Set[str]

    @staticmethod
    def create_empty() -> "IDParserUnit":
        return IDParserUnit(set(), set())


def get_items_identifier(element: XMLElement, *args, **kwargs):
    id_l = []

    for elem in element.iter_non_comment_childrens():
        children = (
            elem.iter_non_comment_childrens() if elem.name == "Override" else [elem]
        )

        id_l.extend(
            f'Item.{child.attributes.get("identifier", child.name)}'
            for child in children
        )

    return id_l


def get_afflictions_identifier(element: XMLElement, *args, **kwargs):
    id_l = []

    for elem in element.iter_non_comment_childrens():
        children = (
            elem.iter_non_comment_childrens() if elem.name == "Override" else [elem]
        )

        id_l.extend(
            f'Affliction.{child.attributes.get("identifier", child.name)}'
            for child in children
        )

    return id_l


def get_sounds_identifier(element: XMLElement, *args, **kwargs):
    id_l = []

    for elem in element.iter_non_comment_childrens():
        children = (
            elem.iter_non_comment_childrens() if elem.name == "Override" else [elem]
        )

        id_l.extend(f"Sound.{child.name}" for child in children)

    return id_l


def get_levelgenerationparameters_identifier(element: XMLElement, *args, **kwargs):
    id_l = []

    for elem in element.iter_non_comment_childrens():
        children = (
            elem.iter_non_comment_childrens() if elem.name == "Override" else [elem]
        )

        id_l.extend(
            f"LevelGenerationParameter.{child.attributes.get('identifier', child.name)}"
            for child in children
        )

    return id_l


def get_item_identifier(element: XMLElement, *args, **kwargs):
    return f'Item.{element.attributes.get("identifier", element.name)}'


def get_talent_identifier(element: XMLElement, *args, **kwargs):
    return f'Talant.{element.attributes.get("identifier", element.name)}'


def get_character_indefier(element: XMLElement, *args, **kwargs):
    return f'Character.{element.attributes.get("SpeciesName", element.name)}'


def get_affliction_identifier(element: XMLElement, *args, **kwargs):
    return f'Affliction.{element.attributes.get("identifier", element.name)}'


def get_ragdoll_indefier(element: XMLElement, *args, **kwargs):
    return f'Ragdoll.{element.attributes.get("type")}'


def get_style_indefier(element: XMLElement, *args, **kwargs):
    return "Style"


def get_talenttree_identifier(element: XMLElement, *args, **kwargs):
    return f'TalentTree.{element.attributes.get('jobidentifier')}'


def get_charactervariant_identifier(element: XMLElement, *args, **kwargs):
    return f'Charactervariant.{element.attributes.get('speciesname')}'


def get_upgrademodule_identifier(element: XMLElement, *args, **kwargs):
    return f'UpgradeModule.{element.attributes.get('identifier')}'


def get_npcset_indefier(element: XMLElement, *args, **kwargs):
    return f'npcset.{element.attributes.get('identifier')}'


def get_scriptedevent_identifier(element: XMLElement, *args, **kwargs):
    return f'ScriptedEvent.{element.attributes.get('identifier')}'


def get_eventset_identifier(element: XMLElement, *args, **kwargs):
    return f'EventSet.{element.attributes.get('identifier')}'


def iterate_children(element: XMLElement, stack: List[XMLElement], *args, **kwargs):
    if element.childrens:
        for child in element.iter_non_comment_childrens():
            stack.append(child)


def ignore(element: XMLElement, *args, **kwargs):
    return None


def is_animation(element: XMLElement) -> Optional[str]:
    if element.attributes.get("animationtype", None):
        return f"GroungAnimation.{element.name}"

    elif element.attributes.get("AnimationType", None):
        return f"WaterAnimation.{element.name}"

    return None


class IDParser:
    processing_rules = {
        "affliction": get_affliction_identifier,
        "afflictions": get_afflictions_identifier,
        "character": get_character_indefier,
        "doc": ignore,
        "infotext": ignore,
        "infotexts": ignore,
        "item": get_item_identifier,
        "items": get_items_identifier,
        "override": iterate_children,
        "ragdoll": get_ragdoll_indefier,
        "sounds": get_sounds_identifier,
        "style": get_style_indefier,
        "talent": get_talent_identifier,
        "talents": iterate_children,
        "talenttrees": iterate_children,
        "charactervariant": get_charactervariant_identifier,
        "runconfig": ignore,
        "itemassembly": ignore,  # Cain: Maybe I'm wrong
        "huskappendage": ignore,  # Cain: Maybe I'm wrong
        "talenttree": get_talenttree_identifier,
        "upgrademodules": iterate_children,
        "upgradecategory": ignore,  # Cain: Maybe I'm wrong
        "upgrademodule": get_upgrademodule_identifier,
        "karmamanager": ignore,  # Cain: Maybe I'm wrong
        "member": ignore,  # Cain: from doc
        "npcsets": iterate_children,
        "npcset": get_npcset_indefier,
        "randomevents": iterate_children,
        "eventprefabs": iterate_children,
        "scriptedevent": get_scriptedevent_identifier,
        "eventset": get_eventset_identifier,
        "levelgenerationparameters": get_levelgenerationparameters_identifier,
    }

    @staticmethod
    def get_ids(root_element: XMLElement) -> IDParserUnit:
        id_parser_unit = IDParserUnit.create_empty()
        stack = [root_element]

        while stack:
            element = stack.pop()
            element_type = element.name.lower()

            rule = IDParser.processing_rules.get(element_type, None)

            if rule:
                element_id = rule(element=element, stack=stack)
                if element_id:
                    if isinstance(element_id, str):
                        id_parser_unit.add_id.add(element_id)

                    elif isinstance(element_id, (set, list)):
                        id_parser_unit.add_id.update(element_id)

            else:
                anim_id = is_animation(element)
                if not anim_id:
                    logger.warning(f"Unknown rule for '{element.name}'")
                else:
                    id_parser_unit.add_id.add(anim_id)

        for override_element in root_element.find("Override"):
            if isinstance(override_element, XMLComment):
                continue

            elements_to_process = (
                list(override_element.iter_non_comment_childrens())
                if override_element is root_element
                else [override_element]
            )

            for elem in elements_to_process:
                elem_type = elem.name.lower()
                rule = IDParser.processing_rules.get(elem_type, None)

                if rule:
                    element_id = rule(element=elem, stack=[])
                    if element_id:
                        if isinstance(element_id, str):
                            id_parser_unit.override_id.add(element_id)
                            id_parser_unit.add_id.discard(element_id)

                        elif isinstance(element_id, (set, list)):
                            id_parser_unit.override_id.update(element_id)
                            for id_ in element_id:
                                id_parser_unit.add_id.discard(id_)

                else:
                    anim_id = is_animation(elem)
                    if not anim_id:
                        logger.warning(f"Unknown rule for '{elem.name}' in override")

                    else:
                        id_parser_unit.override_id.add(anim_id)
                        id_parser_unit.add_id.discard(anim_id)

        return id_parser_unit
