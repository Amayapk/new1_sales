from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    manager_reference = fields.Char("Manager Reference", readonly=True)
    auto_workflow = fields.Boolean("Auto Workflow")


    @api.onchange('manager_reference')
    def _check_sale_admin_access(self):
        if self.env.user.has_group('sale_customizations.group_sale_admin'):
            self.manager_reference = fields.Char("Manager Reference", readonly=False)


    def action_confirm(self):
        sale_order_limit = float(
            self.env['ir.config_parameter'].sudo().get_param('sale_customizations.sale_order_limit', 0))

        for order in self:
            if order.amount_total > sale_order_limit and not self.env.user.has_group(
                    'sale_customizations.group_sale_admin'):
                raise ValidationError(_("Only Sale Admins can confirm orders above the Sale Order Limit."))

        super(SaleOrder, self).action_confirm()

        if self.auto_workflow:
            for order in self:
                delivery_orders = order.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel'))
                for picking in delivery_orders:
                    picking.action_confirm()
                    picking.action_assign()
                    picking.action_done()

                invoices = order.invoice_ids.filtered(lambda inv: inv.state == 'draft')
                for invoice in invoices:
                    invoice.action_post()

                    payment = self.env['account.payment'].create({
                        'amount': invoice.amount_total,
                        'partner_id': invoice.partner_id.id,
                        'payment_type': 'inbound',
                        'partner_type': 'customer',
                        'journal_id': invoice.journal_id.id,
                    })
                    payment.action_post()
                    invoice.assign_payment(payment)