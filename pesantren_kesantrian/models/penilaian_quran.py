from odoo import api, fields, models, _
from datetime import date, datetime

class TahfidzTahsin(models.Model):
    _name = 'cdn.penilaian_quran'
    _description = 'Rekam absensi per Santri'

    name = fields.Char(string='No Referensi', readonly=True, copy=False, default='/')
    tanggal = fields.Date(string='Tanggal', required=True, default=fields.Date.context_today)
    siswa_id = fields.Many2one('cdn.siswa', string='Santri', required=True, ondelete='cascade')
    
    # Data Santri (related)
    barcode = fields.Char(related='siswa_id.barcode_santri', string="Kartu Santri", readonly=True)
    kelas_id = fields.Many2one(related='siswa_id.ruang_kelas_id', string='Kelas', readonly=True, store=True)
    kamar_id = fields.Many2one(related='siswa_id.kamar_id', string='Kamar', readonly=True)
    halaqoh_id = fields.Many2one(related='siswa_id.halaqoh_id', string='Halaqoh', readonly=True, store=True)
    musyrif_id = fields.Many2one(related='siswa_id.musyrif_id', string='Musyrif', readonly=True)

    # Umum
    ustadz_id = fields.Many2one('hr.employee', string='Ustadz', required=True)
    sesi_id = fields.Many2one('cdn.sesi_halaqoh', string='Sesi', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Selesai')
    ], default='draft', string='Status')

    # === TAB TAHFIDZ ===
    surah_id = fields.Many2one('cdn.surah', string='Surah')
    ayat_awal = fields.Many2one('cdn.ayat', string='Ayat Awal', domain="[('surah_id','=',surah_id)]")
    ayat_akhir = fields.Many2one('cdn.ayat', string='Ayat Akhir', domain="[('surah_id','=',surah_id)]")
    jml_baris = fields.Integer(string='Jumlah Baris')
    nilai_hafalan = fields.Integer(string='Nilai Hafalan', default=75)
    predikat = fields.Selection([
        ('a+', 'A+'), ('a', 'A'), ('b+', 'B+'), ('b', 'B'), ('c+', 'C+'), ('c', 'C')
    ], compute='_compute_predikat', store=True)
    keterangan_tahfidz = fields.Text(string='Keterangan Tahfidz')

    # === TAB TAHsin HARIAN ===
    buku_harian_id = fields.Many2one('cdn.buku_tahsin', string='Buku (Harian)')
    jilid_harian_id = fields.Many2one('cdn.jilid_tahsin', string='Jilid (Harian)', 
        domain="[('buku_tahsin_id', '=', buku_harian_id)]")
    halaman_harian = fields.Char(string='Halaman (Harian)')
    nilai_tajwid_harian = fields.Integer(string='Nilai Tajwid')
    nilai_makhroj_harian = fields.Integer(string='Nilai Makhroj')
    nilai_mad_harian = fields.Integer(string='Nilai Mad')
    catatan_harian = fields.Text(string='Catatan (Harian)')

    # === TAB TAHsin UJIAN ===
    buku_ujian_id = fields.Many2one('cdn.buku_tahsin', string='Buku (Ujian)')
    jilid_ujian_id = fields.Many2one('cdn.jilid_tahsin', string='Jilid (Ujian)',
        domain="[('buku_tahsin_id', '=', buku_ujian_id)]")
    halaman_ujian = fields.Char(string='Halaman (Ujian)')
    nilai_tajwid_ujian = fields.Integer(string='Nilai Tajwid')
    nilai_makhroj_ujian = fields.Integer(string='Nilai Makhroj')
    nilai_mad_ujian = fields.Integer(string='Nilai Mad')
    catatan_ujian = fields.Text(string='Catatan (Ujian)')
    last_surah_id = fields.Many2one(
    'cdn.surah',
    string='Surah Terakhir',
    compute='_compute_last_tahfidz'
    )
    last_ayat_akhir = fields.Many2one(
        'cdn.ayat',
        string='Ayat Terakhir',
        compute='_compute_last_tahfidz'
    )

    @api.depends('siswa_id')
    def _compute_last_tahfidz(self):
        for rec in self:
            last = self.env['cdn.penilaian_quran'].search([
                ('siswa_id', '=', rec.siswa_id.id),
                ('state', '=', 'done'),
                ('surah_id', '!=', False)
            ], order='tanggal desc, id desc', limit=1)
            rec.last_surah_id = last.surah_id.id if last else False
            rec.last_ayat_akhir = last.ayat_akhir.id if last else False

    # === COMPUTE & ONCHANGE ===
    @api.depends('nilai_hafalan')
    def _compute_predikat(self):
        for rec in self:
            n = rec.nilai_hafalan
            if n >= 90: rec.predikat = 'a+'
            elif n >= 80: rec.predikat = 'a'
            elif n >= 70: rec.predikat = 'b+'
            elif n >= 60: rec.predikat = 'b'
            elif n >= 50: rec.predikat = 'c+'
            else: rec.predikat = 'c'

    @api.onchange('buku_harian_id')
    def _onchange_buku_harian(self):
        self.jilid_harian_id = False
        self.halaman_harian = False

    @api.onchange('buku_ujian_id')
    def _onchange_buku_ujian(self):
        self.jilid_ujian_id = False
        self.halaman_ujian = False

    # === WORKFLOW ===
    def action_confirm(self):
        for rec in self:
            rec.state = 'done'

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('cdn.penilaian_quran') or '/'
        return super().create(vals)

    def name_get(self):
        result = []
        for rec in self:
            name = f"{rec.siswa_id.name} - {rec.tanggal}"
            result.append((rec.id, name))
        return result
    
    @api.onchange('siswa_id')
    def _onchange_siswa_id(self):
        if self.siswa_id:
            # Reset field Tahfidz
            self.surah_id = False
            self.ayat_awal = False
            self.ayat_akhir = False
            
            # Cari penilaian Tahfidz terakhir yang sudah "done"
            last_tahfidz = self.env['cdn.penilaian_quran'].search([
                ('siswa_id', '=', self.siswa_id.id),
                ('state', '=', 'done'),
                ('surah_id', '!=', False),
                ('ayat_akhir', '!=', False)
            ], order='tanggal desc, id desc', limit=1)
            
            if last_tahfidz:
                surah_terakhir = last_tahfidz.surah_id
                ayat_akhir_terakhir = last_tahfidz.ayat_akhir.name
                total_ayat_surah = surah_terakhir.jml_ayat
                
                if ayat_akhir_terakhir < total_ayat_surah:
                    # Belum selesai → lanjut di surah yang sama
                    self.surah_id = surah_terakhir.id
                    next_ayat = ayat_akhir_terakhir + 1
                    ayat_awal = self.env['cdn.ayat'].search([
                        ('surah_id', '=', surah_terakhir.id),
                        ('name', '=', next_ayat)
                    ], limit=1)
                    self.ayat_awal = ayat_awal.id if ayat_awal else False
                else:
                    # Sudah selesai → lanjut ke surah berikutnya, ayat 1
                    next_surah = self.env['cdn.surah'].search([
                        ('number', '>', surah_terakhir.number)
                    ], order='number', limit=1)
                    if next_surah:
                        self.surah_id = next_surah.id
                        ayat_1 = self.env['cdn.ayat'].search([
                            ('surah_id', '=', next_surah.id),
                            ('name', '=', 1)
                        ], limit=1)
                        self.ayat_awal = ayat_1.id if ayat_1 else False
            else:
                # Belum pernah tahfidz → mulai dari Al-Fatihah ayat 1
                surah_fatihah = self.env['cdn.surah'].search([('number', '=', 1)], limit=1)
                if surah_fatihah:
                    self.surah_id = surah_fatihah.id
                    ayat_1 = self.env['cdn.ayat'].search([
                        ('surah_id', '=', surah_fatihah.id),
                        ('name', '=', 1)
                    ], limit=1)
                    self.ayat_awal = ayat_1.id if ayat_1 else False
        else:
            self.surah_id = False
            self.ayat_awal = False
            self.ayat_akhir = False