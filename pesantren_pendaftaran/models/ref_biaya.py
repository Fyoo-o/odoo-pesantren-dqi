from odoo import api, fields, models


class BiayaPendidikan(models.Model):
    _name           = 'ubig.pendidikan'
    _description    = 'Tabel Data Biaya Pendidikan'

    name            = fields.Char(string='Jenjang Pendidikan', required=True)
    jenjang         = fields.Selection(selection=[('paud','PAUD'),('tk','TK'),('sdmi','SD / MI'),('smpmts','SMP / MTS'),('smama','SMA / MA'),('smk','SMK')], string='Jenjang', required=True)
    biaya           = fields.Integer(string='Biaya Pendidikan')
    keterangan      = fields.Char(string='Keterangan', help='')
    status          = fields.Selection(string='Status', selection=[('draft', 'Draft'), ('konfirm', 'Terkonfirmasi')], default="draft")
    biaya_ids       = fields.One2many('ubig.biaya_daftarulang',inverse_name="biaya_id", string='Rincian Biaya')
    rincian_ids     = fields.One2many('ubig.rincian_biaya',inverse_name="biaya_id", string='Rincian Biaya')


    # Action untuk mengubah status ke 'konfirm'
    def konfirmasi(self):
        for record in self:
            record.status = 'konfirm'

    # Action untuk mengubah status ke 'draft'
    def draft(self):
        for record in self:
            record.status = 'draft'