# -*- coding: utf-8 -*-

from itertools import groupby

from gluon import current

from global_settings import DEFAULT_CURRENCY, SUPPORTED_CURRENCIES, TESTING_LIB_ID
from c2_db import PublLengths


# export for modules
current.auth = auth
current.db = db

auth.settings.create_user_groups = None

# dočasně, dokud ladíme první knihovnu
# TODO: nahradit mechanismem, kdy pro novou knihovnu bude povoleno, pro starou ověří mailem prvnímu uživateli
auth.library_id = auth.user and getattr(auth.user, 'library_id', None) or 1  # první z předvolených or zkušební
if type(auth.library_id) == list:
    auth.library_id = auth.library_id[0]

# TODO: přidej Objednávku do HACTIONS: bude zřejmě vyžadovat extra tabulku jen částečně zpracovaných knih
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
dtformat = T('%d.%m.%Y %H:%M', lazy=False)

"""deaktivovano
class UNIQUE_QUESTION(object):
    def __init__(self, error_message=T('dotaz už je ve frontě')):
        self.error_message = error_message
    def __call__(self, value):
        if db((db.question.question == value) & (db.question.auth_user_id == auth.user_id) & (db.question.live == True)
              ).select(db.question.id, limitby=(0, 1)):
            return (value, self.error_message)
        else:
            return (value, None)
"""


db.define_table('rgroup',
        Field('library_id', db.library,
              default=auth.library_id,
              readable=True, writable=False,
              ondelete='RESTRICT',
              label=T("Knihovna"), comment=T("jméno knihovny")),
        Field('rgroup', 'string', length=48,
              notnull=True, requires=IS_NOT_EMPTY(),
              label=T("Skupina"), comment=T("skupina čtenářů (např. pro školní knihovny školní třída")),
        common_filter=lambda query: db.rgroup.library_id == auth.library_id,
        singular=T("skupina čtenářů"), plural=T("skupiny čtenářů"),
        format='%(rgroup)s'
        )

db.define_table('reader',
        Field('library_id', db.library,
              default=auth.library_id,
              readable=False, writable=False,
              ondelete='CASCADE',
              label=T("Knihovna"), comment=T("jméno knihovny")),
        Field('lastname', 'string', length=32,
              notnull=True, requires=IS_NOT_EMPTY(),
              label=T("Příjmení"), comment=T("příjmení čtenáře")),
        Field('firstname', 'string', length=32,
              label=T("Jméno"), comment=T("křestní jméno čtenáře (a případně jeho/její další jména)")),
        Field('rgroup_id', db.rgroup,
              requires=IS_EMPTY_OR(IS_IN_DB(db, db.rgroup.id, '%(rgroup)s')), ondelete='SET NULL',
              label=T("Skupina"), comment=T("skupina čtenářů")),
        Field('email', 'string', length=64,
              label=T("E-mail"), comment=T("e-mail")),
        common_filter=lambda query: db.reader.library_id == auth.library_id,
        singular=T("čtenář"), plural=T("čtenáři"),
        format='%(lastname)s %(firstname)s'
        )

db.define_table('place',
        Field('library_id', db.library,
              default=auth.library_id,
              readable=False, writable=False,
              ondelete='CASCADE',
              label=T("Knihovna"), comment=T("jméno knihovny")),
        Field('place', 'string', length=64,
              notnull=True, requires=IS_NOT_EMPTY(),
              label=T("Umístění"),
              comment=T("umístění výtisků (např. regál, místnost nebo případně oddělení)")),
        Field('place_id', 'reference place',
              ondelete='RESTRICT', represent = lambda id, row: id and id.place or '',
              label=T("Nadřazené"), comment=T("patří do (širšího) umístění: takto lze vytvořit hierarchickou strukturu (oddělení, místnost, regál)")),
        common_filter=lambda query: db.place.library_id == auth.library_id,
        singular=T("umístění##singular"), plural=T("umístění##plural"),
        format='%(place)s'
        )
# TODO: čti on_define (book 6) při přechodu na lazy_tables
db.place.place_id.requires = IS_EMPTY_OR(IS_IN_DB(db, db.place.id, '%(place)s'))

