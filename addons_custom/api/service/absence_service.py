import logging
from datetime import datetime, time

from odoo.http import request

_logger = logging.getLogger(__name__)


class AbsenceService:

    @staticmethod
    def absence(input_leave):
        request.env.cr.execute("""
            INSERT INTO hr_leave (
                employee_id, 
                user_id, 
                company_id,
                employee_company_id,
                holiday_status_id, 
                state,
                request_date_from_period, 
                request_date_from,
                request_date_to,
                private_name, 
                request_unit_half,
                request_unit_hours, request_hour_from, request_hour_to,
                create_uid, create_date, write_uid, write_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE, 0, 0,
                %s, NOW() AT TIME ZONE 'UTC', %s, NOW() AT TIME ZONE 'UTC')
            RETURNING id
        """, (
            input_leave.get('employee_id'),
            input_leave.get('user_id'),
            input_leave.get('company_id'),
            input_leave.get('company_id'),
            input_leave.get('holiday_status_id'),
            input_leave.get('state'),
            input_leave.get('request_date_from_period'),
            input_leave.get('request_date_from'),
            input_leave.get('request_date_to'),
            input_leave.get('private_name'),
            input_leave.get('request_unit_half'),
            request.uid,
            request.uid
        ))

        leave_id = request.env.cr.fetchone()[0]
        leave_result = request.env['hr.leave'].sudo().browse(leave_id)

        leave_result._compute_department_id()
        leave_result._compute_resource_calendar_id()
        leave_result._compute_date_from_to()
        leave_result._compute_duration()
        leave_result._compute_duration_display()

        return leave_result
