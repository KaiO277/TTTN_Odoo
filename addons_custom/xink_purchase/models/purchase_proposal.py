from odoo import models, fields, api
from odoo.exceptions import UserError
from collections import defaultdict

class PurchaseProposal(models.Model):
    _name = 'purchase.proposal'
    _description = 'Phiếu đề xuất mua hàng'
    _order = 'date_request desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Tên đề xuất', required=True, default='New')
    department_id = fields.Many2one('hr.department', string='Phòng ban', default=lambda self: self._get_default_department())
    purpose = fields.Selection([
        ('purchase', 'Sản xuất'),
        ('sales', 'Bán hàng'),
        ('inventory', 'Kho'),
        ('marketing', 'Marketing'),
        ('research', 'Nghiên cứu'),
        ('development', 'Phát triển'),
        ('maintenance', 'Bảo trì'),
        ('other', 'Khác')
    ], string='Mục đích sử dụng', required=True, default='purchase', tracking=True)
      
    content = fields.Text('Nội dung đề xuất', help='Mô tả chi tiết nội dung đề xuất')
    date_request = fields.Date('Ngày đề xuất', default=fields.Date.context_today)
    usage_period = fields.Date('Thời gian sử dụng', default=fields.Date.context_today, help='Thời gian dự kiến sử dụng sản phẩm')
    
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('submitted', 'Đã gửi'),
        ('approved', 'Đã duyệt'),
        ('rejected', 'Từ chối'),
    ], string='Trạng thái', default='draft', tracking=True)
    line_ids = fields.One2many('purchase.proposal.line', 'proposal_id', string='Chi tiết đề xuất')
    note = fields.Text('Ghi chú')

    status_display = fields.Html(string="Hiển thị trạng thái", compute="_compute_status_display", sanitize=False)

    @api.depends('state')
    def _compute_status_display(self):
        label_map = {
            'draft': 'Nháp',
            'submitted': 'Đã gửi',
            'approved': 'Đã duyệt',
            'rejected': 'Từ chối',
        }
        for rec in self:
            state = rec.state or ''
            label = label_map.get(state, state)
            rec.status_display = (
                f'<span class="badge badge-{state}">{label}</span>'
            )

    def _get_default_department(self):
        """Lấy phòng ban mặc định của user hiện tại"""
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        if employee and employee.department_id:
            return employee.department_id.id
        return False

    def _get_supplier_price(self, product, vendor_id, quantity=1.0):
        if not product or not vendor_id:
            return 0.0
            
        supplier_infos = product.seller_ids.filtered(
            lambda s: s.partner_id.id == vendor_id and (
                s.product_id.id == product.id if s.product_id else True
            )
        )
        
        if not supplier_infos:
            supplier_infos = product.product_tmpl_id.seller_ids.filtered(
                lambda s: s.partner_id.id == vendor_id
            )
        
        if not supplier_infos:
            import logging
            _logger = logging.getLogger(__name__)
            _logger.info(f"No supplier info found for product {product.name} and vendor {vendor_id}")
            return 0.0
        best_price = 0.0
        for supplier_info in supplier_infos:
            if hasattr(supplier_info, 'pricelist_ids') and supplier_info.pricelist_ids:
                applicable_prices = supplier_info.pricelist_ids.filtered(
                    lambda p: p.min_quantity <= quantity
                ).sorted('min_quantity', reverse=True)
                
                if applicable_prices:
                    candidate_price = applicable_prices[0].price
                else:
                    candidate_price = supplier_info.price
            else:
                candidate_price = supplier_info.price
            
            if candidate_price > 0 and (best_price == 0 or candidate_price < best_price):
                best_price = candidate_price
        
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info(f"Supplier price for {product.name} from vendor {vendor_id}: {best_price}")
        
        return best_price

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('purchase.proposal') or 'New'
        return super().create(vals_list)

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        self.write({'state': 'approved'})
        PurchaseOrder = self.env['purchase.order']
        PurchaseOrderLine = self.env['purchase.order.line']
        action = False
        for proposal in self:
            vendor_lines = defaultdict(list)
            for line in proposal.line_ids:
                product = line.product_id
                if not product.seller_ids:
                    raise UserError(f"Sản phẩm {product.display_name} chưa có nhà cung cấp!")
                best_seller = min(product.seller_ids, key=lambda s: s.price if s.price else float('inf'))
                vendor_id = best_seller.partner_id.id
                vendor_lines[vendor_id].append(line)
            po_ids = []
            for vendor_id, lines in vendor_lines.items():
                vendor = self.env['res.partner'].browse(vendor_id)
                po_vals = {
                    'partner_id': vendor_id,
                    'origin': proposal.name,
                    'proposal_id': proposal.id,
                }
                if vendor.vendor_code:
                    po_vals['partner_ref'] = vendor.vendor_code
                
                po = PurchaseOrder.create(po_vals)
                for line in lines:
                    supplier_price = proposal._get_supplier_price(
                        line.product_id, 
                        vendor_id, 
                        line.quantity
                    )
                    
                    if supplier_price > 0:
                        final_price = supplier_price
                    elif line.estimated_price > 0:
                        final_price = line.estimated_price
                    else:
                        final_price = line.product_id.list_price or 0.0
                    
                    PurchaseOrderLine.create({
                        'order_id': po.id,
                        'product_id': line.product_id.id,
                        'name': line.product_name.get('vi_VN') if isinstance(line.product_name, dict) else line.product_name,
                        'product_qty': line.quantity, 
                        'product_uom': line.uom_id.id,
                        'price_unit': final_price,  
                    })
                po_ids.append(po.id)
            if len(po_ids) == 1:
                action = {
                    'type': 'ir.actions.act_window',
                    'res_model': 'purchase.order',
                    'view_mode': 'form',
                    'res_id': po_ids[0],
                    'target': 'current',
                }
            elif len(po_ids) > 1:
                action = {
                    'type': 'ir.actions.act_window',
                    'res_model': 'purchase.order',
                    'view_mode': 'tree,form',
                    'domain': [('id', 'in', po_ids)],
                    'target': 'current',
                }
        return action

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_reset(self):
        self.write({'state': 'draft'})


class PurchaseProposalLine(models.Model):
    _name = 'purchase.proposal.line'
    _description = 'Chi tiết dòng đề xuất'

    proposal_id = fields.Many2one('purchase.proposal', string='Phiếu đề xuất', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Sản phẩm', required=True)
    product_name = fields.Json('Tên sản phẩm')
    quantity = fields.Float('Số lượng', default=1.0)
    uom_id = fields.Many2one('uom.uom', string='ĐVT')
    specification = fields.Text('Đặc tính/quy cách kỹ thuật')
    estimated_price = fields.Float('Giá dự kiến')
    note = fields.Text('Ghi chú')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.uom_id = self.product_id.uom_id
            self.product_name = {
                'vi_VN': self.product_id.with_context(lang='vi_VN').name,
                'en_US': self.product_id.with_context(lang='en_US').name,
            }
        else:
            self.product_name = {}

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    proposal_id = fields.Many2one('purchase.proposal', string='Phiếu đề xuất')
