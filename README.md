# ipsy

Ipsy is a tool for applying IPS (International/Internal Patch System) files. They are typically used for distributing emulator ROM changes as distributing the patched ROM would violate copyright law.

Please see the [readthedocs](https://ipsy.readthedocs.io/en/stable/) page for more information.

You can install ipsy-0.2 via pypi `pip3 install ipsy`

## To-do list

* Improve diff or RLE algorithm. Example: src = 1 2 1 2 1 2 -> dest = 1 1 1 1 1 1 . Currently the patch generated would be wastefull.

* Add support for [UPS](http://fileformats.archiveteam.org/wiki/UPS_(binary_patch_format)) and [BPS](https://github.com/aanunez/ipsy/blob/master/docs/bps_spec/bps_spec.md). 
