# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0

import pathlib

import pytest
from capellambse.filehandler import abc

from capella_ros_tools import data_model
from capella_ros_tools.data_model import (
    CONSTANT_SEPARATOR,
    UPPER_BOUND_TOKEN,
    ConstantDef,
    EnumDef,
    FieldDef,
    MessageDef,
    MessagePkgDef,
    Range,
    TypeDef,
)

PATH = pathlib.Path(__file__).parent

SAMPLE_CLASS_PATH = PATH.joinpath(
    "data/data_model/example_msgs/package1/msg/SampleClass.msg"
)
SAMPLE_ENUM_PATH = PATH.joinpath(
    "data/data_model/example_msgs/package1/msg/types/SampleEnum.msg"
)
SAMPLE_CLASS_ENUM_PATH = PATH.joinpath(
    "data/data_model/example_msgs/package2/msg/SampleClassEnum.msg"
)

SAMPLE_PACKAGE_PATH1 = PATH.joinpath("data/data_model/example_msgs/package1")
SAMPLE_PACKAGE_PATH2 = PATH.joinpath("data/data_model/example_msgs/package2")


# REUSE-IgnoreStart
SAMPLE_LICENSE_HEADER = """\
# SPDX-FileCopyrightText: Copyright DB InfraGO AG
# SPDX-License-Identifier: Apache-2.0
"""
# REUSE-IgnoreEnd


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        (
            ("test_name", Range("1", "1"), "test_package"),
            "test_package/test_name",
        ),
        (
            ("test_name", Range("10", "10"), "test_package"),
            "test_package/test_name[10]",
        ),
        (
            ("test_name", Range("0", "10"), "test_package"),
            f"test_package/test_name[{UPPER_BOUND_TOKEN}10]",
        ),
        (
            ("test_name", Range("1", "1"), None),
            "test_name",
        ),
        (
            ("test_name", Range("0", "*"), None),
            "test_name[]",
        ),
    ],
)
def test_TypeDef_str(
    params: tuple[str, Range, str | None], expected: str
) -> None:
    type_def = TypeDef(*params)

    actual = str(type_def)

    assert actual == expected


@pytest.mark.parametrize(
    ("type_str", "params"),
    [
        (
            "test_package/test_name",
            ("test_name", Range("1", "1"), "test_package"),
        ),
        (
            "test_package/test_name[10]",
            ("test_name", Range("10", "10"), "test_package"),
        ),
        (
            f"test_package/test_name[{UPPER_BOUND_TOKEN}10]",
            ("test_name", Range("0", "10"), "test_package"),
        ),
        (
            "test_name[]",
            ("test_name", Range("0", "*"), None),
        ),
    ],
)
def test_TypeDef_from_string(
    type_str: str, params: tuple[str, Range, str | None]
) -> None:
    expected = TypeDef(*params)

    actual = TypeDef.from_string(type_str)

    assert actual == expected


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        (
            (
                TypeDef.from_string("test_type"),
                "test_name",
                "test_description",
            ),
            "test_type test_name    # test_description",
        ),
        (
            (TypeDef.from_string("test_type"), "test_name", ""),
            "test_type test_name",
        ),
    ],
)
def test_FieldDef_str(params: tuple[TypeDef, str, str], expected: str) -> None:
    field_def = FieldDef(*params)

    actual = str(field_def)

    assert actual == expected


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        (
            (
                TypeDef.from_string("test_type"),
                "test_name",
                "1",
                "test",
            ),
            f"test_type test_name {CONSTANT_SEPARATOR} 1    # test",
        ),
        (
            (TypeDef.from_string("test_type"), "test_name", "10", ""),
            f"test_type test_name {CONSTANT_SEPARATOR} 10",
        ),
    ],
)
def test_ConstantDef_str(
    params: tuple[TypeDef, str, str, str], expected: str
) -> None:
    constant_def = ConstantDef(*params)

    actual = str(constant_def)

    assert actual == expected