db.define_table('stat_group',
        Field('library_id', db.library,
              default=auth.library_id,
              readable=False, writable=False,
              ondelete='CASCADE',
              label=T("Knihovna"), comment=T("jméno knihovny")),
        Field('tbl', 'string', length=1, default='I',
              notnull=True, requires=IS_IN_SET((('I', T("výtisky (exempláře)")), ('T', T("publikace (tituly)")),
                                                ('R', T("čtenáři")))),  #, ('B', T("výpůjčky"))
              label=T("Účel"), comment=T("ve kterém seznamu umožnit výběr této statistiky")),
        Field('stat_group', 'string', length=48,
              notnull=True, requires=IS_NOT_EMPTY(),
              label=T("Kategorie"), comment=T("statistická skupina, která se bude vyhodnocovat")),
        common_filter=lambda query: (db.stat_group.library_id == auth.library_id) & (db.stat_group.tbl == 'I'),
        singular=T("statistická skupina"), plural=T("statistická skupiny"),
        format='%(stat_group)s'
        )

db.define_table('question',
        Field('auth_user_id', db.auth_user, default=auth.user_id,
              readable=False, writable=False,
              ondelete='CASCADE',
              label=T("Uživatel"), comment=T("zadavatel dotazu")),
        Field('question', 'string', length=PublLengths.question,
              requires=IS_LENGTH(minsize=PublLengths.question_min, maxsize=PublLengths.question,
                            error_message=T("zadej %s až %s znaků") % (PublLengths.question_min, PublLengths.question)),
                        #UNIQUE_QUESTION()],
              label=T("Dotaz")),  # comment is dynamic in controller
        Field('asked', 'datetime',
              readable=False, writable=False,
              label=T("Zadáno"), comment=T("čas zadání dotazu")),
        Field('duration_z39', 'integer',
              readable=False, writable=False,
              label=T("Trvání stažení"), comment=T("doba do dokončení stažení dat [s]")),
        Field('duration_marc', 'integer',
              readable=False, writable=False,
              label=T("Trvání získání dat"), comment=T("doba do uložení nalezených knih [s]")),
        Field('duration_total', 'integer',
              readable=False, writable=False,
              label=T("Trvání celkem"), comment=T("doba do vytvoření indexů [s]")),
        Field('known', 'integer',
              readable=False, writable=False,
              label=T("Již známo"), comment=T("počet lokálně známých publikací")),
        Field('we_have', 'integer',
              readable=False, writable=False,
              label=T("Vlastněno"), comment=T("počet vyhovujících publikací v knihovně uživatele")),
        Field('retrieved', 'integer',
              readable=False, writable=False,
              label=T("Celkem získáno"), comment=T("počet nalezených publikací")),
        Field('inserted', 'integer',
              readable=False, writable=False,
              label=T("Nově získáno"), comment=T("nových (dosud nestažených)")),
        Field('live', 'boolean', default=True,
              readable=False, writable=False,
              label=T("Nezpracováno"), comment=T("čeká se na odpověď nebo její použití (katalogizaci)")),
        )

db.define_table('answer',
        Field('marc_id', 'integer',  # type integer and default=1(Aleph/cz) as long we do not support more marc dialects
              default=1, label=T("MARC dialekt"), comment=T("dialekt MARC jazyka")),
        Field('md5publ', 'string', length=32,
              label=T("md5publ"), comment=T("md5publ")),
        Field('md5marc', 'string', length=32,
              label=T("md5marc"), comment=T("md5marc")),
        Field('ean', 'string', length=20,
              label=T("Čarový kód EAN"), comment=T("čarový kód, vytištěný na publikaci")),
        Field('rik', 'string', length=5,
              readable=False, writable=False,
              label=T("Rychlá identifikace"), comment=T("rychlá identifikace knihy (obrácené pořadí)")),
        Field('country', 'string', length=PublLengths.country,
              label=T("Země vydání"), comment=T("země vydání")),
        Field('year_from', 'integer',
              label=T("Vydání od"), comment=T("vydání od roku")),
        Field('year_to', 'integer',
              label=T("Vydání do"), comment=T("vydání do roku")),
        Field('fastinfo', 'text',
              label=T("Hlavní údaje"), comment=T("hlavní údaje")),
        Field('marc', 'text',
              label=T("marc"), comment=T("marc")),
        )

db.define_table('authority',
        Field('name', 'string', length=96,
              label=T("Jméno"), comment=T("příjmení (bez tagu) a jméno (s tagy podpole) autority")),
        Field('atype', 'string', length=1, default="P",
              requires=IS_EMPTY_OR(IS_IN_SET((('P', T("osoba")), ('O', T("organizace, instituce")), ('E', T("událost, akce"))))),
              label=T("Typ autora"), comment=T("P")),
        Field('asex', 'string', length=1,
              requires=IS_EMPTY_OR(IS_IN_SET((('M', T("muž")), ('W', T("žena"))))),
              label=T("Pohlaví"), comment=T("pohlaví autora (fyzické osoby)")),
        Field('year1', 'integer',
              label=T("Narozen"), comment=T("rok narození (nebo začátek existence) pro vyhledávání")),
        Field('year2', 'integer',
              label=T("Zemřel"), comment=T("rok úmrtí (nebo začátek existence) pro vyhledávání")),
        Field('years', 'text',
              label=T("Roky"), comment=T("život (nebo existence) v letech (uvést, pokud roky nejsou známy přesně)")),
        Field('description', 'text',
              label=T("Další"), comment=T("další informace")),
        )

