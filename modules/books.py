# -*- coding: utf-8 -*-

def ean2isbn10(ean):
    """convert EAN to old version (10-char) ISBN
    before the call test if EAN is 978... EAN (no need to call with 979..)
    old version of EAN can but not must really exist (because book can have 13-char ISBN)
    """
    significant = ean[3:-1]
    return significant + check_digit_isbn10(significant)

def ean2issn(ean):
    """convert EAN to ISSN
    before the call test if EAN is 977... EAN
    """
    significant = ean[3:10]
    return significant + check_digit_isbn10(significant)

def check_digit_isbn10(firstninedigits):
    """Check sum ISBN-10 (works for ISSN too)"""
    firstninedigits = firstninedigits.replace('-', '').replace(' ', '')
    val = sum((i + 2) * int(x)
              for i, x in enumerate(reversed(firstninedigits)))
    remainder = int(val % 11)
    if remainder == 0:
        tenthdigit = 0
    else:
        tenthdigit = 11 - remainder
    if tenthdigit == 10:
        tenthdigit = 'X'
    return str(tenthdigit)

def check_digit_ean(firsttwelvedigits):
    """Check sum EAN"""
    checksum = 0
    for pos, digit in enumerate(firsttwelvedigits[:12]):
        if pos % 2:
            checksum += int(digit) * 3
        else:
            checksum += int(digit)
    return str(10 - checksum % 10)[-1:]

def isxn_to_ean(isxn):
    """for ISSN digits [10:12] will be set to 00 - printed EAN may be different in [10:12] position"""
    if not isxn:     # accepts None
        return ''
    isxn = isxn.strip()
    digits = ''.join(i for i in isxn if i.isdigit())
    cnt = len(digits)
    if cnt >= 12:
        ean = digits[:12]
    elif cnt >= 8 and isxn[:1] == 'M':
        ean = '9790' + digits[:8]
    elif cnt >= 9:
        ean = '978' + digits[:9]
    elif cnt >= 7:
        ean = '977' + digits[:7] + '00'
    else:
        return ''
    return ean + check_digit_ean(ean)

def can_be_isxn(txt):
    """to distinguish if the string can be ISxN or not
    warning: this returns True too: without control number and with invalid control number
    """
    txt = txt.replace('-', '').replace(' ', '')
    if txt[-1:] == 'X':
        txt = txt[:-1]    # check it without control digit which will give same result
    if txt[:1] == 'M':
        return 9 <= len(txt) <= 10 and txt[1:].isdigit()
    return len(txt) >= 7 and txt.isdigit() and len(txt) != 11

def add_missing_control(isxn):
    if len(isxn) in (7, 9):
        isxn += check_digit_isbn10(isxn)
    elif len(isxn) == 12:
        isxn += check_digit_ean(isxn)
    return isxn