class TestComments:
    @staticmethod
    def test_extract_file_level_comments_no_comments() -> None:
        msg_string = """uint8 OK = 0
uint8 WARN = 1
uint8 ERROR = 2"""
        comments, _ = data_model._extract_file_level_comments(msg_string)

        assert comments == ""

    @staticmethod
    def test_extract_file_level_comments_no_newline() -> None:
        msg_string = """# This is a comment
# This is another comment
uint8 OK = 0
uint8 WARN = 1
uint8 ERROR = 2"""
        comments, _ = data_model._extract_file_level_comments(msg_string)

        assert comments == ""

    @staticmethod
    def test_extract_file_level_comments() -> None:
        msg_string = """# This is a comment
# This is another comment

uint8 OK = 0
uint8 WARN = 1
uint8 ERROR = 2"""
        comments, _ = data_model._extract_file_level_comments(msg_string)
        expected = "This is a comment This is another comment "

        assert comments == expected

    @staticmethod
    def test_extract_file_level_comments_with_newline() -> None:
        msg_string = """# This is a comment
#
# This is another comment"""
        comments, _ = data_model._extract_file_level_comments(msg_string)
        expected = "This is a comment <br>This is another comment "

        assert comments == expected

    @staticmethod
    def test_extract_file_level_comments_strip_empty_lines_at_top() -> None:
        msg_string = """

# This is a comment

uint8 OK = 0
uint8 WARN = 1
uint8 ERROR = 2"""
        comments, _ = data_model._extract_file_level_comments(msg_string)
        expected = "This is a comment "

        assert comments == expected

    @staticmethod
    def test_parse_comments_no_comments() -> None:
        msg_string = """uint8 field"""
        msg_def = MessageDef.from_string("test_pkg", "test_name", msg_string)
        expected = MessageDef(
            name="test_name",
            fields=[
                FieldDef(
                    type=TypeDef.from_string("uint8"),
                    name="field",
                    description="",
                )
            ],
            enums=[],
            description="",
        )

        assert msg_def == expected

    @staticmethod
    def test_parse_comments_block_comments() -> None:
        msg_string = """# Here is text.
# Here is more text.
#
# This is unrelated text.
uint8 field"""
        msg_def = MessageDef.from_string("test_pkg", "test_name", msg_string)
        expected = MessageDef(
            name="test_name",
            fields=[
                FieldDef(
                    type=TypeDef.from_string("uint8"),
                    name="field",
                    description="Here is text. Here is more text. <br>"
                    "This is unrelated text. ",
                )
            ],
            enums=[],
            description="",
        )

        assert msg_def == expected

    @staticmethod
    def test_parse_comments_inline_comments() -> None:
        msg_string = """uint8 field     # Here is text.
                                        # Here is more text.
                                        #
                                        # This is unrelated text."""
        msg_def = MessageDef.from_string("test_pkg", "test_name", msg_string)
        expected = MessageDef(
            name="test_name",
            fields=[
                FieldDef(
                    type=TypeDef.from_string("uint8"),
                    name="field",
                    description="Here is text. Here is more text. <br>"
                    "This is unrelated text. ",
                )
            ],
            enums=[],
            description="",
        )

        assert msg_def == expected

    @staticmethod
    def test_parse_comments_mixed_comments() -> None:
        msg_string = """# This is a block comment.
# This is still a block comment.
uint8 field     # This is an inline comment.
                # This is still an inline comment."""
        msg_def = MessageDef.from_string("test_pkg", "test_name", msg_string)
        expected = MessageDef(
            name="test_name",
            fields=[
                FieldDef(
                    type=TypeDef.from_string("uint8"),
                    name="field",
                    description="This is a block comment. "
                    "This is still a block comment. "
                    "This is an inline comment. "
                    "This is still an inline comment. ",
                )
            ],
            enums=[],
            description="",
        )

        assert msg_def == expected


