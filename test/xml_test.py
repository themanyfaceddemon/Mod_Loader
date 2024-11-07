import re
from pathlib import Path
from typing import Dict, List, Optional, Union


class XMLParserException(Exception):
    def __init__(
        self, message: str, tag: Optional[str] = None, position: int = 0, line: int = 0
    ):
        super().__init__(message)
        self.tag = tag
        self.position = position
        self.line = line

    def __str__(self):
        return f"{self.args[0]} (Tag: {self.tag}, Position: {self.position}, Line: {self.line})"


class XMLComment:
    def __init__(self, text: str):
        self.text = text

    def dump(
        self, indent=0, indent_char=" ", single_line=False, inline_content=None
    ) -> str:
        indent_str = "" if single_line else indent_char * indent
        return f"{indent_str}<!-- {self.text} -->"

    def to_element(self) -> "XMLElement":
        match = re.match(r"<(\w+)(.*?)>(.*?)</\1>", self.text, re.DOTALL)
        if not match:
            raise XMLParserException("Invalid format to convert comment to element.")

        tag_name = match.group(1)
        attributes = {}

        attr_text = match.group(2).strip()
        for attr in re.finditer(r'(\w+)="(.*?)"', attr_text):
            attributes[attr.group(1)] = attr.group(2)

        element = XMLElement(tag_name, attributes)
        element.content = match.group(3).strip()
        return element

    def __repr__(self):
        return f"XMLComment(text='{self.text}')"


class XMLElement:
    def __init__(self, name: str, attributes: Optional[Dict[str, str]] = None):
        self.name = name
        self.attributes = attributes or {}
        self.children: List[Union["XMLElement", XMLComment]] = []
        self.content = ""

    def add_child(self, child: Union["XMLElement", XMLComment]):
        self.children.append(child)

    def dump(
        self, indent=0, indent_char=" ", single_line=False, inline_content=False
    ) -> str:
        indent_str = "" if single_line else indent_char * indent
        attrs = " ".join(f'{key}="{value}"' for key, value in self.attributes.items())
        opening_tag = f"<{self.name}{(' ' + attrs) if attrs else ''}>"

        if not self.children and not self.content:
            return f"{indent_str}<{self.name}{(' ' + attrs) if attrs else ''} />"

        if not self.children and inline_content and self.content:
            return f"{indent_str}{opening_tag}{self.content}</{self.name}>"

        result = f"{indent_str}{opening_tag}"
        if not single_line:
            result += "\n"

        if self.content:
            result += (
                "" if single_line else indent_str + indent_char * 4
            ) + self.content
            if not single_line:
                result += "\n"

        for child in self.children:
            result += child.dump((indent + 4), indent_char, single_line, inline_content)
            if not single_line:
                result += "\n"

        closing_tag = f"</{self.name}>"
        result += ("" if single_line else indent_str) + closing_tag

        return result

    def to_comment(self) -> XMLComment:
        element_str = self.dump(single_line=True, inline_content=True)
        comment_text = element_str.strip("<>").replace(">", "")
        return XMLComment(comment_text)

    def find(self, pattern: str) -> List[Union["XMLElement", XMLComment]]:
        compiled_pattern = re.compile(pattern)
        result = []

        if compiled_pattern.search(self.name) or any(
            compiled_pattern.search(value) for value in self.attributes.values()
        ):
            result.append(self)

        for child in self.children:
            if isinstance(child, XMLElement):
                if compiled_pattern.search(child.name) or any(
                    compiled_pattern.search(value)
                    for value in child.attributes.values()
                ):
                    result.append(child)
                result.extend(child.find(pattern))

            elif isinstance(child, XMLComment):
                if compiled_pattern.search(child.text):
                    result.append(child)

        return result

    def __repr__(self):
        return f"XMLElement(name={self.name}, attributes={self.attributes}, children={self.children}, content='{self.content}')"


