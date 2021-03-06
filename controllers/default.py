# -*- coding: utf-8 -*-

'''imports in controllers:
    query: from search import handle_qb_form
    onbooklink: import urllib2
'''

'''settings in controllers:
    onbooklink: OBALKY_CACHE
'''

#mz ++z
def models():   # debug (broken migrations, ..)
    return 'models/db finished ok'

@auth.requires_membership('admin')
def diag():   # debug (broken migrations, ..)
    return dict()


def index():
    from search import get_qb_form, handle_qb_form

    public = db((db.library.is_public == True) &
                (db.library.slug != '') &
                (db.library.library != '')
            ).select(db.library.library, db.library.slug)
    lbslug = request.args(0)
    qbform = get_qb_form(lbslug)
    books = handle_qb_form(request.vars, lbslug=lbslug)  # (library, DIV) where library is: (.id, .library, .slug)
    return dict(form=qbform, public=public, books=books[1], library=books[0], news_status=books[2])


# @ajaxMethod
def onbooklink():
    OBALKY_CACHE = 'https://cache.obalkyknih.cz/api/books?isbn=%s'
    # https://cache.obalkyknih.cz/api/books?isbn=9788086964096
    # https://cache.obalkyknih.cz/api/books?multi=[{%22isbn%22:%22978-80-86964-09-6%22,  ...

    ean = request.vars.ean
    if ean:
        import simplejson
        import urllib2
        try:
            hnd = urllib2.urlopen(OBALKY_CACHE % ean)
            metadata = hnd.read()
            hnd.close()
            metadata = simplejson.loads(metadata)
            src = metadata[0]['cover_medium_url'].replace('cache.', 'www.').replace('http:', 'https:')
                    # cache. nefunguje, muselo by se hnat pres server; ale primo z prohlizece funguje www.
        except StandardError:
            src = ''
    return simplejson.dumps({'src': src})


def theme():
    """requires:
    - xxx.min.css in static/css/bootstrap/ (themes from https://bootswatch.com/)
    - added BOOTSTRAP_DEFAULT='slate' in db.py
    - added Field('theme', 'string', length=16, default=BOOTSTRAP_DEFAULT) in db.py, auth.settings.extra_fields['auth_user']
    - patched layout.html
    - redirect in default/index based on: not __active_theme()
    - link in menu
    """
    themes = ('bootstrap', 'cerulean', 'cosmo', 'cyborg', 'darkly', 'flatly', 'journal', 'lumen', 'paper', 'readable',
               'sandstone', 'simplex', 'slate', 'spacelab', 'superhero', 'united', 'yeti')
    new = False
    action = request.args(0)
    if action:
        if action == 'new':
            new = True
        elif action == 'set':
            wish = request.args(1)
            if wish and wish in themes:
                if auth.user:
                    db.auth_user[auth.user_id] = dict(theme=wish)
                    auth.user.theme = wish
                else:
                    session.theme = wish  # warning: admin/ app uses similar session.themes
                redirect(URL())
    active = __active_theme() or BOOTSTRAP_DEFAULT
    themes = [LI(A(B(theme) if theme == active else theme, _href=URL(args=('set', theme)), _class="list-group-item")) for theme in themes]
    return dict(themes=UL(*themes, _class="list-group"), new=new)

def __active_theme():
    return auth.user and auth.user.theme or session.theme


def welcome():
    return {}


def login_newdb():
    session.flash = T("Chcete-li si vytvořit vlastní databázi, přihlašte se, a pak zaškrtněte [Vlastní databáze]")
    redirect(URL('user', args=('login'), vars=request.vars))


def newdb():
    if auth.user and auth.user.librarian:
        redirect(URL('library', 'new'))
    else:
        session.flash = T("Chcete-li si vytvořit vlastní databázi, zaškrtněte [Vlastní_databáze]")
        redirect(URL('user', args=('profile')))


def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/bulk_register
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    also notice there is http://..../[app]/appadmin/manage/auth to allow administrator to manage users
    """
    #mz ++z plugin_splinter
    if db is not db0:
        auth.settings.keep_session_onlogout = True  # this will prevent to leave the TESTING database
    #mz ++k plugin_splinter

    #from mail_send import mail_send
    from plugin_mz import admin_mail

    def userinfo(form):
        return ('\n'
                + '\n' + form.vars.first_name
                + '\n' + form.vars.last_name
                + '\n' + form.vars.email)

    def on_new_user(usr):
        mail.send(admin_mail,
                  subject='%s - %s' % (request.env.http_host, T("nový uživatel")),
                  message=T("Přihlásil se nový uživatel:") + usr
                  )

    def on_new_lib(usr):
        mail.send(admin_mail,
                  subject='%s - %s' % (request.env.http_host, T("nová knihovna")),
                  message=T("Uživatel si zakládá knihovnu:") + usr
                  )
        redirect(URL('library', 'new'))

    def onaccept_new(form):
        usr = userinfo(form)
        on_new_user(usr)
        if form.vars.librarian:
            on_new_lib(usr)

    def onaccept_edit(form):
        if form.vars.librarian and (not auth.library_id or auth.library_id == [TESTING_LIB_ID]):
            on_new_lib(userinfo(form))

    auth.settings.register_onaccept.append(onaccept_new)
    auth.settings.profile_onaccept.append(onaccept_edit)
    return dict(form=auth())
#mz ++k

@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()
