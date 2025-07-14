..
   Copyright DB InfraGO AG and contributors
   SPDX-License-Identifier: Apache-2.0

.. _howtos:

********
Examples
********

This section contains a collection of examples that demonstrate how to use the library.

Using the CLI
=============

Import ROS2 Messages:
---------------------
.. code-block:: bash

   python -m capella_ros_tools \
   import \
   -i tests/data/data_model/example_msgs \
   -m tests/data/empty_project_60 \
   -l la \
   --no-deps

Import ROS2 Messages from Git Repository:
-----------------------------------------
.. code-block:: bash

   python -m capella_ros_tools \
   import \
   -i git+https://github.com/DSD-DBS/dsd-ros-msg-definitions-oss \
   -m tests/data/empty_project_60 \
   -l la

Export Capella data package:
------------------------------------
.. code-block:: bash

   python -m capella_ros_tools \
   export \
   -m tests/data/melody_model_60 \
   -l la \
   -o tests/data/melody_msgs

Export Capella data package from Git Repository:
--------------------------------------------------------
.. code-block:: bash

   python -m capella_ros_tools \
   export \
   -m git+https://github.com/DSD-DBS/coffee-machine \
   -l oa \
   -o tests/data/coffee_msgs

.. note::
   When exporting Capella enumerations, if the enumeration literal values are not defined in the Capella model, the values will be assumed to be 0, 1, 2, 3, etc. and the value's type will be set to unit8.
