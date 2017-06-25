#!/usr/bin/env python3

from collections import namedtuple, deque
from itertools import groupby
from functools import partial
from warnings import warn
from os import SEEK_CUR

# TODO Improve diff or RLE algorithm - src = 1 2 1 2 1 2 -> dest = 1 1 1 1 1 1
# TODO Improve IPS merge (check for dups)

RECORD_HEADER_SIZE = 5
RECORD_OFFSET_SIZE = 3
RECORD_SIZE_SIZE = 2
RECORD_RLE_DATA_SIZE = 1
MIN_PATCH = 14 # in bytes
MIN_RECORD = 6 # Min size of a record
MAX_UNPATCHED = 2**24 # 16 MiB
MIN_COMPRESS = 4 # Compressing a size 4 record only saves 1 byte
MAX_RECORD_SIZE = 2**16-1 # Max value held in 2 bytes

class ips_record( namedtuple('ips_record', 'offset size rle_size data') ):
    '''
    Data container for one record of an IPS file.

    :param offset: offset in first 3 bytes of the record, stored as int
    :param size: size in the next 2 bytes, stored as int
    :param rle_size: size in the next 2 bytes if previous was 0, stored as int
    :param data: bytes object of data with length size or rle_size
    '''
    pass

class IpsyError(Exception):
    '''
    Logged by :func:`ips_read` when IPS corruption is found.
    '''
    pass

def ips_write( fhpatch, records ):
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

def ips_read( fhpatch, EOFcontinue=False ):
    '''
    Read in an IPS file to a list of :class:`ips_record`

    :param fhpatch: File handler for IPS patch
    :param EOFcontinue: Continue processing until the real EOF
                        is found (last 3 bytes of file)
    :returns: List of :class:`ips_record`

    If the file contains any RLE compressed records,
    they are automatically inflated.
    '''
    records = []
    if fhpatch.read(RECORD_HEADER_SIZE) != b"PATCH":
        raise IpsyError(
            "IPS file missing header")
    for offset in iter(partial(fhpatch.read, RECORD_OFFSET_SIZE), b''):
        if offset == b'EOF':
            if EOFcontinue:
                if len(fhpatch.read(MIN_RECORD)) != MIN_RECORD:
                    break
                fhpatch.seek(-MIN_RECORD, SEEK_CUR)
            else:
                break
        size = fhpatch.read(RECORD_SIZE_SIZE)
        if (len(offset) != RECORD_OFFSET_SIZE) or (len(size) != RECORD_SIZE_SIZE):
            raise IpsyError(
                "IPS file unexpectedly ended")
        offset = int.from_bytes( offset, byteorder='big' )
        size = int.from_bytes( size, byteorder='big' )
        if size == 0:
            size = fhpatch.read(RECORD_SIZE_SIZE)
            size = int.from_bytes( size, byteorder='big' )
            if size == 0:
                warn("IPS file has record with both 0 size and 0 RLE size." + \
                    "Continuing to next record.")
                continue
            data = fhpatch.read(RECORD_RLE_DATA_SIZE)
            if data == b'':
                raise IpsyError(
                    "IPS file unexpectedly ended")
            data *= size
        else:
            data = fhpatch.read(size)
            if len(data) != size:
                raise IpsyError(
                    "IPS file unexpectedly ended")
        records.append( ips_record(offset, size, 0, data) )
    if fhpatch.read(1) != b'':
        warn("Data after EOF in IPS file. Truncating.")
    return records

def ips_merge( fhdst, *fhpatches ):
    '''
    Turns several IPS patches into one larger patch.
    Does not try to remove duplicate data written in the patches.

    :param fhdst: File Handler for resulting IPS file
    :param fhpatches: list of File Handlers for IPS files to merge
    '''
    record_collection = []
    for fh in fhpatches:
        records = ips_read( fh, EOFcontinue=True )
        record_collection += records
    ips_write( fhdst, record_collection )

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
                    rle.append( ips_record(o-len(run), len(run), 0, run) )
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
    check, counter, i = deque(maxlen=3), 0, 0
    for val in iter(partial(fhpatch.read, 1), b''):
        check.append(val)
        if b''.join(check) == b'EOF':
            counter += 1
    return (counter == 1)

def diff( fhsrc, fhdst, fhpatch=None, rle=False ):
    '''
    Diff two files, attempt RLE compression, and write the IPS patch to a file.

    :param fhsrc: File handler of orignal file
    :param fhdst: File handler of the patched file
    :param fhpatch: File handler for IPS file
    :param rle: True if RLE compression should be used

    Assumes: Both files are the same size.
    '''
    ips, patch_bytes  = [], b''
    for src_byte in iter(partial(fhsrc.read, 1), b''):
        dst_byte = fhdst.read(1)
        s = len(patch_bytes)
        if (src_byte == dst_byte) or (s == MAX_RECORD_SIZE):
            if s != 0:
                offset = fhdst.tell()-s-1
                if offset.to_bytes(RECORD_OFFSET_SIZE, byteorder='big') == b'EOF':
                    offset, s = offset-1, s+1
                    fhsrc.seek(offset)
                    patch_bytes = fhsrc.read(s)
                ips.append( ips_record(fhdst.tell()-s-1, s, 0, patch_bytes[:]) )
            patch_bytes = b''
        else:
            patch_bytes += dst_byte
    s = len(patch_bytes)
    if s != 0:
        ips.append( ips_record(fhdst.tell()-s, s, 0, patch_bytes[:]) )
    if len(ips) == 0:
        warn("No differances found in files")
    elif rle:
        records = rle_compress( records )
    if fhpatch:
        ips_write( fhpatch, records )
    return ips

def patch_from_records( fhdest, records ):
    '''
    Apply an list of :class:`ips_record` a file. Destructive processes.

    :param fhdest: File handler to-be-patched
    :param fhpatch: File handler of the patch

    :returns: Number of records applied by the patch
    '''
    for r in records:
        fhdest.seek(r.offset)
        fhdest.write(r.data)
    return len(records)

def patch( fhdest, fhpatch, EOFcontinue=False ):
    '''
    Apply an IPS patch to a file. Destructive processes.

    :param fhdest: File handler to-be-patched
    :param fhpatch: File handler of the patch
    :param EOFcontinue: Continue processing until the real EOF
                        is found (last 3 bytes of file)
    :returns: Number of records applied by the patch
    '''
    records = ips_read( fhpatch, EOFcontinue )
    return patch_from_records( fhdest, records )

