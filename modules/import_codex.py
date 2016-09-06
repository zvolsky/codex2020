# -*- coding: utf-8 -*-

"""
    Read from dbf's with codepage unsupported by modules dbf and codecs (like 895 cz Kamenicky)
"""

import os

from c_utils import REPEATJOINER, parse_year_from_text, normalize_authors, publ_fastinfo_and_hash

import dbf
from dbf_read_iffy import fix_init, fix_895
fix_init(dbf)

"""
    import dbf
    from dbf_read_iffy import fix_init, fix_895
    fix_init(dbf)
    t = dbf.Table('autori.dbf')
    t.open('read-only')
    for record in t:
        print fix_895(record.autor)
    t.close()
"""

from dal_import import load_redirects


def imp_codex(db, library_id, src_folder):
    """
        This is the main (entry) function.
    """
    redirects = load_redirects()

    autori = read_xbase_as_dict(os.path.join(src_folder, 'autori.dbf'), key='id_autora')  # AUTOR , need ","->", "
    k_autori = read_xbase_as_list_dict(os.path.join(src_folder, 'k_autori.dbf'), key='id_publ')  # VZTAH, ID_AUTORA
    klsl = read_xbase_as_dict(os.path.join(src_folder, 'klsl.dbf'), key='id_klsl')  # KLSL
    k_klsl = read_xbase_as_list_dict(os.path.join(src_folder, 'k_klsl.dbf'), key='id_publ')  # ID_KLSL
    #dt = read_xbase_as_dict(os.path.join(src_folder, 'dt.dbf'), key='dt')  # DT, DT_TXT
    k_dt = read_xbase_as_list_dict(os.path.join(src_folder, 'k_dt.dbf'), key='id_publ')  # POM_ZNAK, DT
    nakl = read_xbase_as_dict(os.path.join(src_folder, 'dodavat.dbf'), key='id_dodav')  # ICO, NAZEV1, NAZEV2, NAZEV_ZKR, MISTO
    vytisky = read_xbase_as_list_dict(os.path.join(src_folder, 'vytisk.dbf'), key='id_publ', left=4)
                # value: (tail<id>, record)     # PC, SIGNATURA, UC, ZARAZENO, VYRAZENO, CENA, ID_DODAV, UMISTENI, BARCODE, REVIZE, POZNAMKA
    # TODO: VYPUJCKY?

    read_xbase(os.path.join(src_folder, 'knihy.dbf'), import_publ, locals())

def import_publ(record, vars):
    # vars['redirects'], vars['autori'], ... --- dict!
    #   ['k_klsl', 'library_id', 'redirects', 'vytisky', 'k_dt', 'db', 'autori', 'klsl', 'nakl', 'k_autori', ('dt',) 'src_folder']
    # KNIHY: ID_PUBL, RADA_PC, RADA_KNIHY, SIGNATURA, TEMATIKA, EAN, AUTORI, NAZEV, PODNAZEV, PUVOD, KNPOZNAMKA,
    #       JAZYK, VYDANI, IMPRESUM, ANOTACE, ISBN, KS_CELK, KS, KS_JE, POZNAMKA, STUDOVNA, ID_NAKL
    nazev = fix_895(record['nazev'].strip())
    podnazev = fix_895(record['podnazev'].strip())
    nakladatel = nakl[record['id_nakl']]
    misto = fix_895(nakladatel['misto'].strip())
    nakladatel = fix_895(nakladatel['nazev1'].strip() or nakladatel['nazev_zkr'].strip())  # prefer Nazev1 ?
    pubyear = parse_year_from_text(record['impresum'])

    klsl = []
    for klic in k_klsl['id_publ']:
        klsl.append(fix_895(klsl[klic['id_klsl']]['klsl']))
    for klic in k_dt['id_publ']:
        klsl.append(fix_895(klic['dt']))   # zatím neukládám k_dt.pom_znak a dt.dt_txt
    surnamed = []
    full = []
    for osoba in k_autori['id_publ']:
        osoba_tuple = (fix_895(autori[osoba['id_autora']]['autor']),)
        surnamed1, full1 = normalize_authors(osoba_tuple, string_surnamed=True, string_full=True)
        if osoba['vztah'] == 'aut':
            surnamed.append(surnamed1)
            full.append(full1)
        else:  # ostatní osoby
            klsl.append(full1)   # zatím neukládám k_autori.vztah
    surnamed = REPEATJOINER.join(surnamed)
    full = REPEATJOINER.join(full)

    #TODO: publisher = misto, nakladatel
    fastinfo, md5publ = publ_fastinfo_and_hash(title, surnamed, full, publisher, pubyear, subtitle=podnazev, keys=klsl)


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
        rows[current_id] = record

    rows = {}
    read_xbase(filename, rec_to_dict, key, rows)
    return rows

def read_xbase_as_list_dict(filename, key, left=None):
    """
        get rows as dict where keys are given keys (can be non-unique), values are list records (without given key)
    """
    def rec_to_list_dict(record, key, rows, left):
        current_id = record[key]
        if left:
            current_id = current_id[:left]
        if current_id in rows:
            rows[current_id].append(record)
        else:
            rows[current_id] = [record]

    rows = {}
    read_xbase(filename, rec_to_list_dict, key, rows, left)
    return rows
#TODO: end
