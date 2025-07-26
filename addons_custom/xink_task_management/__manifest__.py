{
    'name': 'Xink Task Management',
    'version': '1.0',
    'summary': 'Quản lý công việc nội bộ',
    'category': 'Xink-Tools',
    'author': 'Xink Tech - Xink SJG',
    'license': 'LGPL-3',
    'website': '',
    'depends': ['base', 'mail','sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/task_activity_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
} 