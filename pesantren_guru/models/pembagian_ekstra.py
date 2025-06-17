from odoo import models, fields, api 
from datetime import date, datetime

class PembagianEkstra(models.Model) :
    _name = "cdn.pembagian_ekstra"
    _description = "Tabel untuk Pembagian Ekstrakulikuler untuk Santri"
    # _rec_name = 'display_name'

    def _get_domain_guru(self):
        return [
            ('jns_pegawai','=','guru')
        ]

    
    name                = fields.Many2one("cdn.ekstrakulikuler", string="Ekstrakulikuler")
    # name              = fields.Char(string="Nama",compute="_compute_name", readonly=False ,store=True)
    siswa_ids           = fields.Many2many('cdn.siswa', string='Daftar Siswa', ondelete='cascade')
    penanggung_id       = fields.Many2one("hr.employee",  string="Penanggung Jawab",  help="", domain=_get_domain_guru)
    # display_name      = fields.Char(string="Nama Tampilan", compute="_compute_display_name", store=True)


    # @api.depends('name')
    # def _compute_display_name(self):
    #     for rec in self:
    #         ekskul = rec.name.name if rec.name else 'Belum Ada Nama'
    #         # penanggung = rec.penanggung_id.name if rec.penanggung_id else 'Tanpa Penanggung'
    #         rec.display_name = f"{ekskul}"