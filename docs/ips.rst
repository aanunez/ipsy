.. ipsy documentation master file, created by
   sphinx-quickstart on Sat Jun 10 13:19:21 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

IPS File Format
================================

IPS files consist of a header, a list of records, and a footer. All IPS files are big-endian. Due to fixed length of the offset value, IPS can't be used to patch a file larger that 2^24-1 bytes (16 MB). The minimum viable IPS file (1 record changing 1 byte of data) is 14 bytes in size.

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

+---------+---------------+-------------------------------------------------------------+
| Section | Size in Bytes | Description                                                 |
+=========+===============+=============================================================+
| Offset  | 3             | Zero index offset that the change should be applied at      |
+---------+---------------+-------------------------------------------------------------+
| Size    | 2             | Size of the follow 'data' section in bytes (See below if 0) |
+---------+---------------+-------------------------------------------------------------+
| Data    | size          | Data to be written                                          |
+---------+---------------+-------------------------------------------------------------+

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

