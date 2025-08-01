import logging

from werkzeug.exceptions import NotFound
from odoo import http
from odoo.exceptions import AccessDenied
from odoo.http import request
from ..utils.jwt_helper import xink_current_employee, xink_check_auth_and_company
from ..utils.response_helper import *

_logger = logging.getLogger(__name__)


class XinkAbsenceController(http.Controller):
    @http.route('/api/absence/types', type='http', auth='none', methods=['GET'], csrf=False)
    def absence_type(self):
        try:
            current_employee = xink_current_employee()
            if current_employee["status_code"] != 200:
                return xink_json_response_error(current_employee["message"], current_employee["status_code"])

            employee_id = current_employee["employee_id"]
            leave_types = request.env['hr.leave.type'].sudo().search([('active', '=', True)])
            result = []
            for leave_type in leave_types:
                base_data = {
                    "absenceTypeId": leave_type.id,
                    "absenceTypeName": leave_type.name,
                    "requiresAllocation": leave_type.requires_allocation,
                    "absenceValidationType": leave_type.leave_validation_type,
                    "requestUnit": leave_type.request_unit,
                }
                # Map lựa chọn theo request_unit
                unit = leave_type.request_unit or "day"
                base_data.update({
                    "allowMultipleDays": unit == "day",
                    "allowSingleDay": unit in ["day", "hour"],
                    "allowHalfDayMorning": unit in ["half_day", "hour"],
                    "allowHalfDayAfternoon": unit in ["half_day", "hour"]
                })

                if leave_type.requires_allocation == 'no':
                    base_data["remainingDays"] = None
                    result.append(base_data)
                    continue

                # Tính số ngày phân bổ và đã nghỉ
                total_allocated = sum(request.env['hr.leave.allocation'].sudo().search([
                    ('employee_id', '=', employee_id),
                    ('holiday_status_id', '=', leave_type.id),
                    ('state', '=', 'validate')
                ]).mapped('number_of_days'))

                total_taken = sum(request.env['hr.leave'].sudo().search([
                    ('employee_id', '=', employee_id),
                    ('holiday_status_id', '=', leave_type.id),
                    ('state', 'in', ['validate', 'confirm'])
                ]).mapped('number_of_days'))

                remaining_days = total_allocated - total_taken

                if remaining_days > 0:
                    base_data["remainingDays"] = remaining_days
                    result.append(base_data)

            root_response = RootResponse(message='', data=result)
            return xink_json_response_object(root_response.to_dict())

        except Exception as e:
            _logger.exception("absence_type: exception: " + str(e))
            return xink_json_response_error("Internal Server Error: " + str(e), 500)

    @http.route('/api/absence/request', type='http', auth='none', methods=['POST'], csrf=False)
    def absence_request(self):
        try:
            # Check token
            res = xink_check_auth_and_company()
            if isinstance(res, Response):
                return res
            user, company_id = res
            if not company_id:
                return xink_json_response_error('Unauthorized', 401)

            current_employee = xink_current_employee()
            if current_employee['status_code'] != 200:
                return xink_json_response_error(current_employee['message'], current_employee['status_code'])

            employee_id = current_employee['employee_id']

            # Read JSON body
            try:
                data = json.loads(request.httprequest.data or '{}')
            except json.JSONDecodeError:
                return xink_json_response_error("Invalid JSON body.", 400)

            leave_type_id = int(data.get('absenceTypeId'))
            request_type = data.get('requestType', 'day')  #: days-day-am-pm
            request_date_from = data.get('dateFrom')
            request_date_to = data.get('dateTo')
            private_name = data.get('reason', '')

            if request_type not in ['days', 'day', 'am', 'pm']:
                return xink_json_response_error("Invalid check type. Use 'days', 'day', 'am', 'pm'.", 400)

            leave_type = request.env['hr.leave.type'].sudo().browse(leave_type_id)
            if not leave_type.exists():
                return xink_json_response_error("Absence type not found.", 404)
            request_date_from_period = 'am' if request_type != 'pm' else 'pm'

            # Check overlap
            # overlap = request.env['hr.leave'].sudo().search([
            #     ('employee_id', '=', employee_id),
            #     ('state', 'not in', ['refuse', 'cancel']),
            #     ('request_date_from', '<=', request_date_to),
            #     ('request_date_to', '>=', request_date_from)
            # ], limit=1)
            # if overlap:
            #     return json_response_error(
            #         f"Absence request conflicts with existing leave (ID: {overlap.id}, {overlap.request_date_from} to {overlap.request_date_to}).",
            #         409
            #     )

            #  Input values
            input_leave = {
                'employee_id': employee_id,
                'user_id': user.id,
                'company_id': company_id,
                'holiday_status_id': leave_type.id,
                'state': 'confirm',
                'request_date_from_period': request_date_from_period,
                'request_date_from': request_date_from,
                'request_date_to': request_date_to,
                'private_name': private_name,  # reason
                'request_unit_half': request_type in ['am', 'pm']
            }

            absence = request.env['hr.leave'].sudo().with_context(
                mail_create_nosubscribe=True,
                tracking_disable=True,
                mail_auto_subscribe_no_notify=True,
                mail_activity_quick_update=False,
                x_no_auto_approval_notify=True
            ).create(input_leave)

            # Response object
            record_dict = {
                'id': absence.id,
                'userId': absence.user_id.id if absence.user_id else None,
                'absenceTypeId': leave_type.id,
                'absenceTypeName': leave_type.name,
                'state': absence.state,
                'requestType': request_type,
                'dateFrom': request_date_from,
                'dateTo': request_date_to,
                'reason': private_name,
                'durationDisplay': absence.duration_display,
                'numberOfDays': absence.number_of_days,
                'numberOfHours': absence.number_of_hours
            }

            root_response = RootResponse(message=f'Request absence successful', data=record_dict)
            return xink_json_response_object(root_response.to_dict())
        except Exception as e:
            _logger.exception("absence_request: exception: " + str(e))
            return xink_json_response_error("Internal Server Error: " + str(e), 500)
