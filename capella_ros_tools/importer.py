# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Tool for importing ROS messages to a Capella data package."""

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
    ):
        self.messages = data_model.MessagePkgDef("root", [], [])
        self._promise_ids: set[str] = set()
        self._promise_id_refs: set[str] = set()

        self._add_packages("ros_msgs", msg_path)
        if no_deps:
            return

        for interface_name, interface_url in ROS2_INTERFACES.items():
            self._add_packages(interface_name, interface_url)

    def _add_packages(self, name: str, path: str) -> None:
        root = filehandler.get_filehandler(path).rootdir
        for dir in root.rglob("msg"):
            pkg_name = dir.parent.name or name
            pkg_def = data_model.MessagePkgDef.from_msg_folder(pkg_name, dir)
            self.messages.packages.append(pkg_def)
            logger.info("Loaded package %s from %s", pkg_name, dir)

    def _convert_datatype(self, promise_id: str) -> dict:
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
    ) -> dict:
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

        sync: dict = {}
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
    ) -> tuple[dict, list[dict]]:
        promise_id = f"{pkg_name}.{msg_def.name}"
        self._promise_ids.add(promise_id)
        props = []
        associations = []
        for field_def in msg_def.fields:
            prop_promise_id = f"{promise_id}.{field_def.name}"
            promise_ref = (
                f"{field_def.type.package or pkg_name}.{field_def.type.name}"
            )
            self._promise_id_refs.add(promise_ref)
            prop_yml = {
                "promise_id": prop_promise_id,
                "name": field_def.name,
                "type": decl.Promise(promise_ref),
                "kind": "COMPOSITION",
                "description": field_def.description,
                "min_card": decl.NewObject(
                    "LiteralNumericValue", value=field_def.type.card.min
                ),
                "max_card": decl.NewObject(
                    "LiteralNumericValue", value=field_def.type.card.max
                ),
            }

            associations.append(
                {
                    "find": {"name": prop_promise_id},
                    "set": {
                        "navigable_members": [decl.Promise(prop_promise_id)],
                        "members": [
                            {
                                "_type": "Property",
                                "type": decl.Promise(promise_id),
                                "kind": "ASSOCIATION",
                                "min_card": decl.NewObject(
                                    "LiteralNumericValue", value="1"
                                ),
                                "max_card": decl.NewObject(
                                    "LiteralNumericValue", value="1"
                                ),
                            }
                        ],
                    },
                }
            )
            props.append(prop_yml)

        yml = {
            "promise_id": promise_id,
            "find": {
                "name": msg_def.name,
            },
            "set": {
                "description": msg_def.description,
                "properties": props,
            },
        }
        return yml, associations

    def _convert_enum(
        self, pkg_name: str, enum_def: data_model.EnumDef
    ) -> dict:
        promise_id = f"{pkg_name}.{enum_def.name}"
        self._promise_ids.add(promise_id)
        yml = {
            "promise_id": promise_id,
            "find": {
                "name": enum_def.name,
            },
            "set": {
                "description": enum_def.description,
                "literals": [
                    {
                        "name": literal.name,
                        "description": literal.description,
                        "value": decl.NewObject(
                            "LiteralNumericValue", value=literal.value
                        ),
                    }
                    for literal in enum_def.literals
                ],
            },
        }

        return yml

    def to_yaml(self, layer_data_uuid: str, sa_data_uuid: str) -> str:
        """Import ROS messages into a Capella data package."""
        logger.info("Generating decl YAML")
        instructions = [
            {"parent": decl.UUIDReference(helpers.UUIDString(layer_data_uuid))}
            | self._convert_package(self.messages),
        ]
        if needed_types := self._promise_id_refs - self._promise_ids:
            datatypes = [
                self._convert_datatype(promise_id)
                for promise_id in needed_types
            ]
            instructions.append(
                {
                    "parent": decl.UUIDReference(
                        helpers.UUIDString(sa_data_uuid)
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
        return decl.dump(instructions)
