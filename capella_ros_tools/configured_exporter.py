# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Tool for exporting a Capella data package to ROS messages."""
import dataclasses
import pathlib
import re
from collections import abc as cabc
from html.parser import HTMLParser

import capellambse
import jinja2
from capellambse.metamodel import information

from . import logger

ROS_TYPES = [
    "bool",
    "byte",
    "char",
    "int8",
    "uint8",
    "int16",
    "uint16",
    "int32",
    "uint32",
    "int64",
    "uint64",
    "float32",
    "float64",
    "string",
]

UINT_REGEX = re.compile(r"^uint(\d+)")
INT_REGEX = re.compile(r"^int(\d+)")
FLOAT_REGEX = re.compile(r"^float(\d+)")


def int_bytes(length: int):
    """Return ROS byte length for integers."""
    if length <= 8:
        return 8
    if length <= 16:
        return 16
    if length <= 32:
        return 32
    if length <= 64:
        return 64


def float_bytes(length: int):
    """Return ROS byte length for floats."""
    if length <= 32:
        return 32
    if length <= 64:
        return 64


@dataclasses.dataclass
class LiteralData:
    """Data for class properties and enum values."""

    type: str
    name: str
    value: str | None = None
    docstr: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class ClassData:
    """Data for a class."""

    name: str
    docstr: list[str] = dataclasses.field(default_factory=list)
    literals: list[LiteralData] = dataclasses.field(default_factory=list)


class MyHTMLParser(HTMLParser):
    """An HTML parser to convert an HTML string to a list of plain strings."""

    def __init__(self):
        super().__init__()
        self.text_list = []

    def handle_data(self, data: str):
        """Process data and fill the text list."""
        if data.strip():  # Skipping empty strings
            self.text_list.append(data.strip())


