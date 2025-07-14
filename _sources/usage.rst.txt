..
   Copyright DB InfraGO AG and contributors
   SPDX-License-Identifier: Apache-2.0

.. _usage:

*****
Usage
*****

This section describes how to use the Capella ROS Tools CLI.

Import ROS2 Messages:
----------------------
.. code-block:: bash

   python -m capella_ros_tools import -i <INPUT> -m <MODEL> -l <LAYER> -o <OUTPUT> --no-deps

*  **-i/--input**, path to folder with .msg files.
*  **-m/--model**, path to the Capella model.
*  **-l/--layer**, layer to import the messages to.
*  **-r/--root**, UUID of the root package to import the messages to.
*  **-t/--type**, UUID of the types package to import the generated data types to.
*  **--no-deps**, flag to disable import of ROS2 dependencies (e.g. std_msgs)
*  **-o/--output**, path to output decl YAML.

Export Capella Model (experimental):
------------------------------------
.. code-block:: bash

   python -m capella_ros_tools export -m <MODEL> -l <LAYER> -o <OUTPUT>

* **-m/--model**, path to the Capella model.
* **-l/--layer**, layer to export the messages from.
* **-r/--root**, UUID of the root package to export the messages from.
* **-o/--output**, path to output folder.
