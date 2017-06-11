#!/usr/bin/env python3

from argparse import ArgumentParser, ArgumentTypeError
from collections import namedtuple
from itertools import groupby
from functools import partial
from shutil import copyfile
from os import path

# TODO Max patch size?
# TODO Check that we don't accidently write EOF anywhere
# TODO check for all zero (bad) records in read

HEADER_SIZE = 5
RECORD_OFFSET_SIZE = 3
RECORD_SIZE_SIZE = 2
RLE_DATA_SIZE = 1
MIN_PATCH = 14
MAX_UNPATCHED_SIZE = 2**24 # 16 MiB
MIN_SIZE_TO_COMPRESS = 4 # Compressing a size 4 record only saves 1 byte

ips_record = namedtuple('ips_record', 'offset size rle_size data')

def write_ips_file( fhpatch, records ):
    '''
    Writes out a list of :class:`ips_record` to a file

    :param fhpatch: File handler of the new patch file
    :param records: List of :class:`ips_record`
    '''
    fhpatch.write(b"PATCH")
    for r in records:
        fhpatch.write( (r.offset).to_bytes(RECORD_OFFSET_SIZE, byteorder='big') )
        fhpatch.write( (r.size).to_bytes(RECORD_SIZE_SIZE, byteorder='big') )
        fhpatch.write( r.data )
    fhpatch.write(b"EOF")

def read_ips_file( fhpatch ):
    '''
    Read in an IPS file to a list of :class:`ips_record`

    :param fhpatch: File handler for IPS patch
    :returns: List of :class:`ips_record`
    '''
    records = []
    assert(fhpatch.read(HEADER_SIZE) == b"PATCH"), "IPS file missing header"
    try:
        for offset in iter(partial(fhpatch.read, RECORD_OFFSET_SIZE), b'EOF'):
            rle_size = 0
            if offset == b'':
                raise RuntimeError
            offset = int.from_bytes(offset, byteorder='big' )
            size = int.from_bytes( fhpatch.read(RECORD_SIZE_SIZE), byteorder='big' )
            if size == 0:
                rle_size = int.from_bytes( fhpatch.read(RECORD_SIZE_SIZE), byteorder='big' )
                data = fhpatch.read(RLE_DATA_SIZE)
                data *= size
            else:
                data = fhpatch.read(size)
            records.append( ips_record(offset, size, rle_size, data) )
    except:
        raise RuntimeError("IPS file unexpectedly ended")
    if fhpatch.read(1):
        raise RuntimeError("Data after EOF in IPS file")
    return records

def rle_compress( records ):
    '''
    Attempt to RLE compress a collection of IPS records.

    :param records: List of :class:`ips_record` to compress
    :returns: RLE compressed list of :class:`ips_record`
    '''
    rle = []
    for r in records:
        if (r.size < MIN_SIZE_TO_COMPRESS) or \
            not any([len(list(g)) >= MIN_SIZE_TO_COMPRESS for _,g in groupby(r.data)]):
            rle.append( r )
            continue
        offset, run = 0, b''
        for d,g in groupby(r.data):
            size = len(list(g))
            if size >= MIN_SIZE_TO_COMPRESS:
                if run:
                    rle.append( ips_record(r.offset+offset-len(run), len(run), 0, run) )
                rle.append( ips_record(r.offset+offset, 0, size, bytes([d])) )
                run = b''
            else:
                run = run + (bytes([d])*size)
            offset += size
        if run:
            rle.append( ips_record(r.offset+offset-len(run), len(run), 0, run) )
    return rle

def diff( fhsrc, fhdst ):
    '''
    Diff two files to generate a collection of IPS records.

    :param fhsrc: File handler of orignal file
    :param fhdst: File handler of the patched file
    :returns: List of :class:`ips_record`

    Assumes: Both files are the same size.
    '''
    ips, patch_bytes, size = [], b'', 0
    for src_byte in iter(partial(fhsrc.read, 1), b''):
        dst_byte = fhdst.read(1)
        if src_byte == dst_byte:
            s = len(patch_bytes)
            if s != 0:
                ips.append( ips_record(fhdst.tell()-s-1, s, 0, patch_bytes[:]) )
            patch_bytes = b''
        else:
            patch_bytes += dst_byte
    s = len(patch_bytes)
    if s != 0:
        ips.append( ips_record(fhdst.tell()-s, s, 0, patch_bytes[:]) )
    return ips

def patch( fhdest, fhpatch ):
    '''
    Apply an IPS patch to a file. Destructive processes.

    :param fhdest: File handler to-be-patched
    :param fhpatch: File handler of the patch
    :returns: Number of records applied by the patch

    Assumes: Patch file is at least 14 bytes long.
    '''
    ips = read_ips_file( fhpatch )
    for record in ips:
        fhdest.seek(record.offset)
        fhdest.write(record.data)
    return len(ips)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Script functions below

def operation_type( string ):
    if string.lower() in ['patch','diff']:
        return string.lower()
    raise ArgumentTypeError(string + "is not a valid option")

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
    parser = ArgumentParser(description="Apply an IPS patch or Diff two files to generate a patch.")
    parser.add_argument('operation', type=operation_type, help="'Patch' or 'Diff'")
    parser.add_argument('unpatched', help="The Orignal File")
    parser.add_argument('patch', help="The IPS file (in Patch mode) or the already patched file (in Diff mode)")
    parser.add_argument('output', default='', nargs='?', help="Optional name of resulting patch or patched file")
    parser.add_argument('-rle', help='Attempt to compress the IPS patch when performing a diff. Ignored when patching.', action='store_true')
    return parser.parse_args()

def main():
    opts = parse_args()

    if opts.operation == 'patch':
        assert(path.getsize(opts.patch) > MIN_PATCH), "Patch is too small to be valid"
        assert(path.getsize(opts.unpatched) < MAX_UNPATCHED_SIZE), "IPS can only patch files under 2^24 bytes"
        copy = make_copy( opts.output, opts.unpatched )
        with open( copy, 'r+b') as fhdest:
            with open( opts.patch, 'rb') as fhpatch:
                numb = patch( fhdest, fhpatch )
        print("Applied " + str(numb) + " records from patch.")

    if opts.operation == 'diff':
        assert(path.getsize(opts.unpatched) == path.getsize(opts.patch)), "The two files are of differing size"
        patchfile = opts.output if opts.output else "patch.ips"
        with open( opts.unpatched, 'rb' ) as fhsrc:
            with open( opts.patch, 'rb' ) as fhdest:
                records = diff( fhsrc, fhdest )
                if opts.rle:
                    records = rle_compress( records )
        with open ( patchfile, 'wb' ) as fhpatch:
            write_ips_file( fhpatch, records )
        print("Patch created " + str(path.getsize(patchfile))+ " bytes")

if __name__ == "__main__":
    main()

