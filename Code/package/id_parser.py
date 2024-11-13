import logging
from dataclasses import dataclass
from typing import List, Optional, Set

from Code.xml_object import XMLElement

logger = logging.getLogger("XMLIDParser")


@dataclass
class IDParserUnit:
    add_id: Set[str]
    override_id: Set[str]

    @staticmethod
    def create_empty() -> "IDParserUnit":
        return IDParserUnit(set(), set())


def _get_identifiers_for_list(prefix: str, identifier_key: str = "identifier"):
    return lambda element, *args, **kwargs: [
        f"{prefix}.{child.get_attribute_ignore_case(identifier_key, child.name)}"
        for elem in element.iter_non_comment_childrens()
        for child in (
            elem.iter_non_comment_childrens() if elem.name == "Override" else [elem]
        )
    ]


_get_afflictions_identifier = _get_identifiers_for_list("Affliction")
_get_backgroundcreatures_identifier = _get_identifiers_for_list("BackgroundCreature")
_get_items_identifier = _get_identifiers_for_list("Item")
_get_levelgenerationparameters_identifier = _get_identifiers_for_list(
    "LevelGenerationParameter"
)
_get_levelobjects_identifier = _get_identifiers_for_list("LevelObjects")
_get_locationtypes_identifier = _get_identifiers_for_list("LocationType")
_get_missions_identifier = _get_identifiers_for_list("Mission")
_get_prefabs_identifier = _get_identifiers_for_list("Prefab")
_get_sounds_identifier = _get_identifiers_for_list("Sound")


def _get_identifier(prefix: str, identifier: str = "identifier"):
    return (
        lambda element,
        *args,
        **kwargs: f"{prefix}.{element.get_attribute_ignore_case(identifier, element.name)}"
    )


_get_affliction_identifier = _get_identifier("Affliction")
_get_cave_identifier = _get_identifier("Cave")
_get_character_indefier = _get_identifier("Character", "SpeciesName")
_get_charactervariant_identifier = _get_identifier("Charactervariant", "speciesname")
_get_conversations_identifier = _get_identifier("Conversations")
_get_corpse_identifier = _get_identifier("Corpse")
_get_eventset_identifier = _get_identifier("EventSet")
_get_eventsprites_identifier = _get_identifier("EventSprite")
_get_faction_identifier = _get_identifier("Faction")
_get_item_identifier = _get_identifier("Item")
_get_job_identifier = _get_identifier("Job")
_get_npcset_indefier = _get_identifier("NPCSet")
_get_order_identifier = _get_identifier("Order")
_get_outpostconfig_identifier = _get_identifier("OutpostConfig")
_get_ragdoll_indefier = _get_identifier("Ragdoll", "type")
_get_scriptedevent_identifier = _get_identifier("ScriptedEvent")
_get_talent_identifier = _get_identifier("Talant")
_get_talenttree_identifier = _get_identifier("TalentTree", "jobidentifier")
_get_upgrademodule_identifier = _get_identifier("UpgradeModule")


def iterate_children(element: XMLElement, stack: List[XMLElement], *args, **kwargs):
    if element.childrens:
        for child in element.iter_non_comment_childrens():
            stack.append(child)


def ignore(element: XMLElement, *args, **kwargs):
    return None


def is_animation(element: XMLElement) -> Optional[str]:
    anim_type = element.get_attribute_ignore_case("animationtype")
    if not anim_type:
        return None

    if anim_type in ["SwimSlow", "SwimFast"]:
        return f"WaterAnimation.{element.name}"

    if anim_type in ["Walk", "Run", "Crouch"]:
        return f"GroungAnimation.{element.name}"

    return None


class IDParser:
    processing_rules = {
        "affliction": _get_affliction_identifier,
        "afflictions": _get_afflictions_identifier,
        "backgroundcreatures": _get_backgroundcreatures_identifier,
        "campaignsettingpresets": ignore,  # Cain: Maybe I'm wrong
        "cave": _get_cave_identifier,
        "cavegenerationparameters": iterate_children,
        "character": _get_character_indefier,
        "charactervariant": _get_charactervariant_identifier,
        "clientpermissions": ignore,  # Cain: Maybe I'm wrong
        "conversations": _get_conversations_identifier,
        "corpse": _get_corpse_identifier,
        "corpses": iterate_children,
        "doc": ignore,
        "eventprefabs": iterate_children,
        "eventset": _get_eventset_identifier,
        "eventsprites": _get_eventsprites_identifier,
        "faction": _get_faction_identifier,
        "factions": iterate_children,
        "hintmanager": ignore,  # Cain: wtf?
        "huskappendage": ignore,  # Cain: Maybe I'm wrong
        "infotext": ignore,
        "infotexts": ignore,
        "item": _get_item_identifier,
        "itemassembly": ignore,  # Cain: Maybe I'm wrong
        "items": _get_items_identifier,
        "job": _get_job_identifier,
        "jobs": iterate_children,
        "karmamanager": ignore,  # Cain: Maybe I'm wrong
        "levelgenerationparameters": _get_levelgenerationparameters_identifier,
        "levelobjects": _get_levelobjects_identifier,
        "locationtypes": _get_locationtypes_identifier,
        "mapgenerationparameters": lambda *args, **kwargs: "MapGenerationParameters",
        "member": ignore,  # Cain: from doc
        "missions": _get_missions_identifier,
        "names": ignore,  # Cain: idn how to identifier this
        "npcset": _get_npcset_indefier,
        "npcsets": iterate_children,
        "options": ignore,
        "order": _get_order_identifier,
        "orders": iterate_children,
        "outpostconfig": _get_outpostconfig_identifier,
        "outpostgenerationparameters": iterate_children,
        "override": iterate_children,
        "permissionpresets": ignore,  # Cain: Maybe I'm wrong
        "prefabs": _get_prefabs_identifier,
        "ragdoll": _get_ragdoll_indefier,
        "randomevents": iterate_children,
        "runconfig": ignore,
        "scriptedevent": _get_scriptedevent_identifier,
        "sounds": _get_sounds_identifier,
        "spritedeformation": ignore,  # Cain: Maybe I'm wrong
        "style": lambda *args, **kwargs: "Style",
        "talent": _get_talent_identifier,
        "talents": iterate_children,
        "talenttree": _get_talenttree_identifier,
        "talenttrees": iterate_children,
        "upgradecategory": ignore,  # Cain: Maybe I'm wrong
        "upgrademodule": _get_upgrademodule_identifier,
        "upgrademodules": iterate_children,
        "wreckaiconfig": lambda *args, **kwargs: "WreckAIConfig",
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

        for override_element in root_element.find_only_elements("Override", True):
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
