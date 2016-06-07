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
                 ('oth', T("jiné, nelze zařadit")),
                )
db.define_table('library',
        Field('library', 'string', length=128,
              label=T("Jméno knihovny"), comment=T("jméno vaší knihovny")),
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
        format='%(library)s'
        )

auth.settings.extra_fields['auth_user'] = [
    Field('library_id', 'list:reference library',
          readable=False, writable=False, default=1,
          requires=IS_IN_DB(db, db.library.id, '%(library)s', multiple=(1, 9999999)),
          ondelete='SET NULL',
          label=T("Knihovna"), comment=T("přístup do knihoven")),
    Field('introduce', 'text',
          label=T("Představte se"),
          comment=T("budeme rádi, když napíšete, jak byste rád(a) tento portál používal(a), případně pracujete-li s knihami profesionálně, když uvedete, kde pracujete ... děkujeme")),
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
