# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Tool for importing ROS messages to a Capella data package."""

import os
import pathlib
import re
import typing as t

from capellambse import decl, filehandler, helpers

from capella_ros_tools import data_model

from . import logger

ROS2_INTERFACES = {
    "common_interfaces": "git+https://github.com/ros2/common_interfaces",
    "rcl_interfaces": "git+https://github.com/ros2/rcl_interfaces",
    "unique_identifier_msgs": (
        "git+https://github.com/ros2/unique_identifier_msgs"
    ),
}


class Importer:
    """Class for importing ROS messages to a Capella data package."""

    def __init__(
        self,
        msg_path: str,
        no_deps: bool,
        license_header_path: pathlib.Path | None = None,
        msg_description_regex: str | None = None,
    ):
        self.messages = data_model.MessagePkgDef("root", [], [])
        self._promise_ids: dict[str, None] = {}
        self._promise_id_refs: dict[str, None] = {}
        self._license_header = None
        if license_header_path is not None:
            self._license_header = license_header_path.read_text("utf-8")

        self._add_packages("ros_msgs", msg_path, msg_description_regex)
        if no_deps:
            return

        for interface_name, interface_url in ROS2_INTERFACES.items():
            self._add_packages(interface_name, interface_url)

    def _add_packages(
        self, name: str, path: str, msg_description_regex: str | None = None
    ) -> None:
        root = filehandler.get_filehandler(path).rootdir
        msg_description_pattern = None
        if msg_description_regex is not None:
            msg_description_pattern = re.compile(
                msg_description_regex, re.MULTILINE
            )

        for dir in sorted(root.rglob("msg"), key=os.fspath):
            pkg_name = dir.parent.name or name
            pkg_def = data_model.MessagePkgDef.from_msg_folder(
                pkg_name, dir, self._license_header, msg_description_pattern
            )
            self.messages.packages.append(pkg_def)
            logger.info("Loaded package %s from %s", pkg_name, dir)

    def _convert_datatype(self, promise_id: str) -> dict[str, t.Any]:
        name = promise_id.split(".", 1)[-1]
        if any(t in name for t in ["char", "str"]):
            _type = "StringType"
        elif any(t in name for t in ["bool", "byte"]):
            _type = "BooleanType"
        else:
            _type = "NumericType"
        yml = {
            "promise_id": promise_id,
            "find": {
                "name": name,
                "_type": _type,
            },
        }
        return yml

    def _convert_package(
        self,
        pkg_def: data_model.MessagePkgDef,
    ) -> dict[str, t.Any]:
        classes = []
        enums = []
        packages = []
        associations = []

        for msg_def in pkg_def.messages:
            if msg_def.fields:
                cls_yml, cls_associations = self._convert_class(
                    pkg_def.name, msg_def
                )
                classes.append(cls_yml)
                associations.extend(cls_associations)
            for enum_def in msg_def.enums:
                enums.append(self._convert_enum(msg_def.name, enum_def))

        for new_pkg in pkg_def.packages:
            new_yml = {
                "find": {
                    "name": new_pkg.name,
                },
            } | self._convert_package(new_pkg)
            packages.append(new_yml)

        sync = {}
        if classes:
            sync["classes"] = classes
        if enums:
            sync["enumerations"] = enums
        if packages:
            sync["packages"] = packages
        if associations:
            sync["owned_associations"] = associations

        yml = {}
        if sync:
            yml["sync"] = sync

        return yml

    def _convert_class(
        self, pkg_name: str, msg_def: data_model.MessageDef
    ) -> tuple[dict[str, t.Any], list[dict[str, t.Any]]]:
        promise_id = f"{pkg_name}.{msg_def.name}"
        self._promise_ids[promise_id] = None
        props = []
        associations = []
        for field_def in msg_def.fields:
            prop_promise_id = f"{promise_id}.{field_def.name}"
            promise_ref = (
                f"{field_def.type.package or pkg_name}.{field_def.type.name}"
            )
            self._promise_id_refs[promise_ref] = None
            prop_yml = {
                "promise_id": prop_promise_id,
                "find": {
                    "name": field_def.name,
                },
                "set": {
                    "type": decl.Promise(promise_ref),
                    "kind": "COMPOSITION",
                    "description": field_def.description,
                    "min_card": decl.NewObject(
                        "LiteralNumericValue", value=field_def.type.card.min
                    ),
                    "max_card": decl.NewObject(
                        "LiteralNumericValue", value=field_def.type.card.max
                    ),
                },
            }
            props.append(prop_yml)

            associations.append(
                {
                    "find": {
                        "navigable_members": [decl.Promise(prop_promise_id)],
                    },
                    "sync": {
                        "members": [
                            {
                                "find": {
                                    "type": decl.Promise(promise_id),
                                },
                                "set": {
                                    "_type": "Property",
                                    "kind": "ASSOCIATION",
                                    "min_card": decl.NewObject(
                                        "LiteralNumericValue", value="1"
                                    ),
                                    "max_card": decl.NewObject(
                                        "LiteralNumericValue", value="1"
                                    ),
                                },
                            }
                        ],
                    },
                }
            )

        yml = {
            "promise_id": promise_id,
            "find": {
                "name": msg_def.name,
            },
            "set": {
                "description": msg_def.description,
            },
            "sync": {
                "properties": props,
            },
        }
        return yml, associations

    def _convert_enum(
        self, pkg_name: str, enum_def: data_model.EnumDef
    ) -> dict[str, t.Any]:
        promise_id = f"{pkg_name}.{enum_def.name}"
        self._promise_ids[promise_id] = None
        literals = []
        for literal in enum_def.literals:
            literal_yml = {
                "find": {
                    "name": literal.name,
                },
                "set": {
                    "description": literal.description,
                    "value": decl.NewObject(
                        "LiteralNumericValue", value=literal.value
                    ),
                },
            }
            literals.append(literal_yml)
        yml = {
            "promise_id": promise_id,
            "find": {
                "name": enum_def.name,
            },
            "set": {
                "description": enum_def.description,
            },
            "sync": {
                "literals": literals,
            },
        }

        return yml

    def to_yaml(
        self,
        root_uuid: str,
        types_parent_uuid: str = "",
        types_uuid: str = "",
    ) -> str:
        """Import ROS messages into a Capella data package."""
        logger.info("Generating decl YAML")
        instructions = [
            {"parent": decl.UUIDReference(helpers.UUIDString(root_uuid))}
            | self._convert_package(self.messages),
        ]
        needed_types = [
            p for p in self._promise_id_refs if p not in self._promise_ids
        ]
        if not needed_types:
            return decl.dump(instructions)

        datatypes = [
            self._convert_datatype(promise_id) for promise_id in needed_types
        ]
        if types_uuid:
            instructions.append(
                {
                    "parent": decl.UUIDReference(
                        helpers.UUIDString(types_uuid)
                    ),
                    "sync": {"datatypes": datatypes},
                }
            )
        elif types_parent_uuid:
            instructions.append(
                {
                    "parent": decl.UUIDReference(
                        helpers.UUIDString(types_parent_uuid)
                    ),
                    "sync": {
                        "packages": [
                            {
                                "find": {"name": "Data Types"},
                                "sync": {"datatypes": datatypes},
                            }
                        ],
                    },
                }
            )
        else:
            raise ValueError(
                "Either types_parent_uuid or types_uuid must be provided"
            )
        return decl.dump(instructions)
