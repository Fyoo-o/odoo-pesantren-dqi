from odoo import models, fields


class CdnSiswa(models.Model):
    _inherit = 'cdn.tahsin_quran'

    fashohah = fields.Integer(string='Nilai Fashohah')
    tajwid = fields.Integer(string='Nilai Tajwid')
    ghorib_musykilat = fields.Integer(string='Nilai Ghorib/Musykilat')
    suara_lagu = fields.Integer(string='Nilai Suara Lagu')
