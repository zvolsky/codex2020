# -*- coding: utf-8 -*-

from gluon import current
from gluon.tools import A, B, SPAN, DIV, XML

def codex(welcome=True):
    sw = B('Codex 2020')
    mkeu = B(current.request.env.http_host)
    if welcome:
        more = current.T("čti více")
        c22 = A(sw, SPAN(' (%s)' % (more), _id="c22m"), _href='#', _id='c22')
    else:
        c22 = sw
    return DIV(XML(current.T("Vítejte na portálu %s, kde je Vám k dispozici software pro práci s knihou %s.") % (mkeu, c22)),
                 _class="alert alert-info")
