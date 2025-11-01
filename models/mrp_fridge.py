from odoo import models, fields

class MrpFridge(models.Model):
    _name = 'mrp.fridge'
    _description = 'Manufacturing Fridge'
    
    name = fields.Char('Name', required=True)
    description = fields.Text('Description')
    temperature_threshold = fields.Float('Temperature Threshold (°C)', default=8.0, 
        help="Maximum allowed temperature. Records above this value will be highlighted.")
    temperature_ids = fields.One2many('mrp.fridge.temperature', 'fridge_id', string='Temperature Records')
