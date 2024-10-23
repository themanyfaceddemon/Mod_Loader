import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

logger = logging.getLogger("Package parsing")


class Package:
    def __init__(
        self,
        name: str,
        steamID: Optional[str],
        path: Union[str, Path],
        local: bool = False,
        order: Optional[int] = None,
    ) -> None:
        self.name: str = name
        self.steamID: Optional[str] = steamID
        self.path: Path = Path(path)
        self.local: bool = local
        self.order: Optional[int] = order

        self.ignore_lua_check: bool = False
        self.ignore_cs_dll_check: bool = False
        self.has_lua: bool = self._has_file_type(".lua")
        self.has_cs: bool = self._has_file_type(".cs")
        self.has_dll: bool = self._has_file_type(".dll")

        self.override: Optional[Set[str]] = self._collect_overrides()
        self.dependencies: Dict[str, Dict[str, Dict[str, str]]] = (
            self._parse_dependencies()
        )

    def _has_file_type(self, file_extension: str) -> bool:
        """Check if the specified file type exists in the path."""
        return any(self.path.rglob(f"*{file_extension}"))

    def _collect_overrides(self) -> Optional[Set[str]]:
        """Collect all overrides by parsing XML files."""
        xml_files = self._find_xml_files()
        all_overrides = {
            override
            for xml_file in xml_files
            for override in self._get_override(xml_file) or []
        }
        return all_overrides if all_overrides else None

    def _parse_dependencies(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        """Parse dependencies from the XML file."""
        dependency_file = self.path / "dependens.xml"
        if not dependency_file.exists():
            return {
                category: {}
                for category in ["patch", "requirement", "optional", "conflict"]
            }

        tree = ET.parse(str(dependency_file))
        root = tree.getroot()

        self._parse_ignore_checks(root)
        dependencies = {
            category: self._parse_mods_in_category(root, category)
            for category in ["patch", "requirement", "optional", "conflict"]
        }

        return dependencies

    def _parse_ignore_checks(self, root: ET.Element) -> None:
        """Parse flags for ignoring Lua and CS/DLL checks."""
        self.ignore_lua_check = root.get("IgnoreLUACheck", "false").lower() == "true"
        self.ignore_cs_dll_check = (
            root.get("IgnoreCSDLLCheck", "false").lower() == "true"
        )

    def _parse_mods_in_category(
        self, root: ET.Element, category: str
    ) -> Dict[str, Dict[str, str]]:
        """Parse mods for a given category."""
        category_element = root.find(category)

        if category_element is None:
            return {}

        return {
            mod.get("name", "NotSetModName"): self._extract_mod_info(mod)
            for mod in category_element.findall("mod")
        }

    def _extract_mod_info(self, mod_element: ET.Element) -> Dict[str, str]:
        """Extract mod information including name and optional steamID."""
        mod_info = {"name": mod_element.get("name", "NotSetModName")}

        steam_id = mod_element.get("steamID")
        if steam_id:
            mod_info["steamID"] = steam_id

        return mod_info

    def _find_xml_files(self) -> Set[Path]:
        """Find all XML files in the given path."""
        return set(self.path.rglob("*.xml"))

    def _get_override(self, xml_file: Path) -> Optional[Set[str]]:
        try:
            tree = ET.parse(str(xml_file))
            root = tree.getroot()

            if root.tag in {"infotext", "infotexts"}:
                return None

            if root.tag == "Override":
                return self._process_override(root, root)

            override_elements = root.findall(".//Override")
            return (
                {
                    override
                    for element in override_elements
                    for override in self._process_override(element, root)
                }
                if override_elements
                else None
            )

        except ET.ParseError as e:
            logger.error(f"Failed to parse XML: {xml_file}. Error: {e}")
            return None

    def _process_override(
        self, override_element: ET.Element, parent_element: ET.Element
    ) -> Set[str]:
        overrides = set()

        for elem in override_element:
            method_name = f"_pars_{elem.tag.lower()}"
            parent_method_name = f"_pars_{parent_element.tag.lower()}"

            if hasattr(self, method_name):
                method = getattr(self, method_name)
                overrides.update(method(elem))

            elif hasattr(self, parent_method_name):
                method = getattr(self, parent_method_name)
                overrides.update(method(elem))

            else:
                logger.warning(
                    f"Method not found for element {elem.tag}\n"
                    f"| method_name: {method_name}\n"
                    f"| parent_method_name: {parent_method_name}"
                )

        return overrides

    def _pars_character(self, elem: ET.Element) -> List[str]:
        return [f"Character.{elem.get('SpeciesName')}"]

    def _pars_afflictions(self, elem: ET.Element) -> List[str]:
        return [
            affliction
            for afflict in elem
            for affliction in self._pars_affliction(afflict)
        ]

    def _pars_affliction(self, elem: ET.Element) -> List[str]:
        identifier = elem.get("identifier")
        if identifier:
            return [f"Affliction.{identifier}"]

        if elem.tag == "CPRSettings":
            return ["Affliction.CPRSettings"]

        logger.warning(
            f"Affliction identifier not found in {ET.tostring(elem, encoding='utf-8')}"
        )
        return []

    def _pars_afflictionhusk(self, elem: ET.Element) -> List[str]:
        return ["Affliction.AfflictionHusk"]

    def _pars_talenttrees(self, elem: ET.Element) -> List[str]:
        return [talent for job in elem for talent in self._pars_talenttree(job)]

    def _pars_talenttree(self, elem: ET.Element) -> List[str]:
        job_id = elem.get("jobidentifier")
        return [
            f"TalentTree.{job_id}.{sub_tree.get('identifier')}" for sub_tree in elem
        ]

    def _pars_items(self, elem: ET.Element) -> List[str]:
        return [item for item_elem in elem for item in self._pars_item(item_elem)]

    def _pars_item(self, elem: ET.Element) -> List[str]:
        return [f"Item.{elem.get('identifier')}"]

    def _pars_talent(self, elem: ET.Element) -> List[str]:
        return [f"Talent.{elem.get('identifier')}"]

    def _pars_eventset(self, elem: ET.Element) -> List[str]:
        return [f"EventSet.{elem.get('identifier')}"]

    def _pars_missions(self, elem: ET.Element) -> List[str]:
        return [f"Mission.{mission.get('identifier')}" for mission in elem]

    def _pars_sounds(self, elem: ET.Element) -> List[str]:
        return [sound for sound_elem in elem for sound in self._pars_sound(sound_elem)]

    def _pars_sound(self, elem: ET.Element) -> List[str]:
        sound_type = elem.tag
        sound_value = {
            "music": f"Sound.music.{elem.get('type')}",
            "damagesound": f"Sound.damagesoundtype.{elem.get('damagesoundtype')}",
            "guisound": f"Sound.guisound.{elem.get('guisoundtype')}",
        }.get(sound_type, f"Sound.{sound_type}")

        return [sound_value]

    def _pars_skillsettings(self, elem: ET.Element) -> List[str]:
        return ["SkillSettings"]

    def _pars_biomes(self, elem: ET.Element) -> List[str]:
        return [biome for biome_elem in elem for biome in self._pars_biome(biome_elem)]

    def _pars_biome(self, elem: ET.Element) -> List[str]:
        return [f"Biome.{elem.get('identifier')}"]

    def _pars_levelgenerationparameters(self, elem: ET.Element) -> List[str]:
        return [
            f'LevelGenerationParameters.{el.get("identifier")}'
            for el in elem
            if el.tag not in {"Biomes", "Biome"}
        ]

    def _pars_randomevents(self, elem: ET.Element) -> List[str]:
        events = elem.findall(".//ScriptedEvent")
        return (
            [f"ScriptedEvent.{event.get('ScriptedEvent')}" for event in events]
            if events
            else []
        )

    def _pars_locationtypes(self, elem: ET.Element) -> List[str]:
        return [f"Locationtypes.{location.get('identifier')}" for location in elem]

    def __str__(self) -> str:
        return (
            f"Name: {self.name}\n"
            f"Local mod: {self.local}\n"
            f"Load order: {self.order}\n"
            f"Has lua: {self.has_lua}\n"
            f"Has CS: {self.has_cs}\n"
            f"Has DLL: {self.has_dll}\n"
            f"Override: {self.override}"
        )
