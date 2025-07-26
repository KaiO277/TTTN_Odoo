{
    'name': 'XINK - easyCheckin',
    'version': '1.0',
    'summary': 'For use with the easyCheckin mobile application',
    'author': 'Xink Tech - Xink SJG',
    'license': 'LGPL-3',
    'category': 'Xink-Tools',
    'depends': ['base', 'hr', 'hr_attendance', 'hr_holidays'],
    'data': [
        'security/security.xml',
        'security/access_rights.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}