class Exporter:
    """The exporter class."""

    packages: dict[str, str]  # mapping from ROS pkg name to capella pkg uuid
    build_ins: dict[str, str]  # maps build in ROS pkgs to capella pkg uuids
    package_uuids: list[str]  # list of all pkg uuids
    custom_pkg: dict[str, list[str]]  # maps ROS pkg names to capella cls uuids

    def __init__(
        self,
        packages: dict[str, str],
        build_ins: dict[str, str],
        custom_pkg: dict[str, list[str]],
        model: capellambse.MelodyModel,
    ):
        self.packages = packages
        self.build_ins = build_ins
        self.package_uuids = list(packages.values()) + list(build_ins.values())
        self.custom_pkg = custom_pkg
        self.model = model
        jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(pathlib.Path(__file__).parent)
        )
        self.template = jinja_env.get_template("ros-msg.j2")

    def _get_package_classes(
        self,
        package: information.DataPkg,
        classes: capellambse.model.ElementList | None = None,
    ):
        if classes is None:
            classes = package.classes
        else:
            classes += package.classes

        for sub_pkg in package.packages:
            if sub_pkg.uuid not in self.package_uuids:
                self._get_package_classes(sub_pkg, classes)

        return classes

    def _collect_pure_packages(self):
        package_class_mapping: dict[
            str, capellambse.model.ElementList[information.Class]
        ] = {}
        for package_name, uuid in self.packages.items():
            package_class_mapping[package_name] = self._get_package_classes(
                self.model.by_uuid(uuid)
            )

        return package_class_mapping

    def _get_cls_dependencies(
        self,
        cls: information.Class,
        class_package_mapping: dict[str, str],
        dependency_classes: list[information.Class],
    ):
        for prop in cls.properties:
            _type = prop.type
            if isinstance(_type, information.Class):
                if (
                    _type.uuid in class_package_mapping
                    or _type in dependency_classes
                ):
                    continue

                dependency_classes.append(_type)
                self._get_cls_dependencies(
                    _type, class_package_mapping, dependency_classes
                )

    def _get_missing_dependencies(
        self,
        package_class_mapping: dict[str, cabc.Iterable[information.Class]],
        class_package_mapping: dict[str, str],
    ):
        dependency_classes: dict[str, list[information.Class]] = {}
        for pkg, classes in package_class_mapping.items():
            cls_dependencies: list[information.Class] = []
            dependency_classes[pkg] = cls_dependencies
            for cls in classes:
                self._get_cls_dependencies(
                    cls, class_package_mapping, cls_dependencies
                )
        return dependency_classes

    def _make_doc_str(self, markup: str):
        parser = MyHTMLParser()
        parser.feed(markup)

        return parser.text_list

    def _make_property_name(self, name: str):
        # Convert camelCase to snake_case
        name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name)
        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        name = name.lower()
        # Replace invalid characters with underscores
        name = re.sub("[^a-z0-9_]", "_", name)
        name = re.sub("^[^a-z]+", "", name)
        name = re.sub("_+", "_", name)
        return re.sub("_$", "", name)

    def _make_constant_name(self, name: str):
        # Convert camelCase or camel_case to snake_case
        name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name)
        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)

        name = name.upper()

        # Replace invalid characters with underscores
        name = re.sub("[^A-Z0-9_]", "_", name)
        name = re.sub("^[^A-Z]+", "", name)
        name = re.sub("_+", "_", name)
        name = re.sub("_$", "", name)
        return name

    def _convert_cls_name(self, name: str):
        temp_parts = re.split("[^a-zA-Z0-9]+", name)
        parts = []
        for part in temp_parts:
            parts.extend(re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])", part))

        words = [word for word in parts if word]
        camel_case_name = "".join(word.capitalize() for word in words)

        if not camel_case_name or not camel_case_name[0].isalpha():
            camel_case_name = "A" + camel_case_name

        return camel_case_name

    def _make_type_name(self, _type: information.datatype.DataType):
        type_name = _type.name
        if type_name in ROS_TYPES:
            return _type.name

        if match := UINT_REGEX.match(type_name):
            length = int_bytes(int(match.group(1)))
            return f"uint{length}"

        if match := INT_REGEX.match(type_name):
            length = int_bytes(int(match.group(1)))
            return f"int{length}"

        if match := FLOAT_REGEX.match(type_name):
            length = float_bytes(int(match.group(1)))
            return f"float{length}"

        logger.error("Type %s is unknown.", type_name)
        return type_name

    def _create_class_data(
        self,
        cls: information.Class,
        current_pkg: str,
        class_package_mapping: dict[str, str],
        dependency_classes,
    ):
        cls_data = ClassData(
            self._convert_cls_name(cls.name),
            self._make_doc_str(cls.description),
        )
        for prop in cls.properties:
            _type = prop.type
            if isinstance(_type, information.datatype.DataType):
                if isinstance(_type, information.datatype.Enumeration):
                    type_name = self._make_type_name(_type.domain_type)
                    for val in _type.owned_literals:
                        cls_data.literals.append(
                            LiteralData(
                                type_name,
                                self._make_constant_name(val.name),
                                val.value.value,
                                self._make_doc_str(val.description),
                            )
                        )
                else:
                    type_name = self._make_type_name(_type)
            elif isinstance(_type, information.Class):
                pkg = ""
                if cls_pkg := class_package_mapping.get(_type.uuid):
                    if cls_pkg != current_pkg:
                        pkg = f"{cls_pkg}/"
                elif _type.uuid not in dependency_classes:
                    logger.error(
                        "Class %s was referenced in %s, but not found",
                        _type.name,
                        cls.name,
                    )
                type_name = f"{pkg}{self._convert_cls_name(_type.name)}"
            else:
                logger.error("Unknown type for property %s of class %s")
                type_name = "unknown"

            try:
                card = (prop.min_card.value, prop.max_card.value)
            except AttributeError:
                card = ("1", "1")

            if card != ("1", "1"):
                if card[1] == "*":
                    type_name += "[]"
                elif card[0] == card[1]:
                    type_name += f"[{card[0]}]"
                else:
                    type_name += f"[<={card[1]}]"

            cls_data.literals.append(
                LiteralData(
                    type_name,
                    self._make_property_name(prop.name),
                    docstr=self._make_doc_str(prop.description),
                )
            )

        return cls_data

    def _collect_build_in_classes(self):
        cls_to_pkg_mapping: dict[str, str] = {}
        for pkg_name, uuid in self.build_ins.items():
            for cls in self._get_package_classes(self.model.by_uuid(uuid)):
                cls_to_pkg_mapping[cls.uuid] = pkg_name

        return cls_to_pkg_mapping

    def prepare_export_data(self):
        """Collect export data for all defined packages."""
        package_class_mapping = self._collect_pure_packages()
        package_class_mapping |= self.custom_pkg
        class_package_mapping = self._collect_build_in_classes()
        class_package_mapping |= {
            cls.uuid: pkg_name
            for pkg_name, classes in package_class_mapping.items()
            for cls in classes
        }
        dependency_classes = self._get_missing_dependencies(
            package_class_mapping, class_package_mapping
        )
        result: dict[str, list[ClassData]] = {}
        for pkg, classes in package_class_mapping.items():
            cls_uuids = set()
            result[pkg] = []
            pkg_dependencies = [
                cls.uuid for cls in dependency_classes.get(pkg, [])
            ]
            for cls in classes:
                if cls.uuid not in cls_uuids:
                    cls_uuids.add(cls.uuid)
                    result[pkg].append(
                        self._create_class_data(
                            cls, pkg, class_package_mapping, pkg_dependencies
                        )
                    )

            for cls in dependency_classes.get(pkg, []):
                if cls.uuid not in cls_uuids:
                    cls_uuids.add(cls.uuid)
                    result[pkg].append(
                        self._create_class_data(
                            cls, pkg, class_package_mapping, pkg_dependencies
                        )
                    )

        return result

    def render_package(
        self, out_dir: pathlib.Path, name: str, msgs: list[ClassData]
    ):
        """Render the given messages for the given package."""
        pkg_dir = out_dir / name / "msg"
        pkg_dir.mkdir(parents=True, exist_ok=True)
        for msg in msgs:
            ros_msg = self.template.render(msg=msg)
            ros_path = pkg_dir / f"{msg.name}.msg"
            ros_path.write_text(ros_msg, "utf-8")
