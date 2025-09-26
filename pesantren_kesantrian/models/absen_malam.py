from odoo import api, fields, models
from datetime import date

class AbsensiMalam(models.Model):
    _name = 'cdn.absensi_malam'
    _description = 'Absensi Malam Santri'
    _order = 'tgl desc'

    name        = fields.Char(string='No. Referensi', readonly=True)
    tgl         = fields.Date(string='Tanggal', required=True, default=lambda self: date.today())
    siswa_id    = fields.Many2one('cdn.siswa', string='Santri',  ondelete='cascade', required=True)
    halaqoh_id  = fields.Many2one('cdn.halaqoh', string='Halaqoh', readonly=True, related='siswa_id.halaqoh_id')
    
    barcode          = fields.Char(string="Kartu Santri", readonly=False)

    kamar_id    = fields.Many2one('cdn.kamar_santri', string='Kamar', related='siswa_id.kamar_id', readonly=True)
    musyrif_id  = fields.Many2one('hr.employee', string='Musyrif', related='siswa_id.musyrif_id', readonly=True)
    kelas_id        = fields.Many2one('cdn.ruang_kelas', string='Kelas', related='siswa_id.ruang_kelas_id', readonly=True, store=True)
    halaqoh_id  = fields.Many2one('cdn.halaqoh', string='Halaqoh', related='siswa_id.halaqoh_id', readonly=True)


    kehadiran = fields.Selection([
        ('hadir', 'Hadir'),
        ('masybul', 'Masybul'),
        ('izin', 'Izin'),
        ('sakit', 'Sakit'),
    ], string='Kehadiran', default='hadir')

    keterangan = fields.Char(string='Keterangan')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Selesai'),
    ], default='draft', string='Status')

    # --- onchange barcode & siswa ---
    @api.onchange('siswa_id')
    def _onchange_siswa_id(self):
        if self.siswa_id:
            self.barcode = self.siswa_id.barcode_santri
        else:
            self.barcode = False

    @api.onchange('barcode')
    def _onchange_barcode(self):
        if self.barcode:
            siswa = self.env['cdn.siswa'].search([('barcode_santri', '=', self.barcode)], limit=1)
            if siswa:
                self.siswa_id = siswa.id
            else:
                barcode_sementara = self.barcode
                self.barcode = False
                self.siswa_id = False
                return {
                    'warning': {
                        'title': "Perhatian!",
                        'message': f"Santri dengan kartu {barcode_sementara} tidak ditemukan."
                    }
                }

    # --- Cegah duplikasi absen per santri per hari per sesi ---
    @api.onchange('siswa_id', 'tgl')
    def _onchange_check_duplikat(self):
        if self.siswa_id and self.tgl:
            existing = self.env['cdn.absensi_malam'].search([
                ('siswa_id', '=', self.siswa_id.id),
                ('tgl', '=', self.tgl),
                ('id', '!=', self._origin.id if self._origin else False)
            ])
            if existing:
                return {
                    'warning': {
                        'title': "Duplikasi!",
                        'message': "Santri ini sudah diabsen pada sesi dan tanggal ini."
                    },
                    'value': {
                        'siswa_id': False,
                        'barcode': False,
                        'kehadiran': 'hadir',
                        'keterangan': False
                    }
                }

    # --- Sequence number ---
    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code('cdn.absensi_malam') or '/'
        return super(AbsensiMalam, self).create(vals)

    # --- Tombol action ---
    def action_confirm(self):
        self.write({'state': 'done'})

    def action_draft(self):
        self.write({'state': 'draft'})