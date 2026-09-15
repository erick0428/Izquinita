from odoo import models, fields, api
from odoo.exceptions import UserError 
from odoo.exceptions import ValidationError  

from datetime import datetime
import urllib.parse
import logging
_logger = logging.getLogger(__name__)

class Attendance(models.Model):
    _name = 'tindahan.attendance'
    _description = 'Attendance'
    _order = "date desc"
    _sql_constraints = [
        (
            "order_name_unique",
            "unique(name)",
            "Attendance name already exists.",
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
    remarks = fields.Text('Remarks')
    date = fields.Date('Date', default=fields.Date.context_today)
    attendance_item_ids = fields.One2many(
        'tindahan.attendance_item',
        'attendance_id',
        string='Item List'
    )
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
                raise ValidationError("Attendance name already exists.")
            
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
        sequence = self.env["tindahan.sequence"].search([("name", "=", "Attendance")], limit=1)
        if not sequence:
            raise UserError("Sequence for 'Attendance' not configured in tindahan.sequence.")

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