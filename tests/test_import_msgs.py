# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0

import pathlib

import pytest
from capellambse import decl, helpers

from capella_ros_tools.data_model import (
    ConstantDef,
    EnumDef,
    FieldDef,
    MessageDef,
    MessagePkgDef,
    Range,
    TypeDef,
)
from capella_ros_tools.scripts.import_msgs import Importer

PATH = pathlib.Path(__file__).parent

SAMPLE_PACKAGE_PATH = PATH.joinpath("data/data_model/example_msgs")
SAMPLE_PACKAGE_YAML = PATH.joinpath("data/data_model/example_msgs.yaml")
DUMMY_PATH = PATH.joinpath("data/empty_project_52")

ROOT = helpers.UUIDString("00000000-0000-0000-0000-000000000000")
SA_ROOT = helpers.UUIDString("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def importer():
    return Importer(DUMMY_PATH.as_posix(), True)


@pytest.fixture
def class_def():
    return MessageDef(
        name="MyMessage",
        description="An example message",
        fields=[
            FieldDef(
                name="field",
                type=TypeDef("uint8", Range("1", "1")),
                description="Field",
            ),
        ],
        enums=[],
    )


@pytest.fixture
def enum_def():
    return EnumDef(
        name="MyEnum",
        description="An example enum",
        literals=[
            ConstantDef(
                type=TypeDef("uint8", Range("1", "1")),
                name="LITERAL_A",
                value="0",
                description="Literal A",
            ),
            ConstantDef(
                type=TypeDef("uint8", Range("1", "1")),
                name="LITERAL_B",
                value="1",
                description="Literal B",
            ),
        ],
    )


@pytest.fixture
def class_expected():
    return {
        "promise_id": "my_package.MyMessage",
        "find": {
            "name": "MyMessage",
        },
        "set": {
            "description": "An example message",
            "properties": [
                {
                    "name": "field",
                    "type": decl.Promise("my_package.uint8"),
                    "description": "Field",
                    "min_card": decl.NewObject(
                        "LiteralNumericValue", value="1"
                    ),
                    "max_card": decl.NewObject(
                        "LiteralNumericValue", value="1"
                    ),
                },
            ],
        },
    }


@pytest.fixture
def enum_expected():
    return {
        "promise_id": "types.MyEnum",
        "find": {
            "name": "MyEnum",
        },
        "set": {
            "description": "An example enum",
            "literals": [
                {
                    "name": "LITERAL_A",
                    "description": "Literal A",
                    "value": decl.NewObject("LiteralNumericValue", value="0"),
                },
                {
                    "name": "LITERAL_B",
                    "description": "Literal B",
                    "value": decl.NewObject("LiteralNumericValue", value="1"),
                },
            ],
        },
    }


def test_convert_datatype(importer):
    promise_id = "std_msgs.uint8"

    expected = {
        "promise_id": "std_msgs.uint8",
        "find": {
            "name": "uint8",
            "_type": "NumericType",
        },
    }

    actual = importer._convert_datatype(promise_id)

    assert decl.dump([actual]) == decl.dump([expected])


def test_convert_enum(importer, enum_def, enum_expected):
    actual = importer._convert_enum(enum_def)

    assert decl.dump([actual]) == decl.dump([enum_expected])
    assert "types.MyEnum" in importer._promise_ids


def test_convert_class(importer, class_def, class_expected):
    actual = importer._convert_class("my_package", class_def)

    assert decl.dump([actual]) == decl.dump([class_expected])
    assert "my_package.MyMessage" in importer._promise_ids
    assert "my_package.uint8" in importer._promise_id_refs


def test_convert_class_with_range(importer):
    pkg_name = "my_package"
    msg_def = MessageDef(
        name="MyMessage",
        description="An example message",
        fields=[
            FieldDef(
                name="field",
                type=TypeDef("uint8", Range("1", "1"), Range("0", "10")),
                description="Field",
            ),
        ],
        enums=[],
    )

    expected = {
        "promise_id": "my_package.MyMessage",
        "find": {
            "name": "MyMessage",
        },
        "set": {
            "description": "An example message",
            "properties": [
                {
                    "name": "field",
                    "type": decl.Promise("my_package.uint8"),
                    "description": "Field",
                    "min_card": decl.NewObject(
                        "LiteralNumericValue", value="1"
                    ),
                    "max_card": decl.NewObject(
                        "LiteralNumericValue", value="1"
                    ),
                    "min_value": decl.NewObject(
                        "LiteralNumericValue", value="0"
                    ),
                    "max_value": decl.NewObject(
                        "LiteralNumericValue", value="10"
                    ),
                },
            ],
        },
    }

    actual = importer._convert_class(pkg_name, msg_def)

    assert decl.dump([actual]) == decl.dump([expected])
    assert "my_package.MyMessage" in importer._promise_ids
    assert "my_package.uint8" in importer._promise_id_refs


def test_convert_class_with_ref(importer):
    pkg_name = "my_package"
    msg_def = MessageDef(
        name="MyMessage",
        description="An example message",
        fields=[
            FieldDef(
                name="field",
                type=TypeDef("uint8", Range("1", "1"), None, "std_msgs"),
                description="Field",
            ),
        ],
        enums=[],
    )

    expected = {
        "promise_id": "my_package.MyMessage",
        "find": {
            "name": "MyMessage",
        },
        "set": {
            "description": "An example message",
            "properties": [
                {
                    "name": "field",
                    "type": decl.Promise("std_msgs.uint8"),
                    "description": "Field",
                    "min_card": decl.NewObject(
                        "LiteralNumericValue", value="1"
                    ),
                    "max_card": decl.NewObject(
                        "LiteralNumericValue", value="1"
                    ),
                },
            ],
        },
    }

    actual = importer._convert_class(pkg_name, msg_def)

    assert decl.dump([actual]) == decl.dump([expected])
    assert "my_package.MyMessage" in importer._promise_ids
    assert "std_msgs.uint8" in importer._promise_id_refs


def test_convert_package(
    importer, class_def, enum_def, class_expected, enum_expected
):
    subpkg_def = MessagePkgDef(
        name="sub_package",
        messages=[
            MessageDef(
                name="MyEnum",
                description="An example enum",
                fields=[],
                enums=[enum_def],
            ),
        ],
        packages=[],
    )
    subpkg2_def = MessagePkgDef(
        name="sub_package2",
        messages=[],
        packages=[],
    )
    pkg_def = MessagePkgDef(
        name="my_package",
        messages=[class_def],
        packages=[subpkg_def, subpkg2_def],
    )

    expected = [
        {
            "parent": decl.Promise("my_package.sub_package"),
            "sync": {
                "enumerations": [enum_expected],
            },
        },
        {
            "parent": decl.Promise("root.my_package"),
            "sync": {
                "classes": [class_expected],
                "packages": [
                    {
                        "promise_id": "my_package.sub_package",
                        "find": {
                            "name": "sub_package",
                        },
                    },
                    {
                        "promise_id": "my_package.sub_package2",
                        "find": {
                            "name": "sub_package2",
                        },
                    },
                ],
            },
        },
    ]

    actual = importer._convert_package(
        decl.Promise("root.my_package"), pkg_def
    )
    assert decl.dump(actual) == decl.dump(expected)


def test_import_msgs():
    expected = decl.dump(decl.load(SAMPLE_PACKAGE_YAML))
    actual = Importer(SAMPLE_PACKAGE_PATH.as_posix(), True)(ROOT, SA_ROOT)
    assert actual == expected