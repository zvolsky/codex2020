# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## Customize your APP title, subtitle and menus here
#########################################################################

#mz ++z
response.files.insert(0, URL('static', 'css/codex2020.css'))

logo_library = db(db.library.id == auth.library_id).select(db.library.library).first()
logo_library = logo_library.library if logo_library else ''
response.logo = DIV(
        A(SPAN('', _class="glyphicon glyphicon-home"),
            _class="navbar-brand",
            _href="%s" % URL('codex2020', 'default', 'index'),
            _title=T("zpět na hlavní stránku")
        ),
        A(B(logo_library),
            _class="navbar-brand",
            _href="%s" % URL('codex2020', 'library', 'choose_library'),
            _title=T("zvolit spravovanou knihovnu"),
            _id="menu-library", _style="xxx_background-color: gray"),
        )
#mz ++k
response.title = request.application.replace('_',' ').title()
response.subtitle = ''

## read more at http://dev.w3.org/html5/markup/meta.name.html
#mz ++z
response.meta.author = 'mojeknihovna.eu <admin@mojeknihovna.eu>'
response.meta.description = 'software for work with books'
response.meta.keywords = 'books, libraries, web2py, python'
#mz ++k
response.meta.generator = 'Web2py Web Framework'

## your http://google.com/analytics id
response.google_analytics_id = None

#########################################################################
## this is the main application menu add/remove items as required
#########################################################################

#mz ++z
response.menu = [
    (T('Info'), False, URL('default', 'wiki'), [
        (T('chci vlastní katalog'), False, URL('default', 'welcome'), []),
        (T('návod'), False, URL('default', 'wiki'), []),
        ]),
    (T('Fond'), False, URL('catalogue', 'find'), [
        (T('katalogizace'), False, URL('catalogue', 'find'), []),
        (T('import'), False, URL('upload', 'main'), []),
        (T('revize'), False, URL('pool', 'review'), []),
        (T('nenalezené v revizi'), False, URL('pool', 'missing'), []),
        (T('dlouhodobě nezvěstné'), False, URL('pool', 'lost'), []),
        ]),
    (T('Čtenáři'), False, '#', [
        (T('skupiny čtenářů'), False, URL('readers', 'groups'), []),
        (T('čtenáři'), False, URL('readers', 'readers'), []),
        ]),
    (T('Provoz'), False, '#', [
        (T('obchodní partneři'), False, URL('manage', 'partners'), []),
        (T('přehled dokladů'), False, URL('manage', 'bills'), []),
        (T('nový nákup/doklad'), False, URL('manage', 'new_bill'), []),
        ]),
    (T('Nastavení'), False, '#', [
        (T('volba katalogu/knihovny'), False, URL('library', 'choose_library'), []),
        (T('nastavení knihovny'), False, URL('library', 'library'), []),
        (T('umístění výtisků'), False, URL('library', 'places'), []),
        (T('statistické skupiny výtisků'), False, URL('library', 'stgri'), []),  # uses default common filter
        #(T('statistické skupiny titulů'), False, URL('library', 'stgrt'), []),
        #(T('statistické skupiny čtenářů'), False, URL('library', 'stgrr'), []),
        ###?? (T('statistické skupiny výpůjček'), False, URL('library', 'stgrb'), []),
        (T('vzhled'), False, URL('default', 'theme'), []),
        ]),
]

DEVELOPMENT_MENU = False  # request.is_local
#mz ++k

#########################################################################
## provide shortcuts for development. remove in production
#########################################################################

