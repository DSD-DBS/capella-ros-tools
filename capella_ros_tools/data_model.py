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


def _clean_html(raw_html: str) -> str:
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
    package: str | None = None

    def __str__(self) -> str:
        """Return string representation of the type."""
        out = self.name
        if self.card.min == self.card.max:
            out += f"[{self.card.max}]" if self.card.max != "1" else ""
        else:
            out += (
                f"[{UPPER_BOUND_TOKEN}{self.card.max}]"
                if self.card.max != "*"
                else "[]"
            )
        if self.package:
            out = f"{self.package}{PACKAGE_NAME_MESSAGE_TYPE_SEPARATOR}{out}"
        return out

    @classmethod
    def from_string(cls, type_str: str) -> TypeDef:
        """Create a type definition from a string."""
        name = type_str
        card = Range("1", "1")
        if type_str.endswith("]"):
            name, _, max_card = type_str.partition("[")
            max_card = max_card.removesuffix("]")
            if max_card.startswith(UPPER_BOUND_TOKEN):
                max_card = max_card.removeprefix(UPPER_BOUND_TOKEN)
                card = Range("0", max_card)
            else:
                card = (
                    Range(max_card, max_card) if max_card else Range("0", "*")
                )

        match name.split(PACKAGE_NAME_MESSAGE_TYPE_SEPARATOR):
            case [p, n]:
                package: str | None = p
                name = n
            case _:
                package = None

        return cls(name, card, package)


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


def _process_block_comment(line: str) -> str:
    if comment := _clean_comment(line):
        return f"{comment} "
    return ""


def _extract_file_level_comments(
    msg_string: str, regex: re.Pattern | None = None
) -> tuple[str, list[str]]:
    """Extract comments at the beginning of the message."""
    lines = msg_string.lstrip("\n").splitlines()
    lines.append("")
    file_level_comments = ""
    i = 0
    for i, line in enumerate(lines):  # noqa: B007
        line = line.strip()
        if not line.startswith(COMMENT_DELIMITER):
            if line:
                return "", lines
            break
        file_level_comments += _process_block_comment(line) or "\n"

    if regex is not None:
        if matches := regex.search(file_level_comments):
            file_level_comments = "\n".join(matches.groups())
        else:
            file_level_comments = ""
    file_level_comments = file_level_comments.replace("\n", "<br>")
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
        cls,
        pkg_name: str,
        file: abc.AbstractFilePath | pathlib.Path,
        *,
        license_header: str,
        msg_description_regex: re.Pattern[str] | None = None,
    ) -> MessageDef:
        """Create message definition from a .msg file."""
        msg_name = file.stem
        msg_string = file.read_text().removeprefix(license_header)
        return cls.from_string(
            pkg_name, msg_name, msg_string, msg_description_regex
        )

    @classmethod
    def from_string(  # noqa: C901 # FIXME too complex
        cls,
        pkg_name: str,
        msg_name: str,
        msg_string: str,
        msg_description_regex: re.Pattern[str] | None = None,
    ) -> MessageDef:
        """Create message definition from a string."""
        msg_comments, lines = _extract_file_level_comments(
            msg_string, msg_description_regex
        )
        msg = cls(msg_name, [], [], msg_comments)
        last_element: t.Any = None
        block_comments = ""
        index = -1
        values: list[str] = []

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
                block_comments += _process_block_comment(line) or "<br>"
                continue
            else:
                # inline comment
                comment = _clean_comment(line[index:])
                line = line[:index].rstrip()
                if not line:
                    # indented comment
                    last_element.description += (
                        f"{comment} " if comment else "<br>"
                    )
                    continue
                comment = f"{comment} "

            type_string, _, rest = line.partition(" ")
            name, _, value = rest.partition(CONSTANT_SEPARATOR)
            name = name.strip()
            value = value.strip()
            if value:
                # constant
                if (
                    value in values
                    or not msg.enums
                    or not isinstance(last_element, ConstantDef)
                ):
                    # new enum
                    enum_def = EnumDef("", [], block_comments)
                    block_comments = ""
                    msg.enums.append(enum_def)
                    values = []
                constant_def = ConstantDef(
                    TypeDef.from_string(type_string),
                    name,
                    value,
                    block_comments + comment,
                )
                msg.enums[-1].literals.append(constant_def)
                values.append(value)
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

        if not msg.fields and len(msg.enums) == 1:
            enum = msg.enums[0]
            _process_enums(enum)
            enum.name = msg_name
            return msg

        for field in msg.fields:
            _process_comment(field)

        for enum in msg.enums:
            common_prefix = _process_enums(enum)

            if common_prefix:
                enum.name = _get_enum_identifier(common_prefix)
            else:
                enum.name = msg_name if not msg.fields else msg_name + "Type"

            matched_field = None
            for field in msg.fields:
                if field.type.name == enum.literals[0].type.name:
                    matched_field = matched_field or field
                    if field.name.lower() == enum.name.lower():
                        enum.name = msg_name + matched_field.name.capitalize()
                        field.type.name = enum.name
                        field.type.package = f"{pkg_name}.{msg_name}"
                        break
            else:
                if matched_field:
                    enum.name = msg_name + matched_field.name.capitalize()
                    matched_field.type.name = enum.name
                    matched_field.type.package = f"{pkg_name}.{msg_name}"

        return msg


def _process_enums(enum: EnumDef) -> str:
    common_prefix = os.path.commonprefix(
        [literal.name for literal in enum.literals]
    )
    if not common_prefix.endswith("_"):
        if index := common_prefix.rfind("_"):
            common_prefix = common_prefix[: index + 1]
        else:
            common_prefix = ""

    for literal in enum.literals:
        literal.name = literal.name.removeprefix(common_prefix)

    return common_prefix


def _process_comment(field: FieldDef) -> None:
    """Process comment of a field."""
    if match := VALID_REF_COMMENT_PATTERN.match(field.description):
        ref_msg_name, ref_const_name = match.groups()
        field.type.package = ref_msg_name
        if ref_const_name:
            field.type.name = _get_enum_identifier(
                ref_const_name.removesuffix("_XXX")
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
        cls,
        pkg_name: str,
        msg_path: abc.AbstractFilePath | pathlib.Path,
        license_header: str,
        msg_description_regex: re.Pattern[str] | None = None,
    ) -> MessagePkgDef:
        """Create a message package definition from a folder."""
        out = cls(pkg_name, [], [])
        files = t.cast(
            t.Iterable[abc.AbstractFilePath | pathlib.Path],
            msg_path.rglob("*.msg"),
        )
        for msg_file in sorted(files, key=os.fspath):
            msg_def = MessageDef.from_file(
                pkg_name,
                msg_file,
                license_header=license_header,
                msg_description_regex=msg_description_regex,
            )
            out.messages.append(msg_def)
        return out
