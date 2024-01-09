# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Parser for Capella model."""
import typing as t

from . import BaseCapellaModel, ClassDef, ClassProperty, EnumDef, EnumValue


class CapellaModel(BaseCapellaModel):
    """Capella model definition for parsing model."""

    def get_packages(self, package: t.Any) -> set[str]:
        """Get packages in Capella model."""
        return {pkg.name for pkg in package.packages}

    def get_classes(self, package: t.Any) -> list[ClassDef]:
        """Get classes in Capella model."""
        classes = []
        for cls in package.classes:
            props = []
            for prop in cls.owned_properties:
                type_pkg_name = prop.type.parent.name
                if type_pkg_name in [
                    "Predefined Types",
                    cls.parent.name,
                ]:
                    type_pkg_name = None

                props.append(
                    ClassProperty(
                        prop.type.name,
                        type_pkg_name,
                        prop.name,
                        prop.min_card.value,
                        prop.max_card.value,
                        prop.description,
                    )
                )
            classes.append(
                ClassDef(
                    cls.name,
                    props,
                    cls.description,
                )
            )
        return classes

    def get_enums(self, package: t.Any) -> list[EnumDef]:
        """Get enums in Capella model."""
        enums = []
        for enum in package.enumerations:
            values = []
            for literal in enum.owned_literals:
                try:
                    type_name = literal.value.type.name
                    literal_value = literal.value.value
                except AttributeError:
                    type_name = ""
                    literal_value = ""

                values.append(
                    EnumValue(
                        type_name,
                        literal.name,
                        literal_value,
                        literal.description,
                    )
                )
            enums.append(
                EnumDef(
                    enum.name,
                    values,
                    enum.description,
                )
            )
        return enums
