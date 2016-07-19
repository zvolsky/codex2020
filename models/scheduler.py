# -*- coding: utf-8 -*-

from z39 import get_from_large_library
from c2_marc import parse_Marc_and_updatedb

from gluon.scheduler import Scheduler

from plugin_splinter import run_for_server


def task_catalogize(question_id, question, asked):
    """the time consuming retrieve/parse/db-save action
    called from catalogue/find
    """
    asked = datetime.datetime.strptime(asked, '%Y-%m-%d %H:%M:%S.%f')  # JSON unpack str()
    warning, results = get_from_large_library(question)
    duration_z39 = datetime.datetime.utcnow()
    if warning:     # TODO: save warning value
        retrieved = inserted = 0
        duration_marc = None
    else:
        retrieved, inserted, duration_marc = parse_Marc_and_updatedb(results)
        duration_marc = round((duration_marc - asked).total_seconds(), 0)

    db.question[question_id] = {
            'duration_z39': round((duration_z39 - asked).total_seconds(), 0),
            'duration_marc': duration_marc,
            'duration_total': round((datetime.datetime.utcnow() - asked).total_seconds(), 0),
            'retrieved': retrieved, 'inserted': inserted}
    db.commit()

def run_tests(form_vars, urls):
    for url in urls:
        run_for_server(url, form_vars, myconf)


scheduler = Scheduler(db)
