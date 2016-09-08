# -*- coding: utf-8 -*-

"""Dependent on pydal, but independent on the (rest of) Web2py framework.
The exception is use of current., which makes possible calls from Web2py framework without additional parameters;
    implicit parameter set via current. is always handled at the beginning of the func
"""

from gluon import current

if False:  # for IDE only, need web2py/__init__.py
    from web2py.gluon import current


def load_redirects(db=None):
    if db is None:
        db = current.db

    redirects = db().select(db.import_redirect.md5publ_computed, db.import_redirect.md5publ_final)
    return {redir.md5publ_computed: redir.md5publ_final for redir in redirects}

def load_places(db=None):
    if db is None:
        db = current.db

    places = db().select(db.place.id, db.place.place)
    return {place.place: place.id for place in places}

def place_to_place_id(places_dict, place, db=None):
    # see bellow: if db is None: db = current.db
    if not place:
        return None
    place_id = places_dict.get(place)
    if not place_id:
        if db is None:
            db = current.db
        place_id = db.place.insert(place=place)
        places_dict[place] = place_id
    return place_id

def set_imp_proc(library_id, proc=2.0, db=None):
    if db is None:
        db = current.db

    library = db.library[library_id]
    if proc > library.imp_proc:
        db.library[library_id] = {'imp_proc': min(proc, 100.0)}
        db.commit()


def set_imp_finished(library_id, db=None):
    set_imp_proc(library_id, proc=100.0, db=db)
