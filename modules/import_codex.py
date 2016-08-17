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

import dbf
from dbf_read_iffy import fix_init, fix_895