class TestMergeEnumDef:
    @staticmethod
    @pytest.fixture
    def expected() -> MessageDef:
        type_def = TypeDef("uint8", Range("1", "1"))
        enum_def = EnumDef(
            name="enum_name",
            literals=[
                ConstantDef(
                    type=type_def,
                    name="OK",
                    value="0",
                    description="",
                ),
                ConstantDef(
                    type=type_def,
                    name="WARN",
                    value="1",
                    description="",
                ),
                ConstantDef(
                    type=type_def,
                    name="ERROR",
                    value="2",
                    description="",
                ),
                ConstantDef(
                    type=type_def,
                    name="STALE",
                    value="3",
                    description="",
                ),
            ],
            description="",
        )
        return MessageDef("enum_name", [], [enum_def], "")

    @staticmethod
    def test_merge_enums_before(expected: MessageDef) -> None:
        msg_string = """
uint8 OK = 0

uint8 WARN = 1
uint8 ERROR = 2
uint8 STALE = 3"""
        msg_def = MessageDef.from_string("test_pkg", "enum_name", msg_string)

        assert msg_def == expected

    @staticmethod
    def test_merge_enums_after(expected: MessageDef) -> None:
        msg_string = """
uint8 OK = 0
uint8 WARN = 1
uint8 ERROR = 2

uint8 STALE = 3"""
        msg_def = MessageDef.from_string("test_pkg", "enum_name", msg_string)

        assert msg_def == expected

    @staticmethod
    def test_merge_enums_multiple_after(expected: MessageDef) -> None:
        msg_string = """
uint8 OK = 0
uint8 WARN = 1

uint8 ERROR = 2

uint8 STALE = 3"""
        msg_def = MessageDef.from_string("test_pkg", "enum_name", msg_string)

        assert msg_def == expected

    @staticmethod
    def test_merge_enums_multiple_before(expected: MessageDef) -> None:
        msg_string = """
uint8 OK = 0

uint8 WARN = 1

uint8 ERROR = 2
uint8 STALE = 3"""
        msg_def = MessageDef.from_string("test_pkg", "enum_name", msg_string)

        assert msg_def == expected


def test_enum_non_ascending_values() -> None:
    msg_string = """
uint8 SHAPE_TYPE_UNDEFINED = 0

# Comment block 1

uint8 SHAPE_TYPE_BOX = 1
uint8 SHAPE_TYPE_SPHERE = 2

# Comment block 2

uint8 SHAPE_TYPE_VERTICAL_STRUCTURE = 10
uint8 SHAPE_TYPE_VERTICAL_STRUCTURE_WITH_RADIUS = 101
uint8 SHAPE_TYPE_HORIZONTAL_STRUCTURE = 11"""
    msg_def = MessageDef.from_string("test_pkg", "ShapeTypes", msg_string)
    expected = MessageDef(
        name="ShapeTypes",
        fields=[],
        enums=[
            EnumDef(
                name="ShapeTypes",
                literals=[
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1")),
                        name="UNDEFINED",
                        value="0",
                        description="",
                    ),
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1")),
                        name="BOX",
                        value="1",
                        description="Comment block 1 ",
                    ),
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1")),
                        name="SPHERE",
                        value="2",
                        description="Comment block 1 ",
                    ),
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1")),
                        name="VERTICAL_STRUCTURE",
                        value="10",
                        description="Comment block 2 ",
                    ),
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1")),
                        name="VERTICAL_STRUCTURE_WITH_RADIUS",
                        value="101",
                        description="Comment block 2 ",
                    ),
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1")),
                        name="HORIZONTAL_STRUCTURE",
                        value="11",
                        description="Comment block 2 ",
                    ),
                ],
                description="",
            )
        ],
        description="",
    )

    assert msg_def == expected


