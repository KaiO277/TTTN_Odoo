{
    'name': 'XINK - Workflow',
    'version': '1.0',
    'summary': 'Workflow',
    'author': 'Xink Tech - Xink SJG',
    'license': 'LGPL-3',
    'category': 'Xink-Tools',
    'depends': ['base', 'web', 'sale', 'stock', 'purchase', 'website', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/workflow_json_views.xml',
        'views/workflow_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'xink_workflow/static/src/js/workflow.js',
            'xink_workflow/static/src/css/workflow.css',
            'xink_workflow/static/src/xml/workflow_template.xml',
            'xink_workflow/static/src/data/*.json',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': True,
}