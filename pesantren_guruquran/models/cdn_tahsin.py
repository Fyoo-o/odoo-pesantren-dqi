from odoo import models, fields

class CdnSiswa(models.Model):
    _inherit = 'cdn.tahsin_quran'

    fashohah = fields.Integer(string='Nilai Fashohah',default=75)
    tajwid = fields.Integer(string='Nilai Tajwid',default=75)
    ghorib_musykilat = fields.Integer(string='Nilai Ghorib/Musykilat',default=75)
    suara_lagu = fields.Integer(string='Nilai Suara Lagu',default=75)