db.define_table('book_authority',
        Field('anser_id', db.answer,
              label=T("Publikace"), comment=T("publikace")),
        Field('authority_id', db.authority,
              label=T("Autorita"), comment=T("autorita")),
        Field('role', 'string', length=3,
              requires=IS_EMPTY_OR(IS_IN_SET((('aut', T("autor")), ('ilu', T("ilustrátor")),
                                              ('fot', T("fotograf")), ('prk', T("překladatel"))))),
              label=T("Role"), comment=T("role")),
        )

db.define_table('publisher',
        Field('name', 'string', length=128,
              label=T("Jméno"), comment=T("Jméno nakladatele")),
        Field('plocation', 'string', length=64,
              label=T("Sídlo"), comment=T("Místo vydání")),
        Field('country', 'string', length=PublLengths.country,
              label=T("Země vydání"), comment=T("země vydání")),
        Field('year1', 'integer',
              label=T("Začátek"), comment=T("začátek působení")),
        Field('year2', 'integer',
              label=T("Konec"), comment=T("konec působení")),
        )

db.define_table('book_publisher',
        Field('anser_id', db.answer,
              label=T("Publikace"), comment=T("publikace")),
        Field('publisher_id', db.publisher,
              label=T("Nakladatel"), comment=T("nakladatel")),
        )

db.define_table('idx_long',
        Field('category', 'string', length=1,
              label=T("Kategorie"), comment=T("kategorie (typ) vyhledávacího údaje")),
        Field('item', 'string', length=PublLengths.ilong,
              label=T("Vyhledávací údaj"), comment=T("údaj publikace (dlouhý)")),
        )

db.define_table('idx_join',
        Field('answer_id', db.answer,
              ondelete='CASCADE',
              label=T("Odpověď"), comment=T("příslušnost k odpovědi")),
        Field('idx_long_id', db.idx_long,
              ondelete='CASCADE',
              label=T("Vyhledávací řetězec"), comment=T("příslušnost k vyhledávacímu řetězci")),
        Field('role', 'string', length=PublLengths.irole,
              label=T("Role"), comment=T("role, pořadí v sérii, apod.")),
        )

db.define_table('idx_short',
        Field('answer_id', db.answer,
              ondelete='CASCADE',
              label=T("Publikace"), comment=T("příslušnost k publikaci")),
        Field('category', 'string', length=1,
              label=T("Kategorie"), comment=T("kategorie (typ) vyhledávacího údaje")),
        Field('item', 'string', length=PublLengths.ishort,
              label=T("Vyhledávací údaj"), comment=T("údaj publikace (krátký)")),
        )

db.define_table('idx_word',
        Field('answer_id', db.answer,
              ondelete='CASCADE',
              label=T("Publikace"), comment=T("příslušnost k publikaci")),
        Field('word', 'string', length=PublLengths.iword,
              label=T("Vyhledávací údaj"), comment=T("údaj publikace (krátký)")),
        )

db.define_table('lib_descr',
        Field('answer_id', db.answer,
              notnull=True, ondelete='RESTRICT',
              label=T("Odpověď"), comment=T("příslušnost k odpovědi")),
        Field('descr', 'text',
              label=T("Popis"), comment=T("bibliografický popis, pozměněný pro potřeby knihovny")),
        )

db.define_table('owned_book',
        Field('library_id', db.library,
              default=auth.library_id,
              readable=False, writable=False,
              notnull=True, ondelete='RESTRICT',
              label=T("Knihovna"), comment=T("jméno knihovny")),
        Field('answer_id', db.answer,
              notnull=True, ondelete='RESTRICT',
              label=T("Odpověď"), comment=T("příslušnost k odpovědi")),
        Field('lib_descr_id', db.lib_descr,
              ondelete='RESTRICT',
              label=T("Popis"), comment=T("bibliografický popis, pozměněný pro potřeby knihovny")),
        Field('cnt', 'integer',
              default=0,
              label=T("Výtisků"), comment=T("počet výtisků v knihovně")),
        common_filter=lambda query: (db.owned_book.library_id == auth.library_id) & (db.owned_book.cnt > 0),
        )

