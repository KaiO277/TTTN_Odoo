import math
import json
import logging

from odoo import http
from odoo.http import request, Response
from collections import defaultdict
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from ..service.attendance_service import AttendanceService
from ..utils.jwt_helper import xink_check_auth_and_company, xink_get_roles_by_user
from ..utils.response_helper import *
from ..utils.datetime_helper import xink_format_to_iso_utc

_logger = logging.getLogger(__name__)


class XinkCheckInOutController(http.Controller):

    @http.route('/api/check_in_out/latest', type='http', auth='none', methods=['GET'], csrf=False)
    def get_latest_check_type(self):
        try:
            # Check token
            res = xink_check_auth_and_company()
            if isinstance(res, Response):
                return res
            user, company_id = res
            if not company_id:
                return xink_json_response_error('Unauthorized', 401)

            try:
                latest_inout = AttendanceService.latest_inout(user.id)
                if latest_inout['status_code'] == 200:
                    return xink_json_response_ok(latest_inout['message'])
                else:
                    return xink_json_response_error(latest_inout['message'], latest_inout['status_code'])
            except Exception as e:
                _logger.exception("Call Service.lastest_inout Error: " + str(e))
                return xink_json_response_error("Call Service.lastest_inout Error: " + str(e), 500)

        except Exception as e:
            _logger.exception("Check_in_out: exception: " + str(e))
            return xink_json_response_error("Internal Server Error: " + str(e), 500)

    @http.route('/api/check_in_out/date', type='http', auth='none', methods=['POST'], csrf=False)
    def get_check_in_out_by_date(self):
        try:
            # Check token
            res = xink_check_auth_and_company()
            if isinstance(res, Response):
                return res
            user, company_id = res
            if not company_id:
                return xink_json_response_error('Unauthorized', 401)

            # Read input from JSON body
            try:
                data = json.loads(request.httprequest.data or '{}')
            except json.JSONDecodeError:
                return xink_json_response_error("Invalid JSON body.", 500)

            date_str = data.get('date')  # UTC

            try:
                date_str = date_str.replace("Z", "")
                target_datetime = datetime.fromisoformat(date_str)
            except ValueError:
                return xink_json_response_error("Invalid 'date' format", 400)

            start_date = target_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)

            # Get employee
            employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
            if not employee:
                return xink_json_response_error("Employee not found for the user.", 404)

            # Condition
            domain = [
                ('employee_id', '=', employee.id),
                ('check_in', '>=', start_date),
                ('check_in', '<', end_date)
            ]

            # Query
            attendances = request.env['hr.attendance'].sudo().search(domain, order='check_in asc')
            if not attendances:
                return xink_json_response_object(RootResponse(data={
                    'checkIn': None,
                    'checkInStatus': False,
                    'checkOut': None,
                    'checkOutStatus': False
                }).to_dict())

            earliest_check_in = min((r.check_in for r in attendances if r.check_in), default=None)
            latest_check_out = max((r.check_out for r in attendances if r.check_out), default=None)

            result = {
                'checkIn': xink_format_to_iso_utc(earliest_check_in) if earliest_check_in else None,
                'checkInStatus': True,
                'checkOut': xink_format_to_iso_utc(latest_check_out) if latest_check_out else None,
                'checkOutStatus': True
            }

            return xink_json_response_object(RootResponse(data=result).to_dict())
        except Exception as e:
            _logger.exception("Check_in_out: exception: " + str(e))
            return xink_json_response_error("Internal Server Error: " + str(e), 500)

    @http.route('/api/check_in_out/search', type='http', auth='none', methods=['POST'], csrf=False)
    def search_check_in_out(self):
        try:
            # Check token
            res = xink_check_auth_and_company()
            if isinstance(res, Response):
                return res
            user, company_id = res
            if not company_id:
                return xink_json_response_error('Unauthorized', 401)

            # Read input from JSON body
            try:
                data = json.loads(request.httprequest.data or '{}')
            except json.JSONDecodeError:
                return xink_json_response_error("Invalid JSON body.", 500)

            requested_user_id = data.get('userId')
            month = data.get('month')  # YYYY-MM
            start_date_str = data.get('startDate')  # YYYY-MM-DD
            end_date_str = data.get('endDate')  # YYYY-MM-DD
            page_index = int(data.get('pageIndex', 1))
            page_size = int(data.get('pageSize', 10))
            offset = (page_index - 1) * page_size

            # Get user_id
            if not requested_user_id or str(requested_user_id).strip().lower() == 'mine':
                target_user = user
            else:
                try:
                    user_id = int(requested_user_id)
                    target_user = request.env['res.users'].sudo().browse(user_id)
                    if not target_user.exists():
                        return xink_json_response_error("User not found.", 404)
                except ValueError:
                    return xink_json_response_error("Invalid userId", 400)

            # Tìm employee
            employee = request.env['hr.employee'].sudo().search([('user_id', '=', target_user.id)], limit=1)
            if not employee:
                return xink_json_response_error("Employee not found for the user.", 404)

            # Get filter time range
            if month:
                try:
                    start_date = datetime.strptime(month, "%Y-%m")
                    end_date = start_date + relativedelta(months=1)
                except ValueError:
                    return xink_json_response_error("Invalid 'month' format. Use YYYY-MM.", 400)
            elif start_date_str and end_date_str:
                try:
                    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d") + relativedelta(days=1)
                except ValueError:
                    return xink_json_response_error("Invalid 'start_date' or 'end_date'. Use YYYY-MM-DD.", 400)
            else:
                return xink_json_response_error("Missing 'month' or 'start_date' & 'end_date'.", 400)

            # 5. Condition
            domain = [
                ('employee_id', '=', employee.id),
                ('check_in', '>=', start_date),
                ('check_in', '<', end_date)
            ]

            # Query
            attendances = request.env['hr.attendance'].sudo().search(domain, order='check_in asc')

            grouped = defaultdict(list)
            for att in attendances:
                date_key = att.check_in.date()
                grouped[date_key].append(att)

            # Result object
            grouped_items = []
            for date, records in grouped.items():
                earliest_check_in = min(r.check_in for r in records if r.check_in)
                latest_check_out = max((r.check_out for r in records if r.check_out), default=None)

                in_latitude = next((r.in_latitude for r in records if r.check_in == earliest_check_in), None)
                in_longitude = next((r.in_longitude for r in records if r.check_in == earliest_check_in), None)
                out_latitude = next((r.out_latitude for r in records if r.check_out == latest_check_out), None)
                out_longitude = next((r.out_longitude for r in records if r.check_out == latest_check_out), None)

                total_work_duration = timedelta()
                for r in records:
                    if r.check_in and r.check_out:
                        total_work_duration += (r.check_out - r.check_in)

                total_work_hours = round(total_work_duration.total_seconds() / 3600.0, 2)

                grouped_items.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'employeeId': employee.id,
                    'employeeName': employee.name,
                    'checkIn': earliest_check_in.strftime('%Y-%m-%d %H:%M:%S') if earliest_check_in else None,
                    'inLatitude': in_latitude,
                    'inLongitude': in_longitude,
                    'checkOut': latest_check_out.strftime('%Y-%m-%d %H:%M:%S') if latest_check_out else None,
                    'outLatitude': out_latitude,
                    'outLongitude': out_longitude,
                    'totalSessions': len(records),
                    'totalWorkingHours': total_work_hours,
                    'isStillCheckedIn': any(r.check_out is False for r in records)
                })

            # Pagination
            total_records = len(grouped_items)
            total_pages = math.ceil(total_records / page_size) if page_size > 0 else 1
            paginated_result = grouped_items[offset: offset + page_size]

            root_response = RootResponse(data={
                'pageIndex': page_index,
                'pageSize': page_size,
                'totalPages': total_pages,
                'totalRecords': total_records,
                'results': paginated_result
            })

            return xink_json_response_object(root_response.to_dict())

        except Exception as e:
            _logger.exception("Check_in_out: search: " + str(e))
            return xink_json_response_error("Internal Server Error: " + str(e), 500)

    @http.route('/api/check_in_out', type='http', auth='none', methods=['POST'], csrf=False)
    def check_in_out(self):
        try:
            # Check token
            res = xink_check_auth_and_company()
            if isinstance(res, Response):
                return res
            user, company_id = res
            if not company_id:
                return xink_json_response_error('Unauthorized', 401)

            try:
                request.env.cr.execute("""SELECT id FROM hr_employee WHERE user_id = %s LIMIT 1""", (user.id,))
                row = request.env.cr.fetchone()
                if not row:
                    return xink_json_response_error("No employee linked to this user", 404)

                employee_id = row[0]
                employee = request.env['hr.employee'].sudo().browse(employee_id)
                if not employee:
                    return xink_json_response_error("No employee linked to this user.", 404)
            except Exception as ee:
                request.env.cr.rollback()
                return xink_json_response_error("Cannot get employee for user. " + str(ee), 500)

            last_attendance = (request.env['hr.attendance'].sudo()
                               .search([('employee_id', '=', employee.id)], order='check_in desc', limit=1))

            # 2. Read JSON body
            try:
                data = json.loads(request.httprequest.data or '{}')
            except json.JSONDecodeError:
                return xink_json_response_error("Invalid JSON body.", 400)

            check_type = data.get('checkType')
            latitude = float(data.get('latitude', 0.0))
            longitude = float(data.get('longitude', 0.0))
            network_name = data.get('networkName', '')
            check_time = data.get('checkTime', '')

            if check_type not in ['in', 'out']:
                return xink_json_response_error("Invalid check type. Use 'in' or 'out'.", 400)

            geo_info = {
                'latitude': float(data.get('latitude', 0.0)),
                'longitude': float(data.get('longitude', 0.0)),
                'browser': request.httprequest.user_agent.browser,
                'ip_address': request.httprequest.remote_addr,
                'check_time': check_time,
                'mode': data.get('mode', 'manual'),  # mode: 'manual', 'kiosk', 'systray'
            }
            if check_type == "in":
                if last_attendance and not last_attendance.check_out:
                    return xink_json_response_error("Already checked in, must check out first.", 400)
                att = AttendanceService.check_in(employee.id, geo_info)
            else:  # check_type == "out"
                if not last_attendance or last_attendance.check_out:
                    return xink_json_response_error("No active check-in record to check out.", 400)
                att = AttendanceService.check_out(employee.id, geo_info)

            # 3. Response object
            record_dict = {
                'id': att.id,
                'userId': user.id,
                'employeeId': employee.id,
                'checkType': check_type,
                'checkTime': check_time,
                'latitude': latitude,
                'longitude': longitude,
                'network': network_name
            }

            root_response = RootResponse(message=f'Check-{check_type} successful', data=record_dict)
            return xink_json_response_object(root_response.to_dict())

        except Exception as e:
            _logger.exception("Check_in_out: exception: " + str(e))
            return xink_json_response_error("Internal Server Error: " + str(e), 500)

    # -----------------------
    # -----------------------
    @http.route('/api/check_in_out/settings', type='http', auth='none', methods=['GET'], csrf=False)
    def get_check_in_out_setting(self):
        res = xink_check_auth_and_company()
        if isinstance(res, Response):
            return res
        user, company_id = res
        if not company_id:
            return xink_json_response_error('Unauthorized', 401)

        company = request.env['res.company'].sudo().browse(company_id)
        if not company.exists():
            return xink_json_response_error('Company not found', 404)

        data = {
            'checkinByWifi': company.xink_checkin_by_wifi,
            'checkinByLocation': company.xink_checkin_by_location
        }
        root_response = RootResponse(message='', data=data)
        return xink_json_response_object(root_response.to_dict())

    @http.route('/api/check_in_out/settings', type='http', auth='none', methods=['PUT'], csrf=False)
    def update_check_in_out_setting(self):
        res = xink_check_auth_and_company()
        if isinstance(res, Response):
            return res
        user, company_id = res
        if not company_id:
            return xink_json_response_error('Unauthorized', 401)

        roles = xink_get_roles_by_user(user)
        if not any(r.get('roleId') == 'group_xink_easy_checkin_admin' for r in roles):
            return xink_json_response_error('Not allowed to settings checkin', 400)

        try:
            data = json.loads(request.httprequest.data or '{}')
            company = request.env['res.company'].sudo().browse(company_id)
            if not company.exists():
                return xink_json_response_error('Company not found', 404)

            vals = {}
            if 'checkinByWifi' in data:
                vals['xink_checkin_by_wifi'] = bool(data['checkinByWifi'])
            if 'checkinByLocation' in data:
                vals['xink_checkin_by_location'] = bool(data['checkinByLocation'])

            if not vals:
                return xink_json_response_error('No valid fields to update', 400)

            company.write(vals)
            data = {
                'checkinByWifi': company.xink_checkin_by_wifi,
                'checkinByLocation': company.xink_checkin_by_location
            }
            root_response = RootResponse(data=data)
            return xink_json_response_object(root_response.to_dict())

        except Exception as e:
            return xink_json_response_error('Update failed: ' + str(e), 500)
