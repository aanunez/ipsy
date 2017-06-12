#!/usr/bin/env python3

from argparse import ArgumentParser, ArgumentTypeError
from shutil import copyfile
from sys import argv
from os import path

def operation_type( string ):
    if string.lower() in ['patch','diff']:
        return string.lower()
    raise ArgumentTypeError(
        string + "is not a valid option")

def make_copy( filename, unpatched ):
    dot = unpatched.rfind('.',unpatched.find('/'))
    if filename:
        pass
    elif dot == -1:
        filename = unpatched + "_patched"
    else:
        filename = unpatched[:dot] + "_patched" + unpatched[dot:]
    copyfile(unpatched, filename)
    return filename

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
    return parser.parse_args()

def main(args=None):
    if args is None:
        args = argv[1:]
    opts = parse_args()

    if opts.operation == 'patch':
        assert(path.getsize(opts.patch) > MIN_PATCH), \
            "Patch is too small to be valid"
        assert(path.getsize(opts.unpatched) < MAX_UNPATCHED_SIZE), \
            "IPS can only patch files under 2^24 bytes"
        copy = make_copy( opts.output, opts.unpatched )
        with open( copy, 'r+b') as fhdest:
            with open( opts.patch, 'rb') as fhpatch:
                numb = patch( fhdest, fhpatch )
        print("Applied " + str(numb) + " records from patch.")

    if opts.operation == 'diff':
        assert(path.getsize(opts.unpatched) == path.getsize(opts.patch)), \
            "The two files are of differing size"
        patchfile = opts.output if opts.output else "patch.ips"
        with open( opts.unpatched, 'rb' ) as fhsrc:
            with open( opts.patch, 'rb' ) as fhdest:
                records = diff( fhsrc, fhdest )
                if opts.rle:
                    records = rle_compress( records )
        with open ( patchfile, 'wb' ) as fhpatch:
            write_ips( fhpatch, records )
        if eof_check( patchfile ):
            print("Patch created " + str(path.getsize(patchfile))+ " bytes")
        else:
            print("Multiple EOFs found in resulting patch.\n" + \
                "This will need to be addressed by the developer.")

if __name__ == "__main__":
    main()
