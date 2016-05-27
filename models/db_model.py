# -*- coding: utf-8 -*-

from itertools import groupby

from gluon import current

from plugin_mz import IS_NOT_EMPTY_

from c2_db import PublLengths

# export for modules
current.auth = auth
current.db = db

auth.settings.create_user_groups = None

# dočasně, dokud ladíme první knihovnu
auth.settings.registration_requires_approval = True  # TODO: nahradit mechanismem, kdy pro novou knihovnu bude povoleno, pro starou ověří mailem prvnímu uživateli
auth.library_id = 1


"""deaktivovano
class UNIQUE_QUESTION(object):
    def __init__(self, error_message=T('dotaz už je ve frontě')):
        self.error_message = error_message
    def __call__(self, value):
        if db((db.question.question == value) & (db.question.auth_user_id == auth.user_id) & (db.question.live == True)
              ).select(db.question.id, limitby=(0, 1)):
            return (value, self.error_message)
        else:
            return (value, None)
"""

db.define_table('library',
        Field('library', 'string', length=128,
              label=T("Knihovna"), comment=T("jméno knihovny")),
        format='%(library)s'
        )

db.define_table('rgroup',
        Field('library_id', db.library,
              default=auth.library_id,
              readable=True, writable=False,
              ondelete='RESTRICT',
              label=T("Knihovna"), comment=T("jméno knihovny")),
        Field('rgroup', 'string', length=48,
              notnull=True, requires=IS_NOT_EMPTY_(),
              label=T("Skupina"), comment=T("skupina čtenářů (např. pro školní knihovny školní třída")),
        common_filter = lambda query: db.rgroup.library_id == auth.library_id,
        singular=T("skupina čtenářů"), plural=T("skupiny čtenářů"),
        format='%(rgroup)s'
        )

db.define_table('reader',
        Field('library_id', db.library,
              default=auth.library_id,
              readable=False, writable=False,
              ondelete='CASCADE',
              label=T("Knihovna"), comment=T("jméno knihovny")),
        Field('lastname', 'string', length=32,
              notnull=True, requires=IS_NOT_EMPTY_(),
              label=T("Příjmení"), comment=T("příjmení čtenáře")),
        Field('firstname', 'string', length=32,
              label=T("Jméno"), comment=T("křestní jméno čtenáře (a případně jeho/její další jména)")),
        Field('rgroup_id', db.rgroup,
              ondelete='SET NULL',
              #represent = lambda rgroup_id, row: db.rgroup.id or '',
              label=T("Skupina"), comment=T("skupina čtenářů")),
        Field('email', 'string', length=64,
              label=T("E-mail"), comment=T("e-mail")),
        common_filter = lambda query: db.reader.library_id == auth.library_id,
        singular=T("čtenář"), plural=T("čtenáři"),
        format='%(lastname)s %(firstname)s'
        )

db.define_table('question',
        Field('auth_user_id', db.auth_user, default=auth.user_id,
              readable=False, writable=False,
              ondelete='CASCADE',
              label=T("Uživatel"), comment=T("zadavatel dotazu")),
        Field('question', 'string', length=PublLengths.question,
              requires=IS_LENGTH(minsize=PublLengths.question_min, maxsize=PublLengths.question,
                            error_message=T("zadej %s až %s znaků") % (PublLengths.question_min, PublLengths.question)),
                        #UNIQUE_QUESTION()],
              label=T("Dotaz"), comment=T("zadej počáteční 2-3 slova názvu, nebo sejmi prodejní čarový kód EAN")),
        Field('asked', 'datetime',
              readable=False, writable=False,
              label=T("Zadáno"), comment=T("čas zadání dotazu")),
        Field('duration_z39', 'integer',
              readable=False, writable=False,
              label=T("Trvání stažení"), comment=T("doba do dokončení stažení dat [s]")),
        Field('duration_marc', 'integer',
              readable=False, writable=False,
              label=T("Trvání získání dat"), comment=T("doba do uložení nalezených knih [s]")),
        Field('duration_total', 'integer',
              readable=False, writable=False,
              label=T("Trvání celkem"), comment=T("doba do vytvoření indexů [s]")),
        Field('known', 'integer',
              readable=False, writable=False,
              label=T("Již známo"), comment=T("počet lokálně známých publikací")),
        Field('we_have', 'integer',
              readable=False, writable=False,
              label=T("Vlastněno"), comment=T("počet vyhovujících publikací v knihovně uživatele")),
        Field('retrieved', 'integer',
              readable=False, writable=False,
              label=T("Celkem získáno"), comment=T("počet nalezených publikací")),
        Field('inserted', 'integer',
              readable=False, writable=False,
              label=T("Nově získáno"), comment=T("nových (dosud nestažených)")),
        Field('live', 'boolean', default=True,
              readable=False, writable=False,
              label=T("Nezpracováno"), comment=T("čeká se na odpověď nebo její použití (katalogizaci)")),
        )