class XMLObject:
    def __init__(self) -> None:
        self._stack: list[XMLElement] = []
        self.root: Optional[XMLElement] = None

    def find(self, pattern: str) -> List[Union[XMLElement, XMLComment]]:
        if self.root:
            return self.root.find(pattern)

        return []

    def replace_element_with_comment(self, element_name: str) -> None:
        if self.root:
            self._replace_element_with_comment(self.root, element_name)

    def _replace_element_with_comment(
        self, parent: XMLElement, element_name: str
    ) -> None:
        for i, child in enumerate(parent.children):
            if isinstance(child, XMLElement) and child.name == element_name:
                parent.children[i] = child.to_comment()

            elif isinstance(child, XMLElement):
                self._replace_element_with_comment(child, element_name)

    def replace_comment_with_element(self, comment_text: str) -> None:
        if self.root:
            self._replace_comment_with_element(self.root, comment_text)

    def _replace_comment_with_element(
        self, parent: XMLElement, comment_text: str
    ) -> None:
        for i, child in enumerate(parent.children):
            if isinstance(child, XMLComment) and comment_text in child.text:
                parent.children[i] = child.to_element()

            elif isinstance(child, XMLElement):
                self._replace_comment_with_element(child, comment_text)

    def dump(self, indent_char=" ", single_line=False, inline_content=True) -> str:
        if self.root:
            return self.root.dump(0, indent_char, single_line, inline_content)

        return ""

    @staticmethod
    def load_file(path: (Path | str), encoding="utf-8") -> "XMLObject":
        path = Path(path)

        content = ""
        with open(path, "r", encoding=encoding) as file:
            content = file.read()

        return XMLObject.load_str(content)

    @staticmethod
    def load_str(content: str) -> "XMLObject":
        new_obj = XMLObject()

        if content.startswith("<?xml"):
            end_declaration = content.find("?>") + 2
            content = content[end_declaration:].strip()

        line = 1
        i = 0

        while i < len(content):
            if content[i : i + 4] == "<!--":
                end_comment = content.find("-->", i + 4)
                if end_comment == -1:
                    raise XMLParserException("Unclosed comment", position=i, line=line)

                comment_text = content[i + 4 : end_comment].strip()
                comment = XMLComment(comment_text)
                if new_obj._stack:
                    new_obj._stack[-1].add_child(comment)
                i = end_comment + 3

            elif content[i] == "<":
                if content[i + 1] == "/":
                    tag_start = i + 2
                    tag_end = content.find(">", tag_start)
                    tag_name = content[tag_start:tag_end]
                    if not new_obj._stack or new_obj._stack[-1].name != tag_name:
                        raise XMLParserException(
                            "Unexpected closing tag",
                            tag=tag_name,
                            position=i,
                            line=line,
                        )

                    closed_element = new_obj._stack.pop()
                    if new_obj._stack:
                        new_obj._stack[-1].add_child(closed_element)

                    else:
                        new_obj.root = closed_element
                    i = tag_end + 1

                else:
                    tag_end = content.find(">", i + 1)
                    if tag_end == -1:
                        raise XMLParserException("Malformed tag", position=i, line=line)

                    is_self_closing = content[tag_end - 1] == "/"
                    tag_content = content[i + 1 : tag_end].strip()
                    if is_self_closing:
                        tag_content = tag_content[:-1].strip()

                    tag_parts = re.split(r"\s+(?=[\w-]+=)", tag_content)
                    tag_name = tag_parts[0]
                    attributes = {}

                    for attr in tag_parts[1:]:
                        match = re.match(r'([\w-]+)="(.*?)"', attr)
                        if match:
                            key, value = match.groups()
                            attributes[key] = value

                    element = XMLElement(tag_name, attributes)

                    if not is_self_closing:
                        new_obj._stack.append(element)
                    else:
                        if new_obj._stack:
                            new_obj._stack[-1].add_child(element)
                        else:
                            new_obj.root = element
                    i = tag_end + 1

            else:
                text_start = i
                i = content.find("<", text_start)
                if i == -1:
                    i = len(content)

                if new_obj._stack:
                    new_obj._stack[-1].content = content[text_start:i].strip()

        if new_obj._stack:
            raise XMLParserException(
                "Some tags were not closed",
                tag=new_obj._stack[-1].name,
                position=i,
                line=line,
            )

        return new_obj


try:
    test = XMLObject.load_file(Path("Data/InternalLibrary/3247838390.xml"))
    print(test.dump())
    print("---")
    test.replace_element_with_comment("dependencies")
    print(test.dump())

except XMLParserException as e:
    print(f"XML Error: {e}")
