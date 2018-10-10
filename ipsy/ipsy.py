#!/usr/bin/env python3

from collections import namedtuple
from itertools import groupby
from functools import partial
from warnings import warn
from os import SEEK_CUR
from io import BytesIO

# For 0.3 release
# TODO Improve diff or RLE algorithm - src = 1 2 1 2 1 2 -> dest = 1 1 1 1 1 1

RECORD_HEADER_SIZE = 5
RECORD_OFFSET_SIZE = 3
RECORD_SIZE_SIZE = 2
RECORD_RLE_DATA_SIZE = 1
MIN_PATCH = 14            # Header + Footer + Min_Record
MIN_RECORD = 6            # Minimum viable size of a record
MIN_COMPRESS = 4          # Compressing a size 4 record only saves 1 byte
MAX_UNPATCHED = 2**24     # 16 MiB, largest value we can offset to
MAX_RECORD_SIZE = 2**16-1 # Max value held in 2 bytes

class IpsRecord( namedtuple('IpsRecord', 'offset size rle_size data') ):
    '''
    Data container for one record of an IPS file.

    :param offset: offset in first 3 bytes of the record, stored as int
    :param size: size in the next 2 bytes, stored as int
    :param rle_size: size in the next 2 bytes if previous was 0, stored as int
    :param data: bytes object of data with length 'size' or 'rle_size'
    '''

    def last_byte(self):
        '''
        Calculate the last byte written to when this record is applied to a file.

        :returns: offset of the last byte written to.
        '''
        return self.offset + self.size + self.rle_size

    def inflate(self):
        '''
        Inflate the record if it is currently RLE compressed.

        :returns: self or inflated :class:`IpsRecord`
        '''
        if not self.rle_size:
            return self
        return IpsRecord(self.offset, self.rle_size, 0, self.data*self.rle_size)

    def compress(self):
        '''
        Attempts to RLE compress the record into a single, smaller, record. May
        split the record to multiple.

        :returns: List of: self (no compression) or compressed :class:`IpsRecord`
        '''
        if not self.size or len(self.data) < MIN_COMPRESS or\
           not any(i>=MIN_COMPRESS for i in [len(list(g)) for _,g in groupby(self.data)]):
            return [self]
        if len([len(list(g)) for _,g in groupby(self.data)]) == 1:
            return [IpsRecord(self.offset, 0, len(self.data), self.data[0])]
        offset, run, rle = 0, b'', []
        for d,g in groupby(self.data):
            size = len(list(g))
            if size >= MIN_COMPRESS:
                totaloff = self.offset+offset
                if run:
                    rle.append(IpsRecord(totaloff-len(run), len(run), 0, run))
                    run = b''
                rle.append(IpsRecord( totaloff, 0, size, bytes([d])))
            else:
                run += (bytes([d])*size)
            offset += size
        if run:
            rle.append(IpsRecord(self.offset+offset-len(run), len(run), 0, run))
        return rle

    def flatten(self):
        base = (self.offset).to_bytes(RECORD_OFFSET_SIZE, byteorder='big') +\
               (self.size).to_bytes(RECORD_SIZE_SIZE, byteorder='big')
        if self.size:
            return base + self.data
        return base + (self.rle_size).to_bytes(RECORD_SIZE_SIZE, byteorder='big') + self.data

class IpsyError(Exception):
    '''
    Logged by :func:`ips_read` when IPS corruption is found.
    '''
    pass
    
def write( fhpatch, records ):
    '''
    Writes out a list of :class:`IpsRecord` to a file

    :param fhpatch: File handler of the new patch file
    :param records: List of :class:`IpsRecord`
    '''
    fhpatch.write(b"PATCH")
    for r in records:
        fhpatch.write( r.flatten() )
    fhpatch.write(b"EOF")

