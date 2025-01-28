# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Main entry point into Capella ROS Tools."""

import io
import pathlib
import typing
import uuid

import capellambse
import click
import yaml
from capellambse import cli_helpers, decl

import capella_ros_tools
from capella_ros_tools import configured_exporter, exporter, importer, logger


@click.group()
@click.version_option(
    version=capella_ros_tools.__version__,
    prog_name="capella-ros-tools",
    message="%(prog)s %(version)s",
)
def cli():
    """Console script for Capella ROS Tools."""


@cli.command("import")
@click.option(
    "-i",
    "--input",
    type=str,
    required=True,
    help="Path to the ROS message package.",
)
@click.option(
    "-m",
    "--model",
    type=cli_helpers.ModelCLI(),
    required=True,
    help="Path to the Capella model.",
)
@click.option(
    "-l",
    "--layer",
    type=click.Choice(["oa", "la", "sa", "pa"], case_sensitive=False),
    help="The layer to import the messages to.",
)
@click.option(
    "-r",
    "--root",
    type=click.UUID,
    help="The UUID of the root package to import the messages to.",
)
@click.option(
    "-t",
    "--types",
    type=click.UUID,
    help="The UUID of the types package to import the created data types to.",
)
@click.option(
    "--no-deps",
    "no_deps",
    is_flag=True,
    help="Don't install message dependencies.",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=pathlib.Path, dir_okay=False),
    help="Produce a declarative YAML instead of modifying the source model.",
)
@click.option(
    "--license-header",
    type=click.Path(path_type=pathlib.Path, dir_okay=False),
    help="Ignore the license header from the given file when importing msgs.",
)
@click.option(
    "--description-regex",
    type=str,
    help="Regular expression to extract description from the file .",
)
@click.option(
    "--dependency-json",
    type=click.Path(path_type=pathlib.Path, dir_okay=False),
    help="A path to a JSON containing dependencies which should be imported.",
)
def import_msgs(
    input: str,
    model: capellambse.MelodyModel,
    layer: str,
    root: uuid.UUID,
    types: uuid.UUID,
    no_deps: bool,
    output: pathlib.Path,
    license_header: pathlib.Path | None,
    description_regex: str | None,
    dependency_json: pathlib.Path | None,
) -> None:
    """Import ROS messages into a Capella data package."""
    if root:
        root_uuid = str(root)
    elif layer:
        root_uuid = getattr(model, layer).data_package.uuid
    else:
        raise click.UsageError("Either --root or --layer must be provided")

    if types:
        params = {"types_uuid": str(types)}
    else:
        params = {"types_parent_uuid": model.sa.data_package.uuid}

    parsed = importer.Importer(
        input, no_deps, license_header, description_regex, dependency_json
    )
    logger.info("Loaded %d packages", len(parsed.messages.packages))

    yml = parsed.to_yaml(root_uuid, **params)
    if output:
        logger.info("Writing declarative YAML to file %s", output)
        output.write_text(yml, encoding="utf-8")
    else:
        logger.info("Writing to model %s", model.name)
        decl.apply(model, io.StringIO(yml))
        model.save()


@cli.command("export")
@click.option(
    "-m",
    "--model",
    type=cli_helpers.ModelCLI(),
    required=True,
    help="Path to the Capella model.",
    envvar="CAPELLA_ROS_TOOLS_MODEL",
)
@click.option(
    "-l",
    "--layer",
    type=click.Choice(["oa", "la", "sa", "pa"], case_sensitive=False),
    help="The layer to export the model objects from.",
    envvar="CAPELLA_ROS_TOOLS_LAYER",
)
@click.option(
    "-r",
    "--root",
    type=click.UUID,
    help="The UUID of the root package to import the messages from.",
    envvar="CAPELLA_ROS_TOOLS_ROOT_PACKAGE",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=pathlib.Path, file_okay=False),
    default=pathlib.Path.cwd() / "data-package",
    help="Output directory for the .msg files.",
)
def export_capella(
    model: capellambse.MelodyModel,
    layer: str,
    root: uuid.UUID,
    output: pathlib.Path,
):
    """Export Capella data package to ROS messages."""
    if root:
        current_pkg = model.search("DataPkg").by_uuid(str(root))
    elif layer:
        current_pkg = getattr(model, layer).data_package
    else:
        raise click.UsageError("Either --root or --layer must be provided")

    exporter.export(current_pkg, output)  # type: ignore


@cli.command("configured-export")
@click.option(
    "-m",
    "--model",
    type=cli_helpers.ModelCLI(),
    required=True,
    help="Path to the Capella model.",
    envvar="CAPELLA_ROS_TOOLS_MODEL",
)
@click.option(
    "-c",
    "--config",
    type=click.File(mode="r", encoding="utf8"),
    required=True,
    envvar="CAPELLA_ROS_EXPORT_CONFIG",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=pathlib.Path, file_okay=False),
    default=pathlib.Path.cwd() / "data-package",
    help="Output directory for the .msg files.",
)
def configured_export(
    model: capellambse.MelodyModel,
    config: typing.TextIO,
    output: pathlib.Path,
):
    """Export Capella data package to ROS messages."""
    conf = yaml.safe_load(config)
    _exporter = configured_exporter.Exporter(
        conf["packages"], conf["build_ins"], conf["custom_packages"], model
    )
    export_data = _exporter.prepare_export_data()
    for pkg, msgs in export_data.items():
        _exporter.render_package(output, pkg, msgs)


if __name__ == "__main__":
    cli()
