from odoo import http
from odoo.http import request
import json
import os
import logging

_logger = logging.getLogger(__name__)

class WorkflowSimpleController(http.Controller):

    @http.route('/xink_workflow/get_workflow_data', type='http', auth='user')
    def get_workflow_data(self, module):
        workflow = request.env['xink.workflow.json'].sudo().search([
            ('module', '=', module),
            ('active', '=', True)
        ], limit=1)
        
        if not workflow:
            return json.dumps({
                'error': f'Không tìm thấy cấu hình workflow cho module: {module}'
            })
            
        result = {
            'id': workflow.id,
            'name': workflow.name,
            'module': workflow.module,
            'description': workflow.description,
            'data': workflow.data,
        }
        return json.dumps(result, default=str)
