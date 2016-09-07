# -*- coding: utf-8 -*-

import re


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

def parse_pubyear(pubyear):
    numbers = re.findall(r'\d+', pubyear)
    syear2 = numbers[-1:]
    syear1 = numbers[-2:-1] or syear2
    nyear1 = syear1 and int(syear1[0]) or 0
    nyear2 = syear2 and int(syear2[0]) or 0
    if nyear1 < 100:                      # 1993 -> (1993,1993)
        nyear1 = nyear2
    elif 0 < nyear2 < 10:                 # 1990-2 -> (1990,1992)
        nyear2 += int(nyear1 / 10) * 10
    elif nyear2 < 100:                    # 1990-92 -> (1990,1992), 1989-91 -> (1989,1991)
        nyear2 += int(nyear1 / 100) * 100
    if nyear1 > 100 and nyear2 > 100:
        return (nyear1, nyear2)
    else:
        return (None, None)


# librarian (impressions agenda)

def analyze_barcode(barcode):
    """analyze the barcode to make possiible incrementing for different barcode formats
    works together with format_barcode()
    first found number is intended to be incremented, other parts will remain same

    Returns tuple:
        incr_from - position where the number starts
        len_digits - length of the number (count of digits)
        barcode_no - barcode number (as integer)
    """
    match = re.search(r'\d+', barcode)
    if match:
        start = match.start()
        end = match.end()
        return start, end - start, int(barcode[start:end])
    else:
        return len(barcode), 0, 0

def format_barcode(previous, incr_from, len_digits, barcode_no):
    """will format the barcode number with numeric part 'barcode_no' using information from analyze_barcode()
    to obtain next barcode, 1) analyze_barcode() for previous|starting code, 2) increment barcode_no, call format_barcode()
    """
    return previous[:incr_from] + (len_digits * '0' + str(barcode_no))[-len_digits:] + previous[incr_from + len_digits:]

def next_iid(iid, part=1, maxlen=None):
    """
    Args:
        iid:  current iid; this will be incremented
        part: -1..disable incrementing, 0..increment 1st found number, 1..increment 2nd found number (for numbering styles like 2020/146)
        maxlen: if len() is larger, then will return text '= overflow ===='
    """
    def get_next(number):
        lnu = len(number)
        return ('%0' + str(lnu) + 'd') % (int(number) + 1)

    if part < 0 or iid is None:
        return iid
    numbers = re.findall(r'\d+', iid)
    if len(numbers) <= part:
        return iid   # not enough number-parts
    number = numbers[part]
    next = get_next(number)
    if part == 0 or number not in numbers[:part]:  # can be done easy, because we have no same ocurrence earlier
        new_iid = iid.replace(number, next)
    else:
        # do it the hard way: split in preceding numbers, do replacing in the rest, join back together
        before = []
        split_src = iid
        for pos in xrange(part):
            splitted = split_src.split(numbers[pos], 1)
            before.append(splitted[0] + numbers[pos])
            split_src = splitted[1]
        before.append(split_src.replace(number, next))
        new_iid = ''.join(before)
    if maxlen and len(new_iid) > maxlen:
        return ('= overflow ' + 50*'=')[:maxlen]
    return new_iid

def next_sgn_imp(sgn, sgsep, sgn_2, maxlen=None):
    """Provides impression signature as base signature extended with suffix.
    Then increments the suffix to be ready for next impression.

    Args:
        sgn:   base signature
        sgsep: separator
        sgn_2: suffix as single char: digit|uppercase-letter|lowercase-letter
        maxlen: if len() is larger, then will return text '= overflow ===='

    Returns:
        sgn_imp: complete signature
        sgn_2:   next suffix: digit:1,2,..9,10,11,.. letter:A,B,..,Z,ZA,..,ZZ,ZZA,..

    """
    def inkr_suffix(sfx):
        if sfx.isdigit():
            return str(int(sfx) + 1)
        elif sfx[-1] == 'z':
            return sfx + 'a'
        elif sfx[-1] == 'Z':
            return sfx + 'A'
        else:
            return sfx[:-1] + chr(ord(sfx[-1]) + 1)

    if sgn and sgn_2:
        new_sgn = sgn + sgsep + sgn_2
        if maxlen and len(new_sgn) > maxlen:
            return ('= overflow ' + 50*'=')[:maxlen], sgn_2
        return new_sgn, inkr_suffix(sgn_2)
    else:
        return sgn, sgn_2
