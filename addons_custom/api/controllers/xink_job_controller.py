import logging
import json
from datetime import datetime, timedelta
from werkzeug.exceptions import NotFound
from odoo import http, fields
from odoo.exceptions import AccessDenied, ValidationError
from odoo.http import request
from ..utils.jwt_helper import xink_current_employee, xink_check_auth_and_company
from ..utils.response_helper import *

_logger = logging.getLogger(__name__)


class XinkJobController(http.Controller):
    
    def _format_job_response(self, job):
        return {
            'id': job.id,
            'employeeId': job.employee_id.id,
            'employeeName': job.employee_id.name,
            'longitude': job.longitude,
            'latitude': job.latitude,
            'checkIn': job.check_in.isoformat() if job.check_in else None,
            'shopName': job.shop_name,
            'shopOwnerName': job.shop_owner_name,
            'phoneNumber': job.phone_number,
            'potentialCustomer': job.potential_customer,
            'jobContent': job.job_content,
            'jobNote': job.job_note,
            'locationDisplay': job.location_display,
            'displayName': job.display_name,
        }

    @http.route('/api/job/checkin', type='http', auth='none', methods=['POST'], csrf=False)
    def create_job_checkin(self):
        """Create a new job check-in record"""
        try:
            # Check authentication
            res = xink_check_auth_and_company()
            if isinstance(res, Response):
                return res
            user, company_id = res
            if not company_id:
                return xink_json_response_error('Unauthorized', 401)

            # Get current employee
            current_employee = xink_current_employee()
            if current_employee['status_code'] != 200:
                return xink_json_response_error(current_employee['message'], current_employee['status_code'])

            employee_id = current_employee['employee_id']

            try:
                data = json.loads(request.httprequest.data or '{}')
            except json.JSONDecodeError:
                return xink_json_response_error("Invalid JSON body.", 400)

            required_fields = ['shopName']
            for field in required_fields:
                if not data.get(field):
                    return xink_json_response_error(f"Field '{field}' is required.", 400)

            job_data = {
                'employee_id': employee_id,
                'longitude': data.get('longitude'),
                'latitude': data.get('latitude'),
                'check_in': data.get('checkIn', fields.Datetime.now()),
                'shop_name': data.get('shopName'),
                'shop_owner_name': data.get('shopOwnerName'),
                'phone_number': data.get('phoneNumber'),
                'potential_customer': data.get('potentialCustomer', False),
                'job_content': data.get('jobContent'),
                'job_note': data.get('jobNote'),
            }

            job = request.env['xink.job'].sudo().create(job_data)
            response_data = self._format_job_response(job)

            root_response = RootResponse(message='Job check-in created successfully', data=response_data)
            return xink_json_response_object(root_response.to_dict())

        except ValidationError as e:
            _logger.warning(f"Validation error in create_job_checkin: {str(e)}")
            return xink_json_response_error(str(e), 400)
        except Exception as e:
            _logger.exception("create_job_checkin: exception: " + str(e))
            return xink_json_response_error("Internal Server Error: " + str(e), 500)

    @http.route('/api/job/list', type='http', auth='none', methods=['GET'], csrf=False)
    def get_job_list(self):
        """Get list of job check-ins for current employee"""
        try:
            # Check authentication
            current_employee = xink_current_employee()
            if current_employee['status_code'] != 200:
                return xink_json_response_error(current_employee['message'], current_employee['status_code'])

            employee_id = current_employee['employee_id']

            # Get query parameters
            page = int(request.params.get('page', 1))
            limit = int(request.params.get('limit', 20))
            date_from = request.params.get('dateFrom')
            date_to = request.params.get('dateTo')
            offset = (page - 1) * limit

            domain = [('employee_id', '=', employee_id)]
            
            if date_from:
                try:
                    date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                    domain.append(('check_in', '>=', date_from_obj))
                except ValueError:
                    return xink_json_response_error("Invalid dateFrom format. Use YYYY-MM-DD", 400)
            
            if date_to:
                try:
                    date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                    domain.append(('check_in', '<', date_to_obj))
                except ValueError:
                    return xink_json_response_error("Invalid dateTo format. Use YYYY-MM-DD", 400)

            jobs = request.env['xink.job'].sudo().search(
                domain, 
                order='check_in desc', 
                limit=limit, 
                offset=offset
            )

            job_list = [self._format_job_response(job) for job in jobs]

            response_data = {
                'results': job_list,
                'page': page,
                'limit': limit,
                'total': len(jobs),
                'totalPages': (len(jobs) + limit - 1) // limit
            }

            root_response = RootResponse(message='Jobs retrieved successfully', data=response_data)
            return xink_json_response_object(root_response.to_dict())

        except Exception as e:
            _logger.exception("get_job_list: exception: " + str(e))
            return xink_json_response_error("Internal Server Error: " + str(e), 500)

    @http.route('/api/job/<int:job_id>', type='http', auth='none', methods=['GET'], csrf=False)
    def get_job_detail(self, job_id):
        """Get job detail by ID"""
        try:
            # Check authentication
            current_employee = xink_current_employee()
            if current_employee['status_code'] != 200:
                return xink_json_response_error(current_employee['message'], current_employee['status_code'])

            employee_id = current_employee['employee_id']

            # Get job
            job = request.env['xink.job'].sudo().search([
                ('id', '=', job_id),
                ('employee_id', '=', employee_id)
            ], limit=1)

            if not job:
                return xink_json_response_error("Job not found", 404)

            # Prepare response data
            response_data = self._format_job_response(job)

            root_response = RootResponse(message='Job retrieved successfully', data=response_data)
            return xink_json_response_object(root_response.to_dict())

        except Exception as e:
            _logger.exception("get_job_detail: exception: " + str(e))
            return xink_json_response_error("Internal Server Error: " + str(e), 500)

    @http.route('/api/job/<int:job_id>', type='http', auth='none', methods=['PUT'], csrf=False)
    def update_job(self, job_id):
        """Update job by ID"""
        try:
            res = xink_check_auth_and_company()
            if isinstance(res, Response):
                return res
            user, company_id = res

            current_employee = xink_current_employee()
            if current_employee['status_code'] != 200:
                return xink_json_response_error(current_employee['message'], current_employee['status_code'])

            employee_id = current_employee['employee_id']

            # Parse JSON body
            try:
                data = json.loads(request.httprequest.data or '{}')
            except json.JSONDecodeError:
                return xink_json_response_error("Invalid JSON body.", 400)

            job = request.env['xink.job'].sudo().search([
                ('id', '=', job_id),
                ('employee_id', '=', employee_id)
            ], limit=1)

            if not job:
                return xink_json_response_error("Job not found", 404)

            # Prepare update data
            update_data = {}
            updateable_fields = [
                'longitude', 'latitude', 'shopName', 'shopOwnerName', 
                'phoneNumber', 'potentialCustomer', 'jobContent', 'jobNote'
            ]

            field_mapping = {
                'shopName': 'shop_name',
                'shopOwnerName': 'shop_owner_name',
                'phoneNumber': 'phone_number',
                'potentialCustomer': 'potential_customer',
                'jobContent': 'job_content',
                'jobNote': 'job_note'
            }

            for field in updateable_fields:
                if field in data:
                    odoo_field = field_mapping.get(field, field)
                    update_data[odoo_field] = data[field]

            if update_data:
                job.write(update_data)

            response_data = self._format_job_response(job)

            root_response = RootResponse(message='Job updated successfully', data=response_data)
            return xink_json_response_object(root_response.to_dict())

        except ValidationError as e:
            _logger.warning(f"Validation error in update_job: {str(e)}")
            return xink_json_response_error(str(e), 400)
        except Exception as e:
            _logger.exception("update_job: exception: " + str(e))
            return xink_json_response_error("Internal Server Error: " + str(e), 500)

    @http.route('/api/job/<int:job_id>', type='http', auth='none', methods=['DELETE'], csrf=False)
    def delete_job(self, job_id):
        """Delete job by ID"""
        try:
            # Check authentication
            current_employee = xink_current_employee()
            if current_employee['status_code'] != 200:
                return xink_json_response_error(current_employee['message'], current_employee['status_code'])

            employee_id = current_employee['employee_id']

            # Get job
            job = request.env['xink.job'].sudo().search([
                ('id', '=', job_id),
                ('employee_id', '=', employee_id)
            ], limit=1)

            if not job:
                return xink_json_response_error("Job not found", 404)

            job.unlink()

            root_response = RootResponse(message='Job deleted successfully', data={'id': job_id})
            return xink_json_response_object(root_response.to_dict())

        except Exception as e:
            _logger.exception("delete_job: exception: " + str(e))
            return xink_json_response_error("Internal Server Error: " + str(e), 500)
