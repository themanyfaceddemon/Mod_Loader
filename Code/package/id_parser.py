import logging
from typing import List, Set, Tuple, Union
from Code.xml_object import XMLComment, XMLElement, XMLObject

logger = logging.getLogger("XMLIDParser")


class IDParser:
    @staticmethod
    def get_ids(obj: XMLElement) -> Tuple[Set[str], Set[str]]:
        add_id = set()
        override_id = set()

        obj_name_lower = obj.name.lower()
        if obj_name_lower in {"infotext", "infotexts"}:
            return add_id, override_id

        parse_method = getattr(IDParser, obj_name_lower, None)
        if callable(parse_method):
            parse_method(obj, add_id, override_id)

        else:
            logger.warning(f"XML tag type not found\n| Type: {obj.name}")

        return add_id, override_id

    @staticmethod
    def items(
        elem: XMLElement,
        add_id: Set[str],
        override_id: Set[str],
        override_flag: bool = False,
    ) -> None:
        for item in elem.children:
            if isinstance(item, XMLComment):
                continue

            if item.name == "override":
                for cli in item.children:
                    if isinstance(cli, XMLComment):
                        continue

                    IDParser.item(cli, add_id, override_id, True)
                continue

            IDParser.item(item, add_id, override_id, override_flag)

    @staticmethod
    def item(
        elem: XMLElement,
        add_id: Set[str],
        override_id: Set[str],
        override_flag: bool = False,
    ) -> None:
        id_name = f'Item.{elem.attributes.get("identifier", elem.name)}'

        if override_flag:
            override_id.add(id_name)

        else:
            add_id.add(id_name)