db.define_table('partner',
        Field('library_id', db.library,
              default=auth.library_id,
              readable=False, writable=False,
              notnull=True, ondelete='RESTRICT',
              label=T("Knihovna"), comment=T("jméno knihovny")),
        Field('name', 'string', length=48,
              notnull=True, requires=IS_NOT_EMPTY(),
              label=T("Název"), comment=T("název nebo jméno obchodního partnera")),
        Field('state_reg', 'string', length=16,
              label=T("IČO"), comment=T("IČO/rč (státní identifikátor organizace nebo osoby)")),
        Field('vat_reg', 'string', length=18,
              label=T("DIČ"), comment=T("DIČ (daňový identifikátor organizace nebo osoby)")),
        Field('street', 'string', length=48,
              label=T("Ulice"), comment=T("adresa: ulice a č.domu")),
        Field('place', 'string', length=48,
              label=T("Místo"), comment=T("adresa: místo (město, obec)")),
        Field('plz', 'string', length=8,
              label=T("PSČ"), comment=T("poštovní směrovací číslo")),
        Field('email', 'string', length=64,
              label=T("EMail"), comment=T("hlavní emailová adresa")),
        Field('link', 'string', length=92,
              label=T("Odkaz"), comment=T("URL adresa (webové stránky, www)")),
        Field('contact', 'text',
              label=T("Kontakt"), comment=T("kontaktní osoba, telefony, další e-mailové adresy, apod.")),
        common_filter=lambda query: db.partner.library_id == auth.library_id,
        format=lambda row: ', '.join((row.name, row.place))
        )

bill_format = lambda row: ', '.join(filter(lambda item: item, (row['no_our'], row['htime'].strftime(dtformat)))) if row else ''
            # dict format row['..'] instead of Storage format must be used, because this is used for dict formatting too
db.define_table('bill',
        Field('library_id', db.library,
              default=auth.library_id,
              readable=False, writable=False,
              notnull=True, ondelete='RESTRICT',
              label=T("Knihovna"), comment=T("jméno knihovny")),
        Field('partner_id', db.partner,
              notnull=True, ondelete='RESTRICT',
              label=T("Partner"), comment=T("obchodní partner (např. dodavatel)")),
        Field('take_in', 'boolean', notnull=True, default=True,
              label=T("Příjem"), comment=T("nákup, získaný dar nebo přijatá MVS/zápůjčka (naskladňuji knihy)")),
        Field('gift', 'boolean', notnull=True, default=False,
              label=T("Dar"), comment=T("knihy trvale získané (nebo poskytnuté) darem")),
        Field('loan', 'string', length=2,
              requires=IS_EMPTY_OR(IS_IN_SET(HACTIONS_MVS_HINT)),
              label=T("Zápůjčka"), comment=T("(dočasná) meziknihovní výměna (MVS) nebo zápůjčka)")),
        Field('no_our', 'string', length=16,
              label=T("Naše číslo"), comment=T("naše číslo dokladu (nepovinné)")),
        Field('no_partner', 'string', length=18,
              label=T("Jejich číslo"), comment=T("číslo dokladu dodavatele nebo odběratele (nepovinné)")),
        Field('htime', 'datetime', default=datetime.datetime.utcnow(),
              notnull=True,
              label=T("Čas"), comment=T("čas nákupu (převodu, apod.); i když doklad obsahuje jen datum, je dobré zadat i přibližný čas, který se zapíše v historii výtisků")),
        Field('cnt_imp', 'integer', notnull=True, default=0, writable=False,
              label=T("Výtisků"), comment=T("počet výtisků, zadaných při zápisu dokladu")),
        Field('btotal', 'decimal(12,2)',
              notnull=True,
              label=T("Částka"), comment=T("celková částka na dokladu")),
        Field('bcurrency', 'string', length=3, default=DEFAULT_CURRENCY,
              notnull=True, requires=IS_IN_SET(SUPPORTED_CURRENCIES),
              label=T("Měna"), comment=T("měna")),
        Field('imp_added', 'datetime', writable=False,
              label=T("Zpracován"), comment=T("kdy byly zaznamenány všechny položky dokladu")),
        common_filter=lambda query: db.bill.library_id == auth.library_id,
        format=bill_format
        )

