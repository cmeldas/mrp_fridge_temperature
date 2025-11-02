from odoo import models, fields, api

class MrpFridgeTemperature(models.Model):
    _name = 'mrp.fridge.temperature'
    _description = 'Manufacturing Fridge Temperature'
    _order = 'datetime desc'
    
    datetime = fields.Datetime('Date and Time', required=True, default=fields.Datetime.now)
    fridge_id = fields.Many2one('mrp.fridge', string='Fridge', required=True)
    temperature = fields.Float('Temperature (°C)', required=True)
    threshold = fields.Float(related='fridge_id.temperature_threshold', string='Threshold (°C)')
    is_above_threshold = fields.Boolean('Above Threshold', compute='_compute_is_above_threshold', store=True)

    @api.depends('temperature', 'threshold')
    def _compute_is_above_threshold(self):
        for record in self:
            record.is_above_threshold = record.temperature > record.threshold
