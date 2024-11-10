from typing import List, Tuple, Union
from Code.xml_object import XMLComment, XMLElement, XMLObject


class IDParser:
    @staticmethod
    def get_ids(obj: XMLElement):
        if obj.name.lower() in ["infotext", "infotexts"]:
            return
