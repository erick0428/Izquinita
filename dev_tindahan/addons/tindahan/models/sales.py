from odoo import models, fields, api
from odoo.exceptions import UserError 
from odoo.exceptions import ValidationError  

from datetime import datetime
import urllib.parse
import logging
class Sales(models.Model):
    _name = 'tindahan.sales'
    _description = 'Sales'
    _order = "name"
    _sql_constraints = [
        (
            "order_name_unique",
            "unique(name)",
            "Sales name already exists.",
        )
    ]
    
    name = fields.Char(
        string='Reference No',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: '/',
        tracking=True
    )
    amount = fields.Float('Amount',required=True)
    date = fields.Date('Date', default=fields.Date.context_today)

    user_id = fields.Many2one(
        'res.users',
        string='User',
        default=lambda self: self.env.user
    )
    @api.constrains("name")
    def _check_name_unique(self):
        for rec in self:
            existing = self.search([
                ("id", "!=", rec.id),
                ("name", "=ilike", rec.name),
            ], limit=1)

            if existing:
                raise ValidationError("Sales name already exists.")
            
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Auto-generate name
            if not vals.get("name"):
                vals["name"] = self._generate_name()
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("name"):
            vals["name"] = vals["name"].strip().upper()
        return super().write(vals)      

    def _generate_name(self):
        sequence = self.env["tindahan.sequence"].search([("name", "=", "Sales")], limit=1)
        if not sequence:
            raise UserError("Sequence for 'Sales' not configured in tindahan.sequence.")

        current_year = datetime.now().strftime("%y")
        if sequence.year != current_year:
            sequence.year = current_year
            sequence.count = 0

        while True:
            sequence.count += 1
            name = f"{sequence.year}{str(sequence.count).zfill(5)}"
            if not self.search([('name', '=', name)]):
                break
        return name    
    