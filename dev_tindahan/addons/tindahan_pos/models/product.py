from odoo import models, fields,api
from odoo.exceptions import ValidationError

class Product(models.Model):
    _name = 'tindahan_pos.product'
    _description = 'Product'
    _inherit = ["mail.thread"]
    _order = "name"
    _sql_constraints = [
        (
            "order_name_unique",
            "unique(name)",
            "Product name already exists.",
        )
    ]
    
    name = fields.Char('Name',required=True)
    description = fields.Char('Description',required=True)
    image = fields.Binary('Image', attachment=True)
    cost = fields.Float('Cost', tracking=True )
    srp = fields.Float('Srp', tracking=True)
    variant_id = fields.Many2one(
            'tindahan_pos.variant',
            required=True
    )
    @api.constrains("name")
    def _check_name_unique(self):
        for rec in self:
            existing = self.search([
                ("id", "!=", rec.id),
                ("name", "=ilike", rec.name),
            ], limit=1)

            if existing:
                raise ValidationError("Product name already exists.")
            
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name"):
                vals["name"] = vals["name"].strip().upper()
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("name"):
            vals["name"] = vals["name"].strip().upper()
        return super().write(vals)      
   
    