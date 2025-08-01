{
    'name': 'XINK - Custom API',
    'version': '1.0',
    'summary': 'Custom REST API',
    'author': 'Xink Tech - Xink SJG',
    'license': 'LGPL-3',
    'category': 'Xink-Tools',
    'depends': ['base','hr_holidays', 'mail', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/xink_mail_template_user_activate.xml',
        'data/xink_mail_template_reset_password.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False
}
