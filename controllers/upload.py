# -*- coding: utf-8 -*-

"""
    catalogue import
"""

import os
from urllib import quote

from dal_utils import get_library
from c2_config import get_contact


@auth.requires_login()
def main():
    email = None
    if auth.user.librarian:
        system = get_library().imp_system
        if system:
            redirect(URL(quote(system, safe='')))
        email = get_contact(myconf, 'imports')
    return dict(email=email)

@auth.requires_login()
def codex():
    uploadfolder = os.path.join('applications', request.application, 'uploads', 'codex', get_library().slug)
    form = SQLFORM.factory(
        Field('knihy_d', 'upload', uploadfolder=uploadfolder, label='Knihy.dbf'),
        Field('knihy_m', 'upload', uploadfolder=uploadfolder, label='Knihy.fpt'),
    )
    if form.process().accepted:
        #from dbfread import DBF
        #for record in DBF(os.path.join(uploadfolder, form.vars.knihy_d), load=True)[:5]:
        #    print record
        import dbf
    return dict(form=form)