db.define_table('impression',
        Field('library_id', db.library,
              default=auth.library_id,
              readable=False, writable=False,
              notnull=True, ondelete='RESTRICT',
              label=T("Knihovna"), comment=T("jméno knihovny")),
        Field('answer_id', db.answer,
              notnull=True, ondelete='RESTRICT',
              readable=False, writable=False,
              label=T("Odpověď"), comment=T("příslušnost k odpovědi")),
        Field('owned_book_id', db.owned_book,
              notnull=True, ondelete='RESTRICT',
              readable=False, writable=False,
              label=T("Publikace (vlastní)"), comment=T("publikace - záznam, specifický pro tuto knihovnu")),
        Field('place_id', db.place,
              requires=IS_EMPTY_OR(IS_IN_DB(db, db.place.id, '%(place)s')), ondelete='SET NULL',
              label=T("Umístění"), comment=T("umístění výtisku")),
        Field('live', 'boolean', default=True,
              readable=False, writable=False,
              label=T("Platný výtisk"), comment=T("platný (nevyřazený) výtisk")),
        Field('gift', 'boolean', notnull=True, default=False,
              label=T("Dar"), comment=T("získáno darem")),
        Field('loan', 'boolean', default=False,
              readable=False, writable=False,
              label=T("Dočasná zápůjčka"), comment=T("meziknihovní výměna (MVS) nebo zápůjčka")),
        Field('iorder', 'integer',
              notnull=True, writable=False,
              label=T("Pořadové číslo"), comment=T("pořadové číslo výtisku")),
        Field('barcode', 'string', length=16,
              label=T("Čarový kód"), comment=T("čarový kód výtisku")),
        Field('registered', 'date', default=datetime.date.today(),
              notnull=True, writable=False,
              label=T("Evidován"), comment=T("datum zápisu do počítačové evidence")),
        Field('price_in', 'decimal(12,2)',
              label=T("Nákupní cena"),
              comment=T("nákupní nebo pořizovací cena výtisku (přepočtená na %s)") % (DEFAULT_CURRENCY)),
        Field('icondition', 'text',
              label=T("Stav"), comment=T("stav výtisku, poškození")),
        common_filter=lambda query: (db.impression.library_id == auth.library_id) & (db.impression.live == True),
        format=T('čís.') + ' %(iorder)s'
        )

db.define_table('impr_hist',
        Field('impression_id', db.impression,
              writable=False,
              notnull=True, ondelete='CASCADE',
              label=T("Výtisk"), comment=T("výtisk publikace")),
        Field('auth_user_id', db.auth_user, default=auth.user_id,
              writable=False,
              notnull=True, ondelete='SET NULL',
              label=T("Provedl"), comment=T("uživatel, který provedl akci")),
        Field('reader_id', db.reader,
              writable=False,
              ondelete='SET NULL',
              label=T("Čtenář"), comment=T("čtenář")),
        Field('bill_id', db.bill,
              writable=False,
              ondelete='RESTRICT',
              label=T("Doklad"), comment=T("doklad (např. účtenka, faktura, soupiska zápůjčky)")),
        Field('htime', 'datetime', default=datetime.datetime.utcnow(),
              notnull=True, writable=False,
              label=T("Čas"), comment=T("čas akce (v UTC)")),
        Field('haction', 'string', length=2, default='+o',
              notnull=True, requires=IS_IN_SET(HACTIONS), writable=False,
              label=T("Akce"), comment=T("provedená činnost")),
        )

def book_cnt_insert(flds, id):
    db((db.owned_book.id == flds['owned_book_id']) & (db.owned_book.library_id == auth.library_id),
           ignore_common_filters=True).update(cnt=db.owned_book.cnt + 1)  # without filter as long it contain cnt>0
def book_cnt_update(w2set, flds):
    impressions = w2set.select(db.impression.owned_book_id, db.impression.live)
    for impression in impressions:
        if impression.live is True and flds['live'] is False:
            db(db.owned_book.id == impression.owned_book_id).update(cnt=max(0, db.owned_book.cnt - 1))
        elif impression.live is False and flds['live'] is True:
            db(db.owned_book.id == impression.owned_book_id).update(cnt=db.owned_book.cnt + 1)
def book_cnt_delete(w2set):
    impressions = w2set.select(db.impression.owned_book_id, orderby=db.impression.owned_book_id)
    for key, group in groupby(impressions, lambda impression: impression.owned_book_id):
        db(db.owned_book.id == key).update(cnt=max(0, db.owned_book.cnt - len([bk for bk in group])))
db.impression._after_insert.append(book_cnt_insert)
db.impression._before_update.append(book_cnt_update)
db.impression._before_delete.append(book_cnt_delete)
