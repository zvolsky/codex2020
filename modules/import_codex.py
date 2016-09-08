# -*- coding: utf-8 -*-

"""
    Read from dbf's with codepage unsupported by modules dbf and codecs (like 895 cz Kamenicky)
"""

import os

from c_utils import REPEATJOINER, parse_year_from_text, normalize_authors, publ_fastinfo_and_hash
from dal_import import place_to_place_id

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

from dal_import import load_redirects, load_places


def imp_codex(db, library_id, src_folder):
    """
        This is the main (entry) function.
    """
    param = {}
    param['redirects'] = load_redirects()  # dict: md5publ -> md5publ(main) if book was joined with other (was/will be implemented later)
    param['places'] = load_places()        # dict: place -> (place_id)

    param['autori'] = read_xbase_as_dict(os.path.join(src_folder, 'autori.dbf'), key='id_autora')  # AUTOR , need ","->", "
    param['k_autori'] = read_xbase_as_list_dict(os.path.join(src_folder, 'k_autori.dbf'), key='id_publ')  # VZTAH, ID_AUTORA
    param['klsl'] = read_xbase_as_dict(os.path.join(src_folder, 'klsl.dbf'), key='id_klsl')  # KLSL
    param['k_klsl'] = read_xbase_as_list_dict(os.path.join(src_folder, 'k_klsl.dbf'), key='id_publ')  # ID_KLSL
    #dt'] = read_xbase_as_dict(os.path.join(src_folder, 'dt.dbf'), key='dt')  # DT, DT_TXT
    param['k_dt'] = read_xbase_as_list_dict(os.path.join(src_folder, 'k_dt.dbf'), key='id_publ')  # POM_ZNAK, DT
    param['nakl'] = read_xbase_as_dict(os.path.join(src_folder, 'dodavat.dbf'), key='id_dodav')  # ICO, NAZEV1, NAZEV2, NAZEV_ZKR, MISTO
    param['vytisky'] = read_xbase_as_list_dict(os.path.join(src_folder, 'vytisk.dbf'), key='id_publ', left=4)
                # value: (tail<id>, record)     # PC, SIGNATURA, UC, ZARAZENO, VYRAZENO, CENA, ID_DODAV, UMISTENI, BARCODE, REVIZE, POZNAMKA
    # TODO: VYPUJCKY?

    read_xbase(os.path.join(src_folder, 'knihy.dbf'), import_publ, param)

def import_publ(record, param):
    # KNIHY: ID_PUBL, RADA_PC, RADA_KNIHY, SIGNATURA, TEMATIKA, EAN, AUTORI, NAZEV, PODNAZEV, PUVOD, KNPOZNAMKA,
    #       JAZYK, VYDANI, IMPRESUM, ANOTACE, ISBN, KS_CELK, KS, KS_JE, POZNAMKA, STUDOVNA, ID_NAKL
    def impression_iter(impressions):
        for record in impressions:
            impression = {}
            impression['pc'] = record['pc']
            impression['sg'] = record['signatura']
            impression['bc'] = record['barcode']
            impression['place'] = place_to_place_id(param['places'], record['umisteni'].strip())
            yield impression

    id_publ = record['id_publ']
    nazev = fix_895(record['nazev'].strip())
    podnazev = fix_895(record['podnazev'].strip())
    pubplace = publisher = ''
    nakl_id = record['id_nakl']
    nakladatel = param['nakl'].get(nakl_id)
    if nakladatel:
        pubplace = fix_895(nakladatel['misto'].strip())
        publisher = fix_895(nakladatel['nazev1'].strip() or nakladatel['nazev_zkr'].strip())  # prefer Nazev1 ?
    pubyear = parse_year_from_text(record['impresum'], as_string=True)

    klsl = []
    for klic in param['k_klsl'].get(id_publ, ()):
        klsl.append(fix_895(param['klsl'][klic['id_klsl']]['klsl']))
    for klic in param['k_dt'].get(id_publ, ()):
        klsl.append(fix_895(klic['dt']))   # zatím neukládám k_dt.pom_znak a dt.dt_txt
    surnamed = []
    full = []
    for osoba in param['k_autori'].get(id_publ, ()):
        osoba_tuple = (fix_895(param['autori'][osoba['id_autora']]['autor']),)
        surnamed1, full1 = normalize_authors(osoba_tuple, string_surnamed=True, string_full=True)
        if osoba['vztah'] == 'A':  # aut
            surnamed.append(surnamed1)
            full.append(full1)
        else:  # ostatní osoby
            klsl.append(full1)   # zatím neukládám k_autori.vztah
    surnamed = REPEATJOINER.join(surnamed)
    full = REPEATJOINER.join(full)

    ean = record['ean'].strip()
    if not ean:
        ean = isxn_to_ean(record['isbn'])

    # always, because in case of other system import fastinfo can change together with same ean & md5publ
    fastinfo, md5publ = publ_fastinfo_and_hash(nazev, surnamed, full, pubplace, publisher, pubyear, subtitle=podnazev,
                                               keys=klsl)
    md5publ = param['redirects'].get(md5publ, md5publ)

    impressions = param['vytisky'].get(id_publ, ())
    answer_id = update_or_insert_answer(ean, md5publ, None, fastinfo)  # None ~ md5marc
    owned_book_id = update_or_insert_owned_book(answer_id, len(impressions))
    # impression_gen je generátor podle impression/impressions
    impression_gen = impression_iter(impressions)
    update_or_insert_impressions(answer_id, owned_book_id, impression_gen, param['places'])


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
