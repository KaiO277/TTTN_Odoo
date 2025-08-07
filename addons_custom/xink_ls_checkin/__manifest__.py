{
    "name": "XINK - Checkin",
    "summary": "Ls Checkin",
    "version": "1.0",
    "author": "Xink Tech - Xink SJG",
    "license": "LGPL-3",
    "category": "Xink-Tools",
    "depends": ["base_geolocalize", "contacts", "sale", "web", "hr_attendance"],
    "data": [
        "views/map_menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "web/static/src/xml/**/*",
            "xink_ls_checkin/static/src/js/map_demo_client_action.js",
            "xink_ls_checkin/static/src/xml/map_templates.xml",
            "xink_ls_checkin/static/src/css/map_view_scroll.css",
        ],
    },
    "external_dependencies": {
        "python": ["requests", "responses"],
    },
    "installable": True,
    "application": True,
    "auto_install": True,
}
