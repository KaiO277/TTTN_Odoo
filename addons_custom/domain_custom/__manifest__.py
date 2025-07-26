{
    'name': 'XINK - Custom Domains',
    'version': '1.0',
    'summary': 'Custom Domains',
    'author': 'Xink Tech - Xink SJG',
    'license': 'LGPL-3',
    'category': 'Xink-Tools',
    'depends': ['base', 'sale', 'account', 'stock', 'sales_team', 'sale_pdf_quote_builder'],
    'data': [
        'views/sale/custom_menu.xml',
        'views/sale/custom_button.xml'
    ],
    'application': True,
    'installable': True,
    'auto_install': True
}
