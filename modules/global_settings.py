# -*- coding: utf-8 -*-

# temporary:

USE_TZ_UTC = True   # use server timezone (Europe +1/+2) for all users

# ---------------

DEFAULT_CURRENCY = 'CZK'
SUPPORTED_CURRENCIES = ('CZK', 'EUR', 'PLZ', 'USD')

TESTING_LIB_ID = 1

# impressions history
HACTIONS = (('+o', T("zaevidován zpětně")), ('+g', T("získán jako dar")), ('+n', T("zaevidován - nový nákup")),
            ('--', T("vyřazen (bez dalších podrobností)")),
                ('-d', T("vyřazen (likvidován)")), ('-b', T("předán ke svázání (vyřazen)")),
                ('-g', T("vyřazen (darován)")), ('-n', T("odprodán")), ('-?', T("nezvěstný vyřazen")),
            ('+f', T("cizí dočasně zařazen (zapůjčený výtisk)")), ('-f', T("zapůjčený cizí vyřazen (vrácen zpět - odevzdán)")),
            ('o+', T("náš zapůjčený zařazen (byl vrácen zpět)")), ('o-', T("náš dočasně vyřazen (zapůjčen - předán)")),
            ('l+', T("vrácen")), ('l-', T("vypůjčen")),
            ('l!', T("upomínka")), ('ll', T("prodloužen vzdáleně")), ('lL', T("prodloužen fyzicky")),
            ('r*', T("revidován")), ('r?', T("označen jako nezvěstný")),
            )  # 'r?' status of the impression is active if 'r?' is the last item in the impr_hist
HACTIONS_TMP_LOST = 'r?'
HACTIONS_IN = tuple(filter(lambda ha: ha[0][0] == '+', HACTIONS))
HACTIONS_OUT = tuple(filter(lambda ha: ha[0][0] == '-', HACTIONS))
HACTIONS_MVS = (('+f', T("získali jsme cizí knihy odjinud")),
                ('-f', T("vrátili jsme cizí knihy")),
                ('o-', T("zapůjčili jsme naše knihy jinam")),
                ('o+', T("vrátily se nám naše knihy")))
HACTIONS_MVS_HINT = (('+f', T("cizí knihy dočasně získávám (současně označte Příjem)")),
                ('-f', T("cizí knihy vracím zpět - odevzdávám")),
                ('o-', T("naše knihy zapůjčuji - předávám")),
                ('o+', T("naše knihy se vrátily - zařazuji je zpět (je doporučeno označit Příjem)")))
