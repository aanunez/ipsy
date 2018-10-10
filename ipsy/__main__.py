#!/usr/bin/env python3

from argparse import ArgumentParser
from os.path import splitext, getsize, basename
from shutil import copyfile
from sys import argv
from .ipsy import MIN_PATCH, MAX_UNPATCHED, patch, diff, merge

def parse_args():
    parser = ArgumentParser(description=
        'Apply an IPS patch, Diff two files to generate a patch, or Merge multiple IPS files.',
        prog='ipsy')
    parser.add_argument('-v','--version', action='version', version='%(prog)s 0.3')
    subparsers = parser.add_subparsers(dest='option', help=
        'Options for Ipsy...')

    parser_patch = subparsers.add_parser('patch', help=
        'Apply a patch to an unpatched file.')
    parser_patch.add_argument('unpatched', help=
        'The unpatched file. ')
    parser_patch.add_argument('patch', nargs='+', help=
        'IPS file(s) to apply to the target. Each file will create its own rom.')
    parser_patch.add_argument('-eof', action='store_true', help=
        'Ignore "EOF" markers unless they are actually found at the end of the file.')
    parser_patch.add_argument('-o','--output', default=None, help=
        'Name for the new ROM file.')

    parser_diff = subparsers.add_parser('diff', help=
        'Generate an IPS file by diffing the original and modified versions.')
    parser_diff.add_argument('unpatched', help=
        'The orignal or unpatched file.')
    parser_diff.add_argument('patched', help=
        'The modified or already patched file.')
    parser_diff.add_argument('-norle', action='store_true', help=
        "Do not attempt to compress the patch via run length encoding.")
    parser_diff.add_argument('-o','--output', default=None, help=
        'Name for the new IPS file.')

    parser_merge = subparsers.add_parser('merge', help=
        'Combine several IPS files into one.')
    parser_merge.add_argument('-d','--destination', default=None, help=
        'The target file that these patches are intended to be applied to. ' + \
        'Providing this can greatly reduce the size of the resulting patch.')
    parser_merge.add_argument('patch', nargs='+', help=
        'List of IPS files to merge.')
    parser_merge.add_argument('-o','--output', default=None, help=
        'Name for the merged IPS file.')
        
    return parser.parse_args()

def main():
    argv += ['-h'] if len(argv) < 3 else []
    opts = parse_args()

    if opts.option == 'patch':
        if getsize(opts.patch[0]) < MIN_PATCH:
            raise IOError("Patch is too small to be valid")
        if getsize(opts.unpatched) > MAX_UNPATCHED:
            raise IOError("IPS can only patch files under 2^24 bytes")
        if (len(opts.unpatched) == 1) and opts.output:
            rom_names = [opts.output]
            copyfile(opts.unpatched[0], opts.output)
        else:
            rom_names = [splitext(patch)[0] + splittext(opts.unpatched)[-1] for patch in opts.patch]
            _ = [copyfile( opts.unpatched, rom_file ) for rom_file in rom_names]
        try:
            fhdst = [open( fn, 'r+b') for fn in rom_names]
            fhips = [open( fn, 'rb') for fn in opts.patch]
            for n,fh in enumerate(fhips):
                numb = patch( fhdest, fh )
                print("Applied " + str(numb) + " records from patch " + basename(opts.patch[n]))
        finally:
            _ = [file.close() for file in fhips]
            _ = [file.close() for file in fhdst]

    if opts.option == 'diff':
        if getsize(opts.unpatched) != getsize(opts.patched):
            raise IOError("The two files are of differing size")
        patchfile = opts.output if opts.output else splitext(opts.patched)[0] + "_patch.ips"
        with open(opts.unpatched,'rb') as fhsrc, open(opts.patched,'rb') as fhdst,\
        open(patchfile,'wb') as fhpatch:
            records = diff( fhsrc, fhdst, fhpatch, not opts.norle )
        print("Patch created, " + str(getsize(patchfile)) + " bytes, " + \
            str(len(records)) + " records.")

    if opts.option == 'merge':
        for ips_file in opts.patch:
            if getsize(ips_file) < MIN_PATCH:
                raise IOError("Patch " + ips_file + " is too small to be valid")
        patchfile = opts.output if opts.output else splitext(opts.patch[0])[0] + '_merged.ips'
        try:
            fhips = [open(ips_file, 'rb') for ips_file in opts.patch]
            with open( patchfile, 'w+b' ) as fhdst:
                merge( fhdst, *fhips, opts.destination )
        finally:
            _ = [ips_file.close() for ips_file in fhips]
        print("Merged " + str( len(opts.patch) ) + " IPS files into one.")

if __name__ == "__main__":
    main()
