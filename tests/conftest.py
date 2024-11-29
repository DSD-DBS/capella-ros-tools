# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0

import pytest

from capella_ros_tools.data_model import (
    ConstantDef,
    EnumDef,
    FieldDef,
    MessageDef,
    Range,
    TypeDef,
)


@pytest.fixture
def sample_class_def() -> MessageDef:
    return MessageDef(
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


@pytest.fixture
def sample_enum_def() -> MessageDef:
    return MessageDef(
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
                        description="This inline comment "
                        "is added to the "
                        "enum literal "
                        "description of BLUE. ",
                    ),
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None),
                        name="YELLOW",
                        value="2",
                        description="This block comment is added to the "
                        "enum literal descriptions of YELLOW and GREEN. ",
                    ),
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None),
                        name="GREEN",
                        value="3",
                        description="This block comment is added to the "
                        "enum literal descriptions of YELLOW and GREEN. ",
                    ),
                ],
                description="SampleEnum.msg "
                "This block comment is added to the "
                "enum description of SampleEnumValue. ",
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
                description="This block comment is added to the "
                "enum description of SampleEnum. "
                "In a file, there can only be one or no enum "
                "whose literal names do not share a common prefix. ",
            ),
        ],
        description="",
    )


@pytest.fixture
def sample_class_enum_def() -> MessageDef:
    return MessageDef(
        name="SampleClassEnum",
        fields=[
            FieldDef(
                type=TypeDef(
                    "SampleClassEnumStatus",
                    Range("1", "1"),
                    "SampleClassEnum",
                ),
                name="status",
                description="The property status is of type "
                "SampleClassEnumStatus. ",
            ),
            FieldDef(
                type=TypeDef("Color", Range("1", "1"), "SampleClassEnum"),
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
                description="This block comment is added to the "
                "enum description of SampleClassEnumStatus. ",
            ),
            EnumDef(
                name="Color",
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
                description="This block comment is added to the "
                "enum description of Color. ",
            ),
        ],
        description="SampleClassEnum.msg "
        "Properties in SampleClassEnum can reference "
        "enums in the same file. ",
    )
