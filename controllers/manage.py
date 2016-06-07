# -*- coding: utf-8 -*-

from plugin_mz import formstyle_bootstrap3_compact_factory


@auth.requires_login()
def partners():
    db.partner.id.readable = False
    grid = SQLFORM.grid(db.partner,
            formstyle=formstyle_bootstrap3_compact_factory(),
            showbuttontext=False,
            csv=False
            )
    return dict(grid=grid)
