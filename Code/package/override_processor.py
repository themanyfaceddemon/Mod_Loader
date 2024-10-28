import logging
from typing import List, Set
import xml.etree.ElementTree as ET
from pathlib import Path

from .metadata import MetaData

logger = logging.getLogger("OverrideProcessor")


class OverrideProcessor:
    @staticmethod
    def process(metadata: MetaData, path: Path) -> None:
        root_process: List[Path] = []
        somethwere_process: List[Path] = []
        override_ids: Set[str] = set()

        for xml_file in path.rglob("*.xml"):
            if xml_file.name in {"filelist.xml", "metadata.xml"}:
                continue

            try:
                tree = ET.parse(str(xml_file))
                root = tree.getroot()
                if root.tag in {"infotext", "infotexts"}:
                    continue

                if root.tag == "Override":
                    root_process.append(xml_file)
                    continue

                elif root.find("Override") is not None:
                    if root.tag in {"infotext", "infotexts"}:
                        continue

                    somethwere_process.append(xml_file)
                    continue

            except ET.ParseError as err:
                logger.error(
                    "Error while process xml file\n"
                    f"| Path: {xml_file}\n"
                    f"| Error: {err}\n"
                )

        if root_process != []:
            override_ids.update(OverrideProcessor._process_root_override(root_process))

        if somethwere_process != []:
            override_ids.update(
                OverrideProcessor._process_somethwere_override(somethwere_process)
            )

        metadata.overrides = override_ids

    @staticmethod
    def _process_root_override(list_of_path: List[Path]) -> Set[str]:
        override_elements = set()

        for path in list_of_path:
            tree = ET.parse(str(path))
            root = tree.getroot()

            for elem in root:
                func_name = f"_parse_{elem.tag.lower()}"
                if not hasattr(OverrideProcessor, func_name):
                    logger.warning(
                        f"Processor does not recognize the element type.\n"
                        f"| Element type: {elem.tag}\n"
                        f"| Path: {path}\n"
                    )
                    continue

                method = getattr(OverrideProcessor, func_name)
                override_elements.update(method(elem))

        return override_elements

    @staticmethod
    def _process_somethwere_override(list_of_path: List[Path]) -> Set[str]:
        override_elements = set()

        for path in list_of_path:
            tree = ET.parse(str(path))
            root = tree.getroot()

            func_name = f"_parse_{root.tag.lower()}"
            if not hasattr(OverrideProcessor, func_name):
                logger.warning(
                    f"Processor does not recognize the element type.\n"
                    f"| Element type: {root.tag}\n"
                    f"| Path: {path}\n"
                )
                continue

            method = getattr(OverrideProcessor, func_name)

            temp_elements = set()

            for override in root.findall("Override"):
                for child in list(override):
                    root.append(child)
                    temp_elements.add(child.tag)

                root.remove(override)

            for child in list(root):
                if child.tag not in temp_elements:
                    root.remove(child)

            override_elements.update(method(root))

        return override_elements

    @staticmethod
    def _parse_items(element: ET.Element) -> Set[str]:
        result = set()
        for item in element:
            result.add(f"Item.{item.get('identifier', item.tag)}")

        return result

    @staticmethod
    def _parse_item(element: ET.Element) -> Set[str]:
        return {f"Item.{element.get('identifier')}"}

    @staticmethod
    def _parse_afflictions(element: ET.Element) -> Set[str]:
        result = set()
        for affliction in element:
            result.add(f"Affliction.{affliction.get("identifier", affliction.tag)}")

        return result

    @staticmethod
    def _parse_prefabs(element: ET.Element) -> Set[str]:
        result = set()
        for prefab in element:
            result.add(f"Prefab.{prefab.get("identifier")}")

        return result

    @staticmethod
    def _parse_style(element: ET.Element) -> Set[str]:
        return {"Style"}

    @staticmethod
    def _parse_randomevents(element: ET.Element) -> Set[str]:
        result = set()

        for rdv_element in element:
            if rdv_element.tag == "EventPrefabs":
                for ep_element in rdv_element:
                    if ep_element.tag == "ScriptedEvent":
                        result.add(
                            f"Randomevents.EventPrefabs.ScriptedEvent.{ep_element.get('identifier', ep_element.tag)}"
                        )

                    else:
                        logger.warning(
                            f"Processor does not recognize the randomevents override type.\n"
                            f"| Element type: {ep_element.tag}\n"
                            f"| Element: {ET.tostring(ep_element, encoding='utf-8')}\n"
                        )

            elif rdv_element.tag == "EventSet":
                result.add(f"Randomevents.EventSet.{rdv_element.get('identifier')}")

            elif rdv_element.tag == "EventSprites":
                for spr_element in rdv_element:
                    result.add(
                        f"Randomevents.EventSprites.{spr_element.get('identifier')}"
                    )

            else:
                logger.warning(
                    f"Processor does not recognize the randomevents override type.\n"
                    f"| Element type: {rdv_element.tag}\n"
                    f"| Element: {ET.tostring(rdv_element, encoding='utf-8')}\n"
                )

        return result

    @staticmethod
    def _parse_missions(element: ET.Element) -> Set[str]:
        result = set()
        for mission in element:
            result.add(f"Missions.{mission.tag}.{mission.get('identifier')}")

        return result

    @staticmethod
    def _parse_talents(element: ET.Element) -> Set[str]:
        result = set()
        for talant in element:
            result.add(f"Talant.{talant.get('identifier')}")

        return result

    @staticmethod
    def _parse_character(element: ET.Element) -> Set[str]:
        return {f"Character.{element.get('SpeciesName')}"}

    @staticmethod
    def _parse_orders(element: ET.Element) -> Set[str]:
        result = set()

        for order in element:
            result.add(f"Order.{order.get('identifier')}")

        return result

    @staticmethod
    def _parse_talenttrees(element: ET.Element) -> Set[str]:
        result = set()

        for talent_tree in element:
            result.add(f"TalentTree.{talent_tree.get('identifier')}")

        return result

    @staticmethod
    def _parse_talenttree(element: ET.Element) -> Set[str]:
        return {f"TalentTree.{element.get('identifier')}"}

    @staticmethod
    def _parse_corpses(element: ET.Element) -> Set[str]:
        result = set()

        for corpses in element:
            result.add(f"Corpse.{corpses.get('identifier')}")

        return result
