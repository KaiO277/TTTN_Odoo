import logging

from odoo.http import request
from ..utils.datetime_helper import xink_format_to_iso_utc

_logger = logging.getLogger(__name__)


class AttendanceService:

    @staticmethod
    def get_last_attendance(employee_id):
        request.env.cr.execute("""
            SELECT id, check_in, check_out FROM hr_attendance
            WHERE employee_id = %s
            ORDER BY check_in DESC
            LIMIT 1
        """, (employee_id,))
        row = request.env.cr.fetchone()
        return row if row else None

    @staticmethod
    def check_in(employee_id, geo_info):
        request.env.cr.execute("""
            INSERT INTO hr_attendance (
                employee_id,
                check_in,
                in_latitude,
                in_longitude,
                in_browser,
                in_ip_address,
                in_mode,
                create_uid,
                create_date,
                write_uid,
                write_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW() AT TIME ZONE 'UTC', %s, NOW() AT TIME ZONE 'UTC')
            RETURNING id
        """, (
            employee_id,
            geo_info.get('check_time'),
            geo_info.get('latitude'),
            geo_info.get('longitude'),
            geo_info.get('browser'),
            geo_info.get('ip_address'),
            geo_info.get('mode'),
            request.uid,
            request.uid
        ))

        att_id = request.env.cr.fetchone()[0]
        return request.env['hr.attendance'].sudo().browse(att_id)

    @staticmethod
    def check_out(employee_id, geo_info):
        last_att = AttendanceService.get_last_attendance(employee_id)

        if not last_att or last_att[2]:  # Nếu không có hoặc đã check_out
            return None

        att_id = last_att[0]
        request.env.cr.execute("""
            UPDATE hr_attendance
            SET
                check_out = %s,
                out_latitude = %s,
                out_longitude = %s,
                out_browser = %s,
                out_ip_address = %s,
                out_mode = %s,
                write_uid = %s,
                write_date = NOW() AT TIME ZONE 'UTC'
            WHERE id = %s
        """, (
            geo_info.get('check_time'),
            geo_info.get('latitude'),
            geo_info.get('longitude'),
            geo_info.get('browser'),
            geo_info.get('ip_address'),
            geo_info.get('mode'),
            request.uid,
            att_id
        ))

        return request.env['hr.attendance'].sudo().browse(att_id)

    @staticmethod
    def latest_inout(user_id):
        try:
            request.env.cr.execute("""SELECT id FROM hr_employee WHERE user_id = %s LIMIT 1""", (int(user_id),))
            row = request.env.cr.fetchone()
            if not row:
                return {'status_code': 404, 'message': 'No employee linked to this user.'}

            employee_id = row[0]
            employee = request.env['hr.employee'].sudo().browse(employee_id)
            if not employee:
                return {'status_code': 404, 'message': 'No employee linked to this user.'}
        except Exception as ee:
            request.env.cr.rollback()
            return {'status_code': 500, 'message': "Cannot get employee for user. " + str(ee)}

        last_att = (request.env['hr.attendance'].sudo()
                    .search([('employee_id', '=', employee.id)], order='check_in desc', limit=1))

        if last_att and not last_att.check_out:
            check_type = 'in'
            return {
                'status_code': 200,
                'message': check_type,
                'check_in': xink_format_to_iso_utc(last_att.check_in) if last_att.check_in else None,
                'check_out': None
            }
        elif last_att and last_att.check_out:
            check_type = 'out'
            return {
                'status_code': 200,
                'message': check_type,
                'check_in': xink_format_to_iso_utc(last_att.check_in) if last_att.check_in else None,
                'check_out': xink_format_to_iso_utc(last_att.check_out) if last_att.check_out else None
            }
        else:
            check_type = 'out'
            return {
                'status_code': 200,
                'message': check_type,
                'check_in': None,
                'check_out': None
            }

    @staticmethod
    def latest_inout_info(user_id):
        try:
            latest_inout = AttendanceService.latest_inout(user_id)
            if latest_inout['status_code'] == 200:
                latest_inout_info = {
                    'check_type': latest_inout['message'],
                    'check_in_time': latest_inout.get('check_in'),
                    'check_out_time': latest_inout.get('check_out')
                }
            else:
                latest_inout_info = {
                    'check_type': None,
                    'check_in_time': None,
                    'check_out_time': None
                }
        except Exception:
            latest_inout_info = {
                'check_type': None,
                'check_in_time': None,
                'check_out_time': None
            }
        return latest_inout_info