def read( fhpatch, EOFcontinue=False ):
    '''
    Read in an IPS file to a list of :class:`IpsRecord`

    :param fhpatch: File handler for IPS patch
    :param EOFcontinue: Continue processing until the real EOF
                        is found (last 3 bytes of file)
    :returns: List of :class:`IpsRecord`
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
            records.append(IpsRecord(offset, 0, size, data))
        else:
            data = fhpatch.read(size)
            if len(data) != size:
                raise IpsyError(
                    "IPS file unexpectedly ended")
            records.append(IpsRecord(offset, size, 0, data))
    if fhpatch.read(1) != b'':
        warn("Data after EOF in IPS file. Truncating.")
    return records

def merge( fhpatch, *fhpatches, path_dst=None ):
    '''
    Turns several IPS patches into one larger patch.
    The order that the patches are applied in is preserved.
    If the destination file is provided then further
    simplifications can be made.

    :param fhpatch: File Handler for resulting IPS file
    :param fhpatches: list of File Handlers for IPS files to
                      merge
    :param path_dst: Path to file that these patches are
                     intended to be used on.
    '''
    records = [i for s in map(lambda fh:read( fh, EOFcontinue=True ), fhpatches[:-1]) for i in s]
    if path_dst:
        records = cleanup_records( records, path_dst )
    write( fhpatch, records )

def cleanup_records( ips_records, path_dst ):
    '''
    Removes useless records and combines records when possible.

    :param ips_records: List of :class:`IpsRecord`
    :param path_dst: Path to file that these patches are intended
                     to be used on.
    :returns: List of :class:`IpsRecord`, simplified where
              possible.
    '''
    with open(path_dst, 'r') as fh:
        dstfh = BytesIO(fh.read())
    srcfh = BytesIO(dstfh.read())
    patch_from_records( dstfh, ips_records )
    return diff( srcfh, dstfh, fhpatch=None, rle=True )

def rle_compress( records ):
    '''
    Attempt to RLE compress a collection of IPS records.

    :param records: List of :class:`IpsRecord` to compress
    :returns: RLE compressed list of :class:`IpsRecord`
    '''
    # TODO Improve this by compresing RLE records that sandwich a run of the RLE
    # data. Might be more trouble than its worth.  
    return [i for s in map(lambda r:r.compress(),records) for i in s]

def diff( fhsrc, fhdst, fhpatch=None, rle=False ):
    '''
    Diff two files, attempt RLE compression, and write the IPS patch to a file.
    Assumes both files are the same size.

    :param fhsrc: File handler of orignal file
    :param fhdst: File handler of the patched file
    :param fhpatch: File handler for IPS file
    :param rle: True if RLE compression should be used
    
    :returns: List of :class:`IpsRecord` that were written to the file.
    '''
    records, patch_bytes  = [], b''
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
                records.append(IpsRecord(fhdst.tell()-s-1, s, 0, patch_bytes[:]))
            patch_bytes = b''
        else:
            patch_bytes += dst_byte
    s = len(patch_bytes)
    if s != 0:
        records.append(IpsRecord(fhdst.tell()-s, s, 0, patch_bytes[:]))
    if len(records) == 0:
        warn("No differences found in files")
    if rle:
        records = rle_compress( records )
    if fhpatch:
        write( fhpatch, records )
    return records

def patch_from_records( fhdest, records ):
    '''
    Apply an list of :class:`IpsRecord` to a file. Destructive processes.

    :param fhdest: File handler to-be-patched
    :param fhpatch: File handler of the patch

    :returns: Number of records applied by the patch
    '''
    for r in records:
        fhdest.seek(r.offset)
        fhdest.write(r.inflate().data)
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
    return patch_from_records( fhdest, read( fhpatch, EOFcontinue ) )
    
#from zlib import crc32
#from shutil import copyfileobj
#from os import SEEK_END, SEEK_SET
#from tempfile import TemporaryFile
#
#class UPS:
#
#    RECORD_HEADER_SIZE = 4
#
#    class UpsRecord( namedtuple('UpsRecord', 'skip xor') ):
#        pass
#        
#    def crc_check( fhpatch, fhsrc, fhdst ):
#        crcSrc, crcDst = crc32(fhsrc), crc32(fhdst)
#        crcPat = crc32(fhpatch, ignorelast32=True)
#        fhpatch.seek(-12, SEEK_END)
#        fcrcSrc, fcrcDst, fcrcPat = list(iter(partial(fhpatch.read, 4), b''))
#        # Do compare
#        
#    def read( fhpatch ):
#        if fhpatch.read(RECORD_HEADER_SIZE) != b"UPS1":
#            raise IpsyError(
#                "UPS file missing header")
#        fhpatch.seek(-12, SEEK_END)
#        list(iter(partial(fhpatch.read, 4), b''))
#        ## OTher stuff
#
#    def varaible_int_read( fhpatch ):
#        result, shift = 0, 0
#        for chunk in iter(partial(fhpatch.read, 1), b''):
#            chunk = int.from_bytes( chunk, byteorder='big' )
#            if chunk & 0x80:
#                result += (chunk & 0x7f) << shift
#                break
#            result += (chunk | 0x80) << shift
#            shift += 7
#        return result
#
#    def crc32( fh, ignorelast32=False ):
#        fh = strip_crc32(fh) if ignorelast32 else fh
#        out = 0
#        for chunk in iter(partial(fh.read, 16384), b''):
#            out = zlib.crc32(chunk, out)
#        return out & 0xFFFFFFFF
#
#    # This is a bad idea for big files
#    def strip_crc32( fh ):
#        copyfh = TemporaryFile()
#        copyfileobj(fh, copyfh, size)
#        copyfh.seek(-4, SEEK_END)
#        copyfh.truncate()
