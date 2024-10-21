import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional, Set, Union


class Package:
    def __init__(
        self,
        name: str,
        path: Union[str, Path],
        local: bool = False,
        order: Optional[int] = None,
    ) -> None:
        self.name: str = name
        self.path: Path = Path(path)
        self.local: bool = local
        self.order: Optional[int] = order

        self.has_lua: bool = False
        self.has_cs: bool = False
        self.has_dll: bool = False

        self.override: Optional[Set[str]] = None
        self._check_files()

    def _check_files(self) -> None:
        xml_files = self._find_xml_files(self.path)
        all_overrides = set()
        for xml_file in xml_files:
            result = self._get_override(xml_file)
            if result:
                all_overrides.update(result)

        self.override = all_overrides if all_overrides else None

        if self._find_lua_files(self.path):
            self.has_lua = True

        if self._find_cs_files(self.path):
            self.has_cs = True

        if self._find_dll_files(self.path):
            self.has_dll = True

    def _find_xml_files(self, directory: Path) -> Set[Path]:
        return set(directory.rglob("*.xml"))

    def _find_lua_files(self, directory: Path) -> Set[Path]:
        return set(directory.rglob("*.lua"))

    def _find_dll_files(self, directory: Path) -> Set[Path]:
        return set(directory.rglob("*.dll"))

    def _find_cs_files(self, directory: Path) -> Set[Path]:
        return set(directory.rglob("*.cs"))

    def _get_override(self, xml_file: Path) -> Optional[Set[str]]:
        override = set()

        try:
            tree = ET.parse(str(xml_file))
            root = tree.getroot()
            if root.tag in {"infotext", "infotexts"}:
                return None

            if root.tag == "Override":
                override.update(self._process_override(root, root))

            else:
                override_elements = root.findall(".//Override")

                if override_elements:
                    for override_element in override_elements:
                        override.update(self._process_override(override_element, root))

        except ET.ParseError as e:
            logging.error(f"Failed to parse XML: {xml_file}. Error: {e}")

        return override if override else None

    def _process_override(
        self, override_element: ET.Element, parent_element: ET.Element
    ) -> Set[str]:
        override = set()

        for elem in override_element:
            elem_name = elem.tag.lower()
            parent_method_name = f"_pars_{parent_element.tag.lower()}"
            method_name = f"_pars_{elem_name}"

            if hasattr(self, method_name):
                method = getattr(self, method_name)
                override.update(method(elem))

            elif hasattr(self, parent_method_name):
                method = getattr(self, parent_method_name)
                override.update(method(elem))

            else:
                logging.warning(
                    f"Method not found for element {elem.tag} | method_name: {method_name} | parent_method_name: {parent_method_name}"
                )

        return override

    def _pars_character(self, elem: ET.Element) -> List[str]:
        return [f"Character.{elem.get('SpeciesName')}"]

    def _pars_afflictions(self, elem: ET.Element) -> List[str]:
        ids = []
        for afflict in elem:
            ids.extend(self._pars_affliction(afflict))

        return ids

    def _pars_affliction(self, elem: ET.Element) -> List[str]:
        ids = []
        id = elem.get("identifier")

        if id is None:
            if elem.tag == "CPRSettings":
                ids.append("Affliction.CPRSettings")
            else:
                logging.warning(
                    f"Affliction identifier not found in {ET.tostring(elem, encoding='utf-8')}"
                )
        else:
            ids.append(f"Affliction.{id}")

        return ids

    def _pars_afflictionhusk(self, elem: ET.Element) -> List[str]:
        return [f"AfflictionHusk.{elem.get('identifier')}"]

    def _pars_talenttrees(self, elem: ET.Element) -> List[str]:
        ids = []
        for job in elem:
            ids.extend(self._pars_talenttree(job))

        return ids

    def _pars_talenttree(self, elem: ET.Element) -> List[str]:
        ids = []

        job_id = elem.get("jobidentifier")
        for sub_tree in elem:
            sub_tree_id = sub_tree.get("identifier")
            ids.append(f"TalentTree.{job_id}.{sub_tree_id}")

        return ids

    def _pars_items(self, elem: ET.Element) -> List[str]:
        ids = []
        for item in elem:
            ids.extend(self._pars_item(item))

        return ids

    def _pars_item(self, elem: ET.Element) -> List[str]:
        return [f"Item.{elem.get('identifier')}"]

    def _pars_talent(self, elem: ET.Element) -> List[str]:
        return [f"Talent.{elem.get('identifier')}"]

    def _pars_eventset(self, elem: ET.Element) -> List[str]:
        return [f"EventSet.{elem.get('identifier')}"]

    def _pars_missions(self, elem: ET.Element) -> List[str]:
        ids = []
        for mission in elem:
            ids.append(f"Mission.{mission.get('identifier')}")

        return ids

    def _pars_sounds(self, elem: ET.Element) -> List[str]:
        ids = []
        for sound in elem:
            sound_type = sound.tag
            if sound_type == "music":
                ids.append(f"Sound.music.{sound.get('type')}")
            elif sound_type == "damagesound":
                ids.append(f"Sound.damagesoundtype.{sound.get('damagesoundtype')}")
            elif sound_type == "guisound":
                ids.append(f"Sound.guisound.{sound.get('guisoundtype')}")
            else:
                ids.append(f"Sound.{sound_type}")  # WARNING Может вызвать баги

        return ids

    def _pars_skillsettings(self, elem: ET.Element) -> List[str]:
        return ["SkillSettings"]

    def _pars_biomes(self, elem: ET.Element) -> List[str]:
        ids = []
        for biome in elem:
            ids.extend(self._pars_biome(biome))

        return ids

    def _pars_biome(self, elem: ET.Element) -> List[str]:
        return [f"Biome.{elem.get('identifier')}"]

    def _pars_levelgenerationparameters(self, elem: ET.Element) -> List[str]:
        ids = []
        for el in elem:
            if el.tag not in {"Biomes", "Biome"}:
                ids.append(f'LevelGenerationParameters.{el.get('identifier')}')

        return ids

    def _pars_randomevents(self, elem: ET.Element) -> List[str]:
        ids = []
        events = elem.findall(
            ".//ScriptedEvent"
        )  # WARNING Возможны проблемы при перезаписи иконок. ХЗ
        if events:
            for event in events:
                ids.append(f"ScriptedEvent.{event.get('ScriptedEvent')}")

        return ids

    def _pars_locationtypes(self, elem: ET.Element) -> List[str]:
        ids = []
        for location in elem:
            ids.append(f"Locationtypes.{location.get('identifier')}")

        return ids

    def __str__(self) -> str:
        return f"Name: {self.name}\nLocal mod: {self.local}\nLoad order: {self.order}\nHas lua: {self.has_lua}\nHas CS: {self.has_cs}\nHas DLL: {self.has_dll}\nOverride: {self.override}"
