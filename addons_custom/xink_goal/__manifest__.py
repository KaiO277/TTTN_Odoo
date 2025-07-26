{
    'name': 'Xink Goal',
    'version': '1.0',
    'summary': 'Manage sales targets for employees',
    'category': 'Xink-Tools',
    'author': 'Xink Tech - Xink SJG',
    'license': 'LGPL-3',
    'website': '',
    'depends': ['base', 'hr', 'sale'],
    'data': [
        'data/sales_target_sequence.xml',
        'security/ir.model.access.csv',
        'views/sales_target_views.xml',
        'views/menu.xml',
    ],
    # 'assets': {
    #     'web.assets_backend': [
    #         'xink_goal/static/src/xml/sales_target_form.xml',
    #     ],
    # },
    'installable': True,
    'application': True,
    'auto_install': True,
}