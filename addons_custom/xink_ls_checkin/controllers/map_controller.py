# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

class MapViewController(http.Controller):

    @http.route('/xink_ls_checkin/get_locations', type='json', auth='user')
    def get_locations(self, employee_id=None, checkin_date=None, location=None, **kwargs):
        """
        Gọi model hr.attendance để lấy dữ liệu điểm check-in có lọc theo:
        - employee_id (ID của nhân viên)
        - checkin_date (ngày check-in, dạng YYYY-MM-DD)
        - location (tên shop nếu có)
        """
        _logger.info("📌 Gọi get_locations với employee_id=%s, checkin_date=%s, location=%s", employee_id, checkin_date, location)

        domain = []

        # Lọc theo employee_id nếu có
        if employee_id:
            try:
                domain.append(('employee_id', '=', int(employee_id)))
            except Exception as e:
                _logger.warning("⚠️ Không parse được employee_id: %s", e)

        # Lọc theo ngày nếu có
        if checkin_date:
            try:
                check_date = datetime.strptime(checkin_date, "%Y-%m-%d").date()
                domain += [
                    ('check_in', '>=', f"{check_date} 00:00:00"),
                    ('check_in', '<=', f"{check_date} 23:59:59")
                ]
            except Exception as e:
                _logger.warning("⚠️ Không parse được checkin_date: %s", e)

        # Lọc theo shop nếu có
        if location:
            domain.append(('xink_shop_name', '=', location))

        # Gọi hàm từ model
        attendance_model = request.env['hr.attendance'].sudo()
        result = attendance_model.get_attendance_records_json(domain=domain)

        return result

    @http.route('/xink_ls_checkin/get_employees', type='json', auth='user')
    def get_employees(self):
        """
        Lấy danh sách nhân viên
        """
        employees = request.env['hr.employee'].sudo().search([])
        result = [{'id': emp.id, 'name': emp.name} for emp in employees]
        _logger.info("📌 Đã lấy danh sách %s nhân viên", len(result))
        return result
