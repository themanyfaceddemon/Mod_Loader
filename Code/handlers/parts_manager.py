import logging
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Set

from Code.app_vars import AppConfig
from Code.package import ModUnit
from Code.xml_object import XMLBuilder, XMLComment, XMLElement

from .condition_manager import process_condition

logger = logging.getLogger(__name__)


# TODO: Это бы рефакторнуть разок
class PartsManager:
    # BTM: conditions="", setState="on/off"
    @staticmethod
    def do_chenges(mod: ModUnit, active_mod_id: Set[str]):
        PartsManager._corrupt_xml_by_config(mod.path, active_mod_id)

        for xml_path in mod.path.rglob("*.xml"):
            if xml_path.name.lower() in AppConfig.xml_system_dirs:
                continue

            with ThreadPoolExecutor() as executor:
                executor.submit(
                    PartsManager._corrupt_xml_by_commits, xml_path, active_mod_id
                )

    @staticmethod
    def rollback_chenges(mod: ModUnit):
        PartsManager._fix_xml_by_config(mod.path)

        for xml_path in mod.path.rglob("*.xml"):
            if xml_path.name.lower() in AppConfig.xml_system_dirs:
                continue

            with ThreadPoolExecutor() as executor:
                executor.submit(PartsManager._fix_xml_by_commits, xml_path)

    @staticmethod
    def rollback_changes_no_thread(mod: ModUnit):
        PartsManager._fix_xml_by_config(mod.path)

        for xml_path in mod.path.rglob("*.xml"):
            if xml_path.name.lower() in AppConfig.xml_system_dirs:
                continue

            PartsManager._fix_xml_by_commits(xml_path)

    @staticmethod
    def _corrupt_xml_by_commits(file_path: Path, active_mod_id: Set[str]):
        xml_obj = XMLBuilder.load(file_path)
        if xml_obj is None:
            return

        for com_start, objs, com_end in xml_obj.find_between_comments(
            "BTM:*:start", "BTM:*end"
        ):
            match = re.search(r"condition=(.*?)", com_start.content)
            if match:
                condition_value = match.group(1)
            else:
                logger.error(
                    f"Error in searching for switching condition value\n|Path: {file_path}"
                )
                continue

            match = re.search(r"setState=(.*?)", com_start.content)
            if match:
                set_state_to = (
                    True if match.group(1).lower() in ["on", "1", "true"] else False
                )
            else:
                logger.error(
                    f"Error in searching for set state value\n|Path: {file_path}"
                )
                continue

            if process_condition(condition_value, active_mods_ids=active_mod_id):
                for obj in objs:
                    if obj.index is None:
                        continue

                    if set_state_to:
                        if isinstance(obj, XMLElement):
                            continue

                    else:
                        if isinstance(obj, XMLComment):
                            continue

                    try:
                        if isinstance(obj, XMLComment):
                            xml_obj.replace(obj.index, obj.to_element())

                        else:
                            xml_obj.replace(obj.index, obj.to_comment())

                    except Exception:
                        continue

        XMLBuilder.save(xml_obj, file_path)

    @staticmethod
    def _corrupt_xml_by_config(mod_path: Path, active_mod_id: Set[str]):
        xml_obj = XMLBuilder.load((mod_path / "modparts.xml"))
        xml_file_list = XMLBuilder.load((mod_path / "filelist.xml"))

        if not all((xml_obj, xml_file_list)):
            return

        for action in xml_obj.iter_non_comment_childrens():  # type: ignore
            if not process_condition(
                action.get_attribute_ignore_case("conditions"),
                active_mod_id=active_mod_id,
            ):
                continue

            path_to_file = action.get_attribute_ignore_case("file")
            cond_type = action.get_attribute_ignore_case("type")
            set_to = action.get_attribute_ignore_case("setState")

            if not all((path_to_file, cond_type, set_to)):
                continue

            for item in xml_file_list.childrens:  # type: ignore # TODO Think about optimization
                if isinstance(item, XMLComment):
                    tag_item_start = item.content.find("<")
                    if tag_item_start == -1:
                        continue

                    tag_item = item.content[
                        tag_item_start : item.content.find(" ", tag_item_start)
                    ]

                    match = re.search(r"file=(.*?)", item.content)
                    if match:
                        item_file = match.group(1)

                    else:
                        continue

                    match = re.search(r"setState=(.*?)", item.content)
                    if match:
                        set_to = (
                            True if match.group(1).lower() in ["true", "on"] else False
                        )

                    else:
                        continue

                else:
                    tag_item = item.tag
                    item_file = item.get_attribute_ignore_case("file")
                    set_to = item.get_attribute_ignore_case("setState")
                    if not all((tag_item, item_file, set_to)):
                        continue

                    set_to = True if set_to.lower() in ["true", "on"] else False  # type: ignore

                if set_to:
                    if isinstance(item, XMLElement):
                        continue

                else:
                    if isinstance(item, XMLComment):
                        continue

                if tag_item == cond_type and item_file == path_to_file:
                    try:
                        if isinstance(item, XMLComment):
                            xml_file_list.replace(item.index, item.to_element())  # type: ignore

                        else:
                            xml_file_list.replace(item.index, item.to_comment())  # type: ignore

                    except Exception:
                        continue

        XMLBuilder.save(xml_file_list, (mod_path / "filelist.xml"))  # type: ignore

    @staticmethod
    def _fix_xml_by_commits(file_path: Path):
        xml_obj = XMLBuilder.load(file_path)
        if xml_obj is None:
            return

        for com_start, objs, com_end in xml_obj.find_between_comments(
            "BTM:*:start", "BTM:*end"
        ):
            match = re.search(r"setState=(.*?)", com_start.content)
            if match:
                set_state_to = (
                    True if match.group(1).lower() in ["on", "1", "true"] else False
                )
            else:
                logger.error(
                    f"Error in searching for set state value\n|Path: {file_path}"
                )
                continue

            set_state_to = not set_state_to
            for obj in objs:
                if obj.index is None:
                    continue

                if set_state_to:
                    if isinstance(obj, XMLElement):
                        continue

                else:
                    if isinstance(obj, XMLComment):
                        continue

                try:
                    if isinstance(obj, XMLComment):
                        xml_obj.replace(obj.index, obj.to_element())

                    else:
                        xml_obj.replace(obj.index, obj.to_comment())

                except Exception:
                    continue

        XMLBuilder.save(xml_obj, file_path)

    @staticmethod
    def _fix_xml_by_config(mod_path: Path):
        xml_obj = XMLBuilder.load((mod_path / "modparts.xml"))
        xml_file_list = XMLBuilder.load((mod_path / "filelist.xml"))

        if not all((xml_obj, xml_file_list)):
            return

        for action in xml_obj.iter_non_comment_childrens():  # type: ignore
            path_to_file = action.get_attribute_ignore_case("file")
            cond_type = action.get_attribute_ignore_case("type")
            set_to = action.get_attribute_ignore_case("setState")

            if not all((path_to_file, cond_type, set_to)):
                continue

            for item in xml_file_list.childrens:  # type: ignore # TODO Think about optimization
                if isinstance(item, XMLComment):
                    tag_item_start = item.content.find("<")
                    if tag_item_start == -1:
                        continue

                    tag_item = item.content[
                        tag_item_start : item.content.find(" ", tag_item_start)
                    ]

                    match = re.search(r"file=(.*?)", item.content)
                    if match:
                        item_file = match.group(1)

                    else:
                        continue

                    match = re.search(r"setState=(.*?)", item.content)
                    if match:
                        set_to = (
                            True if match.group(1).lower() in ["true", "on"] else False
                        )

                    else:
                        continue

                else:
                    tag_item = item.tag
                    item_file = item.get_attribute_ignore_case("file")
                    set_to = item.get_attribute_ignore_case("setState")
                    if not all((tag_item, item_file, set_to)):
                        continue

                    set_to = True if set_to.lower() in ["true", "on"] else False  # type: ignore

                set_to = not set_to
                if set_to:
                    if isinstance(item, XMLElement):
                        continue

                else:
                    if isinstance(item, XMLComment):
                        continue

                if tag_item == cond_type and item_file == path_to_file:
                    try:
                        if isinstance(item, XMLComment):
                            xml_file_list.replace(item.index, item.to_element())  # type: ignore

                        else:
                            xml_file_list.replace(item.index, item.to_comment())  # type: ignore

                    except Exception:
                        continue

        XMLBuilder.save(xml_file_list, (mod_path / "filelist.xml"))  # type: ignore
