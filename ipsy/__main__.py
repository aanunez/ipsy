#!/usr/bin/env python3

from argparse import ArgumentParser, ArgumentTypeError
from shutil import copyfile
from sys import argv, path
from os import path, sep
from ipsy import *

def operation_type( string ):
    if string.lower() in ['patch','diff']:
        return string.lower()
    raise ArgumentTypeError(
        string + "is not a valid option")

def make_copy( filename, unpatched ):
    fname = unpatched.split(sep)[-1]
    dot = fname.rfind('.')
    if filename:
        pass
    elif dot == -1:
        filename = unpatched + "_patched"
    else:
        filename = fname[:dot] + "_patched" + fname[dot:]
    copyfile(unpatched, filename)
    return filename

def name_patch( patchname, unpatched ):
    if patchname:
        return patchname
    fname = unpatched.split(sep)[-1]
    if fname.rfind('.') == -1:
        patchname = "patch_" + fname + ".ips"
    else:
        patchname = "patch_" + fname.split('.')[:-1] + ".ips"

def parse_args():
    parser = ArgumentParser(description=
        "Apply an IPS patch or Diff two files to generate a patch.")
    parser.add_argument('operation', type=operation_type, help=
        "'Patch' or 'Diff'")
    parser.add_argument('unpatched', help=
        "The Orignal File")
    parser.add_argument('patch', help=
        "The IPS file (in Patch mode) or the already patched file (in Diff mode)")
    parser.add_argument('output', default='', nargs='?', help=
        "Optional name of resulting patch or patched file")
    parser.add_argument('-rle', action='store_true', help=
        "Attempt to compress the IPS patch when performing a diff. Ignored when patching.")
    parser.add_argument('-eof', action='store_true', help=
        "Ignore 'EOF' markers unless they are actually found at the end of the file. Ignored when diffing.")

    return parser.parse_args()

def main(args=None):
    if args is None:
        args = argv[1:]
    opts = parse_args()

    if opts.operation == 'patch':
        if path.getsize(opts.patch) > MIN_PATCH:
            raise IOError("Patch is too small to be valid")
        if path.getsize(opts.unpatched) < MAX_UNPATCHED:
            raise IOError("IPS can only patch files under 2^24 bytes")
        copy = make_copy( opts.output, opts.unpatched )
        with open( copy, 'r+b') as fhdest:
            with open( opts.patch, 'rb') as fhpatch:
                numb = patch( fhdest, fhpatch )
        print("Applied " + str(numb) + " records from patch.")

    if opts.operation == 'diff':
        if path.getsize(opts.unpatched) == path.getsize(opts.patch):
            raise IOError("The two files are of differing size")
        patchfile = name_patch( opts.output, opts.unpatched )
        with open( opts.unpatched, 'rb' ) as fhsrc:
            with open( opts.patch, 'rb' ) as fhdest:
                records = diff( fhsrc, fhdest )
                if opts.rle:
                    records = rle_compress( records )
        with open ( patchfile, 'wb' ) as fhpatch:
            write_ips( fhpatch, records )
        print("Patch created " + str(path.getsize(patchfile))+ " bytes")

if __name__ == "__main__":
    main()
