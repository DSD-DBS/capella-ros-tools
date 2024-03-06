..
   Copyright DB InfraGO AG and contributors
   SPDX-License-Identifier: Apache-2.0

.. _messages:

*******************
ROS2 Message Layout
*******************

The Capella ROS Tools API expects ROS2 messages to be organized in a specific way:

Class Definition
================
* A `.msg` file can contain one class definition.
* The comment at the top of the file followed by an empty line is added to the class description.
* **Inline Comments:** Comments on the same line as a property definition are directly added to that property's description.
* **Indented Comment Lines:** Comments on a line of their own but indented are added to the description of the last encountered property.
* **Block Comments:** Comments on a line of their own and not indented are added to the description of the next properties until an empty line and the block comment has been used.

.. literalinclude:: ../../tests/data/data_model/example_msgs/package1/msg/SampleClass.msg
  :language: python


Enum definition
===============
* A `.msg` file can contain multiple enum definitions.
* Multiple enum definitions are separated by an empty line.
* Enum names are determined based on the longest common prefix of all enum literals in the enum definition.
* If no common prefix exists, the enum name is derived from the file name (excluding the extension).
* Two or more enums must not have literal names without a common prefix.
* **Inline Comments:** Comments on the same line as an enum literal definition are directly added to the that enum literal's description.
* **Indented Comment Lines:** Comments on a line of their own but indented are added to the description of the last encountered enum literal.
* **Block Comments:** Comments on a line of their own and not indented are added to the description of the next/current enum definition until an empty line and the block comment has been used.

.. literalinclude:: ../../tests/data/data_model/example_msgs/package1/msg/SampleEnum.msg
  :language: python

Enum and Class Definition
=========================
* A `.msg` file can contain one class definition and multiple enum definitions.
* Enums without a common literal name prefix are named using the file name plus the suffix "Type".
* There can only be one or no enum whose literal names do not share a common prefix.
* Comments at the top of the file are added to the class description.
* **Inline Comments:** Comments on the same line as a property or enum literal are directly added to the description of that element.
* **Indented Comment Lines:** Comments on a line of their own but indented are added to the description of the last encountered property or enum literal.
* **Block Comments:** Comments on a line of their own and not indented are added to the descriptions of the next properties or added to the descriptions of the next/current enum until an empty line and the block comment has been used.

.. literalinclude:: ../../tests/data/data_model/example_msgs/package2/msg/SampleClassEnum.msg
  :language: python

Referencing enums
=================

In the Same File
----------------
*  In files that define a class along with enums, the class properties can reference enums defined in the same file. This can be achieved in two ways:

   * **Name Match:** The property name matches the enum name.
   * **Type Match:** The property type matches the enum literals type, in which case the updated enum name is derived from the file name plus the property name.

*  Name matching takes precedence over type matching.

.. literalinclude:: ../../tests/data/data_model/example_msgs/package2/msg/SampleClassEnum.msg
  :language: python

In another file
---------------
*  If a property definition references an enum in the comments, the property type is updated based on this reference.
*  The reference should follow either of the following formats:

   * **cf. <File Name>:** The enum name was derived from the file name (excluding the extension).
   * **cf. <File Name>, <Common Prefix>_XXX:** The enum name was derived from the longest common prefix of all enum literals in the definition.

.. literalinclude:: ../../tests/data/data_model/example_msgs/package1/msg/SampleEnum.msg
  :language: python

.. literalinclude:: ../../tests/data/data_model/example_msgs/package1/msg/SampleClass.msg
  :language: python