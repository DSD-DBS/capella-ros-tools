# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Tool for parsing ROS messages."""

from __future__ import annotations

import os
import pathlib
import re
import typing as t
from dataclasses import dataclass

from capellambse.filehandler import abc

PACKAGE_NAME_MESSAGE_TYPE_SEPARATOR = "/"
COMMENT_DELIMITER = "#"
CONSTANT_SEPARATOR = "="
UPPER_BOUND_TOKEN = "<="

VALID_MESSAGE_NAME_PATTERN = "[A-Z][A-Za-z0-9]*"
VALID_CONSTANT_NAME_PATTERN = "[A-Z](?:[A-Z0-9_]*[A-Z0-9])?"
VALID_REF_COMMENT_PATTERN = re.compile(
    r".*cf\.\s*"
    rf"({VALID_MESSAGE_NAME_PATTERN})"
    r"(?:,\s*"
    rf"({VALID_CONSTANT_NAME_PATTERN}))?"
    r"\s*.*"
)

HTML_TAG_PATTERN = re.compile("<.*?>")


def _clean_html(raw_html: str):
    return re.sub(HTML_TAG_PATTERN, "", raw_html)


def _clean_comment(comment: str) -> str:
    return comment.strip(COMMENT_DELIMITER).strip()


class Range(t.NamedTuple):
    """Define range of values."""

    min: str
    max: str


@dataclass
class TypeDef:
    """Type definition."""

    name: str
    card: Range
    range: Range | None = None
    package: str | None = None

    def __str__(self) -> str:
        """Return string representation of the type."""
        out = self.name
        if self.range:
            out += f"[{UPPER_BOUND_TOKEN}{self.range.max}]"
        elif self.card.min != self.card.max:
            out += f"[{self.card.max if self.card.max != '*' else ''}]"
        if self.package:
            out = f"{self.package}{PACKAGE_NAME_MESSAGE_TYPE_SEPARATOR}{out}"
        return out

    @classmethod
    def from_string(cls, type_str: str) -> TypeDef:
        """Create a type definition from a string."""
        if type_str.endswith("]"):
            name, _, max_card = type_str.partition("[")
            max_card = max_card.rstrip("]")
            if max_card.startswith(UPPER_BOUND_TOKEN):
                range = Range("0", max_card.strip(UPPER_BOUND_TOKEN))
                card = Range("1", "1")
            else:
                range = None
                max_card = max_card if max_card else "*"
                card = Range("0", max_card)
        else:
            name = type_str
            card = Range("1", "1")
            range = None

        if len(temp := name.split(PACKAGE_NAME_MESSAGE_TYPE_SEPARATOR)) == 2:
            package, name = temp
        else:
            package = None

        return cls(name, card, range, package)


@dataclass
class FieldDef:
    """Definition of a field in a ROS message."""

    type: TypeDef
    name: str
    description: str

    def __str__(self) -> str:
        """Return string representation of the field."""
        out = f"{self.type} {self.name}"
        if self.description:
            out += f"    # {_clean_html(self.description)}"
        return out


@dataclass
class ConstantDef:
    """Definition of a constant in a ROS message."""

    type: TypeDef
    name: str
    value: str
    description: str

    def __str__(self) -> str:
        """Return string representation of the constant."""
        out = f"{self.type} {self.name} = {self.value}"
        if self.description:
            out += f"    # {_clean_html(self.description)}"
        return out


@dataclass
class EnumDef:
    """Definition of an enum in a ROS message."""

    name: str
    literals: list[ConstantDef]
    description: str

    def __str__(self) -> str:
        """Return string representation of the enum."""
        out = f"# {_clean_html(self.description)}" if self.description else ""
        for literal in self.literals:
            out += f"\n{literal}"
        return out

    def __eq__(self, other: object) -> bool:
        """Return whether the enum is equal to another."""
        if not isinstance(other, EnumDef):
            return NotImplemented
        return (
            other.name == self.name
            and all(literal in self.literals for literal in other.literals)
            and other.description == self.description
        )


def _extract_file_level_comments(
    msg_string: str,
) -> t.Tuple[str, list[str]]:
    """Extract comments at the beginning of the message."""
    lines = msg_string.lstrip("\n").splitlines()
    lines.append("")
    file_level_comments = ""
    i = 0
    for i, line in enumerate(lines):
        line = line.strip()
        if not line.startswith(COMMENT_DELIMITER):
            if line:
                return "", lines
            else:
                break
        file_level_comments += f"<p>{_clean_comment(line)}</p>"

    file_content = lines[i:]
    return file_level_comments, file_content


