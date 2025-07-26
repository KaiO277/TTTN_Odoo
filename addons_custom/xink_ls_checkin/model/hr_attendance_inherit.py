# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools import format_datetime
from odoo.exceptions import AccessError
import logging

_logger = logging.getLogger(__name__)

class HrAttendanceInherit(models.Model):
    _inherit = 'hr.attendance'

    xink_shop_name = fields.Char(string='Shop Name')
    xink_shop_owner_name = fields.Char(string='Shop Owner Name')
    xink_job_content = fields.Text(string='Job Content')
    xink_potential_customer = fields.Boolean(string='Potential Customer')

    @api.model
    def get_attendance_records_json(self, location=None, employee_id=None, domain=None, limit=None, offset=0):
        try:
            if domain is None:
                domain = []

            # Nếu truyền thêm location ngoài domain
            if location:
                domain.append(('xink_shop_name', '=', location))

            # Nếu truyền thêm employee_id ngoài domain
            if employee_id:
                domain.append(('employee_id', '=', int(employee_id)))

            _logger.info("📌 Calling get_attendance_records_json | User: %s | Domain: %s | Limit: %s | Offset: %s",
                         self.env.user.name, domain, limit, offset)

            records = self.search(domain, limit=limit, offset=offset)
            _logger.info("✅ Found %s records: %s", len(records), records.ids)

            result = []
            for rec in records:
                result.append({
                    'id': rec.id,
                    'xink_shop_name': rec.xink_shop_name or '',
                    'xink_shop_owner_name': rec.xink_shop_owner_name or '',
                    'employee_id': rec.employee_id.name or '',
                    'job_content': rec.xink_job_content or '',
                    'check_in': rec.check_in.strftime("%H:%M") if rec.check_in else False,
                    'xink_potential_customer': rec.xink_potential_customer or False,
                    'in_latitude': float(rec.in_latitude) if rec.in_latitude else 0.0,
                    'in_longitude': float(rec.in_longitude) if rec.in_longitude else 0.0,
                })

            _logger.debug("🟢 Result data: %s", result)
            return {"data": result}

        except AccessError as e:
            _logger.warning("🚫 AccessError: %s", e)
            return {"data": []}
        except Exception as e:
            _logger.error("❌ Unexpected error in get_attendance_records_json: %s", e)
            return {"data": []}
