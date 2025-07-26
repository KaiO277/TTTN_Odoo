{
    'name': 'XINK - Custom Mail Template',
    'version': '1.0',
    'summary': 'Custom Mail Template',
    'license': 'LGPL-3',
    'category': 'Tools',
    'depends': ['base', 'sale_management', 'sale', 'mail', 'auth_signup', 'web', 'digest'],
    'data': [
        'views/digest_section_mobile.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/xink_mail_template_custom/static/src/js/custom_dialog.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': True,
}