@dataclass
class MessageDef:
    """Definition of a ROS message."""

    name: str
    fields: list[FieldDef]
    enums: list[EnumDef]
    description: str

    def __str__(self) -> str:
        """Return string representation of the message."""
        if self.description:
            out = f"# {_clean_html(self.description)}\n\n"
        else:
            out = ""
        for enum in self.enums:
            out += f"{enum}\n\n"
        for field in self.fields:
            out += f"{field}\n"
        return out

    def __eq__(self, other: object) -> bool:
        """Return whether the message is equal to another."""
        if not isinstance(other, MessageDef):
            return NotImplemented
        return (
            other.name == self.name
            and all(field in self.fields for field in other.fields)
            and all(enum in self.enums for enum in other.enums)
            and other.description == self.description
        )

    @classmethod
    def from_file(
        cls, file: abc.AbstractFilePath | pathlib.Path
    ) -> MessageDef:
        """Create message definition from a .msg file."""
        msg_name = file.stem
        msg_string = file.read_text()
        return cls.from_string(msg_name, msg_string)

    @classmethod
    def from_string(cls, msg_name: str, msg_string: str) -> MessageDef:
        """Create message definition from a string."""
        msg_comments, lines = _extract_file_level_comments(msg_string)
        msg = cls(msg_name, [], [], msg_comments)
        last_element: t.Any = None
        block_comments = ""
        index = -1
        last_value = float("inf")

        for line in lines:
            line = line.rstrip()
            if not line:
                # new block
                if index != 0:
                    block_comments = ""
                continue

            last_index = index
            index = line.find(COMMENT_DELIMITER)
            if index == -1:
                # no comment
                comment = ""
            elif index == 0:
                # block comment
                if last_index > 0:
                    # block comments were used
                    block_comments = ""
                block_comments += f"<p>{_clean_comment(line)}</p>"
                continue
            else:
                # inline comment
                comment = f"<p>{_clean_comment(line[index:])}</p>"
                line = line[:index].rstrip()
                if not line:
                    # indented comment
                    last_element.description += comment
                    continue

            type_string, _, rest = line.partition(" ")
            name, _, value = rest.partition(CONSTANT_SEPARATOR)
            name = name.strip()
            value = value.strip()
            if value:
                # constant
                if int(value) <= last_value:
                    # new enum
                    enum_def = EnumDef("", [], block_comments)
                    block_comments = ""
                    msg.enums.append(enum_def)
                last_value = int(value)
                constant_def = ConstantDef(
                    TypeDef.from_string(type_string),
                    name,
                    value,
                    block_comments + comment,
                )
                msg.enums[-1].literals.append(constant_def)
                last_element = constant_def
            else:
                # field
                field_def = FieldDef(
                    TypeDef.from_string(type_string),
                    name,
                    block_comments + comment,
                )
                msg.fields.append(field_def)
                last_element = field_def

        for field in msg.fields:
            _process_comment(field)

        for enum in msg.enums:
            common_prefix = os.path.commonprefix(
                [literal.name for literal in enum.literals]
            )
            if common_prefix:
                enum.name = _get_enum_identifier(common_prefix)
                for literal in enum.literals:
                    literal.name = literal.name.removeprefix(common_prefix)
            else:
                enum.name = msg_name if not msg.fields else msg_name + "Type"

            for field in msg.fields:
                if field.name.lower() == enum.name.lower():
                    # name match found
                    field.type.name = enum.name
                    field.type.package = "types"
                    break
            else:
                # no name match found
                for field in msg.fields:
                    if field.type.name == enum.literals[0].type.name:
                        # type match found
                        enum.name = msg_name + field.name.capitalize()
                        field.type.name = enum.name
                        field.type.package = "types"
                        break

        return msg


def _process_comment(field: FieldDef) -> None:
    """Process comment of a field."""
    if match := VALID_REF_COMMENT_PATTERN.match(field.description):
        field.type.package = "types"
        ref_msg_name, ref_const_name = match.groups()
        if ref_const_name:
            field.type.name = _get_enum_identifier(
                ref_const_name.rstrip("_XXX")
            )
        else:
            field.type.name = ref_msg_name


def _get_enum_identifier(common_prefix: str) -> str:
    """Get the identifier of an enum."""
    return "".join([x.capitalize() for x in common_prefix.split("_")])


@dataclass
class MessagePkgDef:
    """Definition of a ROS message package."""

    name: str
    messages: list[MessageDef]
    packages: list[MessagePkgDef]

    def __eq__(self, other: object) -> bool:
        """Return whether the message package is equal to another."""
        if not isinstance(other, MessagePkgDef):
            return NotImplemented
        return (
            other.name == self.name
            and all(message in self.messages for message in other.messages)
            and all(package in self.packages for package in other.packages)
        )

    @classmethod
    def from_msg_folder(
        cls, pkg_name: str, msg_path: abc.AbstractFilePath | pathlib.Path
    ) -> MessagePkgDef:
        """Create a message package definition from a folder."""
        out = cls(pkg_name, [], [])
        for msg_file in msg_path.rglob("*.msg"):
            msg_def = MessageDef.from_file(msg_file)
            out.messages.append(msg_def)
        return out