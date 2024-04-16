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
    Range,
    TypeDef,
)
from capella_ros_tools.importer import Importer

# pylint: disable=redefined-outer-name

PATH = pathlib.Path(__file__).parent

SAMPLE_PACKAGE_PATH = PATH.joinpath("data/data_model/example_msgs")
SAMPLE_PACKAGE_YAML = PATH.joinpath("data/data_model/example_msgs.yaml")
DUMMY_PATH = PATH.joinpath("data/empty_project_60")

ROOT = helpers.UUIDString("00000000-0000-0000-0000-000000000000")
SA_ROOT = helpers.UUIDString("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def importer() -> Importer:
    return Importer(DUMMY_PATH.as_posix(), True)


def test_convert_datatype(importer: Importer):
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


def test_convert_enum(importer: Importer):
    enum_def = EnumDef(
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
    expected = {
        "promise_id": "MyMessage.MyEnum",
        "find": {
            "name": "MyEnum",
        },
        "set": {
            "description": "An example enum",
        },
        "sync": {
            "literals": [
                {
                    "find": {
                        "name": "LITERAL_A",
                    },
                    "set": {
                        "description": "Literal A",
                        "value": decl.NewObject(
                            "LiteralNumericValue", value="0"
                        ),
                    },
                },
                {
                    "find": {
                        "name": "LITERAL_B",
                    },
                    "set": {
                        "description": "Literal B",
                        "value": decl.NewObject(
                            "LiteralNumericValue", value="1"
                        ),
                    },
                },
            ],
        },
    }

    actual = importer._convert_enum("MyMessage", enum_def)

    assert decl.dump([actual]) == decl.dump([expected])
    assert "MyMessage.MyEnum" in importer._promise_ids


def test_convert_class(importer: Importer):
    class_def = MessageDef(
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
    expected = {
        "promise_id": "my_package.MyMessage",
        "find": {
            "name": "MyMessage",
        },
        "set": {
            "description": "An example message",
        },
        "sync": {
            "properties": [
                {
                    "promise_id": "my_package.MyMessage.field",
                    "find": {
                        "name": "field",
                    },
                    "set": {
                        "type": decl.Promise("my_package.uint8"),
                        "kind": "COMPOSITION",
                        "description": "Field",
                        "min_card": decl.NewObject(
                            "LiteralNumericValue", value="1"
                        ),
                        "max_card": decl.NewObject(
                            "LiteralNumericValue", value="1"
                        ),
                    },
                },
            ],
        },
    }

    actual, _ = importer._convert_class("my_package", class_def)

    assert decl.dump([actual]) == decl.dump([expected])
    assert "my_package.MyMessage" in importer._promise_ids
    assert "my_package.uint8" in importer._promise_id_refs


def test_convert_class_with_ref(importer: Importer):
    pkg_name = "my_package"
    msg_def = MessageDef(
        name="MyMessage",
        description="An example message",
        fields=[
            FieldDef(
                name="field",
                type=TypeDef("uint8", Range("1", "1"), "std_msgs"),
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
        },
        "sync": {
            "properties": [
                {
                    "promise_id": "my_package.MyMessage.field",
                    "find": {
                        "name": "field",
                    },
                    "set": {
                        "type": decl.Promise("std_msgs.uint8"),
                        "kind": "COMPOSITION",
                        "description": "Field",
                        "min_card": decl.NewObject(
                            "LiteralNumericValue", value="1"
                        ),
                        "max_card": decl.NewObject(
                            "LiteralNumericValue", value="1"
                        ),
                    },
                },
            ],
        },
    }

    actual, _ = importer._convert_class(pkg_name, msg_def)

    assert decl.dump([actual]) == decl.dump([expected])
    assert "my_package.MyMessage" in importer._promise_ids
    assert "std_msgs.uint8" in importer._promise_id_refs


def test_convert_package():
    expected = decl.dump(decl.load(SAMPLE_PACKAGE_YAML))

    actual = Importer(SAMPLE_PACKAGE_PATH.as_posix(), True).to_yaml(
        ROOT, SA_ROOT
    )

    assert actual == expected
