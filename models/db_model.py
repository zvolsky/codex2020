# -*- coding: utf-8 -*-

class PublLengths(object):
    title = 255
    uniformtitle = 255
    author = 200
    isbn = 20
    subjects = 255
    addedentries = 255
    publ_location = 255
    notes = 255
    physicaldescription = 255
    publisher = 255
    pubyear = 100

db.define_table('answer',
        Field('md5publ', 'string', length=32,
              label=T("md5publ"), comment=T("md5publ")),
        Field('md5marc', 'string', length=32,
              label=T("md5marc"), comment=T("md5marc")),
        Field('ean', 'string', length=20,
              label=T("Čarový kód EAN"), comment=T("čarový kód, vytištěný na publikaci")),
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
        Field('subjects', 'string', length=PublLengths.subjects,
              label=T("subjects"), comment=T("subjects")),
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
