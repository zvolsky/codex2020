# -*- coding: utf-8 -*-

'''
def __xxx():
    # alexandermendes/marc2excel

def __xxx2():
    # Flask-Z3950
    #   github.com/alexandermendes/Flask-Z3950
    #   pythonhosted.org/Flask-Z3950/
    # apt install libxml2-dev libxslt-dev python-dev lib32z1-dev
    # pip install Flask-Z3950
    from flask_z3950 import Z3950Manager
    class pseudoFlask(object):
        pass
    app = pseudoFlask()
    app.config = {}
    app.extensions = {}
    db_config = {"db": "Voyager", "host": "z3950.loc.gov", "port": 7090}
    app.config["Z3950_DATABASES"] = {"loc": db_config}
    z3950_manager = Z3950Manager(app)
    z3950_db = z3950_manager.databases['loc']
    dataset = z3950_db.search('ti=1066 and all that')
    print dataset.to_str()
    print dataset.to_json()
'''

from dal_idx import idx_restart, idx_schedule


@auth.requires_membership('admin')
def restart_idx():
    idx_restart()
    redirect(URL('start_idx'))


@auth.requires_membership('admin')
def start_idx():    # hint: use restart_idx()
    if DEBUG_SCHEDULER:
        idx()
        return 'Indexing finished.'
    else:
        if idx_schedule():
            return 'Task idx was added.'
        else:
            return 'Task idx already queued. Remove it from scheduler_task table (sysadmin/restart_idx/) if you want re-create it.'
