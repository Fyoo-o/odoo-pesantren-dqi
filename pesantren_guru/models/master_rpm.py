# -*- coding: utf-8 -*-

import base64
from odoo import api, fields, models
from odoo.exceptions import UserError


class MasterRPM(models.Model):
    _name = 'cdn.master_rpm'
    _description = 'Data Rencana Pelaksanaan Mingguan'

    name = fields.Char(string='Materi', required=True,
                       help="Judul atau topik materi pembelajaran")
    jenjang = fields.Selection([
        ('sd', 'SD/MI'),
        ('smp', 'SMP/MTS'),
        ('sma', 'SMA/MA'),
        ('nonformal', 'Nonformal'),
    ], string='Jenjang')
    matpel_id = fields.Many2one('cdn.mata_pelajaran', string='Mata Pelajaran')
    tingkat_id = fields.Many2one('cdn.tingkat', string='Kelas')
    jurusan_id = fields.Many2one('cdn.master_jurusan', string='Jurusan')
    waktu = fields.Char(string='Alokasi Waktu')
    kd = fields.Char(string='Kompentensi Dasar',
                     help="Kompetensi dasar (KD) yang menjadi acuan")
    dokumen = fields.Binary(string='Dokumen RPM')
    tujuan = fields.Text(
        string='Tujuan', help="Tujuan pembelajaran yang ingin dicapai setelah materi ini disampaikan")

    @api.constrains('dokumen')
    def _check_dokumen(self):
        for record in self:
            if record.dokumen:
                try:
                    doc_bytes = base64.b64decode(record.dokumen)
                    if not doc_bytes.startswith(b'%PDF'):
                        raise UserError('Dokumen harus berformat PDF')
                except Exception as e:
                    if isinstance(e, UserError):
                        raise e
                    raise UserError('Dokumen harus berformat PDF')
