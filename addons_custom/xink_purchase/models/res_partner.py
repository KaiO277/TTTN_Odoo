from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    supplier_evaluation_ids = fields.One2many(
        'supplier.evaluation', 'supplier_id', string='Lịch sử đánh giá nhà cung cấp'
    )
    vendor_code = fields.Char(
        string='Mã nhà cung cấp', 
        copy=False, 
        index=True,
        readonly=True,
        default=lambda self: self._generate_vendor_code_default(),
        compute='_compute_vendor_code_auto',
        store=True
    )
    
    def _generate_vendor_code_default(self):
        if self.env.context.get('default_supplier_rank') or self.env.context.get('default_is_company'):
            vendor_code = self.env['ir.sequence'].next_by_code('res.partner.vendor')
            return vendor_code
        return False

    @api.model_create_multi
    def create(self, vals_list):        
        for vals in vals_list:
            is_supplier = vals.get('supplier_rank', 0) > 0
            is_company = vals.get('is_company', False)
            
            if is_supplier:
                vals['is_company'] = True
                is_company = True
            if is_company and not vals.get('vendor_code'):
                vendor_code = self.env['ir.sequence'].next_by_code('res.partner.vendor')
                if vendor_code:
                    vals['vendor_code'] = vendor_code
        
        records = super().create(vals_list)
        for record in records:
            
            if record.is_company and not record.vendor_code:
                vendor_code = self.env['ir.sequence'].next_by_code('res.partner.vendor')
                if vendor_code:
                    record.vendor_code = vendor_code
        return records

    def write(self, vals):
        result = super().write(vals)
        
        triggers = ['is_company', 'supplier_rank', 'name', 'vat', 'email', 'phone']
        if any(key in vals for key in triggers):
            for partner in self:                
                if (partner.is_company or partner.supplier_rank > 0) and not partner.vendor_code:
                    vendor_code = self.env['ir.sequence'].next_by_code('res.partner.vendor')
                    if vendor_code:
                        partner.sudo().vendor_code = vendor_code
        return result

    def generate_vendor_codes_for_existing_companies(self):
        companies_without_code = self.search([
            ('is_company', '=', True),
            ('vendor_code', '=', False)
        ])
        
        for company in companies_without_code:
            company.vendor_code = self.env['ir.sequence'].next_by_code('res.partner.vendor') or False
        
        return len(companies_without_code)
    @api.depends('is_company', 'supplier_rank')
    def _compute_vendor_code_auto(self):
        for record in self:
            if (record.is_company or record.supplier_rank > 0) and not record.vendor_code:
                vendor_code = self.env['ir.sequence'].next_by_code('res.partner.vendor')
                if vendor_code:
                    record.sudo().vendor_code = vendor_code