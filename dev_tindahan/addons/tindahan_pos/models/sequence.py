from odoo import models, fields

class PosSequence(models.Model):
    _name = 'tindahan_pos.sequence'
    _description = 'Pos Sequence'
    
    name = fields.Char()
    user_id = fields.Many2one("res.users", required=True)
    date = fields.Date()
    count = fields.Integer(default=0)