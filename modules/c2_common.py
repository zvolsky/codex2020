# -*- coding: utf-8 -*-

from c_utils import parse_fastinfo
from dal_common import impressions_by_usrid

from gluon.html import TABLE, TR


def fmt_impressions_by_usrid(question):
    def imp_info():
        return book['rik']  # TODO: + libstyle/separator + impressions:iorder   -or-  :iid
    books, overflow = impressions_by_usrid(question)
        '''boooks is list of dictionaries, one dict for one publication, keys are:
              'owned_book_id', 'answer_id', 'rik', 'fastinfo' and 'imp', where 'imp' is list of impressions (of single book)
              each item in 'imp' is tuple: (id, iorder, iid)
        '''
    fmt = []
    for book in books:
        impressions = book['imp']
        cnt_imp = len(impressions)
        title, author, publisher, pubyear = parse_fastinfo(book['fastinfo'])
        if cnt_imp > 1:
            # summary as visible
            fmt.append(TR(cnt_imp, author, title))
            # detail rows as hidden
            #fmt.append()
        else:  # single impression
            # summary=detail as visible
            fmt.append(TR(imp_info(), author, title))
    return TABLE(*fmt)
