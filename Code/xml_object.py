import re
from pathlib import Path
from typing import Dict, Generator, List, Optional, Union


class XMLParserException(Exception):
    def __init__(
        self,
        message: str,
        tag: Optional[str] = None,
        position: Optional[int] = None,
        line: Optional[int] = None,
        content: Optional[str] = None,
    ):
        super().__init__(message)
        self.tag = tag
        self.position = position
        self.line = line
        self.content = content

    def __str__(self):
        return (
            f"{self.args[0]} "
            f"(Tag: {self.tag}, Position: {self.position}, Line: {self.line})\n"
            f"{self.content}"
        )


class XMLComment:
    def __init__(self, text: str):
        self.text = text

    def dump(
        self, indent: int = 0, indent_char: str = " ", single_line: bool = False, *args
    ) -> str:
        indent_str = "" if single_line else indent_char * indent
        return f"{indent_str}<!-- {self.text} -->"

    def to_element(self) -> "XMLElement":
        xml_obj = XMLElement.build_element(self.text)
        if xml_obj is None:
            raise XMLParserException(
                "Unable to convert comment to element: Empty content.",
                content=self.text,
            )

        return xml_obj

    def __repr__(self):
        return f"XMLComment(text={repr(self.text)})"


class XMLElement:
    def __init__(self, name: str, attributes: Optional[Dict[str, str]] = None):
        self.name = name
        self.attributes: Dict[str, str] = attributes if attributes is not None else {}
        self.childrens: List[Union["XMLElement", XMLComment]] = []
        self.content: str = ""
        self.parent: Optional[XMLElement] = None

    def add_child(self, child: Union["XMLElement", XMLComment]):
        self.childrens.append(child)
        if isinstance(child, XMLElement):
            child.parent = self

    def get_attribute_ignore_case(self, key: str, default=None):
        key_lower = key.lower()
        for attr_key, attr_value in self.attributes.items():
            if attr_key.lower() == key_lower:
                return attr_value

        return default

    def iter_comment_childrens(self) -> Generator[XMLComment, None, None]:
        for elem in self.childrens:
            if isinstance(elem, XMLElement):
                continue

            yield elem

    def iter_non_comment_childrens(self) -> Generator["XMLElement", None, None]:
        for elem in self.childrens:
            if isinstance(elem, XMLComment):
                continue

            yield elem

    def dump(
        self,
        indent: int = 0,
        indent_char: str = " ",
        single_line: bool = False,
        inline_content: bool = False,
    ) -> str:
        indent_str = "" if single_line else indent_char * indent
        attrs = " ".join(f'{key}="{value}"' for key, value in self.attributes.items())
        opening_tag = f"<{self.name}{(' ' + attrs) if attrs else ''}>"

        if not self.childrens and not self.content:
            return f"{indent_str}<{self.name}{(' ' + attrs) if attrs else ''} />"

        if not self.childrens and inline_content and self.content:
            return f"{indent_str}{opening_tag}{self.content}</{self.name}>"

        result = f"{indent_str}{opening_tag}"
        if not single_line:
            result += "\n"

        if self.content:
            content_str = f"{self.content}"
            if not single_line:
                content_str = indent_char * (indent + 4) + content_str + "\n"

            result += content_str

        for child in self.childrens:
            child_str = child.dump(indent + 4, indent_char, single_line, inline_content)
            if not single_line:
                child_str += "\n"

            result += child_str

        closing_tag = f"</{self.name}>"
        if not single_line:
            result += indent_char * indent

        result += closing_tag

        return result

    def to_comment(self) -> XMLComment:
        element_str = self.dump(single_line=True, inline_content=True)
        return XMLComment(element_str)

    @staticmethod
    def build_element(content: str) -> Optional["XMLElement"]:
        stack: List[XMLElement] = []
        root = None

        content = content.strip()
        i = 0
        line = 1

        while i < len(content):
            if content[i] == "\n":
                line += 1
                i += 1
                continue

            if content.startswith("<?", i):
                pi_end = content.find("?>", i + 2)
                if pi_end == -1:
                    raise XMLParserException(
                        "Invalid processing instruction",
                        line=line,
                        position=i,
                        content=content,
                    )

                i = pi_end + 2

            elif content.startswith("<!--", i):
                end_comment = content.find("-->", i + 4)
                if end_comment == -1:
                    raise XMLParserException(
                        "Unclosed comment", position=i, line=line, content=content
                    )

                comment_text = content[i + 4 : end_comment].strip()
                comment = XMLComment(comment_text)
                if stack:
                    stack[-1].add_child(comment)

                i = end_comment + 3

            elif content[i] == "<":
                if content.startswith("</", i):
                    tag_start = i + 2
                    tag_end = content.find(">", tag_start)
                    if tag_end == -1:
                        raise XMLParserException(
                            "Malformed closing tag",
                            position=i,
                            line=line,
                            content=content,
                        )

                    tag_name = content[tag_start:tag_end].strip()
                    if not stack or stack[-1].name != tag_name:
                        raise XMLParserException(
                            "Unexpected closing tag",
                            tag=tag_name,
                            position=i,
                            line=line,
                            content=content,
                        )

                    closed_element = stack.pop()
                    if not stack:
                        root = closed_element

                    else:
                        stack[-1].add_child(closed_element)

                    i = tag_end + 1

                else:
                    tag_start = i + 1
                    tag_end = content.find(">", tag_start)
                    if tag_end == -1:
                        raise XMLParserException(
                            "Malformed tag", position=i, line=line, content=content
                        )

                    is_self_closing = content[tag_end - 1] == "/"
                    tag_content = content[tag_start:tag_end].strip()
                    if is_self_closing:
                        tag_content = tag_content[:-1].strip()

                    parts = re.split(r"\s+", tag_content, maxsplit=1)
                    tag_name = parts[0]
                    attributes = {}
                    if len(parts) > 1:
                        attr_str = parts[1]
                        attr_regex = re.compile(r'(\w[\w-]*)\s*=\s*(".*?"|\'.*?\'|\S+)')
                        for match in attr_regex.finditer(attr_str):
                            key, value = match.groups()
                            if value[0] in "\"'":
                                value = value[1:-1]

                            attributes[key] = value

                    element = XMLElement(tag_name, attributes)
                    if is_self_closing:
                        if stack:
                            stack[-1].add_child(element)

                        else:
                            root = element

                    else:
                        stack.append(element)

                    i = tag_end + 1

            else:
                text_start = i
                next_tag_pos = content.find("<", i)
                if next_tag_pos == -1:
                    next_tag_pos = len(content)

                text_content = content[text_start:next_tag_pos]
                if stack and text_content.strip():
                    stack[-1].content += text_content.strip()

                i = next_tag_pos

        if stack:
            raise XMLParserException(
                "Unclosed tags remain",
                tag=stack[-1].name,
                position=i,
                line=line,
                content=content,
            )

        return root

    @staticmethod
    def _match_name_and_attributes(
        element: "XMLElement", pattern: str, exact_match: bool
    ) -> bool:
        if exact_match:
            element_name_lower = element.name.lower()
            pattern_lower = pattern.lower()
            return element_name_lower == pattern_lower or pattern_lower in (
                value.lower() for value in element.attributes.values()
            )

        compiled_pattern = re.compile(pattern, re.IGNORECASE)
        return compiled_pattern.search(element.name) is not None or any(
            compiled_pattern.search(value) for value in element.attributes.values()
        )

    @staticmethod
    def _match_comment(text: str, pattern: str, exact_match: bool) -> bool:
        if exact_match:
            return text == pattern

        return re.search(pattern, text) is not None

    def find(
        self, pattern: str, exact_match: bool = False
    ) -> Generator[Union["XMLElement", "XMLComment"], None, None]:
        def match_element(element: "XMLElement"):
            if XMLElement._match_name_and_attributes(element, pattern, exact_match):
                yield element

            for child in element.childrens:
                if isinstance(child, XMLElement):
                    yield from match_element(child)

                elif isinstance(child, XMLComment) and XMLElement._match_comment(
                    child.text, pattern, exact_match
                ):
                    yield child

        yield from match_element(self)

    def find_only_comments(
        self, pattern: str, exact_match: bool = False
    ) -> Generator["XMLComment", None, None]:
        def match_element(element: "XMLElement"):
            for child in element.childrens:
                if isinstance(child, XMLElement):
                    yield from match_element(child)

                elif isinstance(child, XMLComment) and XMLElement._match_comment(
                    child.text, pattern, exact_match
                ):
                    yield child

        yield from match_element(self)

    def find_only_elements(
        self, pattern: str, exact_match: bool = False
    ) -> Generator["XMLElement", None, None]:
        def match_element(element: "XMLElement"):
            if XMLElement._match_name_and_attributes(element, pattern, exact_match):
                yield element

            for child in element.childrens:
                if isinstance(child, XMLElement):
                    yield from match_element(child)

        yield from match_element(self)

    def find_element_after_comment(
        self, pattern: str, exact_match: bool = False
    ) -> Generator["XMLElement", None, None]:
        def match_element(element: "XMLElement"):
            previous_was_comment = False
            for child in element.childrens:
                if isinstance(child, XMLComment) and XMLElement._match_comment(
                    child.text, pattern, exact_match
                ):
                    previous_was_comment = True

                elif isinstance(child, XMLElement):
                    if previous_was_comment:
                        yield child
                        previous_was_comment = False

                    yield from match_element(child)

                else:
                    previous_was_comment = False

        yield from match_element(self)

    def __repr__(self):
        return (
            f"XMLElement(name={repr(self.name)}, attributes={self.attributes}, "
            f"children={self.childrens}, content={repr(self.content)})"
        )


class XMLBuilder:
    @staticmethod
    def build_form_file(
        path: Union[Path, str], encoding: str = "utf-8-sig"
    ) -> Union[XMLElement, None]:
        path = Path(path)
        with open(path, "r", encoding=encoding) as file:
            content = file.read()

        return XMLElement.build_element(content)
