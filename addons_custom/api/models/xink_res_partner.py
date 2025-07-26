import uuid
import random
from datetime import timedelta
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    signup_token = fields.Char(string='Signup Token', copy=False, groups="base.group_erp_manager")
    signup_expiration = fields.Datetime(string='Signup Expiration', copy=False, groups="base.group_erp_manager")
    xink_reset_otp = fields.Char(string="Reset OTP")
    xink_reset_otp_expiration = fields.Datetime(string="OTP Expiration")
    xink_reset_otp_fail_count = fields.Integer(string="OTP Fail Count", default=0)

    def xink_generate_signup_token(self, expiration_minutes=60):
        for rec in self:
            rec.signup_token = str(uuid.uuid4())
            rec.signup_expiration = fields.Datetime.now() + timedelta(minutes=expiration_minutes)

    def xink_generate_reset_otp(self, expiration_minutes=15):
        for rec in self:
            rec.xink_reset_otp = str(random.randint(100000, 999999))
            rec.xink_reset_otp_expiration = fields.Datetime.now() + timedelta(minutes=expiration_minutes)
            rec.xink_reset_otp_fail_count = 0
