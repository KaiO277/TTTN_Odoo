from odoo import http
from odoo.http import request
import json
import logging
from datetime import datetime, timedelta
from ..utils.jwt_helper import xink_current_employee, xink_check_auth_and_company
from ..utils.response_helper import *

_logger = logging.getLogger(__name__)

# Activity Type Constants
class ActivityType:
    ALL = 'all'
    ASSIGNED = 'assigned'
    CREATED = 'created'

# Activity Status Constants  
class ActivityStatus:
    ALL = 'all'
    DONE = 'done'
    NOT_DONE = 'notDone'
    OVERDUE = 'overdue'
    IMPORTANT_WORK = 'importantWork'


class MailActivityController(http.Controller):
    
    def _get_activity_model(self):
        """Get mail.activity model"""
        return request.env['mail.activity'].sudo()
    
    def _format_activity_response(self, activity):
        """Format activity data for API response"""
        hash_tags = []
        if activity.xink_hash_tag_ids:
            for tag in activity.xink_hash_tag_ids:
                hash_tags.append({
                    'id': tag.id,
                    'name': tag.name,
                    'color': tag.color
                })
        
        return {
            'id': activity.id,
            'summary': activity.summary,
            'note': activity.note,
            'activityTypeId': activity.activity_type_id.id if activity.activity_type_id else None,
            'activityTypeName': activity.activity_type_id.name if activity.activity_type_id else None,
            'resName': activity.res_name,
            'resModel': activity.res_model,
            'resId': activity.res_id,
            'userId': activity.user_id.id if activity.user_id else None,
            'userName': activity.user_id.name if activity.user_id else None,
            'dateDeadline': activity.date_deadline.strftime('%Y-%m-%d') if activity.date_deadline else None,
            'dateDone': activity.date_done.strftime('%Y-%m-%d') if activity.date_done else None,
            'active': activity.active,
            'hashTags': hash_tags,
            'importantWork': activity.important_work if hasattr(activity, 'important_work') else False,
            'createDate': activity.create_date.strftime('%Y-%m-%d %H:%M:%S') if activity.create_date else None,
            'writeDate': activity.write_date.strftime('%Y-%m-%d %H:%M:%S') if activity.write_date else None,
        }

    @http.route('/api/mail-activities', type='http', auth='none', methods=['GET'], csrf=False)
    def get_activities(self):
        """
        GET /api/mail-activities
        Get list of mail activities with filters
        """
        try:
            res = xink_check_auth_and_company()
            if isinstance(res, Response):
                return res
            user, company_id = res
            if not company_id:
                return xink_json_response_error('Unauthorized', 401)
            
            page = int(request.params.get('page', 1))
            limit = int(request.params.get('limit', 20))
            date_from = request.params.get('dateFrom')
            date_to = request.params.get('dateTo')
            offset = (page - 1) * limit
            
            search_domain = request.params.get('search', '')
            hash_tags_param = request.params.get('hashTags', [])

            type_param = request.params.get('type', ActivityType.ALL)
            
            status_param = request.params.get('status', ActivityStatus.ALL)
            
            domain = []
            domain.append(('user_id', '=', user.id))
            domain.append(('active', 'in', [True, False]))
            
            if search_domain:
                domain.append(('summary', 'ilike', f'%{search_domain}%'))
                domain.append(('note', 'ilike', f'%{search_domain}%'))
                    
            hash_tags = []
            if hash_tags_param:
                try:
                    hash_tags = json.loads(hash_tags_param)
                    if not isinstance(hash_tags, list):
                        hash_tags = [hash_tags]
                except json.JSONDecodeError:
                    _logger.warning(f"hashTags param invalid JSON: {hash_tags_param}")

            if hash_tags:
                domain.append(('xink_hash_tag_ids.id', 'in', hash_tags))

            if type_param == ActivityType.ASSIGNED:
                domain.append(('user_id', '=', user.id))
                domain.append(('create_uid', '!=', user.id))
            elif type_param == ActivityType.CREATED:
                domain.append(('create_uid', '=', user.id))
                domain.append(('user_id', '=', user.id))
        
            if status_param == ActivityStatus.DONE:
                domain.append(('date_done', '!=', False))
            elif status_param == ActivityStatus.NOT_DONE:
                domain.append(('date_done', '=', False))
            elif status_param == ActivityStatus.OVERDUE:
                domain.append(('date_deadline', '<', datetime.now().strftime('%Y-%m-%d')))

            if date_from:
                try:
                    date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                    domain.append(('write_date', '>=', date_from_obj))
                except ValueError:
                    return xink_json_response_error("Invalid dateFrom format. Use YYYY-MM-DD", 400)
            
            if date_to:
                try:
                    date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                    domain.append(('write_date', '<', date_to_obj))
                except ValueError:
                    return xink_json_response_error("Invalid dateTo format. Use YYYY-MM-DD", 400)

            activities = request.env['mail.activity'].sudo().search(domain, limit=limit, offset=offset, order='date_deadline desc, id desc')
            activities_data = [self._format_activity_response(activity) for activity in activities]
            
            response_data = {
                'results': activities_data,
                'page': page,
                'limit': limit,
                'total': len(activities),
                'totalPages': (len(activities) + limit - 1) // limit
            }
            
            root_response = RootResponse(message='Successfully', data=response_data)
            return xink_json_response_object(root_response.to_dict())

        except Exception as e:
            _logger.error(f"Error getting activities: {str(e)}")
            return xink_json_response_error("Internal Server Error: " + str(e), 500)

    @http.route('/api/mail-activities/<int:activity_id>', type='http',  auth='none', methods=['GET'], csrf=False)
    def get_activity(self, activity_id):
        """
        GET /api/mail-activities/{id}
        Get single mail activity by ID
        """
        try:
            res = xink_check_auth_and_company()
            if isinstance(res, Response):
                return res
            user, company_id = res
            if not company_id:
                return xink_json_response_error('Unauthorized', 401)

            domain = [('id', '=', activity_id), ('user_id', '=', user.id),('active', 'in', [True, False])]
            
            _logger.info(f"Fetching activity {activity_id} for user {user.id}")
            activity = request.env['mail.activity'].sudo().search(domain, limit=1)

            if not activity:
                 return xink_json_response_error("Not found", 404)
            
            response_data = self._format_activity_response(activity)
            
            root_response = RootResponse(message='Successfully', data=response_data)
            return xink_json_response_object(root_response.to_dict())

            
        except Exception as e:
            _logger.error(f"Error getting activity {activity_id}: {str(e)}")
            return xink_json_response_error("Internal Server Error: " + str(e), 500)

    @http.route('/api/mail-activities', type='http', auth='none', methods=['POST'], csrf=False)
    def create_activity(self):
        """
        POST /api/mail-activities
        Create new mail activity
        """
        try:
            res = xink_check_auth_and_company()
            if isinstance(res, Response):
                return res
            user, company_id = res
            if not company_id:
                return xink_json_response_error('Unauthorized', 401)
            try:
                data = json.loads(request.httprequest.data or '{}')
            except json.JSONDecodeError:
                return xink_json_response_error("Invalid JSON body.", 400)

            domain = [('model', '=', 'res.partner')]
            model = request.env['ir.model'].sudo().search(domain, limit=1)
            
            hash_tags_data = data.get('hashTags', [])
            
            activity_data = {
                'user_id': user.id,
                'summary': data.get('summary', ''),
                'note': data.get('note', ''),
                'res_model': model.model,
                'res_model_id': model.id,
                'date_deadline': data.get('dateDeadline'),
                'res_id': 3,
                'activity_type_id': 4,
                'important_work': data.get('importantWork', False),
            }
            
            activity = request.env['mail.activity'].sudo().create(activity_data)
            
            if hash_tags_data:
                for tag_data in hash_tags_data:
                    if isinstance(tag_data, dict) and tag_data.get('name'):
                        request.env['xink.hash.tag'].sudo().create({
                            'name': tag_data.get('name'),
                            'color': tag_data.get('color', '#0066CC'),
                            'activity_id': activity.id
                        })
            return xink_json_response_ok('Successfully')
        except Exception as e:
            _logger.error(f"Error creating activity: {str(e)}")
            return xink_json_response_error("Internal Server Error: " + str(e), 500)

    @http.route('/api/mail-activities/action_done/<int:activity_id>', type='http', auth='none', methods=['PUT'], csrf=False)
    def action_done(self, activity_id):
        """
        PUT /api/mail-activities/action_done/{id}
        """
        try:
            res = xink_check_auth_and_company()
            if isinstance(res, Response):
                return res
            user, company_id = res
            if not company_id:
                return xink_json_response_error('Unauthorized', 401)

            domain = [('id', '=', activity_id), ('user_id', '=', user.id),('active', 'in', [True, False])]
            activity = request.env['mail.activity'].sudo().search(domain, limit=1)

            if not activity:
                return xink_json_response_error('Not found', 404)

            activity.action_done()

            return xink_json_response_ok('Successfully')

        except Exception as e:
            _logger.error(f"Error updating activity {activity_id}: {str(e)}")
            return xink_json_response_error("Internal Server Error: " + str(e), 500)

    @http.route('/api/mail-activities/<int:activity_id>', type='http', auth='none', methods=['DELETE'], csrf=False)
    def delete_activity(self, activity_id):
        """
        DELETE /api/mail-activities/{id}
        Delete mail activity
        """
        try:
            res = xink_check_auth_and_company()
            if isinstance(res, Response):
                return res
            user, company_id = res
            if not company_id:
                return xink_json_response_error('Unauthorized', 401)

            domain = [('id', '=', activity_id), ('user_id', '=', user.id),('active', 'in', [True, False])]
            activity = request.env['mail.activity'].sudo().search(domain, limit=1)
            
            if not activity.exists():
                return xink_json_response_error('Not found', 404)
            activity.unlink()
            return xink_json_response_ok('Successfully')

        except Exception as e:
            _logger.error(f"Error deleting activity {activity_id}: {str(e)}")
            return xink_json_response_error("Internal Server Error: " + str(e), 500)

    def _format_hash_tag_response(self, hash_tag):
        return {
            'id': hash_tag.id,
            'name': hash_tag.name,
            'color': hash_tag.color,
        }

    @http.route('/api/hash-tags', type='http', auth='none', methods=['GET'], csrf=False)
    def get_all_hash_tags(self):
        """
        GET /api/hash-tags
        Get all hash tags in the system (not filtered by activity)
        """
        try:
            res = xink_check_auth_and_company()
            if isinstance(res, Response):
                return res
            user, company_id = res
            if not company_id:
                return xink_json_response_error('Unauthorized', 401)
            
            page = int(request.params.get('page', 1))
            limit = int(request.params.get('limit', 50))
            search = request.params.get('search', '')
            offset = (page - 1) * limit
            
            domain = []
        
            if search:
                domain.append(('name', 'ilike', f'%{search}%'))

            total_count = request.env['xink.hash.tag'].sudo().search_count(domain)
            
            hash_tags = request.env['xink.hash.tag'].sudo().search(
                domain, 
                limit=limit, 
                offset=offset, 
                order='id desc'
            )
            
            hash_tags_data = [self._format_hash_tag_response(tag) for tag in hash_tags]
            
            response_data = {
                'results': hash_tags_data,
                'page': page,
                'limit': limit,
                'total': total_count,
                'totalPages': (total_count + limit - 1) // limit if total_count > 0 else 0
            }
            
            root_response = RootResponse(message='Successfully', data=response_data)
            return xink_json_response_object(root_response.to_dict())

        except Exception as e:
            _logger.error(f"Error getting all hash tags: {str(e)}")
            return xink_json_response_error("Internal Server Error: " + str(e), 500)