{
    'name': 'XINK - Stock Custom',
    'version': '1.0',
    'summary': 'Stock Custom',
    'author': 'Xink Tech - Xink SJG',
    'license': 'LGPL-3',
    'category': 'Xink-Tools',
    'depends': ['stock','base', 'stock_account'],
    'data': [
        'views/hide_print_button.xml',
        'views/hide_field_stock_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'xink_stock_custom/static/src/css/hide_activity_button.css',
        ],
    },
    'application': True,
    'installable': True,
    'auto_install': True
}