class TestEnumName:
    @staticmethod
    def test_enum_name_commonprefix_no_underscore() -> None:
        msg_string = """
uint8 START = 0
uint8 STOP = 1
int8 field"""
        msg_def = MessageDef.from_string("test_pkg", "enum_name", msg_string)
        expected = "enum_nameType"

        actual = msg_def.enums[0].name

        assert actual == expected

    @staticmethod
    def test_enum_name_commonprefix_with_underscore() -> None:
        msg_string = """
uint8 ST_ART = 0
uint8 ST_OP = 1
int8 field"""
        msg_def = MessageDef.from_string("test_pkg", "enum_name", msg_string)
        expected = "St"

        actual = msg_def.enums[0].name

        assert actual == expected

    @staticmethod
    def test_enum_name_commonprefix_with_multiple_underscore() -> None:
        msg_string = """
uint8 S_T_ART = 0
uint8 S_T_OP = 1
int8 field"""
        msg_def = MessageDef.from_string("test_pkg", "enum_name", msg_string)
        expected = "ST"

        actual = msg_def.enums[0].name

        assert actual == expected

    @staticmethod
    def test_enum_name_match() -> None:
        msg_string = """
int8 STATUS_NO_FIX =  -1
int8 STATUS_FIX =      0
int8 STATUS_SBAS_FIX = 1
int8 STATUS_GBAS_FIX = 2

int8 status

uint16 SERVICE_GPS =     1
uint16 SERVICE_GLONASS = 2
uint16 SERVICE_COMPASS = 4
uint16 SERVICE_GALILEO = 8

uint16 service"""
        msg_def = MessageDef.from_string(
            "test_pkg", "NavSatStatus", msg_string
        )

        enum_names = [i.name for i in msg_def.enums]
        assert enum_names == ["NavSatStatusStatus", "NavSatStatusService"]

        status_literals = [
            (i.name, i.value) for i in msg_def.enums[0].literals
        ]
        assert status_literals == [
            ("NO_FIX", "-1"),
            ("FIX", "0"),
            ("SBAS_FIX", "1"),
            ("GBAS_FIX", "2"),
        ]

        service_literals = [
            (i.name, i.value) for i in msg_def.enums[1].literals
        ]
        assert service_literals == [
            ("GPS", "1"),
            ("GLONASS", "2"),
            ("COMPASS", "4"),
            ("GALILEO", "8"),
        ]


def test_MessageDef_class() -> None:
    expected = MessageDef(
        name="SampleClass",
        fields=[
            FieldDef(
                type=TypeDef("uint8", Range("0", "10"), None),
                name="sample_field1",
                description="This block comment is added to the "
                "property description of sample_field1. "
                "This block comment is also added to the "
                "property description of sample_field1. ",
            ),
            FieldDef(
                type=TypeDef("SampleClassEnum", Range("0", "*"), "package2"),
                name="sample_field2",
                description="This block comment is added to the property "
                "descriptions of sample_field2 and sample_field3. ",
            ),
            FieldDef(
                TypeDef("uint8", Range("3", "3"), None),
                name="sample_field3",
                description="This block comment is added to the property "
                "descriptions of sample_field2 and sample_field3. ",
            ),
            FieldDef(
                type=TypeDef("SampleEnum", Range("1", "1"), "SampleEnum"),
                name="sample_field4",
                description="This block comment is added to the property "
                "descriptions of sample_field4 and sample_field5. "
                "Fields in SampleClass can reference "
                "enums in other files. "
                "The property sample_field4 "
                "is of type SampleEnum. "
                "cf. SampleEnum ",
            ),
            FieldDef(
                type=TypeDef("SampleEnumValue", Range("1", "1"), "SampleEnum"),
                name="sample_field5",
                description="This block comment is added to the property "
                "descriptions of sample_field4 and sample_field5. "
                "This inline comment "
                "is added to the "
                "property description of "
                "sample_field5. "
                "The property sample_field5 "
                "is of type SampleEnumValue. "
                "cf. SampleEnum, SAMPLE_ENUM_VALUE_XXX ",
            ),
        ],
        enums=[],
        description="SampleClass.msg "
        "The first comment block at the top of the file "
        "is added to the class description of SampleClass. ",
    )

    msg_path = SAMPLE_CLASS_PATH
    msg_def = MessageDef.from_file(
        "test_pkg",
        msg_path,
        license_header=SAMPLE_LICENSE_HEADER,
    )

    assert msg_def == expected