def _():
    # shortcuts
    app = request.application
    ctr = request.controller
    # useful links to internal and external resources
    response.menu += [
        (T('My Sites'), False, URL('admin', 'default', 'site')),
          (T('This App'), False, '#', [
              (T('Design'), False, URL('admin', 'default', 'design/%s' % app)),
              LI(_class="divider"),
              (T('Controller'), False,
               URL(
               'admin', 'default', 'edit/%s/controllers/%s.py' % (app, ctr))),
              (T('View'), False,
               URL(
               'admin', 'default', 'edit/%s/views/%s' % (app, response.view))),
              (T('DB Model'), False,
               URL(
               'admin', 'default', 'edit/%s/models/db.py' % app)),
              (T('Menu Model'), False,
               URL(
               'admin', 'default', 'edit/%s/models/menu.py' % app)),
              (T('Config.ini'), False,
               URL(
               'admin', 'default', 'edit/%s/private/appconfig.ini' % app)),
              (T('Layout'), False,
               URL(
               'admin', 'default', 'edit/%s/views/layout.html' % app)),
              (T('Stylesheet'), False,
               URL(
               'admin', 'default', 'edit/%s/static/css/web2py-bootstrap3.css' % app)),
              (T('Database'), False, URL(app, 'appadmin', 'index')),
              (T('Errors'), False, URL(
               'admin', 'default', 'errors/' + app)),
              (T('About'), False, URL(
               'admin', 'default', 'about/' + app)),
              ]),
          ('web2py.com', False, '#', [
             (T('Download'), False,
              'http://www.web2py.com/examples/default/download'),
             (T('Support'), False,
              'http://www.web2py.com/examples/default/support'),
             (T('Demo'), False, 'http://web2py.com/demo_admin'),
             (T('Quick Examples'), False,
              'http://web2py.com/examples/default/examples'),
             (T('FAQ'), False, 'http://web2py.com/AlterEgo'),
             (T('Videos'), False,
              'http://www.web2py.com/examples/default/videos/'),
             (T('Free Applications'),
              False, 'http://web2py.com/appliances'),
             (T('Plugins'), False, 'http://web2py.com/plugins'),
             (T('Recipes'), False, 'http://web2pyslices.com/'),
             ]),
          (T('Documentation'), False, '#', [
             (T('Online book'), False, 'http://www.web2py.com/book'),
             LI(_class="divider"),
             (T('Preface'), False,
              'http://www.web2py.com/book/default/chapter/00'),
             (T('Introduction'), False,
              'http://www.web2py.com/book/default/chapter/01'),
             (T('Python'), False,
              'http://www.web2py.com/book/default/chapter/02'),
             (T('Overview'), False,
              'http://www.web2py.com/book/default/chapter/03'),
             (T('The Core'), False,
              'http://www.web2py.com/book/default/chapter/04'),
             (T('The Views'), False,
              'http://www.web2py.com/book/default/chapter/05'),
             (T('Database'), False,
              'http://www.web2py.com/book/default/chapter/06'),
             (T('Forms and Validators'), False,
              'http://www.web2py.com/book/default/chapter/07'),
             (T('Email and SMS'), False,
              'http://www.web2py.com/book/default/chapter/08'),
             (T('Access Control'), False,
              'http://www.web2py.com/book/default/chapter/09'),
             (T('Services'), False,
              'http://www.web2py.com/book/default/chapter/10'),
             (T('Ajax Recipes'), False,
              'http://www.web2py.com/book/default/chapter/11'),
             (T('Components and Plugins'), False,
              'http://www.web2py.com/book/default/chapter/12'),
             (T('Deployment Recipes'), False,
              'http://www.web2py.com/book/default/chapter/13'),
             (T('Other Recipes'), False,
              'http://www.web2py.com/book/default/chapter/14'),
             (T('Helping web2py'), False,
              'http://www.web2py.com/book/default/chapter/15'),
             (T("Buy web2py's book"), False,
              'http://stores.lulu.com/web2py'),
             ]),
          (T('Community'), False, None, [
             (T('Groups'), False,
              'http://www.web2py.com/examples/default/usergroups'),
              (T('Twitter'), False, 'http://twitter.com/web2py'),
              (T('Live Chat'), False,
               'http://webchat.freenode.net/?channels=web2py'),
              ]),
        ]
if DEVELOPMENT_MENU: _()

if "auth" in locals(): auth.wikimenu() 
