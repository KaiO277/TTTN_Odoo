from odoo import models


class ResUsers(models.Model):
    _inherit = 'res.users'

    def _notify_security_setting_update(self, subject, body):
        if self.env.context.get('no_notify'):
            return None
        return super()._notify_security_setting_update(subject, body)
