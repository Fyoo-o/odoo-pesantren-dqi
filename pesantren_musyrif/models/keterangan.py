from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import timedelta, datetime
import logging



class MasterKeterangan(models.Model):
    _name = 'master.keterangan'
    _description = 'Master Keterangan Izin'
    
    name = fields.Char("Keterangan Ijin", required=True)
    active = fields.Boolean("Aktif", default=True)