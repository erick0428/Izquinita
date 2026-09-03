from odoo import models, fields,api
from odoo.exceptions import ValidationError

class AttendanceItem(models.Model):
    _name = 'tindahan.attendance_item'
    _description = 'attendance Item'


    attendance_id = fields.Many2one(
        'tindahan.attendance',
        ondelete='cascade'
    )
   
    amount = fields.Float('Amount',required=True)
    employee_id = fields.Many2one(
        'tindahan.employee',
        required=True
    )
    status = fields.Selection(
        [
            ('not_paid', 'UNPAID'),
            ('paid', 'PAID'),
        ],
        default='not_paid',
        string='Status',
    )
        
   
    