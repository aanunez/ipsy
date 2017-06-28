#!/usr/bin/env python3

from argparse import ArgumentParser, ArgumentTypeError
from shutil import copyfile
from sys import argv
from os import path, sep
from .ipsy import MIN_PATCH, MAX_UNPATCHED, patch, diff

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
    return patchname

def parse_args():
    parser = ArgumentParser(description=
        "Apply an IPS patch, Diff two files to generate a patch, or Merge multiple IPS files.")
    subparsers = parser.add_subparsers(dest='option', help=
        'Options for Ipsy...')

    parser_patch = subparsers.add_parser('patch', help=
        'Apply a patch to an unpatched file.')
    parser_patch.add_argument('unpatched', help=
        'The unpatched file. ')
    parser_patch.add_argument('patch', help=
        'IPS file to apply.')
    parser_patch.add_argument('-eof', action='store_true', help=
        "Ignore 'EOF' markers unless they are actually found at the end of the file.")

    parser_diff = subparsers.add_parser('diff', help=
        'Generate an IPS file by diffing the unpatched and patched versions.')
    parser_diff.add_argument('unpatched', help=
        'The orignal and unpatched file.')
    parser_diff.add_argument('patched', help=
        'The modified or already patched file.')
    parser_diff.add_argument('-rle', action='store_true', help=
        "Attempt to compress the IPS patch when performing a diff.")

    parser_merge = subparsers.add_parser('merge', help=
        'Combine several IPS files into one.')
    parser_merge.add_argument('patch', nargs='*', help=
        'List of IPS files.')

    parser.add_argument('output', default=None, nargs='?', help=
        'Name for the new file')

    return parser.parse_args()

def main():
    if len(argv) == 1:
        argv.append('-h')
    opts = parse_args()

    if opts.option == 'patch':
        if path.getsize(opts.patch) < MIN_PATCH:
            raise IOError("Patch is too small to be valid")
        if path.getsize(opts.unpatched) > MAX_UNPATCHED:
            raise IOError("IPS can only patch files under 2^24 bytes")
        copy = make_copy( opts.output, opts.unpatched )
        with open( copy, 'r+b') as fhdest:
            with open( opts.patch, 'rb') as fhpatch:
                numb = patch( fhdest, fhpatch )
        print("Applied " + str(numb) + " records from patch.")

    if opts.option == 'diff':
        if path.getsize(opts.unpatched) != path.getsize(opts.patch):
            raise IOError("The two files are of differing size")
        patchfile = name_patch( opts.output, opts.unpatched )
        with open( opts.unpatched, 'rb' ) as fhsrc:
            with open( opts.patch, 'rb' ) as fhdest:
                with open ( patchfile, 'wb' ) as fhpatch:
                    diff( fhsrc, fhdest )
        print("Patch created, " + str(path.getsize(patchfile))+ " bytes")

    if opts.option == 'merge':
        for ips_file in opts.patch:
            if path.getsize(ips_file) < MIN_PATCH:
                raise IOError("Patch " + ips_file + "is too small to be valid")
        patchfile = name_patch( opts.output, opts.patch[0] )
        fhips = []
        try:
            for ips_file in opts.patch:
                fhips.append( open(ips_file, 'r') )
            with open( patchfile, 'wb' ) as fhdst:
                ips_merge( fhdst, *fhips )
        finally:
            for ips_file in fhips:
                ips_file.close()
        print("Merged " + str( len(opts.patch) ) + " IPS files into one.")

if __name__ == "__main__":
    main()
