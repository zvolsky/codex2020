# -*- coding: utf-8 -*-

@auth.requires_membership('admin')
def start_idx():
    if db((db.scheduler_task.application_name == 'codex2020/sysadmin') &
            (db.scheduler_task.task_name == 'idx')).select().first():
        return 'Task idx already queued. Remove it from scheduler_task table if you want re-create it.'
    else:
        scheduler.queue_task(
            idx,
            pargs=[],
            pvars={},
            start_time=datetime.datetime.now(),
            stop_time=None,
            timeout=2147483647,
            prevent_drift=False,
            period=20,
            immediate=False,
            repeats=0
        )
        return 'Task idx was added.'
