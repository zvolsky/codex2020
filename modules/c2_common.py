# -*- coding: utf-8 -*-

from c_utils import parse_fastinfo
from dal_common import impressions_by_usrid
from dal_utils import get_libstyle

from gluon import current
from gluon.html import A, B, DIV, SPAN, URL


def get_book_line(tit, aut, pub=None, puy=None):
    """formatted info line about book
    if publisher is used then pubyear is obligatory
    """
    book_line = [B(tit), ' ', SPAN(aut, _class="bg-primary")]
    if pub is not None:
        book_line += [' ', SPAN(pub, ' ', puy, _class="smaller")]
    return book_line

def fmt_impressions_by_usrid(question, f='#', c=None, T=None):
    """
    Args:
        question: rik, ean, isxn (title?) of the book which we want find for review or loan
        f: action if clicked; if '#' you can set jQuery .click() later to call ajax (based on <a data_id="nnn">)
        c: controller for the action (if it is different as the current one)
    Returns:
        formatted output
    """

    if T is None:
        T = current.T

    def imp_info(imp):
        iorder = imp[1]
        lbl = SPAN('%s-%s' % (rik, iorder))
        if uses_iid:
            lbl.append(' ')
            lbl.append(B(imp[2]))
        return A(lbl, _href="%s/%s" % ((URL(c, f) if c else URL(f)), imp[0]),
                     _data_id="%s" % imp[0], _class='btn btn-warning')

    libstyle = get_libstyle()
    rik_short_pos = - libstyle['lrik'] + 1
    uses_iid = libstyle['id'][0] == 'I'
    books, overflow = impressions_by_usrid(question)
    '''boooks is list of dictionaries, one dict for one publication, keys are:
          'owned_book_id', 'answer_id', 'rik', 'fastinfo' and 'imp', where 'imp' is list of impressions (of single book)
          each item in 'imp' is tuple: (id, iorder, iid)
    '''
    fmt = []
    if books:
        for book in books:
            rik = book['rik'][rik_short_pos::-1]
            impressions = book['imp']
            cnt_imp = len(impressions)
            tit, aut, pub, puy = parse_fastinfo(book['fastinfo'])
            book_div = DIV(*get_book_line(tit, aut), _class='btn btn-default btn-sm')
            if cnt_imp > 1:
                # summary as visible
                fmt.append(DIV(DIV('%s x' % cnt_imp, _class='btn btn-info btn-sm'), book_div))
                # detail rows as hidden
                imps = DIV(_style="overflow: auto;")
                for imp in impressions:
                    imps.append(imp_info(imp))
                fmt.append(imps)
            else:  # single impression
                # summary=detail as visible
                fmt.append(DIV(imp_info(impressions[0]), book_div))
        result = DIV()
        if overflow:
            result.append(DIV(T("Je zobrazen omezený počet - méně výtisků než odpovídá zadání. Použij přesnější zadání.")))
        result.append(DIV(*fmt))
    else:
        result = DIV(T("Zadání neodpovídá žádný výtisk."))
    return result
