#!/usr/bin/env python
# -*- coding: utf-8 -*-

import thread

import redis

from gluon import current


locker = thread.allocate_lock()


def redis_app(*args, **vars):
    if hasattr(redis_app, 'r'):
        r = redis_app.r
    else:
        locker.acquire()  # prevent create more redis objects (regardless if it would work and share same data)
        r = redis.Redis(*args, **vars)
        redis_app.r = r
        locker.release()
    app_key = 'app:' + current.request.application
    app = r.get(app_key)
    if not app:
        locker.acquire()  # prevent set 2 different ids for same app
        app_id = '%s:' % r.incr('app:*')
        r.set(app_key, app_id)
        locker.release()
    return r, app


def redis_user(auth, *args, **vars):
    r, app_id = redis_app(*args, **vars)
    return r, '%s%s:' % (app_id, auth.user_id)
