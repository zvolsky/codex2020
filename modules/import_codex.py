# -*- coding: utf-8 -*-

"""
Make possible read from dbf's with codepage unsupported by modules dbf and codecs (like 895 cz Kamenicky)


import dbf
from dbf_read_iffy import fix_init, fix_895

fix_init(dbf)
t = dbf.Table('autori.dbf')
t.open('read-only')
for record in t:
    print fix_895(record.autor)
t.close()
"""

try:
    from __future__ import unicode_literals
except ImportError:
    pass

def fix_620(txt):
    """
    convert 620 pl Mazovia if imported as 437

    NOT IMPLEMENTED YET
    """

    # TODO: implement Mazovia
    return fix_iffy(txt, {})

def fix_895(txt):
    """
    convert 895 cz Kamenicky if imported as 437

    https://cs.wikipedia.org/wiki/K%C3%B3d_Kamenick%C3%BDch
    https://en.wikipedia.org/wiki/Code_page_437
    http://www.rapidtables.com/code/text/unicode-characters.htm
    """

    return fix_iffy(txt, {
        '\xc7': 'Č',
        # '\xfc': 'ü',
        # '\xe9': 'é',  # 130
        '\xe2': 'ď',
        # '\xe4': 'ä',
        '\xe0': 'Ď',
        '\xe5': 'Ť',
        '\xe7': 'č',  # 135
        '\xea': 'ě',
        '\xeb': 'Ě',
        '\xe8': 'Ĺ',
        '\xef': 'Í',
        '\xee': 'ľ',  # 140
        '\xec': 'ĺ',
        '\xc4': 'Ä',
        '\xc5': 'Á',
        # '\xc9': 'É',
        '\xe6': 'ž',  # 145
        '\xc6': 'Ž',
        # '\xf4': '\xf4',  # o vokan
        # '\xf6': 'ö',
        '\xf2': 'Ó',
        '\xfb': 'ů',  # 150
        '\xf9': 'Ú',
        '\xff': 'ý',
        # '\xd6': 'Ö',
        # '\xdc': 'Ü',
        '\xa2': 'Š',  # 155
        '\xa3': 'Ľ',
        '\xa5': 'Ý',
        '\u20a7': 'Ř',
        '\u0192': 'ť',
        # '\xe1': 'á',  # 160
        # '\xed': 'í',
        # '\xf3': 'ó',
        # '\xfa': 'ú',
        '\xf1': 'ň',
        '\xd1': 'Ň',  # 165
        '\xaa': 'Ů',
        '\xba': '\xd4',  # O vokan
        '\xbf': 'š',
        '\u2310': 'ř',
        '\xac': 'ŕ',  # 170
        '\xbd': 'Ŕ',
        })

def fix_iffy(txt, conversion_map):
    retval = ''
    for ch in txt:
        retval += conversion_map.get(ch, ch)
    return retval

def fix_init(dbf):
    if dbf.code_pages['h'][0] is None:
        dbf.code_pages['h'] = ('cp437', 'Kamenicky (Czech) MS-DOS')
    if dbf.code_pages['i'][0] is None:
        dbf.code_pages['i'] = ('cp437', 'Mazovia (Polish) MS-DOS')

# from dbf_read_iffy import fix_init, fix_895
# fix_init(dbf)
# t = dbf.Table('/home/mirek/mz/codex_data/stichovice/AUTORI.DBF')
# t.open('read-only')
# for record in t[:5]:
#    print fix_895(record.autor)
# t.close()

"""
need read dbf cp895 Kamenicky
http://code.activestate.com/recipes/362715/
"""

import datetime
import decimal
import itertools
import struct


def read_db(filename):
    with open(filename, 'rb') as f:
        db = list(dbfreader(f))
    #for record in db:
    #    print record
    return db


def dbfreader(f):
    """Returns an iterator over records in a Xbase DBF file.

    The first row returned contains the field names.
    The second row contains field specs: (type, size, decimal places).
    Subsequent rows contain the data records.
    If a record is marked as deleted, it is skipped.

    File should be opened for binary reads.
    """
    # See DBF format spec at:
    #     http://www.pgts.com.au/download/public/xbase.htm#DBF_STRUCT

    numrec, lenheader = struct.unpack('<xxxxLH22x', f.read(32))
    numfields = (lenheader - 33) // 32

    fields = []
    for fieldno in xrange(numfields):
        name, typ, size, deci = struct.unpack('<11sc4xBB14x', f.read(32))
        name = name.replace('\0', '')       # eliminate NULs from string
        fields.append((name, typ, size, deci))
    yield [field[0] for field in fields]
    yield [tuple(field[1:]) for field in fields]

    terminator = f.read(1)
    assert terminator == '\r'

    fields.insert(0, ('DeletionFlag', 'C', 1, 0))
    fmt = ''.join(['%ds' % fieldinfo[2] for fieldinfo in fields])
    fmtsiz = struct.calcsize(fmt)
    for i in xrange(numrec):
        record = struct.unpack(fmt, f.read(fmtsiz))
        if record[0] != ' ':
            continue                        # deleted record
        result = []
        for (name, typ, size, deci), value in itertools.izip(fields, record):
            if name == 'DeletionFlag':
                continue
            if typ == "N":
                value = value.replace('\0', '').lstrip()
                if value == '':
                    value = 0
                elif deci:
                    value = decimal.Decimal(value)
                else:
                    value = int(value)
            elif typ == 'D':
                y, m, d = int(value[:4]), int(value[4:6]), int(value[6:8])
                value = datetime.date(y, m, d)
            elif typ == 'L':
                value = (value in 'YyTt' and 'T') or (value in 'NnFf' and 'F') or '?'
            elif typ == 'F':
                value = float(value)
            result.append(value)
        yield result


