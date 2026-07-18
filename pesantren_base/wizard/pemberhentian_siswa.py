# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError

class PemberhentianSiswa(models.TransientModel):
    _name = 'cdn.pemberhentian_siswa'
    _description = 'Wizard Pemberhentian Santri'

    tanggal = fields.Date(string='Tanggal Keluar', required=True, default=fields.Date.context_today)
    alasan = fields.Selection([
        ('lulus', 'Lulus'),
        ('pindah', 'Pindah Sekolah'),
        ('berhenti', 'Berhenti / Mengundurkan Diri'),
        ('dikeluarkan', 'Dikeluarkan (Pelanggaran)'),
        ('meninggal', 'Meninggal Dunia'),
        ('lainnya', 'Lainnya')
    ], string='Alasan Keluar', required=True)
    catatan = fields.Text(string='Catatan / Keterangan Tambahan')
    
    siswa_ids = fields.Many2many(
        'cdn.siswa', 
        'pemberhentian_siswa_rel', 
        'pemberhentian_id', 
        'siswa_id', 
        string='Daftar Santri',
        domain=[('active', '=', True)]
    )

    blokir_akun = fields.Boolean(
        string='Blokir Akun Keuangan?',
        default=True,
        help="Jika dicentang, status kartu/akun santri akan otomatis diubah menjadi 'Diblokir'."
    )

    @api.model
    def default_get(self, fields_list):
        res = super(PemberhentianSiswa, self).default_get(fields_list)
        active_ids = self._context.get('active_ids')
        if active_ids and self._context.get('active_model') == 'cdn.siswa':
            res['siswa_ids'] = [(6, 0, active_ids)]
        return res

    def action_proses_berhenti(self):
        if not self.siswa_ids:
            raise UserError("Silakan pilih minimal satu santri yang akan diberhentikan!")

        alasan_dict = dict(self._fields['alasan'].selection)
        alasan_label = alasan_dict.get(self.alasan)

        for siswa in self.siswa_ids:
            # Format pesan log
            pesan = f"<b>Siswa diberhentikan / keluar:</b><br/>" \
                    f"Tanggal: {self.tanggal}<br/>" \
                    f"Alasan: {alasan_label}<br/>"
            if self.catatan:
                pesan += f"Catatan: {self.catatan}<br/>"
            
            siswa.message_post(body=pesan)

            # Update data santri
            update_vals = {
                'active': False,
                'ruang_kelas_id': False,  # Keluarkan dari kelas
                'alasan_keluar': self.alasan,
                'tanggal_keluar': self.tanggal,
            }

            if self.blokir_akun:
                update_vals['status_akun'] = 'blokir'
            
            siswa.write(update_vals)
            
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
