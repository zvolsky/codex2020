# -*- coding: utf-8 -*-

db.define_table('publikace',
        Field('EAN', 'string', length=20,
              label=T("Čarový kód EAN"), comment=T("čarový kód, vytištěný na publikaci")),
        Field('appendkey', 'string', length=20,
              label=T("Zkus najít podle"), comment=T("počáteční znaky názvu pro pokus nalézt publikaci online nebo offline (např. 10-15 znaků)")),
        Field('nazev', 'string', length=255,
              label=T("Název"), comment=T("hlavní název publikace")),
        )
