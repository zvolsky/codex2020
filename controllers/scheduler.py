# -*- coding: utf-8 -*-

def status():
    sch = db(db.scheduler_run).select(orderby=~db.scheduler_run.id, limitby=(0,1)).first()
    if sch:
        return '%s %s<br /><br />%s' % (sch.status, sch.start_time.strftime('%Y.%m.%d %H:%M'), sch.traceback.replace('\n', '<br />'))
    else:
        return "scheduler_run: nothing found"
