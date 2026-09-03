from odoo import models, fields,api
from odoo.exceptions import ValidationError

class Employee(models.Model):
    _name = 'tindahan.employee'
    _description = 'Employee'
    
    name = fields.Char('Name')
    address = fields.Char('Address')
    phone_number = fields.Char('Phone No')
    mobile_number = fields.Char('Mobile No')
    email = fields.Char('Email')
    rate = fields.Float('Rate')
   
    @api.constrains("name")
    def _check_name_unique(self):
        for rec in self:
            existing = self.search([
                ("id", "!=", rec.id),
                ("name", "=ilike", rec.name),
            ], limit=1)

            if existing:
                raise ValidationError("Employee name already exists.")
            
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