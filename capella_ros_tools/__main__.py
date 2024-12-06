# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Main entry point into Capella ROS Tools."""

import io
import json
import logging
import pathlib
import uuid

import capellambse
import click
from capellambse import cli_helpers, decl

import capella_ros_tools
from capella_ros_tools import exporter, importer, logger


@click.group()
@click.version_option(
    version=capella_ros_tools.__version__,
    prog_name="capella-ros-tools",
    message="%(prog)s %(version)s",
)
def cli() -> None:
    """Console script for Capella ROS Tools."""

    logging.basicConfig(level=logging.INFO)


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
    "license_header_path",
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
    *,
    input: str,
    model: capellambse.MelodyModel,
    layer: str,
    root: uuid.UUID,
    types: uuid.UUID,
    no_deps: bool,
    output: pathlib.Path,
    license_header_path: pathlib.Path | None,
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

    if dependency_json:
        if no_deps:
            raise click.UsageError(
                "--no-deps and --dependency-json are mutually exclusive"
            )
        dependencies = json.loads(dependency_json.read_text())
    elif no_deps:
        dependencies = {}
    else:
        dependencies = None

    if license_header_path is None:
        license_header = ""
    else:
        license_header = license_header_path.read_text()

    imp = importer.Importer(
        input,
        dependencies=dependencies,
        license_header=license_header,
        msg_description_regex=description_regex,
    )
    logger.info("Loaded %d packages", len(imp.messages.packages))

    yml = imp.to_yaml(root_uuid, **params)
    if output:
        logger.info("Writing declarative YAML to file %s", output)
        output.write_text(yml, encoding="utf-8")
    else:
        logger.info("Applying changes to model %r", model.name)
        decl.apply(model, io.StringIO(yml))
        logger.info("Saving model")
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
) -> None:
    """Export Capella data package to ROS messages."""
    if root:
        current_pkg = model.search("DataPkg").by_uuid(str(root))
    elif layer:
        current_pkg = getattr(model, layer).data_package
    else:
        raise click.UsageError("Either --root or --layer must be provided")

    exporter.export(current_pkg, output)  # type: ignore


if __name__ == "__main__":
    cli()
