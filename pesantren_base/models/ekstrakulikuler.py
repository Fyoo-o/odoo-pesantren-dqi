from odoo import api, fields, models


class Ekstrakulikuler(models.Model):
    _name = 'cdn.ekstrakulikuler'
    _description = 'Data Ekstrakulikuler'

    name = fields.Char(string='Nama', required=True, help="Nama kegiatan ekstrakurikuler")
