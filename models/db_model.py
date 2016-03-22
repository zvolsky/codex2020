# -*- coding: utf-8 -*-

db.define_table('publication',
        Field('md5', 'string', length=32,
              label=T("md5"), comment=T("md5")),
        Field('EAN', 'string', length=20,
              label=T("Čarový kód EAN"), comment=T("čarový kód, vytištěný na publikaci")),
        Field('title', 'string', length=255,
              label=T("Název"), comment=T("hlavní název publikace")),
        Field('uniformtitle', 'string', length=255,
              label=T("uniformtitle"), comment=T("uniformtitle")),
        Field('author', 'string', length=200,
              label=T("Autor"), comment=T("autor")),
        Field('isbn', 'string', length=20,
              label=T("ISBN"), comment=T("ISBN")),
        Field('subjects', 'string', length=255,
              label=T("subjects"), comment=T("subjects")),
        Field('addedentries', 'string', length=255,
              label=T("addedentries"), comment=T("addedentries")),
        Field('location', 'string', length=255,
              label=T("location"), comment=T("location")),
        Field('notes', 'string', length=255,
              label=T("notes"), comment=T("notes")),
        Field('physicaldescription', 'string', length=255,
              label=T("physicaldescription"), comment=T("physicaldescription")),
        Field('publisher', 'string', length=255,
              label=T("publisher"), comment=T("publisher")),
        Field('pubyear', 'string', length=100,
              label=T("pubyear"), comment=T("pubyear")),
        Field('marc', 'text',
              label=T("marc"), comment=T("marc")),
        )
