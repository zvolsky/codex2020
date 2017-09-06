# -*- coding: utf-8 -*-

def index():
    """
    Warning:
        to edit wiki use plugin_manage_groups/group/wiki_editor and assign the approved user
        if you receive UNAUTHORIZED after this, please logout and login (clearing session is necessary)
    """
    return auth.wiki()

''' example:

## Search for books

- To search just enter the beginning of the word.

[[Search books /codex2020/default/index]]

## My own catalogue

- You are a library and you want have here your own catalogue ..
- You are the visitor and want to have online database of your books ..

[[Read more /codex2020/default/welcome]]

'''
