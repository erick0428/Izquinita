from odoo import models, fields, _
from odoo.exceptions import UserError


class POSLineWizard(models.TransientModel):
    _name = "tindahan_pos.pos.line.wizard"
    _description = "Add Product to POS Order"

    pos_id = fields.Many2one(
        "tindahan_pos.pos",
        string="POS Transaction",
        required=True,
        readonly=True,
    )

    product_id = fields.Many2one(
        "tindahan_pos.product",
        string="Product",
        required=True,
        domain=[("active", "=", True)],
    )

    quantity = fields.Float(
        string="Quantity",
        default=1.0,
        required=True,
    )

    def action_add_product(self):
        self.ensure_one()

        if self.quantity <= 0:
            raise UserError(_("Quantity must be greater than zero."))

        order = self.pos_id

        if not order.exists():
            raise UserError(_("POS transaction not found."))

        if order.payment_status == "paid":
            raise UserError(_("You cannot modify a paid order."))

        # Use the existing POS product model.
        # Variant, price and subtotal are computed by POSLine.
        self.env["tindahan_pos.pos.line"].create({
            "pos_id": order.id,
            "product_id": self.product_id.id,
            "quantity": self.quantity,
        })

        return {"type": "ir.actions.act_window_close"}