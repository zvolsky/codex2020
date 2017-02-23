# -*- coding: utf-8 -*-

# natvrdo video-src
def play():
    return dict()

# src nastaveno pomoci js
def play2():
    return dict()

# not exposed pomoci controlleru
def play3():
    return dict()
def play3b():
    import os
    with open(os.path.join(os.getcwd(), 'applications', request.application, 'static', 'video/6')) as v:
        return v.read()
