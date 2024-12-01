import logging
from dataclasses import dataclass
from typing import List, Optional, Set, Tuple

from Code.xml_object import XMLElement

logger = logging.getLogger(__name__)


@dataclass
class IDParserUnit:
    add_id: Set[str]
    override_id: Set[str]

    @staticmethod
    def create_empty() -> "IDParserUnit":
        return IDParserUnit(set(), set())


def extract_ids(obj: Optional[XMLElement]) -> IDParserUnit:
    parsed_ids = IDParserUnit.create_empty()

    if not obj or obj.tag.lower() in ["infotext", "infotexts"]:
        return parsed_ids

    _parse_object(obj, parsed_ids)

    return parsed_ids


def _context_rule(context_type: Optional[str] = None):
    def _rule(
        obj: XMLElement,
        stack: List[Tuple[XMLElement, bool, Optional[str]]],
        is_override: bool,
        id_parser_unit: IDParserUnit,
        current_context: Optional[str],
    ):
        if context_type:
            for child in obj.iter_non_comment_childrens():
                if obj.tag.lower() == "override":
                    stack.append((child, True, context_type))
                    continue

                stack.append((child, is_override, context_type))

        else:
            for child in obj.iter_non_comment_childrens():
                if obj.tag.lower() == "override":
                    stack.append((child, True, current_context))
                    continue

                stack.append((child, is_override, current_context))

    return _rule


def _special_id_rule(name: str):
    def _rule(
        obj: XMLElement,
        stack: List[Tuple[XMLElement, bool, Optional[str]]],
        is_override: bool,
        id_parser_unit: IDParserUnit,
        current_context: Optional[str],
    ):
        if is_override:
            id_parser_unit.override_id.add(name)

        else:
            id_parser_unit.add_id.add(name)

    return _rule


def _id_rule(prefix: str, id_field: str = "identifier"):
    def _rule(
        obj: XMLElement,
        stack: List[Tuple[XMLElement, bool, Optional[str]]],
        is_override: bool,
        id_parser_unit: IDParserUnit,
        current_context: Optional[str],
    ):
        identifier = obj.attributes.get(id_field, obj.tag)
        full_id = f"{prefix}.{identifier}"

        if is_override:
            id_parser_unit.override_id.add(full_id)

        else:
            id_parser_unit.add_id.add(full_id)

    return _rule


def _ignore_rule():
    def _rule(*args, **kwargs):
        return

    return _rule


def _detect_animation(obj: XMLElement) -> Optional[str]:
    animation_type = obj.get_attribute_ignore_case("animationtype")
    if not animation_type:
        return None

    if animation_type in ["SwimSlow", "SwimFast"]:
        return f"WaterAnimation.{obj.tag}"

    if animation_type in ["Walk", "Run", "Crouch"]:
        return f"GroundAnimation.{obj.tag}"

    return None


