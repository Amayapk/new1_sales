from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_order_limit = fields.Float("Sale Order Limit", config_parameter="sale_customizations.sale_order_limit")
