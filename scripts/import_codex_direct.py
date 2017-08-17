# for debug purposes only

def do_import(imp_func, library_id, src_folder=None, full=False):
    # delayed imports
    def init_imp_codex():
        from import_codex import imp_codex
        return imp_codex

    auth.library_id = library_id
    imp_func = {'imp_codex': init_imp_codex}[imp_func]()
    if full:
        db(db.owned_book.library_id == library_id).update(found_at_last=False)
        db(db.impression.library_id == library_id).update(found_at_last=False)
        db.commit()
    imp_func(db, library_id, src_folder)
    db.commit()   # to be sure; but imp_func itself should commit (in chunks or so)

do_import("imp_codex", 2, src_folder="/home/www-data/web2py/applications/codex2020/imports/2/src", full=True)

#{"library_id": 2, "imp_func": "imp_codex", "full": true, "src_folder": "/home/www-data/web2py/applications/codex2020/imports/2/src"}
