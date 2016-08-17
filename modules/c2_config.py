# -*- coding: utf-8 -*-

def get_contact(myconf, item=None):
    """
        Find a suitable email receiver on admin (portal) side

        item: if used then contact.<item> key will be used (otherwise contact.contact and as last instance smtp.sender
    """
    try:
        return item and myconf.take('contact.' + item) or myconf.take('contact.contact')
    except BaseException:
        return myconf.take('smtp.sender')
