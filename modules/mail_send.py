#!/usr/bin/env python
# -*- coding: utf8 -*-

import base64
import os
import mimetypes

from sparkpost import SparkPost

appdir = os.path.join(os.getcwd(), 'applications', 'platby')
sparkpost_key = myconf.take('smtp.login').split(':')[-1].strip()

def mail_send(subject, txt, prilohy=[], prijemci=
      [{'email': 'mirek.zvolsky@gmail.com', 'name': u'Mirek Zvolský na Googlu'},
      {'email': 'zvolsky@seznam.cz', 'name': u'Mirek Zvolský na Seznamu'}],
      styl='text'):
    '''
    subject, txt - nejlépe unicode objekty
    prijemci - viz příklad defaultní hodnoty
    styl = 'html'/'text'
    přílohy je třeba uložit přes FTP do mail_attachments/ a po odeslání smazat
    '''

    attachments = []
    for priloha in prilohy:
        attachments.append({
                'filename': priloha,
                'name': os.path.basename(priloha),
                'type': mimetypes.guess_type(priloha)[0] or 'application/octet-stream'
        })

    stylDict = {styl: txt}
    sp = SparkPost(sparkpost_key)
    sp.transmissions.send(
        recipients=[prijemce['email'] for prijemce in prijemci],
        from_email=u'Společné Aktivity <spolecneaktivity@zitranavylet.cz>',
        subject=subject,
        attachments=attachments,
        **stylDict
    )
