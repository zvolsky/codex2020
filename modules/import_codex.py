# -*- coding: utf-8 -*-

import os

import dbf
from dbf_read_iffy import fix_init, fix_895
fix_init(dbf)
"""
<<<<<<< Updated upstream
    Read from dbf's with codepage unsupported by modules dbf and codecs (like 895 cz Kamenicky)
=======
Read from dbf's with codepage unsupported by modules dbf and codecs (like 895 cz Kamenicky)
>>>>>>> Stashed changes

import dbf
from dbf_read_iffy import fix_init, fix_895

<<<<<<< Updated upstream
    fix_init(dbf)
    t = dbf.Table('autori.dbf')
    t.open('read-only')
    for record in t:
        print fix_895(record.autor)
    t.close()
=======
fix_init(dbf)
t = dbf.Table('autori.dbf')
t.open('read-only')
for record in t:
    print fix_895(record.autor)
t.close()
>>>>>>> Stashed changes
"""

from dal_import import load_redirects


def imp_codex(db, library_id, src_folder):
    """
        This is the main (entry) function.
    """
    redirects = load_redirects()

    autori = read_xbase_as_dict(os.path.join(src_folder, 'autori.dbf', key='id_autora'))
    k_autori = read_xbase_as_list_dict(os.path.join(src_folder, 'k_autori.dbf'), key='id_publ')
    klsl = read_xbase_as_dict(os.path.join(src_folder, 'klsl.dbf'))
    k_klsl = read_xbase_as_list_dict(os.path.join(src_folder, 'k_klsl.dbf'), key='id_publ')
    dt = read_xbase_as_dict(os.path.join(src_folder, 'dt.dbf'))
    k_dt = read_xbase_as_list_dict(os.path.join(src_folder, 'k_dt.dbf'), key='id_publ')
    nakl = read_xbase_as_dict(os.path.join(src_folder, 'dodavat.dbf'))
    vytisky = read_xbase_as_list_dict(os.path.join(src_folder, 'vytisk.dbf'), key='id_publ')

    read_xbase(os.path.join(src_folder, 'knihy.dbf'), import_publ, locals())

def import_publ(vars):
    # vars['redirects'], vars['autori'], ...
    pass


#TODO: rest should be moved into modules/c_import with next xBase import (import dbf + fix_init(dbf) can be used in c_import too)
def read_xbase(filename, callback, *args, **kwargs):
    """
        run the callback function for each row in the table (similar to xBase SCAN)
    """
    t = dbf.Table(filename)
    t.open('read-only')
    for record in t:
        callback(record, *args, **kwargs)
    t.close()

def read_xbase_as_dict(filename, key='id'):
    """
        get rows as dict where keys are primary keys, values are records (without primary key)
    """
    def rec_to_dict(record, key, rows):
        current_id = record[key]
        del record[key]
        rows[current_id] = record

    rows = {}
    read_xbase(filename, rec_to_dict, key, rows)
    return rows

def read_xbase_as_list_dict(filename, key):
    """
        get rows as dict where keys are given keys (can be non-unique), values are list records (without given key)
    """
    def rec_to_list_dict(record, key, rows):
        current_id = record[key]
        del record[key]
        if current_id in rows:
            rows[current_id].append(record)
        else:
            rows[current_id] = [record]

    rows = {}
    read_xbase(filename, rec_to_list_dict, key, rows)
    return rows
#TODO: end
