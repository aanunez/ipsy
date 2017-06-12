#!/usr/bin/env python3

from collections import namedtuple, deque
from itertools import groupby
from functools import partial

# TODO Max patch size?
# TODO Prevent accidently writing EOF anywhere
# TODO Improve RLE algorithm
# TODO change Exceptions to warnings

HEADER_SIZE = 5
RECORD_OFFSET_SIZE = 3
RECORD_SIZE_SIZE = 2
RLE_DATA_SIZE = 1
MIN_PATCH = 14
MAX_UNPATCHED_SIZE = 2**24 # 16 MiB
MIN_COMPRESS = 4 # Compressing a size 4 record only saves 1 byte

ips_record = namedtuple('ips_record', 'offset size rle_size data')

class IpsyError(Exception):
    pass

def write_ips( fhpatch, records ):
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

def read_ips( fhpatch ):
    '''
    Read in an IPS file to a list of :class:`ips_record`

    :param fhpatch: File handler for IPS patch
    :returns: List of :class:`ips_record`

    If the file contains any RLE compressed records,
    they are automatically inflated.
    '''
    records = []
    if fhpatch.read(HEADER_SIZE) != b"PATCH":
        raise IpsyError(
            "IPS file missing header")
    for offset in iter(partial(fhpatch.read, RECORD_OFFSET_SIZE), b'EOF'):
        rle_size = 0
        size = fhpatch.read(RECORD_SIZE_SIZE)
        if (offset == b'') or (size == b''):
            raise IpsyError(
                "IPS file unexpectedly ended")
        offset = int.from_bytes( offset, byteorder='big' )
        size = int.from_bytes( size, byteorder='big' )
        if size == 0:
            rle_size = fhpatch.read(RECORD_SIZE_SIZE)
            rle_size = int.from_bytes( rle_size, byteorder='big' )
            if rle_size == 0:
                raise IpsyError(
                    "IPS file has record with both 0 size and 0 RLE size")
            data = fhpatch.read(RLE_DATA_SIZE)
            if data == b'':
                raise IpsyError(
                    "IPS file unexpectedly ended")
            data *= size
        else:
            data = fhpatch.read(size)
            if len(data) != size:
                raise IpsyError(
                    "IPS file unexpectedly ended")
        records.append( ips_record(offset, size, rle_size, data) )
    if fhpatch.read(1) != b'':
        raise IpsyError(
            "Data after EOF in IPS file")
    return records

def rle_compress( records ):
    '''
    Attempt to RLE compress a collection of IPS records.

    :param records: List of :class:`ips_record` to compress
    :returns: RLE compressed list of :class:`ips_record`
    '''
    rle = []
    for r in records:
        if (r.size < MIN_COMPRESS) or \
        not any([len(list(g)) >= MIN_COMPRESS for _,g in groupby(r.data)]):
            rle.append( r )
            continue
        offset, run = 0, b''
        for d,g in groupby(r.data):
            size = len(list(g))
            if size >= MIN_COMPRESS:
                if run:
                    o = r.offset+offset
                    rle.append( ips_record( o-len(run), len(run), 0, run) )
                rle.append( ips_record( o, 0, size, bytes([d])) )
                run = b''
            else:
                run = run + (bytes([d])*size)
            offset += size
        if run:
            rle.append( ips_record(r.offset+offset-len(run), len(run), 0, run) )
    return rle

def eof_check( fhpatch ):
    '''
    Reviews an IPS patch to insure it has only one EOF marker.

    :param fhpatch: File handler of IPS patch
    :returns: True if exactly one marker, else False
    '''
    check, counter = deque(maxlen=3), 0
    for val in iter(partial(fhpatch.read, 1), b''):
        check.append(val)
        if check == b'EOF':
            counter += 1
    return counter == 1

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
    ips = read_ips( fhpatch )
    for record in ips:
        fhdest.seek(record.offset)
        fhdest.write(record.data)
    return len(ips)
