# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PindahKelasWizard(models.TransientModel):
    _name = 'cdn.pindah_kelas_wizard'
    _description = 'Wizard Konfirmasi Pemindahan Santri Ke Kelas Baru'

    ruang_kelas_id = fields.Many2one(
        'cdn.ruang_kelas',
        string='Kelas Tujuan Baru',
        required=True,
        readonly=True
    )
    siswa_id = fields.Many2one(
        'cdn.siswa',
        string='Santri',
        required=True,
        readonly=True
    )
    kelas_lama_id = fields.Many2one(
        'cdn.ruang_kelas',
        string='Kelas Asal / Lama',
        readonly=True
    )

    jenjang_lama = fields.Selection(
        selection=[
            ('paud', 'PAUD'),
            ('tk', 'TK/RA'),
            ('sd', 'SD/MI'),
            ('smp', 'SMP/MTS'),
            ('sma', 'SMA/MA/SMK'),
            ('nonformal', 'Non formal'),
            ('rtq', 'Rumah Tahfidz Quran')
        ],
        string='Jenjang Kelas Asal',
        related='kelas_lama_id.jenjang',
        readonly=True
    )
    jenjang_baru = fields.Selection(
        selection=[
            ('paud', 'PAUD'),
            ('tk', 'TK/RA'),
            ('sd', 'SD/MI'),
            ('smp', 'SMP/MTS'),
            ('sma', 'SMA/MA/SMK'),
            ('nonformal', 'Non formal'),
            ('rtq', 'Rumah Tahfidz Quran')
        ],
        string='Jenjang Kelas Tujuan',
        related='ruang_kelas_id.jenjang',
        readonly=True
    )

    update_jenjang_siswa = fields.Boolean(
        string='Perbarui Jenjang Santri Secara Otomatis',
        default=True,
        help='Jika dicentang, jenjang santri di profilnya akan otomatis diubah sesuai jenjang kelas tujuan.'
    )

    catatan = fields.Text(
        string='Alasan / Catatan Pemindahan',
        help='Keterangan opsional mengenai alasan pemindahan santri.'
    )

    def action_confirm_pindah(self):
        self.ensure_one()
        siswa = self.siswa_id.sudo()
        ruang_kelas_baru = self.ruang_kelas_id.sudo()
        kelas_lama = self.kelas_lama_id.sudo() if self.kelas_lama_id else False

        if not siswa or not ruang_kelas_baru:
            raise UserError(_("Data santri atau kelas tujuan tidak valid."))

        # 1. Hapus dari kelas lama (jika ada)
        if kelas_lama and siswa.id in kelas_lama.siswa_ids.ids:
            kelas_lama.with_context(skip_ruang_kelas_sync=True).write({
                'siswa_ids': [(3, siswa.id)]
            })

        # 2. Tambahkan ke kelas baru jika belum ada
        if siswa.id not in ruang_kelas_baru.siswa_ids.ids:
            ruang_kelas_baru.with_context(skip_ruang_kelas_sync=True).write({
                'siswa_ids': [(4, siswa.id)]
            })

        # 3. Update profil santri (ruang_kelas_id, tahunajaran_id)
        update_vals = {
            'ruang_kelas_id': ruang_kelas_baru.id,
            'tahunajaran_id': ruang_kelas_baru.tahunajaran_id.id if ruang_kelas_baru.tahunajaran_id else False,
        }

        # 4. Update jenjang santri jika dipilih dan ada perbedaan
        if self.update_jenjang_siswa and ruang_kelas_baru.jenjang and siswa.jenjang != ruang_kelas_baru.jenjang:
            update_vals['jenjang'] = ruang_kelas_baru.jenjang

        siswa.with_context(skip_ruang_kelas_sync=True).write(update_vals)

        # Recalculate jml_siswa pada kedua kelas
        if kelas_lama:
            kelas_lama._compute_jml_siswa()
        ruang_kelas_baru._compute_jml_siswa()

        # Tampilkan wizard notifikasi sukses
        siswa_name = siswa.name or '-'
        nis_str = f" (NIS: {siswa.nis})" if siswa.nis else ""
        kelas_lama_title = (kelas_lama.name.name if (kelas_lama and kelas_lama.name) else (kelas_lama.nama_kelas or '-')) if kelas_lama else '-'
        kelas_baru_title = ruang_kelas_baru.name.name if (ruang_kelas_baru.name) else (ruang_kelas_baru.nama_kelas or '-')

        message_id = self.env['message.wizard'].create({
            'message': _(
                f"✅ PEMINDAHAN SANTRI BERHASIL!\n\n"
                f"Santri '{siswa_name}'{nis_str} telah berhasil dipindahkan dari "
                f"kelas '{kelas_lama_title}' ke kelas '{kelas_baru_title}'."
            )
        })
        return {
            'name': _('Pemindahan Santri Berhasil'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'message.wizard',
            'res_id': message_id.id,
            'target': 'new'
        }
