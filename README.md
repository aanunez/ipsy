# ipsy

Ipsy is a tool for applying IPS (International/Internal Patch System) files. They are typically used for distributing emulator ROM changes as distributing the patched ROM would violate copyright law.

Please see the [readthedocs](http://ipsy.readthedocs.io/en/latest/) page for more information.

You can install ipsy-0.2 via pypi `pip3 install ipsy`

## To-do list

* Make real tests

* Improve diff or RLE algorithm. Example: src = 1 2 1 2 1 2 -> dest = 1 1 1 1 1 1 . Currently the patch generated would be wastefull.

* EOF checking is only in data segment right now, check elsewhere too, remove the check in main when you do.

* Add support for [UPS](http://fileformats.archiveteam.org/wiki/UPS_(binary_patch_format)) and [BPS](https://raw.githubusercontent.com/aanunez/ipsy/master/docs/bps_spec/bps_spec.html)
