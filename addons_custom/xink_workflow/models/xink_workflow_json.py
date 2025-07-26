from odoo import models, fields, api

class WorkflowJson(models.Model):
    _name = 'xink.workflow.json'
    _description = 'Workflow JSON Configuration'
    _order = 'created_at desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Workflow Name", required=True, help="Name of the workflow configuration")
    module = fields.Char(string="Module", required=True, help="Target module for this workflow")
    data = fields.Json(string="JSON Data", required=True, default=lambda self: {
        'workflow': {
            'name': 'Sample Workflow', 
            'mainflow': [], 
            'dependency': [], 
            'report': []
        }
    }, help="Workflow configuration in JSON format")
    created_at = fields.Datetime(string="Created At", default=fields.Datetime.now, readonly=True)
    updated_at = fields.Datetime(string="Updated At", default=fields.Datetime.now)
    active = fields.Boolean(string="Active", default=True)
    description = fields.Text(string="Description", help="Description of this workflow configuration")
    
    # Computed fields
    data_preview = fields.Text(string="Data Preview", compute="_compute_data_preview", store=False)
    
    @api.depends('data')
    def _compute_data_preview(self):
        for record in self:
            if record.data:
                import json
                try:
                    # Pretty print JSON for preview - without truncation to allow full view
                    record.data_preview = json.dumps(record.data, indent=2, ensure_ascii=False)
                except:
                    record.data_preview = str(record.data)
            else:
                record.data_preview = ""
    
    @api.model
    def create(self, vals):
        vals['created_at'] = fields.Datetime.now()
        vals['updated_at'] = fields.Datetime.now()
        return super().create(vals)
    
    def write(self, vals):
        vals['updated_at'] = fields.Datetime.now()
        return super().write(vals)
    
    def action_activate(self):
        """Activate the workflow configuration"""
        self.write({'active': True})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': f'Workflow "{self.name}" has been activated.',
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_deactivate(self):
        """Deactivate the workflow configuration"""
        self.write({'active': False})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success', 
                'message': f'Workflow "{self.name}" has been deactivated.',
                'type': 'warning',
                'sticky': False,
            }
        }
