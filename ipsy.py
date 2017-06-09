#!/usr/bin/env python3

from collections import namedtuple
from shutil import copyfile

# TODO check max sizes
# TODO diff
# TODO Support compression

HEADER_SIZE = 5
RECORD_OFFSET_SIZE = 3
RECORD_SIZE_SIZE = 2

ips_record = namedtuple('ips_record', 'offset' 'size' 'data')

def write_ips_file( fhpatch, records ):
    fhpatch.write(b"PATCH")
    for r in records:
        fhpatch.write( (r.offset).to_bytes(RECORD_OFFSET_SIZE, byteorder='big') )
        fhpatch.write( (r.size).to_bytes(RECORD_SIZE_SIZE, byteorder='big') )
        fhpatch.write( data )
    fhpatch.write(b"EOF")

def read_ips_file( fhpatch ):
    records = []

    try:
        header = fh.read(HEADER_SIZE)
    except:
        raise IOError("IPS file missing header")
    assert(header == "PATCH"), "IPS file missing header"

    try:
        while True:
            offset = int.from_bytes( fh.read(RECORD_OFFSET_SIZE), byteorder='big' )
            if offset == "EOF":
                break
            size = int.from_bytes( fh.read(RECORD_SIZE_SIZE), byteorder='big' )
            data = fh.read(size)
            records.append( ips_record(offset, size, data) )
    except:
        raise IOError("IPS file unexpectedly ended")

    if fh.read(1):
        raise IOError("Data after EOF in IPS file")

    return records

def diff( fhsrc, fhdest ):
    records = []

    return records

def patch( fhdest, fhpatch ):
    ips = read_ips_file( fhpatch )

    try:
        for record in ips:
            fhdest.seek(record.offset)
            fhdest.write(record.data)
    except:
        raise IOError("The patch has made an illegal access to an offest that doesn't exist")

def operation_type(string):
    if string.lower() in ['patch','diff']:
        return string.lower()
    raise argparse.ArgumentTypeError(string + "is not a valid option")

def parse_args():
    parser = ArgumentParser(description="Does a thing")
    parser.add_argument('operation', type=operation_type, help="Patch or Diff")
    parser.add_argument('unpatched', type=file, help="The Orignal File")
    parser.add_argument('patch', type=file, help="The IPS file (in Patch mode) or the already patched file (in Diff mode)")
    parser.add_argument('output', nargs='?', help="Name of resulting patch or patched file")
    return parser.parse_args()

def main():
    opts = parse_args()

    if opts.operation == 'patch':
        input_copy = opts.output if opts.output else "patched_" + opts.input
        copyfile(opts.unpatched, input_copy)

        with open( input_copy, 'w+') as fhdest:
            with open( opts.patch, 'rb') as fhpatch:
                patch( fhdest, fhpatch )

    if opts.operation == 'diff':
        patch = opts.output if opts.ouput else "patch.ips"

        with open( opts.unpatched, 'rb') as fhsrc:
            with open( opts.patch, 'rb') as fhdest:
                records = diff( fhsrc, fhdest )

        with open ( patch, 'wb' ) as fhpatch:
            write_ips_file( fhpatch, records )


if __name__ == "__main__":
    main()

