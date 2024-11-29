# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Tool for exporting a Capella data package to ROS messages."""

import pathlib
import re

from capellambse.metamodel import information

from capella_ros_tools import data_model

from . import logger


def _clean_name(name: str) -> str:
    return re.sub(r"\W", "", name)


def export(
    current_pkg: information.DataPkg,
    current_path: pathlib.Path,
) -> None:
    """Export a Capella data package to ROS messages."""
    current_path.mkdir(parents=True, exist_ok=True)
    for cls_obj in current_pkg.classes:
        fields = []
        for prop_obj in cls_obj.owned_properties:
            try:
                card = data_model.Range(
                    prop_obj.min_card.value, prop_obj.max_card.value
                )
            except AttributeError:
                card = data_model.Range("1", "1")

            if (_type := prop_obj.type) is not None:
                type_name = _type.name
            else:
                logger.error(
                    "Type of property %s is None", prop_obj._short_repr_()
                )
                type_name = "<undefined>"

            type_def = data_model.TypeDef(name=type_name, card=card)
            prop_def = data_model.FieldDef(
                type=type_def,
                name=prop_obj.name,
                description=prop_obj.description or "",
            )
            fields.append(prop_def)
        cls_def = data_model.MessageDef(
            name=cls_obj.name,
            fields=fields,
            enums=[],
            description=cls_obj.description or "",
        )
        (current_path / f"{_clean_name(cls_obj.name)}.msg").write_text(
            str(cls_def)
        )

    for enum_obj in current_pkg.enumerations:
        literals = []
        for i, lit_obj in enumerate(enum_obj.owned_literals):
            try:
                type_name = lit_obj.value.type.name
            except AttributeError:
                type_name = "uint8"
            try:
                literal_value = lit_obj.value.value
            except AttributeError:
                literal_value = i
            type_def = data_model.TypeDef(
                type_name, data_model.Range("1", "1")
            )
            lit_def = data_model.ConstantDef(
                type=type_def,
                name=lit_obj.name,
                value=literal_value,
                description=lit_obj.description or "",
            )
            literals.append(lit_def)
        enum_def = data_model.EnumDef(
            name=enum_obj.name,
            literals=literals,
            description=enum_obj.description or "",
        )
        (current_path / f"{_clean_name(enum_obj.name)}.msg").write_text(
            str(enum_def)
        )

    for pkg_obj in current_pkg.packages:
        pkg_path = current_path / _clean_name(pkg_obj.name)
        export(pkg_obj, pkg_path)
        logger.info("Exported package %s to %s", pkg_obj.name, pkg_path)
