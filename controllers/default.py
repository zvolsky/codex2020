# -*- coding: utf-8 -*-

#mz ++z
def models():   # debug (broken migrations, ..)
    return 'models/db finished ok'

def index():
    if __active_theme():
        redirect(URL('wiki'))
    else:
        redirect(URL('theme', args=('new')))

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

def wiki():
    return auth.wiki()

def welcome():
    return {}

def pokus():
    mail.send('zvolsky@seznam.cz',
          subject='pokus',
          message=request.env.http_host
          )
    return 'xxx'

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
    #from mail_send import mail_send
    def onaccept(form):
        session.flash = T("Děkujeme. Registrace bude nyní čekat na schválení. Dostanete zprávu mailem.")
        mail.send('admin@' + request.env.http_host,
                  subject='%s - %s' % (request.env.http_host, T("nový uživatel")),
                  message=T("Přihlásil se nový uživatel:")
                          + '\n'
                          + '\n' + form.vars.first_name
                          + '\n' + form.vars.last_name
                          + '\n' + form.vars.email
                          + '\n' + form.vars.introduce
                  )

    auth.settings.register_onaccept.append(onaccept)
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
