Ipsy's documentation
================================

Ipsy is a tool for applying IPS (International/Internal Patch System) files. They are typically used for distributing emulator ROM changes as distributing the patched ROM would violate copyright law. IPS has a rather strait forward format expalined below.

|

Using ipsy
==========

You should only install this using sudo if you have reviewed the source. You can run Ipsy without installing by passing it into python with the '-m' flag from the root directory of the package.

::

    python3 -m ipsy [Ipsy Arguments]

Install as you would any other python program. You shouldn't use `sudo` to install Ipsy unless you have reviewed the source code.
::

    pip3 install --user .

Ipsy has three major options: Patch, Diff, and Merge.

If you have to files 'game.rom' and 'patch_for_game.ips' you can patch the game.
::

    ipsy patch ./game.rom ./patch_for_game.ips -o new_rom

This will generate a file named 'new_rom' or, if no output name is given, 'game_patched.rom'. The 'o' flag always supersedes any name that might be assigned by Ipsy regardless of the operation.

If you want to generate a patch use...
::

    ipsy diff ./game.rom ./edited_game.ips

This will generate a file named 'patch.ips'

When diffing you can also enable Run Length Encoding (RLE)
::

    ipsy diff ./game.rom ./edited_game.ips -rle

RLE finds groups of edits where the same value is written is succession and replaces them with the value and the number of times that value should be written.

Lastly, you can merge multiple IPS files using the merge option
::

    ipsy merge patchOne patchTwo patchThree patchFour

Results in a single file named after the first patch.

Ipsy's help output:
::

    usage: ipsy [-h] {patch,diff,merge} ... [output]

    Apply an IPS patch, Diff two files to generate a patch, or Merge multiple IPS
    files.

    positional arguments:
      {patch,diff,merge}  Options for Ipsy...
        patch             Apply a patch to an unpatched file.
        diff              Generate an IPS file by diffing the unpatched and
                          patched versions.
        merge             Combine several IPS files into one.
      output              Name for the new, patched, file.

    optional arguments:
      -h, --help          show this help message and exit

|

Ipsy API
========

.. automodule:: ipsy
   :members:

|

IPS File Format
===============

IPS files consist of a header, a list of records, and a footer. All IPS files are big-endian. Due to fixed length of the offset value, IPS files can't be used to patch a target larger that 2^24-1 bytes (16 MB). The minimum viable IPS file (1 record changing 1 byte of data) is 14 bytes in size. There are a handfull of concerns with the format. A literal 'EOF' marker is used that is intended to be found instead of an offset value, however if the offset value is RAM address 0x454f46 then we have a problem. Ipsy, and most differs, resolves this by checking the offset and, if needed, decriments it while increamenting the size of the record and pre-appending the previous byte's value to data.

+------------+---------------+----------------------------------------------------------------+
| Section    | Size in Bytes | Description                                                    |
+============+===============+================================================================+
| Header     | 5             | String literal 'PATCH' (Hex: 50 41 54 43 48)                   |
+------------+---------------+----------------------------------------------------------------+
| Record(s)  | See Below     | Repeatable section that contains describes a change to be made |
+------------+---------------+----------------------------------------------------------------+
| Footer     | 3             | String literal 'EOF' (Hex: 45 4f 46)                           |
+------------+---------------+----------------------------------------------------------------+

Each record has the format ...

+---------+---------------+--------------------------------------------------------+
| Section | Size in Bytes | Description                                            |
+=========+===============+========================================================+
| Offset  | 3             | Zero index offset that the change should be applied at |
+---------+---------------+--------------------------------------------------------+
| Size    | 2             | Size of the 'data' section in bytes (See below if 0)   |
+---------+---------------+--------------------------------------------------------+
| Data    | size          | Data to be written                                     |
+---------+---------------+--------------------------------------------------------+

There is one exception to the format of a record. Records with size 0 are Run Length Encoded (RLE). This means that the record represents a one byte value that is to be written many times starting at the offset. The format for an RLE Record is below.

+----------+---------------+--------------------------------------------------------+
| Section  | Size in Bytes | Description                                            |
+==========+===============+========================================================+
| Offset   | 3             | Zero index offset that the change should be applied at |
+----------+---------------+--------------------------------------------------------+
| Size     | 2             | 0 (See above if not)                                   |
+----------+---------------+--------------------------------------------------------+
| RLE_Size | 2             | Number of times to repeat the below one-byte value     |
+----------+---------------+--------------------------------------------------------+
| Data     | 1             | Value to be repeated                                   |
+----------+---------------+--------------------------------------------------------+


.. toctree::
   :hidden:
   :maxdepth: 2

|

.. Indices and tables
   ==================

   * :ref:`genindex`
   * :ref:`modindex`
   * :ref:`search`
