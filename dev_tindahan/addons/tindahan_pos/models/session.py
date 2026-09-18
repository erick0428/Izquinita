from odoo import models, fields, api


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

    @api.depends('pos_ids.total')
    def _compute_total_sales(self):
        for rec in self:
            rec.total_sales = sum(
                order.total for order in rec.pos_ids
            )

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