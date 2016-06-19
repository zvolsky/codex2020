# -*- coding: utf-8 -*-

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()

## app configuration made easy. Look inside private/appconfig.ini
from gluon.contrib.appconfig import AppConfig
## once in production, remove reload=True to gain full speed
#mz ++z
myconf = AppConfig(reload=request.is_local)
#mz ++k

if not request.env.web2py_runtime_gae:
    ## if NOT running on Google App Engine use SQLite or other DB
    db = DAL(myconf.take('db.uri'), pool_size=myconf.take('db.pool_size', cast=int), check_reserved=['all'])
                            #, fake_migrate_all=True)
else:
    ## connect to Google BigTable (optional 'google:datastore://namespace')
    db = DAL('google:datastore+ndb')
    ## store sessions and tickets there
    session.connect(request, response, db=db)
    ## or store session in Memcache, Redis, etc.
    ## from gluon.contrib.memdb import MEMDB
    ## from google.appengine.api.memcache import Client
    ## session.connect(request, response, db = MEMDB(Client()))

## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []
## choose a style for forms
response.formstyle = myconf.take('forms.formstyle')  # or 'bootstrap3_stacked' or 'bootstrap2' or other
response.form_label_separator = myconf.take('forms.separator')


## (optional) optimize handling of static files
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'
## (optional) static assets folder versioning
# response.static_version = '0.0.0'
#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - old style crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

from gluon.tools import Auth, Service, PluginManager

auth = Auth(db)
service = Service()
plugins = PluginManager()

#mz ++z
LIBRARY_TYPES = (('per', T("osobní knihovna")), ('pub', T("veřejná knihovna")), ('sch', T("školní knihovna")),
                 ('pri', T("knihovna firmy nebo instituce")), ('ant', T("antkvariát")),
                 ('bsr', T("knihkupec")), ('bsd', T("knižní velkoobchod, distribuce")), ('plr', T("nakladatel")),
                 ('tst', T("jen pro odzkoušení")), ('oth', T("jiné, nelze zařadit")),
                )
