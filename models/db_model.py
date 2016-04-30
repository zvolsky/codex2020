# -*- coding: utf-8 -*-

class PublLengths(object):
    title = 255
    uniformtitle = 255
    author = 200
    isbn = 20
    series = 100
    subjects = 255
    categories = 100
    addedentries = 255
    publ_location = 255
    notes = 255
    physicaldescription = 255
    publisher = 255
    pubyear = 100
    country = 3

    question_min = 3
    question = 60

class UNIQUE_QUESTION(object):
    def __init__(self, error_message=T('dotaz už je ve frontě')):
        self.error_message = error_message
    def __call__(self, value):
        if db((db.question.question == value) & (db.question.auth_user_id == auth.user_id) & (db.question.live == True)
              ).select(db.question.id, limitby=(0, 1)):
            return (value, self.error_message)
        else:
            return (value, None)

db.define_table('question',
        Field('auth_user_id', db.auth_user, default=auth.user_id,
              readable=False, writable=False,
              label=T("Uživatel"), comment=T("zadavatel dotazu")),
        Field('question', 'string', length=PublLengths.question,
              requires=[IS_LENGTH(minsize=PublLengths.question_min, maxsize=PublLengths.question,
                            error_message=T("zadej %s až %s znaků") % (PublLengths.question_min, PublLengths.question)),
                        UNIQUE_QUESTION()],
              label=T("Dotaz"), comment=T("zadej počáteční 2-3 slova názvu, nebo sejmi prodejní čarový kód EAN")),
        Field('answered', 'datetime',
              readable=False, writable=False,
              label=T("Dokončeno"), comment=T("čas dokončení zpracování po odpovědi")),
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
        Field('marc', 'text',
              label=T("marc"), comment=T("marc")),
        )

db.define_table('answer_starter',
        Field('starter_type', 'string', length=1,
              label=T("Typ řetězce"), comment=T("typ řetězce (T=titul, A=autor)")),
        Field('starter', 'string', length=60,
              label=T("Řetězec"), comment=T("začátek řetězce")),
        Field('starter_hash', 'integer',
              label=T("Hash řetězce"), comment=T("hash (kontrolní součet) řetězce")),
        )

db.define_table('answer_link',
        Field('answer_id', db.answer,
              label=T("Odpověď"), comment=T("příslušnost k odpovědi")),
        Field('answer_starter_id', db.answer_starter,
              label=T("Vyhledávací řetězec"), comment=T("příslušnost k vyhledávacímu řetězci")),
        Field('role', 'string', length=3,
              label=T("Role"), comment=T("role, pořadí v sérii, apod.")),
        )

db.define_table('answer_lang',
        Field('answer_id', db.answer,
              label=T("Odpověď"), comment=T("příslušnost k odpovědi")),
        Field('lang', 'string', length=3,
              label=T("Jazyk"), comment=T("jazyk publikace nebo její části")),
        )

db.define_table('publication',
        Field('md5', 'string', length=32,
              label=T("md5"), comment=T("md5")),
        Field('ean', 'string', length=20,
              label=T("Čarový kód EAN"), comment=T("čarový kód, vytištěný na publikaci")),
        Field('title', 'string', length=PublLengths.title,
              label=T("Název"), comment=T("hlavní název publikace")),
        Field('uniformtitle', 'string', length=PublLengths.uniformtitle,
              label=T("uniformtitle"), comment=T("uniformtitle")),
        Field('author', 'string', length=PublLengths.author,
              label=T("Autor"), comment=T("autor")),
        Field('isbn', 'string', length=PublLengths.isbn,
              label=T("ISBN"), comment=T("ISBN")),
        Field('series', 'string', length=PublLengths.series,
              label=T("series"), comment=T("series")),
        Field('subjects', 'string', length=PublLengths.subjects,
              label=T("subjects"), comment=T("subjects")),
        Field('categories', 'string', length=PublLengths.categories,
              label=T("categories"), comment=T("categories")),
        Field('addedentries', 'string', length=PublLengths.addedentries,
              label=T("addedentries"), comment=T("addedentries")),
        Field('publ_location', 'string', length=PublLengths.publ_location,   # location is reserved word
              label=T("location"), comment=T("location")),
        Field('notes', 'string', length=PublLengths.notes,
              label=T("notes"), comment=T("physicaldescription")),
        Field('physicaldescription', 'string', length=PublLengths.physicaldescription,
              label=T("physicaldescription"), comment=T("physicaldescription")),
        Field('publisher', 'string', length=PublLengths.publisher,
              label=T("publisher"), comment=T("publisher")),
        Field('pubyear', 'string', length=PublLengths.pubyear,
              label=T("pubyear"), comment=T("pubyear")),
        Field('marc', 'text',
              label=T("marc"), comment=T("marc")),
        )
