.. ipsy documentation master file, created by
   sphinx-quickstart on Sat Jun 10 13:19:21 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

ipsy documentation
==================

Ipsy is a tool for applying IPS (International/Internal Patch System) files. They are typically used for distributing emulator ROM changes as distributing the patched ROM would violate copyright law. IPS has a rather strait forward format expalined on the IPS File Format page.

**Using ipsy**

If you have to files 'game.rom' and 'patch_for_game.ips' you can patch the game by...
::

    ./ipsy.py patch ./game.rom ./patch_for_game.ips

This will generate a file named 'game_patched.rom'
If you want to generate a patch use...
::

    ./ipsy.py diff ./game.rom ./edited_game.ips

This will generate a file named 'patch.ips'

::

    usage: ipsy.py [-h] operation unpatched patch [output]

    Apply an IPS patch or Diff two files to generate a patch.

    positional arguments:
      operation   'Patch' or 'Diff'
      unpatched   The Orignal File
      patch       The IPS file (in Patch mode) or the already patched file (in
                  Diff mode)
      output      Name of resulting patch or patched file

    optional arguments:
      -h, --help  show this help message and exit


.. toctree::
   :maxdepth: 2

   api
   ips