db.define_table('library',
        Field('library', 'string', length=128, requires=IS_NOT_EMPTY(),
              label=T("Jméno knihovny"), comment=T("jméno vaší knihovny")),
        Field('slug', 'string', length=32,
              requires=[IS_NOT_EMPTY(), IS_NOT_IN_DB(db, 'library.slug')],
              label=T("URL jméno"), comment=T("jméno do URL adresy [malá písmena, číslice, pomlčka/podtržítko]")),
        Field('street', 'string', length=48,
              label=T("Ulice"), comment=T("ulice (nepovinné)")),
        Field('city', 'string', length=48,
              label=T("Místo"), comment=T("město nebo obec")),
        Field('plz', 'string', length=8,
              label=T("PSČ"), comment=T("poštovní směrovací číslo obce")),
        Field('ltype', 'string', length=3, default=LIBRARY_TYPES[0][0],
              notnull=True, requires=IS_IN_SET(LIBRARY_TYPES),
              label=T("Typ knihovny"), comment=T("typ knihovny")),
        Field('old_system', 'string', length=48,
              label=T("Jiný systém"), comment=T("předchozí nebo hlavní evidenční knihovnický systém")),
        Field('created', 'datetime', default=datetime.datetime.utcnow(),
              notnull=True, writable=False,
              label=T("Vytvořeno"), comment=T("čas vytvoření evidence")),
        Field('completed', 'date',
              label=T("Dokončeno"), comment=T("datum dokončení zápisu fondu knihovny")),
        Field('review_date', 'date', default=datetime.date.today(),
              notnull=True, requires=[IS_NOT_EMPTY(), IS_DATE(format=T('%d.%m.%Y'))],
              label=T("Zahájení revize"), comment=T("den zahájení revize (vypíší se výtisky, nenalezené od tohoto data)")),
        Field('st_imp_id', 'boolean', notnull=True, default=False,  # libstyle[0] = I
              label=T("Přír.číslo ?"), comment=T("označte, pokud knihovna používá přírůstková čísla výtisků")),
        Field('st_imp_idx', 'integer', default=1,  # libstyle[1] = 0|1|2|.. which number-part of ID should be incremented
              label=T("Přír.číslo ?"), comment=T("označte, pokud knihovna používá přírůstková čísla výtisků")),
        Field('st_imp_ord', 'boolean', notnull=True, default=False,  # libstyle[2] = O
              label=T("Čís.výtisku ?"), comment=T("označte, pokud se má zobrazovat číslo výtisku jako rozlišení výtisků každé publikace")),
        Field('st_imp_rik', 'integer',  # libstyle[3] = 2/3/4/5/6
              notnull=True, default=3, requires=IS_INT_IN_RANGE(2, 7),
              label=T("Rychlá identifikace"), comment=T("kolikamístné číslo zobrazit pro rychlé hledání knihy z klávesnice? zvol podle velikosti knihovny: 2 - do počtu 50 výtisků, 3 - do 500, 4 - do 5000, 5 - nad 5000")),
        Field('st_imp_bc', 'boolean', notnull=True, default=False,  # libstyle[4] = B
              label=T("Čarové kódy ?"), comment=T("označte, pokud knihovna používá vlastní čarové kódy")),
        Field('st_imp_pl', 'boolean', notnull=True, default=False,  # libstyle[5] = P
              label=T("Umístění výtisku ?"), comment=T("označte, pokud chcete zapisovat, kde je výtisk umístěn (oddělení, místnost, regál, apod.)")),
        Field('st_imp_sg', 'boolean', notnull=True, default=False,  # libstyle[6] = G
              label=T("Signatura výtisku ?"), comment=T("označte, pokud používáte signatury a každý výtisk má mít unikátní")),
        Field('st_imp_sgsep', 'string', length=3, notnull=True, default='',  # libstyle[7:11] 7 is len (0|1|2|3), 8:11 are characters
              label=T("Oddělovač v signatuře"), comment=T("unikátní signatura výtisku (je-li použita): znak(y) pro oddělení dodatku")),
        Field('st_imp_sgmod1', 'string', length=1, notnull=True, default='',  # libstyle[11]
              label=T("Signatura, 1.výtisk"), comment=T("unikátní signatura výtisku (je-li použita): přídavný znak 1.výtisku (např. prázdný, a, A, 1)")),
        Field('st_imp_sgmod2', 'string', length=1, notnull=True, default='b',  # libstyle[12]
              label=T("Signatura, 2.výtisk"), comment=T("unikátní signatura výtisku (je-li použita): přídavný znak 2.výtisku (např. a, b, B, 2)")),
        Field('st_imp_st', 'boolean', notnull=True, default=False,  # libstyle[13] = s
              label=T("Stat.dělení výtisků ?"), comment=T("označte, pokud chcete pro účel statistiky rozdělovat výtisky (tip: i pro oddělení dosp/děts, pokud výtisky titulu mohou být přiděleny do různých oddělení)")),
        Field('st_tit_st', 'boolean', notnull=True, default=False,  # libstyle[14] = S
              label=T("Stat.dělení titulů ?"), comment=T("označte, pokud chcete pro účel statistiky rozdělovat tituly")),
        format='%(library)s'
        )

BOOTSTRAP_DEFAULT = 'slate'
auth.settings.extra_fields['auth_user'] = [
    Field('library_id', 'list:reference library',
          readable=False, writable=False, default=1,
          requires=IS_IN_DB(db, db.library.id, '%(library)s', multiple=(1, 9999999)),
          ondelete='SET NULL',
          label=T("Knihovna"), comment=T("přístup do knihoven")),
    Field('theme', 'string', length=16,
          readable=False, writable=False, default=BOOTSTRAP_DEFAULT,
          label=T("Vzhled"), comment=T("vzhled aplikace (styl/téma)")),
    Field('librarian', 'boolean', notnull=True, default=False, readable=True, writable=True,
          label=T("Vlastní databáze"), comment=T("označ, jestliže chceš vytvořit vlastní databázi (pro knihovnu [domácí zdarma] nebo knižní obchod)")),
    ]
#mz ++k

## create all tables needed by auth if not custom tables
auth.define_tables(username=False, signature=False)

## configure email
mail = auth.settings.mailer
mail.settings.server = 'logging' if request.is_local else myconf.take('smtp.server')
mail.settings.sender = myconf.take('smtp.sender')
mail.settings.login = myconf.take('smtp.login')

## configure auth policy
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True

#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################

## after defining tables, uncomment below to enable auditing
# auth.enable_record_versioning(db)