db.define_table('answer',
        Field('marc_id', 'integer',  # type integer and default=1(Aleph/cz) as long we do not support more marc dialects
              default=1, label=T("MARC dialekt"), comment=T("dialekt MARC jazyka")),
        Field('md5publ', 'string', length=32,
              label=T("md5publ"), comment=T("md5publ")),
        Field('md5marc', 'string', length=32,
              label=T("md5marc"), comment=T("md5marc")),
        Field('ean', 'string', length=20,
              label=T("Čarový kód EAN"), comment=T("čarový kód, vytištěný na publikaci")),
        Field('country', 'string', length=PublLengths.country,
              label=T("Země vydání"), comment=T("země vydání")),
        Field('year_from', 'integer',
              label=T("vydání od"), comment=T("vydání od roku")),
        Field('year_to', 'integer',
              label=T("vydání do"), comment=T("vydání do roku")),
        Field('fastinfo', 'text',
              label=T("hlavní údaje"), comment=T("hlavní údaje")),
        Field('marc', 'text',
              label=T("marc"), comment=T("marc")),
        )

db.define_table('idx_long',
        Field('category', 'string', length=1,
              label=T("Kategorie"), comment=T("kategorie (typ) vyhledávacího údaje")),
        Field('item', 'string', length=PublLengths.ilong,
              label=T("Vyhledávací údaj"), comment=T("údaj publikace (dlouhý)")),
        )

db.define_table('idx_join',
        Field('answer_id', db.answer,
              ondelete='CASCADE',
              label=T("Odpověď"), comment=T("příslušnost k odpovědi")),
        Field('idx_long_id', db.idx_long,
              ondelete='CASCADE',
              label=T("Vyhledávací řetězec"), comment=T("příslušnost k vyhledávacímu řetězci")),
        Field('role', 'string', length=PublLengths.irole,
              label=T("Role"), comment=T("role, pořadí v sérii, apod.")),
        )

db.define_table('idx_short',
        Field('answer_id', db.answer,
              ondelete='CASCADE',
              label=T("Publikace"), comment=T("příslušnost k publikaci")),
        Field('category', 'string', length=1,
              label=T("Kategorie"), comment=T("kategorie (typ) vyhledávacího údaje")),
        Field('item', 'string', length=PublLengths.ishort,
              label=T("Vyhledávací údaj"), comment=T("údaj publikace (krátký)")),
        )

db.define_table('idx_word',
        Field('answer_id', db.answer,
              ondelete='CASCADE',
              label=T("Publikace"), comment=T("příslušnost k publikaci")),
        Field('word', 'string', length=PublLengths.iword,
              label=T("Vyhledávací údaj"), comment=T("údaj publikace (krátký)")),
        )

db.define_table('lib_descr',
        Field('answer_id', db.answer,
              notnull=True, ondelete='RESTRICT',
              label=T("Odpověď"), comment=T("příslušnost k odpovědi")),
        Field('descr', 'text',
              label=T("Popis"), comment=T("bibliografický popis, pozměněný pro potřeby knihovny")),
        )

