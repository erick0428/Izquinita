from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError 
from psycopg2 import OperationalError
import time
from datetime import datetime

class POS(models.Model):
    _name = 'tindahan_pos.pos'
    _description = 'POS'
    _order = 'id desc'

    name = fields.Char(
        string='Reference',
        required=True,
        default='New',
        copy=False
    )
    customer_name = fields.Char(string="Customer") 
    session_id = fields.Many2one(
        'tindahan_pos.session',
        string='Session',
        required=True
    )
    line_ids = fields.One2many(
        'tindahan_pos.pos.line',
        'pos_id',
        string='Order Lines'
    )

    total = fields.Float(
        string='Total',
        compute='_compute_total',
        store=True
    )

    @api.depends('line_ids.subtotal')
    def _compute_total(self):
        for record in self:
            record.total = sum(
                line.subtotal
                for line in record.line_ids
            )
    def _generate_name(self):
        user = self.env.user
        today = datetime.now().date()

        sequence = self.env["tindahan_pos.sequence"].search([
            ("name", "=", "Sales"),
            ("user_id", "=", user.id),
        ], limit=1)

        # Create sequence per user if not exists
        if not sequence:
            sequence = self.env["tindahan_pos.sequence"].create({
                "name": "Sales",
                "user_id": user.id,
                "date": today,
                "count": 0,
            })

        # Reset daily per user
        if sequence.date != today:
            sequence.date = today
            sequence.count = 0

        while True:
            sequence.count += 1

            name = f"{datetime.now().strftime('%y%m%d')}-{user.id}-{str(sequence.count).zfill(5)}"

            if not self.search([('name', '=', name)]):
                break

        return name              
            
    @api.model_create_multi
    def create(self, vals_list):
        for attempt in range(3):
            try:
                session = self.env['tindahan_pos.session'].search(
                    [('state', '=', 'open')],
                    limit=1
                )

                if not session:
                    raise ValidationError("No open session. Please open POS first.")

                for vals in vals_list:
                    vals['session_id'] = session.id
                    vals["name"] = self._generate_name()                

                return super().create(vals_list)

            except OperationalError:
                if attempt == 2:
                    raise
                time.sleep(0.2)

    def action_open_session(self):
        self.create({
            'name': 'Session ' + fields.Datetime.now().strftime('%Y-%m-%d %H:%M'),
            'opening_cash': 0,
        })
    def action_close_session(self):
        for rec in self:
            rec.state = 'closed'
            rec.closing_cash = rec.total_sales        
class POSLine(models.Model):
    _name = 'tindahan_pos.pos.line'
    _description = 'POS Order Line'

    pos_id = fields.Many2one(
        'tindahan_pos.pos',
        string='POS',
        required=True,
        ondelete='cascade'
    )

    product_id = fields.Many2one(
        'tindahan_pos.product',
        string='Code',
        required=True
    )
    product_description = fields.Char(
        related='product_id.description',
        string='Name',
        store=True
    )

    variant_id = fields.Many2one(
        related='product_id.variant_id',
        string='Variant',
        store=True,
        readonly=True
    )

    quantity = fields.Float(
        string='Quantity',
        required=True,
        default=1.0
    )

    price = fields.Float(
        string='Price',
        related='product_id.srp',
        store=True,
        readonly=True
    )

    subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_subtotal',
        store=True
    )

    @api.depends('quantity', 'price')
    def _compute_subtotal(self):
        for record in self:
            record.subtotal = record.quantity * record.price

    @api.constrains('quantity')
    def _check_quantity(self):
        for record in self:
            if record.quantity <= 0:
                raise ValidationError(
                    'Quantity must be greater than zero.'
                )
                
                               