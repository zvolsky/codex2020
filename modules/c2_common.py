# -*- coding: utf-8 -*-

from c_utils import parse_fastinfo
from dal_common import impressions_by_usrid
from dal_utils import get_libstyle

from gluon import current
from gluon.html import A, DIV, SPAN, URL


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
        rik = book['rik']
        iorder = imp[1]
        if uses_iid:
            lbl = '%s-%s %s' % (rik, iorder, imp[2])
        else:
            lbl = '%s-%s' % (rik, iorder)
        return DIV(A(lbl, _href="%s/%s" % ((URL(c, f) if c else URL(f)), imp[0]),
                     _data_id="%s" % imp[0]), _class='pull-left')

    uses_iid = get_libstyle()['id'][0] == 'I'
    books, overflow = impressions_by_usrid(question)
    '''boooks is list of dictionaries, one dict for one publication, keys are:
          'owned_book_id', 'answer_id', 'rik', 'fastinfo' and 'imp', where 'imp' is list of impressions (of single book)
          each item in 'imp' is tuple: (id, iorder, iid)
    '''
    fmt = []
    if books:
        for book in books:
            impressions = book['imp']
            cnt_imp = len(impressions)
            title, author, publisher, pubyear = parse_fastinfo(book['fastinfo'])
            book_div = DIV(author, title)
            if cnt_imp > 1:
                # summary as visible
                fmt.append(DIV(DIV('%s x' % cnt_imp, _class='pull-left'), book_div))
                # detail rows as hidden
                for imp in impressions:
                    fmt.append(imp_info(imp))
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