# Rules configuration
_RULES = {
    "items": _context_rule("item"),
    "item": _id_rule("item"),
    "afflictions": _context_rule("affliction"),
    "affliction": _id_rule("affliction"),
    "cprsettings": _special_id_rule("CPRSettings"),
    # demon: I wouldn't say that I understand how to enter this into the ID sheets.
    "sounds": _ignore_rule(),
    "names": _ignore_rule(),
    "conversations": _ignore_rule(),
    ###
    "doc": _ignore_rule(),
    "prefabs": _ignore_rule(),
    "hintmanager": _ignore_rule(),
    "options": _ignore_rule(),
    "runconfig": _ignore_rule(),
    "character": _id_rule("Character", "speciesname"),
    "ragdoll": _id_rule("Ragdoll", "type"),
    # demon: Bullshit
    "huskappendage": _context_rule(),
    "limb": _id_rule("HuskAppendage.limb", "name"),
    "joint": _id_rule("HuskAppendage.joint", "name"),
    "permissionpresets": _ignore_rule(),
    "campaignsettingpresets": _ignore_rule(),
    "clientpermissions": _ignore_rule(),
    "karmamanager": _ignore_rule(),
    ###
    "levelobjects": _context_rule("levelobjects"),
    "levelobject": _id_rule("LevelObject"),
    "itemassembly": _id_rule("ItemAssembly", "name"),
    "upgrademodules": _context_rule(),
    "upgrademodule": _id_rule("UpgradeModule"),
    "upgradecategory": _id_rule("UpgradeCategory"),
    "talenttrees": _context_rule(),
    "talenttree": _id_rule("TalentTree", "jobidentifier"),
    "talents": _context_rule(),
    "talent": _id_rule("Talent"),
    "jobs": _context_rule(),
    "job": _id_rule("Job"),
    "corpses": _context_rule(),
    "corpse": _id_rule("Corpse"),
    "style": _special_id_rule("Style"),
    "backgroundcreatures": _context_rule("backgroundcreature"),
    "backgroundcreature": _id_rule("BackgroundCreature", ""),
    "randomevents": _context_rule(),
    "eventset": _id_rule("EventSet"),
    "missions": _context_rule(
        "mission"
    ),  # demon: If I forgot something, it will simply be marked as a mission.
    "mission": _context_rule("Mission"),
    "abandonedoutpostmission": _id_rule("Mission.Outpost"),
    "crawlerlairmission": _id_rule("Mission.AbandonedOutpost"),
    "salvagemission": _id_rule("Mission.Salvage"),
    "monstermission": _id_rule("Mission.Monster"),
    "piratemission": _id_rule("Mission.Pirate"),
    "mudraptorlairmission": _id_rule("Mission.MudraptorLair"),
    "thresherlairmission": _id_rule("Mission.ThresherLair"),
    "huskcrawlerlairmission": _id_rule("Mission.HuskCrawlerLair"),
    "outpostdestroymission": _id_rule("Mission.OutpostDestroy"),
    "mineralmission": _id_rule("Mission.Mineral"),
    "gotomission": _id_rule("Mission.Goto"),
    "escortmission": _id_rule("Mission.Escort"),
    "outpostmission": _id_rule("Mission.Outpost"),
    "cargomission": _id_rule("Mission.Cargo"),
    "eventprefabs": _context_rule(),
    "scriptedevent": _id_rule("ScriptedEvent"),
    "cavegenerationparameters": _context_rule(),
    "cave": _id_rule("Cave"),
    "outpostgenerationparameters": _context_rule(),
    "outpostconfig": _id_rule("OutpostConfig"),
    "mapgenerationparameters": _special_id_rule("MapGenerationParameters"),
    "orders": _context_rule(),
    "order": _id_rule("Order"),
    "factions": _context_rule(),
    "faction": _id_rule("Faction"),
    "levelgenerationparameters": _context_rule("levelgenerationparameter"),
    "levelgenerationparameter": _id_rule(
        "LevelGenerationParameter"
    ),  # demon: I'm not going to fucking write down every object
    "biomes": _context_rule("biome"),
    "biome": _id_rule("Biome"),
    "charactervariant": _id_rule("Charactervariant", "speciesname"),
    "wreckaiconfig": _id_rule("WreckAIConfig", "Entity"),
    "eventsprites": _context_rule("eventsprite"),
    "eventsprite": _id_rule("EventSprites"),
    "locationtypes": _context_rule("locationtype"),
    "locationtype": _id_rule("LocationType"),
    "npcsets": _context_rule(),
    "npcset": _context_rule("npc"),
    "npc": _id_rule("NPC"),
}


def _parse_object(
    obj: XMLElement,
    id_parser_unit: IDParserUnit,
):
    processing_stack: List[Tuple[XMLElement, bool, Optional[str]]] = [
        (obj, False, None)
    ]

    while processing_stack:
        current_obj, is_override, current_context = processing_stack.pop()
        obj_name_lower = current_obj.tag.lower()

        if obj_name_lower == "override":
            for child in current_obj.iter_non_comment_childrens():
                processing_stack.append((child, True, current_context))

            continue

        name_rule = _RULES.get(obj_name_lower)
        if name_rule:
            name_rule(
                current_obj,
                processing_stack,
                is_override,
                id_parser_unit,
                current_context,
            )

        elif current_context:
            context_rule = _RULES.get(current_context)
            if context_rule:
                context_rule(
                    current_obj,
                    processing_stack,
                    is_override,
                    id_parser_unit,
                    current_context,
                )

            else:
                _handle_animation(current_obj, is_override, id_parser_unit)

        else:
            _handle_animation(current_obj, is_override, id_parser_unit)


def _handle_animation(obj: XMLElement, is_override: bool, id_parser_unit: IDParserUnit):
    animation_id = _detect_animation(obj)
    if animation_id:
        if is_override:
            id_parser_unit.override_id.add(animation_id)
        else:
            id_parser_unit.add_id.add(animation_id)

    else:
        logger.warning(f"No rule found for object: {obj.tag} | {obj.tag.lower()}")
