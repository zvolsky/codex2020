# -*- coding: utf-8 -*-

import re
import unicodedata


def stripAccents(s):
    """
        will replace accented characters with their basic ASCII characters)
    """
    if type(s) != unicode:  # if s is 2.7 string then auto-decode it from utf8
        s = s.decode('utf8')
    return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))


def hash_prepared(s, title=False):
    """
        string suitable for hashing if we want compare unsafe text sources
        example: Graz,Kärnten == Graz, Karnten == graz;kárnten
    """
    if title:
        s = re.sub('[@#?]', 'X', s)
        for item in re.findall('[0-9IVXLCDM]\s*-\s*[0-9IVXLCDM]', s):  # Story I-II. vs. Story III.
            s = s.replace(item, item.replace('-', 'Q'))
    return filter(lambda ch: ch.isalnum(), stripAccents(s)).lower()


def slugify(value, defaultIfEmpty='name', removeAccents=True, stringCoding='utf-8', connectChar='-'):
    """(from Django with small changes)
    Convert to ASCII. Convert spaces to hyphens.
    Remove characters that aren't alphanumerics, underscores, or hyphens.
    Convert to lowercase. Also strip leading and trailing whitespace.
    """
    if type(value) == str:
        value = unicode(value, stringCoding)
    if removeAccents:
        value = stripAccents(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub('[^\w\s-]', '-', value).strip().lower()
    value = re.sub('[-\s]+', '-', value)
    if not value.replace('-', '') and defaultIfEmpty:
        value = defaultIfEmpty
    if connectChar != '-':
        value = value.replace('-', connectChar).strip()
    return value


def shortened(txt, maxlen=12, tail='..'):
    if txt is None:
        return ''
    txt = txt.lstrip()[:maxlen + 10].replace('\n', '').replace('\r', '').replace('\t', ' ').strip()
    shorter = txt[:maxlen]
    if len(shorter) < len(txt):
        candidate = shorter.rsplit(' ', 1)[0]
        if maxlen > 6 and len(candidate) <= 3:
            candidate = shorter
        shorter = candidate + tail
    return shorter
