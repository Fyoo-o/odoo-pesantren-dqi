from odoo import api, fields, models
from odoo.exceptions import UserError

class Santri(models.Model):
    _inherit = 'cdn.siswa'
    _sql_constraints = [
        ('nis_unique', 'unique(nis)', 'NIS harus unik!'),
    ]
    partner_id          = fields.Many2one('res.partner', string='Siswa', required=True)
    last_tahfidz        = fields.Many2one('cdn.tahfidz_quran', string='Tahfidz Terakhir', readonly=True )
    ruang_kelas_id      = fields.Many2one('cdn.ruang_kelas', string='Ruang Kelas')
    kamar_id            = fields.Many2one('cdn.kamar_santri', string='Kamar', readonly=True)
    musyrif_id          = fields.Many2one('hr.employee', related='kamar_id.musyrif_id', string='Musyrif/Pembina', readonly=True)
    musyrif_ganti_ids   = fields.Many2many(comodel_name='hr.employee', related='kamar_id.pengganti_ids', string='Musyrif Pengganti', readonly=True)
    halaqoh_id          = fields.Many2one('cdn.halaqoh', string='Halaqoh', readonly=True)
    penanggung_jawab_id = fields.Many2one(comodel_name='hr.employee', related='halaqoh_id.penanggung_jawab_id', string='Penanggung Jawab', readonly=True)
    pengganti_ids       = fields.Many2many(comodel_name ='hr.employee', related='halaqoh_id.pengganti_ids', string='Ustadz Pengganti', readonly=True)
    
    tahfidz_quran_ids   = fields.One2many('cdn.tahfidz_quran', 'siswa_id', string='Tahfidz Quran', readonly=True)

    #state info smart button
    kesehatan_count     = fields.Integer(string='Kesehatan', compute='_compute_count_kesehatan')
    pelanggaran_count   = fields.Integer(string='Pelanggaran', compute='_compute_count_pelanggaran')
    prestasi_siswa_count = fields.Integer(string='Prestasi', compute='_compute_count_prestasi')
    tahfidz_quran_count = fields.Integer(string='Tahfidz Quran', compute='_compute_count_tahfidz_quran')

    saldo_tagihan_count = fields.Float(string='Saldo Tagihan', compute='_compute_count_saldo_tagihan', widget="integer")
    uang_saku_count = fields.Float(string='Uang Saku', compute='_compute_count_uang_saku', widget="integer")
    
    saldo_tagihan_formatted = fields.Integer(string='Saldo Tagihan (Format)', compute='_compute_saldo_tagihan_formatted')
    uang_saku_formatted = fields.Integer(string='Uang Saku (Format)', compute='_compute_uang_saku_formatted')


    def _compute_count_kesehatan(self):
        for siswa in self:
            siswa.kesehatan_count = self.env['cdn.kesehatan'].search_count([('siswa_id', '=', siswa.id)])
    def _compute_count_pelanggaran(self):
        for siswa in self:
            siswa.pelanggaran_count = self.env['cdn.pelanggaran'].search_count([('siswa_id', '=', siswa.id)])
    def _compute_count_prestasi(self):
        for siswa in self:
            siswa.prestasi_siswa_count = self.env['cdn.prestasi_siswa'].search_count([('siswa_id', '=', siswa.id)])
    def _compute_count_tahfidz_quran(self):
        for siswa in self:
            siswa.tahfidz_quran_count = self.env['cdn.tahfidz_quran'].search_count([('siswa_id', '=', siswa.id)])

    def _compute_count_saldo_tagihan(self):
        for siswa in self:
            if siswa.partner_id:
                # Ambil semua tagihan yang terkait dengan partner siswa
                tagihan = self.env['account.move'].search([
                    ('partner_id', '=', siswa.partner_id.id),
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'posted')  # Hanya tagihan yang sudah diposting
                ])
                # Hitung sisa tagihan (amount_residual_signed)
                siswa.saldo_tagihan_count = sum(tagihan.mapped('amount_residual_signed'))

    def _compute_count_uang_saku(self):
        for siswa in self:
            if siswa.partner_id:
                uang_saku = self.env['cdn.uang_saku'].search([('siswa_id', '=', siswa.partner_id.id), ('state', '=', 'confirm')])
                print(uang_saku)
                siswa.uang_saku_count = sum(uang_saku.mapped('amount_in')) - sum(uang_saku.mapped('amount_out'))

    @api.depends('saldo_tagihan_count')
    def _compute_saldo_tagihan_formatted(self):
        for record in self:
            record.saldo_tagihan_formatted = int(record.saldo_tagihan_count)

    @api.depends('uang_saku_count')
    def _compute_uang_saku_formatted(self):
        for record in self:
            record.uang_saku_formatted = int(record.uang_saku_count)

    # actions smart button
    def action_saldo_tagihan(self):
        self.ensure_one()
        # Action untuk menampilkan daftar tagihan siswa
        action = {
            'name': 'Tagihan Santri',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('siswa_id', '=', self.id), ('move_type', '=', 'out_invoice')],
            'context': {'default_siswa_id': self.id, 'default_move_type': 'out_invoice'},
        }
        return action

    def action_kesehatan(self):
        return {
            'name': 'Kesehatan',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'cdn.kesehatan',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {
                'default_siswa_id': self.id,
            },
            'domain': [('siswa_id', '=', self.id)]
        }
    def action_pelanggaran(self):
        return {
            'name': 'Pelanggaran',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'cdn.pelanggaran',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {
                'default_siswa_id': self.id,
            },
            'domain': [('siswa_id', '=', self.id)]
        }

    # def action_open_custom_wizard(self):
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'custom_pin_popup',
    #         'name': 'Change PIN',
    #         'params': {
    #             'record_id': self.id,
    #             'model': self._name,
    #         }
    #     }

    # def action_open_custom_wizard(self):
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'custom_pin_popup',
    #         'name': 'Change PIN',
    #         'params': {
    #             'model': 'res.partner.change.pin',
    #             'partner_id': self.partner_id.id,
    #         }
    #     }

    def action_open_custom_wizard(self):
         # This should be on the CDN.Siswa model
        if not hasattr(self, 'partner_id') or not self.partner_id:
            raise UserError("Santri tidak memiliki partner yang terkait!")
            
        return {
            'type': 'ir.actions.client',
            'tag': 'custom_pin_popup',
            'name': 'Change PIN',
            'params': {
                'model': 'res.partner.change.pin',
                'partner_id': self.partner_id.id,
                'context': {'active_id': self.id, 'active_model': 'cdn.siswa'}
            }
        }

    
    def action_prestasi_siswa(self):
        return {
            'name': 'Prestasi',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'cdn.prestasi_siswa',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {
                'default_siswa_id': self.id,
            },
            'domain': [('siswa_id', '=', self.id)]
        }
    def action_tahfidz_quran(self):
        return {
            'name': 'Tahfidz Quran',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'cdn.tahfidz_quran',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {
                'default_siswa_id': self.id,
            },
            'domain': [('siswa_id', '=', self.id)]
        }

    # def action_saldo_tagihan(self):
    #     return {
    #         'name': 'Saldo Tagihan',
    #         'view_mode': 'list,form',
    #         'res_model': 'account.move',
    #         'type': 'ir.actions.act_window',
    #         'target': 'current',
    #         'context': {'default_partner_id': self.partner_id.id, 'default_move_type': 'out_invoice'},
    #         'domain': [('partner_id', '=', self.partner_id.id),('move_type', '=', 'out_invoice')]
    #     }

    def action_saldo_tagihan(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tagihan Santri',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'view_id': False,  # Biarkan False supaya mengambil view default
            'res_id': False,
            'target': 'current',
            'context': {
                'default_siswa_id': self.id,  # Gunakan self.id jika ini dipanggil dari model siswa
                'default_partner_id': self.partner_id.id,
                'default_move_type': 'out_invoice',
                'search_default_filter_by_blm_lunas': 1,
            },
            'domain': [
                ('siswa_id', '=', self.id),  # Gunakan siswa_id yang lebih spesifik
                ('move_type', '=', 'out_invoice'),
            ],
            'views': [(self.env.ref('pesantren_keuangan.pesantren_tagihan_keuangan_view_tree').id, 'list'),
                    (self.env.ref('pesantren_keuangan.pesantren_tagihan_keuangan_view_form').id, 'form')],
        }


    def action_uang_saku(self):
        return {
            'name': 'Uang Saku',
            'view_mode': 'list,form',
            'res_model': 'cdn.uang_saku',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {'default_siswa_id': self.partner_id.id},
            'domain': [('siswa_id', '=', self.partner_id.id)]
        }
