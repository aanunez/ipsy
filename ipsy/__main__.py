#!/usr/bin/env python3

from argparse import ArgumentParser
from os.path import splitext, getsize, basename
from shutil import copyfile
from sys import argv
from .ipsy import MIN_PATCH, MAX_UNPATCHED, patch, diff, merge

def make_copy( filename, unpatched ):
    if not filename:
        tmp = splitext( basename(unpatched) )
        filename = tmp[0] + "_patched" + tmp[1]
    copyfile(unpatched, filename)
    return filename

def name_patch( patchname, unpatched ):
    if not patchname:
        tmp = splitext( basename(unpatched) )
        patchname = "patch_" + tmp[0] + ".ips"
    return patchname

def parse_args():
    parser = ArgumentParser(description=
        'Apply an IPS patch, Diff two files to generate a patch, or Merge multiple IPS files.')
    subparsers = parser.add_subparsers(dest='option', help=
        'Options for Ipsy...')

    parser_patch = subparsers.add_parser('patch', help=
        'Apply a patch to an unpatched file.')
    parser_patch.add_argument('unpatched', help=
        'The unpatched file. ')
    parser_patch.add_argument('patch', help=
        'IPS file to apply.')
    parser_patch.add_argument('-eof', action='store_true', help=
        'Ignore "EOF" markers unless they are actually found at the end of the file.')

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
    parser_merge.add_argument('-d','--destination', default=None, help=
        'File that these patches are intended to be applied to. Providing this can, ' +\
        'greatly reduce the size of the resulting merged patch.')
    parser_merge.add_argument('patch', nargs='*', help=
        'List of IPS files.')

    parser.add_argument('-o','--output', default=None, help=
        'Name for the new file')

    return parser.parse_args()

def main():
    if len(argv) < 3:
        argv.append('-h')
    opts = parse_args()

    if opts.option == 'patch':
        if getsize(opts.patch) < MIN_PATCH:
            raise IOError("Patch is too small to be valid")
        if getsize(opts.unpatched) > MAX_UNPATCHED:
            raise IOError("IPS can only patch files under 2^24 bytes")
        copy = make_copy( opts.output, opts.unpatched )
        with open( copy, 'r+b') as fhdest, open( opts.patch, 'rb') as fhpatch:
            numb = patch( fhdest, fhpatch )
        print("Applied " + str(numb) + " records from patch.")

    if opts.option == 'diff':
        if getsize(opts.unpatched) != getsize(opts.patched):
            raise IOError("The two files are of differing size")
        patchfile = name_patch( opts.output, opts.unpatched )
        with open(opts.unpatched,'rb') as fhsrc, open(opts.patched,'rb') as fhdst,\
        open(patchfile,'wb') as fhpatch:
            records = diff( fhsrc, fhdst, fhpatch, opts.rle )
        print("Patch created, " + str(getsize(patchfile)) + " bytes, " + \
            str(len(records)) + " records.")

    if opts.option == 'merge':
        for ips_file in opts.patch:
            if getsize(ips_file) < MIN_PATCH:
                raise IOError("Patch " + ips_file + " is too small to be valid")
        patchfile = name_patch( opts.output, 'ipsy_merge' )
        try:
            fhips = [open(ips_file, 'rb') for ips_file in opts.patch]
            with open( patchfile, 'r+b' ) as fhdst:
                merge( fhdst, *fhips, opts.destination )
        finally:
            _ = [ips_file.close() for ips_file in fhips]
        print("Merged " + str( len(opts.patch) ) + " IPS files into one.")

if __name__ == "__main__":
    main()