db.define_table('owned_book',
        Field('library_id', db.library,
              default=auth.library_id,
              readable=False, writable=False,
              notnull=True, ondelete='RESTRICT',
              label=T("Knihovna"), comment=T("jméno knihovny")),
        Field('answer_id', db.answer,
              notnull=True, ondelete='RESTRICT',
              label=T("Odpověď"), comment=T("příslušnost k odpovědi")),
        Field('lib_descr_id', db.lib_descr,
              ondelete='RESTRICT',
              label=T("Popis"), comment=T("bibliografický popis, pozměněný pro potřeby knihovny")),
        Field('cnt', 'integer',
              default=0,
              label=T("Výtisků"), comment=T("počet výtisků v knihovně")),
        common_filter = lambda query: db.owned_book.library_id == auth.library_id,
        )

db.define_table('impression',
        Field('library_id', db.library,
              default=auth.library_id,
              readable=False, writable=False,
              notnull=True, ondelete='RESTRICT',
              label=T("Knihovna"), comment=T("jméno knihovny")),
        Field('answer_id', db.answer,
              notnull=True, ondelete='RESTRICT',
              readable=False, writable=False,
              label=T("Odpověď"), comment=T("příslušnost k odpovědi")),
        Field('owned_book_id', db.owned_book,
              notnull=True, ondelete='RESTRICT',
              readable=False, writable=False,
              label=T("Odpověď"), comment=T("příslušnost k odpovědi")),
        Field('live', 'boolean', default=True,
              readable=False, writable=False,
              label=T("Platný výtisk"), comment=T("platný (nevyřazený) výtisk")),
        Field('iorder', 'integer',
              notnull=True, writable=False,
              label=T("Pořadové číslo"), comment=T("pořadové číslo výtisku")),
        Field('registered', 'date', default=datetime.date.today(),
              notnull=True, writable=False,
              represent=lambda registered, row=None: registered.strftime(T('%d.%m.%y')),
              label=T("Evidován"), comment=T("datum zápisu do počítačové evidence")),
        common_filter = lambda query: (db.impression.live == True) & (db.impression.library_id == auth.library_id),
        format=T('čís.') + ' %(iorder)s'
        )

db.define_table('impr_hist',
        Field('impression_id', db.impression,
              writable=False,
              notnull=True, ondelete='CASCADE',
              label=T("Výtisk"), comment=T("výtisk publikace")),
        Field('auth_user_id', db.auth_user, default=auth.user_id,
              writable=False,
              notnull=True, ondelete='SET NULL',
              label=T("Provedl"), comment=T("uživatel, který provedl akci")),
        Field('reader_id', db.reader,
              writable=False,
              ondelete='SET NULL',
              label=T("Čtenář"), comment=T("čtenář")),
        Field('htime', 'datetime', default=datetime.datetime.utcnow(),
              notnull=True, writable=False,
              label=T("Čas"), comment=T("čas akce (v UTC)")),
        Field('haction', 'integer',
              requires=IS_IN_SET(((1, T("zaevidován")), (2, T("vyřazen")), (3, ''))),
              notnull=True, writable=False,
              label=T("Akce"), comment=T("provedená činnost")),
        )

def book_cnt_plus(flds, id):
    db(db.owned_book.id == flds['owned_book_id']).update(cnt=db.owned_book.cnt + 1)
def book_cnt_minus(w2set):
    books = w2set.select(db.impression.owned_book_id, orderby=db.impression.owned_book_id)
    for key, group in groupby(books, lambda impression: impression.owned_book_id):
        db(db.owned_book.id == key).update(cnt=max(0, db.owned_book.cnt - len([bk for bk in group])))
db.impression._after_insert.append(book_cnt_plus)
db.impression._before_delete.append(book_cnt_minus)