def dbfwriter(f, fieldnames, fieldspecs, records):
    """ Return a string suitable for writing directly to a binary dbf file.

    File f should be open for writing in a binary mode.

    Fieldnames should be no longer than ten characters and not include \x00.
    Fieldspecs are in the form (type, size, deci) where
        type is one of:
            C for ascii character data
            M for ascii character memo data (real memo fields not supported)
            D for datetime objects
            N for ints or decimal objects
            L for logical values 'T', 'F', or '?'
        size is the field width
        deci is the number of decimal places in the provided decimal object
    Records can be an iterable over the records (sequences of field values).

    """
    # header info
    ver = 3
    now = datetime.datetime.now()
    yr, mon, day = now.year-1900, now.month, now.day
    numrec = len(records)
    numfields = len(fieldspecs)
    lenheader = numfields * 32 + 33
    lenrecord = sum(field[1] for field in fieldspecs) + 1
    hdr = struct.pack('<BBBBLHH20x', ver, yr, mon, day, numrec, lenheader, lenrecord)
    f.write(hdr)

    # field specs
    for name, (typ, size, deci) in itertools.izip(fieldnames, fieldspecs):
        name = name.ljust(11, '\x00')
        fld = struct.pack('<11sc4xBB14x', name, typ, size, deci)
        f.write(fld)

    # terminator
    f.write('\r')

    # records
    for record in records:
        f.write(' ')                        # deletion flag
        for (typ, size, deci), value in itertools.izip(fieldspecs, record):
            if typ == "N":
                value = str(value).rjust(size, ' ')
            elif typ == 'D':
                value = value.strftime('%Y%m%d')
            elif typ == 'L':
                value = str(value)[0].upper()
            else:
                value = str(value)[:size].ljust(size, ' ')
            assert len(value) == size
            f.write(value)

    # End of file
    f.write('\x1A')

'''
# -------------------------------------------------------
# Example calls
if __name__ == '__main__':
    import sys, csv
    from cStringIO import StringIO
    from operator import itemgetter

    # Read a database
    filename = '/pydev/databases/orders.dbf'
    if len(sys.argv) == 2:
        filename = sys.argv[1]
    f = open(filename, 'rb')
    db = list(dbfreader(f))
    f.close()
    for record in db:
        print record
    fieldnames, fieldspecs, records = db[0], db[1], db[2:]

    # Alter the database
    del records[4]
    records.sort(key=itemgetter(4))

    # Remove a field
    del fieldnames[0]
    del fieldspecs[0]
    records = [rec[1:] for rec in records]

    # Create a new DBF
    f = StringIO()
    dbfwriter(f, fieldnames, fieldspecs, records)

    # Read the data back from the new DBF
    print '-' * 20
    f.seek(0)
    for line in dbfreader(f):
        print line
    f.close()

    # Convert to CSV
    print '.' * 20
    f = StringIO()
    csv.writer(f).writerow(fieldnames)
    csv.writer(f).writerows(records)
    print f.getvalue()
    f.close()

# Example Output
"""
['ORDER_ID', 'CUSTMR_ID', 'EMPLOY_ID', 'ORDER_DATE', 'ORDER_AMT']
[('C', 10, 0), ('C', 11, 0), ('C', 11, 0), ('D', 8, 0), ('N', 12, 2)]
['10005     ', 'WALNG      ', '555        ', datetime.date(1995, 5, 22), Decimal("173.40")]
['10004     ', 'BMARK      ', '777        ', datetime.date(1995, 5, 18), Decimal("3194.20")]
[.........]
--------------------
['CUSTMR_ID', 'EMPLOY_ID', 'ORDER_DATE', 'ORDER_AMT']
[('C', 11, 0), ('C', 11, 0), ('D', 8, 0), ('N', 12, 2)]
['MORNS      ', '555        ', datetime.date(1995, 6, 26), Decimal("17.40")]
['SAWYH      ', '777        ', datetime.date(1995, 6, 29), Decimal("97.30")]
[.........]
--------------------
CUSTMR_ID,EMPLOY_ID,ORDER_DATE,ORDER_AMT
MORNS      ,555        ,1995-06-26,17.40
SAWYH      ,777        ,1995-06-29,97.30
.........
"""
'''
