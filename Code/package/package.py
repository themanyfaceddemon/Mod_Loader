import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional, Set, Union

logger = logging.getLogger("PackageParsing")


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
        self.dependencies: Optional[Dict[str, Dict[str, Dict[str, str]]]] = (
            self._parse_dependencies()
        )

    def get_identifier(self) -> str:
        return self.steamID if self.steamID else self.name

    def _has_file_type(self, file_extension: str) -> bool:
        return any(self.path.rglob(f"*{file_extension}"))

    def _collect_overrides(self) -> Optional[Set[str]]:
        overrides = set()
        for xml_file in self._find_xml_files():
            file_overrides = self._get_overrides_from_file(xml_file)
            if file_overrides:
                overrides.update(file_overrides)
        return overrides if overrides else None

    def _parse_dependencies(self) -> Optional[Dict[str, Dict[str, Dict[str, str]]]]:
        dependency_file = self.path / "dependencies.xml"
        if not dependency_file.exists():
            return None

        tree = ET.parse(dependency_file)
        root = tree.getroot()

        self._parse_ignore_checks(root)
        dependencies = {
            category: self._parse_mods_in_category(root, category)
            for category in ["patch", "requirement", "optional", "conflict"]
        }

        return dependencies

    def _parse_ignore_checks(self, root: ET.Element) -> None:
        self.ignore_lua_check = root.get("IgnoreLUACheck", "false").lower() == "true"
        self.ignore_cs_dll_check = (
            root.get("IgnoreCSDLLCheck", "false").lower() == "true"
        )

    def _parse_mods_in_category(
        self, root: ET.Element, category: str
    ) -> Dict[str, Dict[str, str]]:
        category_element = root.find(category)
        if category_element is None:
            return {}

        dep_dict = {}
        for mod in category_element.findall("mod"):
            mod_info = self._extract_mod_info(mod)
            dep_id = mod_info.get("steamID") or mod_info.get("name")
            if dep_id:
                dep_dict[dep_id] = mod_info
        return dep_dict

    def _extract_mod_info(self, mod_element: ET.Element) -> Dict[str, str]:
        mod_info = {"name": mod_element.get("name", "NotSetModName")}
        steam_id = mod_element.get("steamID")
        if steam_id:
            mod_info["steamID"] = steam_id

        return mod_info

    def _find_xml_files(self) -> Set[Path]:
        return set(self.path.rglob("*.xml"))

    def _get_overrides_from_file(self, xml_file: Path) -> Optional[Set[str]]:
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
            method_name = f"_parse_{elem.tag.lower()}"
            parent_method_name = f"_parse_{parent_element.tag.lower()}"

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

    def _parse_character(self, elem: ET.Element) -> Set[str]:
        species_name = elem.get("SpeciesName")
        if species_name:
            return {f"Character.{species_name}"}
        return set()

    def _parse_afflictions(self, elem: ET.Element) -> Set[str]:
        return {
            affliction
            for afflict in elem
            for affliction in self._parse_affliction(afflict)
        }

    def _parse_affliction(self, elem: ET.Element) -> Set[str]:
        identifier = elem.get("identifier")
        if identifier:
            return {f"Affliction.{identifier}"}
        elif elem.tag == "CPRSettings":
            return {"Affliction.CPRSettings"}
        else:
            logger.warning(
                f"Affliction identifier not found in element {elem.tag}\n"
                f"| Full element: {ET.tostring(elem, encoding='unicode')}"
            )
            return set()

    def _parse_afflictionhusk(self, elem: ET.Element) -> Set[str]:
        return {"Affliction.AfflictionHusk"}

    def _parse_nastyscar(self, elem: ET.Element) -> Set[str]:  # fuck u DynamicEuropa
        return {f"Affliction.{elem.get("identifier")}"}

    def _parse_talenttrees(self, elem: ET.Element) -> Set[str]:
        return {talent for job in elem for talent in self._parse_talenttree(job)}

    def _parse_talenttree(self, elem: ET.Element) -> Set[str]:
        job_id = elem.get("jobidentifier")
        return {
            f"TalentTree.{job_id}.{sub_tree.get('identifier')}" for sub_tree in elem
        }

    def _parse_items(self, elem: ET.Element) -> Set[str]:
        return {item for item_elem in elem for item in self._parse_item(item_elem)}

    def _parse_item(self, elem: ET.Element) -> Set[str]:
        identifier = elem.get("identifier")
        if identifier:
            return {f"Item.{identifier}"}
        return set()

    def _parse_talent(self, elem: ET.Element) -> Set[str]:
        identifier = elem.get("identifier")
        if identifier:
            return {f"Talent.{identifier}"}
        return set()

    def _parse_eventset(self, elem: ET.Element) -> Set[str]:
        identifier = elem.get("identifier")
        if identifier:
            return {f"EventSet.{identifier}"}
        return set()

    def _parse_missions(self, elem: ET.Element) -> Set[str]:
        return {
            f"Mission.{mission.get('identifier')}"
            for mission in elem
            if mission.get("identifier")
        }

    def _parse_sounds(self, elem: ET.Element) -> Set[str]:
        return {sound for sound_elem in elem for sound in self._parse_sound(sound_elem)}

    def _parse_sound(self, elem: ET.Element) -> Set[str]:
        sound_type = elem.tag.lower()
        if sound_type == "music":
            music_type = elem.get("type")
            if music_type:
                return {f"Sound.music.{music_type}"}
        elif sound_type == "damagesound":
            damage_sound_type = elem.get("damagesoundtype")
            if damage_sound_type:
                return {f"Sound.damagesoundtype.{damage_sound_type}"}
        elif sound_type == "guisound":
            gui_sound_type = elem.get("guisoundtype")
            if gui_sound_type:
                return {f"Sound.guisound.{gui_sound_type}"}
        else:
            return {f"Sound.{sound_type}"}
        return set()

    def _parse_skillsettings(self, elem: ET.Element) -> Set[str]:
        return {"SkillSettings"}

    def _parse_biomes(self, elem: ET.Element) -> Set[str]:
        return {biome for biome_elem in elem for biome in self._parse_biome(biome_elem)}

    def _parse_biome(self, elem: ET.Element) -> Set[str]:
        identifier = elem.get("identifier")
        if identifier:
            return {f"Biome.{identifier}"}
        return set()

    def _parse_levelgenerationparameters(self, elem: ET.Element) -> Set[str]:
        return {
            f"LevelGenerationParameters.{el.get('identifier')}"
            for el in elem
            if el.tag not in {"Biomes", "Biome"} and el.get("identifier")
        }

    def _parse_randomevents(self, elem: ET.Element) -> Set[str]:
        events = elem.findall(".//ScriptedEvent")
        return {
            f"ScriptedEvent.{event.get('ScriptedEvent')}"
            for event in events
            if event.get("ScriptedEvent")
        }

    def _parse_locationtypes(self, elem: ET.Element) -> Set[str]:
        return {
            f"Locationtypes.{location.get('identifier')}"
            for location in elem
            if location.get("identifier")
        }

    def __str__(self) -> str:
        return (
            f"Name: {self.name}\n"
            f"SteamID: {self.steamID}\n"
            f"Local mod: {self.local}\n"
            f"Load order: {self.order}\n"
            f"Has lua: {self.has_lua}\n"
            f"Has CS: {self.has_cs}\n"
            f"Has DLL: {self.has_dll}\n"
            f"Override: {self.override}"
        )
