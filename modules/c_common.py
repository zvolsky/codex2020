# -*- coding: utf-8 -*-

"""Codex 2020 code, completely independent on the Web2py framework
"""

def group_imp_by_book(imps, limitby=None):
    """requires iterable imps,
            - where each of items is object with subobjects and properties:
                impression.id, impression.iorder, impression.iid, impression.sgn, owned_book.id, db.answer.id, db.answer.rik, db.answer.fastinfo
                (in Web2py implementation these are pydal/web2py/gluon Storage() objects)
            - sorted by owned_book.id
    return: list of dictionaries, one dict for one publication, where dict item key='imp' contains list of its impressions
    """
    def imp_as_tuple():
        return (imp.impression.id, imp.impression.iorder, imp.impression.iid, imp.impression.sgn)

    cnt = 0
    overflow = False
    books = []
    previous_book = None
    for imp in imps:
        if imp.owned_book.id == previous_book:
            books[-1]['imp'].append(imp_as_tuple())
        else:
            if limitby:
                cnt += 1
                if cnt > limitby:
                    overflow = True
                    break
            previous_book = imp.owned_book.id
            books.append({'imp': [imp_as_tuple()],
                          'owned_book_id': imp.owned_book.id,
                          'answer_id': imp.answer.id,
                          'rik': imp.answer.rik,
                          'fastinfo': imp.answer.fastinfo})
    return books, overflow
