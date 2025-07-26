{
    'name': 'XINK -Approval Workflow',
    'version': '1.0',
    'summary': 'Approval Workflow',
    'author': 'Xink Tech - Xink SJG',
    'license': 'LGPL-3',
    'category': 'Xink-Tools',
    'depends': [
        'base', 
        'web', 
        'mail', 
        'purchase',
        'hr'
    ],
    'data': [
        'security/approval_security.xml',
        'security/ir.model.access.csv',
        'views/approval_workflow_views.xml',
        'views/approval_menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
}