def test_MessageDef_enum() -> None:
    expected = MessageDef(
        name="SampleEnum",
        fields=[],
        enums=[
            EnumDef(
                name="SampleEnumValue",
                literals=[
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None),
                        name="RED",
                        value="0",
                        description="",
                    ),
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None),
                        name="BLUE",
                        value="1",
                        description=(
                            "This inline comment "
                            "is added to the "
                            "enum literal "
                            "description of BLUE. "
                        ),
                    ),
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None),
                        name="YELLOW",
                        value="2",
                        description=(
                            "This block comment is added to the "
                            "enum literal descriptions of YELLOW and GREEN. "
                        ),
                    ),
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None),
                        name="GREEN",
                        value="3",
                        description=(
                            "This block comment is added to the "
                            "enum literal descriptions of YELLOW and GREEN. "
                        ),
                    ),
                ],
                description=(
                    "SampleEnum.msg "
                    "This block comment is added to the "
                    "enum description of SampleEnumValue. "
                ),
            ),
            EnumDef(
                name="SampleEnum",
                literals=[
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None),
                        name="OK",
                        value="0",
                        description="",
                    ),
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None),
                        name="WARN",
                        value="1",
                        description="",
                    ),
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None),
                        name="ERROR",
                        value="2",
                        description="",
                    ),
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None),
                        name="STALE",
                        value="3",
                        description="",
                    ),
                ],
                description=(
                    "This block comment is added to the "
                    "enum description of SampleEnum. "
                    "In a file, there can only be one or no enum "
                    "whose literal names do not share a common prefix. "
                ),
            ),
        ],
        description="",
    )

    msg_path = SAMPLE_ENUM_PATH
    msg_def = MessageDef.from_file(
        "test_pkg",
        msg_path,
        license_header=SAMPLE_LICENSE_HEADER,
    )

    assert msg_def == expected


def test_MessageDef_class_enum() -> None:
    expected = MessageDef(
        name="SampleClassEnum",
        fields=[
            FieldDef(
                type=TypeDef(
                    "SampleClassEnumStatus",
                    Range("1", "1"),
                    "package2.SampleClassEnum",
                ),
                name="status",
                description=(
                    "The property status is of type SampleClassEnumStatus. "
                ),
            ),
            FieldDef(
                type=TypeDef(
                    "SampleClassEnumColor",
                    Range("1", "1"),
                    "package2.SampleClassEnum",
                ),
                name="color",
                description="The property color is of type Color. ",
            ),
            FieldDef(
                type=TypeDef("uint8", Range("1", "1"), None),
                name="field",
                description="",
            ),
        ],
        enums=[
            EnumDef(
                name="SampleClassEnumStatus",
                literals=[
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None),
                        name="OK",
                        value="0",
                        description="",
                    ),
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None),
                        name="WARN",
                        value="1",
                        description="",
                    ),
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None),
                        name="ERROR",
                        value="2",
                        description="",
                    ),
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None),
                        name="STALE",
                        value="3",
                        description="",
                    ),
                ],
                description=(
                    "This block comment is added to the "
                    "enum description of SampleClassEnumStatus. "
                ),
            ),
            EnumDef(
                name="SampleClassEnumColor",
                literals=[
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None),
                        name="RED",
                        value="0",
                        description="",
                    ),
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None),
                        name="BLUE",
                        value="1",
                        description="",
                    ),
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None),
                        name="YELLOW",
                        value="2",
                        description="",
                    ),
                ],
                description=(
                    "This block comment is added to the "
                    "enum description of Color. "
                ),
            ),
        ],
        description=(
            "SampleClassEnum.msg "
            "Properties in SampleClassEnum can reference "
            "enums in the same file. "
        ),
    )

    msg_path = SAMPLE_CLASS_ENUM_PATH
    msg_def = MessageDef.from_file(
        "package2",
        msg_path,
        license_header=SAMPLE_LICENSE_HEADER,
    )

    assert msg_def == expected


@pytest.mark.parametrize(
    "msg_pkg_path",
    [
        SAMPLE_PACKAGE_PATH1,
        SAMPLE_PACKAGE_PATH2,
    ],
)
def test_MessagePkgDef_from_msg_folder(
    msg_pkg_path: abc.AbstractFilePath | pathlib.Path,
) -> None:
    message_pkg_def = MessagePkgDef.from_msg_folder(
        "",
        msg_pkg_path,
        license_header=SAMPLE_LICENSE_HEADER,
    )

    assert message_pkg_def.messages
