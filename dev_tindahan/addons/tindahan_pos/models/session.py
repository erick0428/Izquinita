from odoo import models, fields, api
import time
from datetime import datetime
from odoo.exceptions import ValidationError
from psycopg2 import OperationalError
class POSSession(models.Model):
    _name = 'tindahan_pos.session'
    _description = 'POS Session'
    _order = 'id desc'

    name = fields.Char(default='New', required=True)

    state = fields.Selection([
        ('open', 'Open'),
        ('closed', 'Closed'),
    ], default='open')

    # Cash
    opening_cash = fields.Float(string="Opening Cash")
    closing_cash = fields.Float(
        string="Expected Closing Cash",
        readonly=True
    )
    closing_input = fields.Float(
        string="Actual Cash Counted"
    )

    pos_ids = fields.One2many(
        'tindahan_pos.pos',
        'session_id',
        string="Orders"
    )

    total_sales = fields.Float(
        compute="_compute_total_sales",
        store=True
    )
    total_cash = fields.Float(
        compute="_compute_total_cash",
        store=True
    )
    total_gcash = fields.Float(
        compute="_compute_total_gcash",
        store=True
    )
    total_df = fields.Float(
        compute="_compute_total_df",
        store=True
    )
    date = fields.Datetime(
        string='Date',
        readonly=True,
        default=fields.Datetime.now,
        copy=False
    )
   
    
    def _generate_name(self):
        user = self.env.user
        today = fields.Date.today()

        sequence = self.env["tindahan_pos.sequence"].search([
            ("name", "=", "Session"),
            ("user_id", "=", user.id),
        ], limit=1)

        if not sequence:
            sequence = self.env["tindahan_pos.sequence"].create({
                "name": "Session",
                "user_id": user.id,
                "date": today,
                "count": 0,
            })

        # Reset counter every day
        if sequence.date != today:
            sequence.write({
                "date": today,
                "count": 0,
            })

        sequence.count += 1

        return f"{today.strftime('%y%m%d')}-{user.id}-{sequence.count:03d}"

    
    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:
                   
            vals["name"] = self._generate_name()                

        return super().create(vals_list)      

  
    
     
    @api.depends('pos_ids.total')
    def _compute_total_sales(self):
        for rec in self:
            rec.total_sales = sum(
                order.total for order in rec.pos_ids
            )
    @api.depends('pos_ids.total', 'pos_ids.payment_type')
    def _compute_total_cash(self):
        for rec in self:
            rec.total_cash = sum(
                order.total
                for order in rec.pos_ids
                if order.payment_type == 'cash'
                and order.payment_status == 'paid'
            )


    @api.depends('pos_ids.total', 'pos_ids.payment_type')
    def _compute_total_gcash(self):
        for rec in self:
            rec.total_gcash = sum(
                order.total
                for order in rec.pos_ids
                if order.payment_type == 'gcash'
                and order.payment_status == 'paid'
            )
    @api.depends('pos_ids.delivery_fee')
    def _compute_total_df(self):
        for rec in self:
            rec.total_df = sum(rec.pos_ids.mapped('delivery_fee'))

            

    difference = fields.Float(
        compute="_compute_difference",
        store=True
    )

    @api.depends(
        'closing_input',
        'total_sales',
        'opening_cash'
    )
    def _compute_difference(self):
        for rec in self:
            expected = rec.opening_cash + rec.total_sales

            rec.difference = (
                rec.closing_input - expected
            )

    def get_report_data(self):
        self.ensure_one()

        expected_cash = (
            self.opening_cash +
            self.total_sales
        )

        return {
            "name": self.name,
            "total_orders": len(self.pos_ids),
            "total_sales": self.total_sales,
            "opening_cash": self.opening_cash,
            "expected_cash": expected_cash,
            "closing_cash": self.closing_cash,
            "closing_input": self.closing_input,
            "difference": self.difference,
        }
        

    def close_session(self, actual_cash):
        self.ensure_one()

        if self.state != 'open':
            raise ValidationError(
                "Only an open session can be closed."
            )

        total_sales = self.total_sales
        total_df = self.total_df
        total_cash = self.total_cash
        total_gcash = self.total_gcash

        expected_cash = (
            self.opening_cash +
            total_sales
        )

        difference = (
            actual_cash -
            expected_cash
        )

        self.write({
            'total_sales': total_sales,
            'total_df': total_df,
            'total_cash': total_cash,
            'total_gcash': total_gcash,
            'closing_cash': expected_cash,
            'closing_input': actual_cash,
            'state': 'closed',
        })

        return {
            'opening_cash': self.opening_cash,
            'total_sales': total_sales,
            'total_df': total_df,
            'total_cash': total_cash,
            'total_gcash': total_gcash,
            'expected_cash': expected_cash,
            'closing_input': actual_cash,
            'difference': difference,
        }

