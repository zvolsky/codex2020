# -*- coding: utf-8 -*-

@auth.requires_login()
def review():
    if not auth.library_id:
        redirect(URL('default', 'index'))
    review_date = db(db.library.id == auth.library_id).select(db.library.review_date).first().review_date
    '''
    db.place.id.readable = False
    grid = SQLFORM.grid(db.place,
            searchable=False,
            showbuttontext=False,
            csv=False
            )
    '''
    return dict(cnt_t=db(db.owned_book).count(), cnt_i=db(db.impression).count(), review_date=review_date)
