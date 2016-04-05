import re
import unicodedata

def stripAccents(s):
    """will replace accented characters with their basic ASCII characters)
    """
    return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))

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
