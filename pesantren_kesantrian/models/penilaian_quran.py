from odoo import api, fields, models, _
from datetime import date, datetime
import logging

_logger = logging.getLogger(__name__)

class TahfidzTahsin(models.Model):
    _name = 'cdn.penilaian_quran'
    _description = 'Rekam absensi per Santri'

    def _get_default_ustadz(self):
        user = self.env.user
        employee = self.env['hr.employee'].search([('user_id','=',user.id)], limit=1)
        return employee.id if employee else False

    ustadz_id = fields.Many2one(
        'hr.employee',
        string='Ustadz',
        required=True,
        default=_get_default_ustadz,
        store=True
    )
    name = fields.Char(string='No Referensi', readonly=True, copy=False, default='/')
    tanggal = fields.Date(string='Tanggal', required=True, default=fields.Date.context_today)
    siswa_id = fields.Many2one('cdn.siswa', string='Santri', required=True, ondelete='cascade')
    # Data Santri (related)
    barcode = fields.Char(related='siswa_id.barcode_santri', string="Kartu Santri", readonly=True)
    kelas_id = fields.Many2one(related='siswa_id.ruang_kelas_id', string='Kelas', readonly=True, store=True)
    kamar_id = fields.Many2one(related='siswa_id.kamar_id', string='Kamar', readonly=True)
    halaqoh_id = fields.Many2one(related='siswa_id.halaqoh_id', string='Halaqoh', readonly=True, store=True)
    musyrif_id = fields.Many2one(related='siswa_id.musyrif_id', string='Musyrif', readonly=True)
    penanggung_jawab_id = fields.Many2one('hr.employee', string="Penanggung Jawab")
    pengganti_ids = fields.Many2many('hr.employee', string="Pengganti")
    # Umum
    # ustadz_id = fields.Many2one('hr.employee', string='Ustadz', required=True)
    jenjang_display = fields.Selection(related='siswa_id.jenjang', string='Jenjang', store=True)

    sesi_id = fields.Many2one('cdn.sesi_halaqoh', string='Sesi')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Selesai')
    ], default='draft', string='Status')

    # === TAB TAHFIDZ ===
    surah_id = fields.Many2one('cdn.surah', compute='_compute_main_fields', string='Surah')
    ayat_awal = fields.Many2one('cdn.ayat', string='Ayat Awal', compute='_compute_main_fields', domain="[('surah_id','=',surah_id)]")
    ayat_akhir = fields.Many2one('cdn.ayat', string='Ayat Akhir', compute='_compute_main_fields', domain="[('surah_id','=',surah_id)]")
    jml_baris = fields.Integer(string="Jumlah Maqra'", store=True)
    # === TAHFIDZ ===
    nilai_hafalan = fields.Integer(string='Nilai Hafalan')
    nilai_tahfidz = fields.Many2one('cdn.nilai_tahfidz', string='Nilai Tahfidz')

    # PREDIKAT (otomatis tergantung jenjang)
    predikat = fields.Char(string='Predikat', compute='_compute_predikat', store=True)
    keterangan_predikat = fields.Char(string='Keterangan', compute='_compute_predikat', store=True)
    keterangan_tahfidz = fields.Text(string='Keterangan Tahfidz')
    tahfidz_line_ids = fields.One2many(
        'cdn.penilaian_quran_line',
        'penilaian_id',
        string='Setoran Tahfidz'
    )

    # === TAB Murajaah Harian ===
    buku_murajaah_id = fields.Many2one(
        'cdn.buku_tahsin',
        string='Buku',
        default=lambda self: self.env['cdn.buku_tahsin'].search([('name', '=', "Al-Qur'an")], limit=1),
        readonly=True
    )

    # Ambil daftar Juz unik dari cdn.ayat
    juz_murajaah = fields.Selection(
        selection=lambda self: self._get_juz_selection(),
        string='Juz'
    )

    # Surah (akan difilter berdasar juz)
    surah_murajaah_id = fields.Many2one(
        'cdn.surah',
        string='Surah',
        domain="[('id', 'in', available_surah_ids)]"
    )

    halaman_murajaah = fields.Char(string='Halaman')
    catatan_murajaah_harian = fields.Text(string='Catatan Murajaah (Harian)')

    # Field bantu (computed, tidak disimpan)
    available_surah_ids = fields.Many2many(
        'cdn.surah',
        compute='_compute_available_surah_ids',
        string='Available Surahs'
    )

    # === Helper Functions ===
    def _get_juz_selection(self):
        try:
            ayat_records = self.env['cdn.ayat'].search([('juz', '!=', False), ('juz', '!=', 0)])
            juz_values = sorted(set(ayat_records.mapped('juz')))
            return [(str(j), f"Juz {j}") for j in juz_values]
        except Exception:
            return []

    @api.depends('juz_murajaah')
    def _compute_available_surah_ids(self):
        for rec in self:
            if rec.juz_murajaah:
                ayat_ids = self.env['cdn.ayat'].search([('juz', '=', rec.juz_murajaah)])
                rec.available_surah_ids = ayat_ids.mapped('surah_id')
            else:
                rec.available_surah_ids = False

    # === TAB TAHsin HARIAN ===
    buku_harian_id = fields.Many2one('cdn.buku_tahsin', string='Buku (Harian)')
    jilid_harian_id = fields.Many2one('cdn.jilid_tahsin', string='Jilid (Harian)', 
        domain="[('buku_tahsin_id', '=', buku_harian_id)]")
    halaman_harian = fields.Char(string='Halaman (Harian)')
    nilai_tajwid_harian = fields.Integer(string='Nilai Tajwid')
    nilai_makhroj_harian = fields.Integer(string='Nilai Makhroj')
    nilai_mad_harian = fields.Integer(string='Nilai Mad')
    catatan_harian = fields.Text(string='Catatan (Harian)')
    surah_id_harian = fields.Many2one('cdn.surah', string='Surah')
    ayat_awal_harian = fields.Many2one('cdn.ayat', string='Ayat Awal',domain="[('surah_id','=',surah_id_harian)]")
    ayat_akhir_harian = fields.Many2one('cdn.ayat', string='Ayat Akhir', domain="[('surah_id','=',surah_id_harian)]")
    

    # === TAB TAHsin UJIAN ===
    buku_ujian_id = fields.Many2one('cdn.buku_tahsin', string='Buku (Ujian)')
    jilid_ujian_id = fields.Many2one('cdn.jilid_tahsin', string='Jilid (Ujian)',
        domain="[('buku_tahsin_id', '=', buku_ujian_id)]")
    halaman_ujian = fields.Char(string='Halaman (Ujian)')
    nilai_tajwid_ujian = fields.Integer(string='Nilai Tajwid')
    nilai_makhroj_ujian = fields.Integer(string='Nilai Makhroj')
    nilai_mad_ujian = fields.Integer(string='Nilai Mad')
    catatan_ujian = fields.Text(string='Catatan (Ujian)')
    surah_id_ujian = fields.Many2one('cdn.surah', string='Surah')
    ayat_awal_ujian = fields.Many2one('cdn.ayat', string='Ayat Awal', domain="[('surah_id','=',surah_id_ujian)]")
    ayat_akhir_ujian = fields.Many2one('cdn.ayat', string='Ayat Akhir', domain="[('surah_id','=',surah_id_ujian)]")
    # === INFORMASI TAHFIDZ TERAKHIR ===
    last_surah_id = fields.Many2one(
        'cdn.surah', string='Surah Terakhir',
        compute='_compute_last_tahfidz', store=True, readonly=True
    )
    last_ayat_akhir = fields.Many2one(
        'cdn.ayat', string='Ayat Terakhir',
        compute='_compute_last_tahfidz', store=True, readonly=True
    )
    # === COMPUTE ===
    @api.depends('nilai_tahfidz.name', 'jenjang_display')
    def _compute_predikat(self):
        for rec in self:
            n = rec.nilai_tahfidz.name if rec.nilai_tahfidz else 0
            jenjang = (rec.jenjang_display or '').lower()

            # Sistem KB/PAUD/TK pakai BB-MB-BSA-BSB
            if jenjang in ['paud', 'tk', 'tk/ra']:
                if n >= 90:
                    rec.predikat = 'BSB'
                    rec.keterangan_predikat = 'Berkembang Sangat Bagus'
                elif n >= 75:
                    rec.predikat = 'BSA'
                    rec.keterangan_predikat = 'Berkembang Sesuai Harapan'
                elif n >= 60:
                    rec.predikat = 'MB'
                    rec.keterangan_predikat = 'Mulai Berkembang'
                else:
                    rec.predikat = 'BB'
                    rec.keterangan_predikat = 'Belum Berkembang'

            # Sistem SD
            elif jenjang in ['sd']:
                if n >= 95:
                    rec.predikat = 'A+'
                    rec.keterangan_predikat = 'Mumtaz'
                elif n >= 91:
                    rec.predikat = 'A'
                    rec.keterangan_predikat = 'Jayyid Jiddan'
                elif n >= 80:
                    rec.predikat = 'B+'
                    rec.keterangan_predikat = 'Jayyid'
                elif n >= 70:
                    rec.predikat = 'B'
                    rec.keterangan_predikat = 'Maqbul'
                elif n >= 60:
                    rec.predikat = 'C'
                    rec.keterangan_predikat = 'Dhaif'
                else:
                    rec.predikat = 'D'
                    rec.keterangan_predikat = 'Dhaif Jiddan'
                
            # Sistem SMP  
            elif jenjang in ['smp']: 
                if n >= 90:
                    rec.predikat = 'A'
                    rec.keterangan_predikat = 'Mumtaz'
                elif n >= 80:
                    rec.predikat = 'B'
                    rec.keterangan_predikat = 'Jayyid Jiddan'
                elif n >= 70:
                    rec.predikat = 'C'
                    rec.keterangan_predikat = 'Jayyid'
                else:
                    rec.predikat = 'D'
                    rec.keterangan_predikat = 'Mardud'
                    
            # Sistem SMA
            elif jenjang in ['sma']:
                if n >= 96:
                    rec.predikat = 'A+'
                    rec.keterangan_predikat = 'Mumtaz'
                elif n >= 90:
                    rec.predikat = 'A'
                    rec.keterangan_predikat = 'Mumtaz'
                elif n >= 80:
                    rec.predikat = 'B+'
                    rec.keterangan_predikat = 'Jayyid Jiddan'
                elif n >= 75:
                    rec.predikat = 'B'
                    rec.keterangan_predikat = 'Jayyid'
                elif n >= 70:
                    rec.predikat = 'C'
                    rec.keterangan_predikat = 'Maqbul'
                elif n >= 60:
                    rec.predikat = 'D'
                    rec.keterangan_predikat = 'Dhaif'
                else:
                    rec.predikat = 'E'
                    rec.keterangan_predikat = 'Dhaif Jiddan'
                    
            # Default (jika jenjang tidak dikenali) 
            else: 
                rec.predikat = False 
                rec.keterangan_predikat = False

    @api.depends('tahfidz_line_ids', 'tahfidz_line_ids.sequence')
    def _compute_main_fields(self):
        for rec in self:
            lines = rec.tahfidz_line_ids
            if lines:
                # urutkan manual berdasarkan sequence saja (aman tanpa id)
                sorted_lines = lines.sorted(key=lambda r: (r.sequence or 0))
                first_line = sorted_lines[0]
                last_line = sorted_lines[-1]

                rec.surah_id = last_line.surah_id.id
                rec.ayat_awal = first_line.ayat_awal.id
                rec.ayat_akhir = last_line.ayat_akhir.id
            else:
                rec.surah_id = False
                rec.ayat_awal = False
                rec.ayat_akhir = False


    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._compute_main_fields()  # isi surah_id, ayat_awal, ayat_akhir
        return record
    
    @api.depends('siswa_id', 'tahfidz_line_ids.surah_id', 'tahfidz_line_ids.ayat_akhir')
    def _compute_last_tahfidz(self):
        for rec in self:
            if not rec.siswa_id:
                rec.last_surah_id = False
                rec.last_ayat_akhir = False
                continue

            # Ambil penilaian terakhir yang sudah done
            last = self.env['cdn.penilaian_quran'].search([
                ('siswa_id', '=', rec.siswa_id.id),
                ('state', '=', 'done')
            ], order='tanggal desc, id desc', limit=1)

            if last and last.tahfidz_line_ids:
                last_line = last.tahfidz_line_ids.sorted(key=lambda r: (r.sequence or 0, r.id))[-1]
                rec.last_surah_id = last_line.surah_id.id
                rec.last_ayat_akhir = last_line.ayat_akhir.id
            elif last:
                rec.last_surah_id = last.surah_id.id
                rec.last_ayat_akhir = last.ayat_akhir.id
            else:
                # Belum ada data → mulai dari Al-Fatihah ayat 1
                surah_fatihah = self.env['cdn.surah'].search([('number', '=', 1)], limit=1)
                if surah_fatihah:
                    rec.last_surah_id = surah_fatihah.id
                    ayat_1 = self.env['cdn.ayat'].search([
                        ('surah_id', '=', surah_fatihah.id),
                        ('name', '=', 1)
                    ], limit=1)
                    rec.last_ayat_akhir = ayat_1.id
                else:
                    rec.last_surah_id = False
                    rec.last_ayat_akhir = False

    # === ONCHANGE ===
    @api.onchange('buku_harian_id')
    def _onchange_buku_harian(self):
        self.jilid_harian_id = False
        self.halaman_harian = False

    @api.onchange('buku_ujian_id')
    def _onchange_buku_ujian(self):
        self.jilid_ujian_id = False
        self.halaman_ujian = False

    @api.onchange('siswa_id')
    def _onchange_siswa_id(self):
        _logger.warning("ONCHANGE: siswa_id = %s", self.siswa_id)
        if not self.siswa_id:
            return

        # Ambil penilaian terakhir DONE (pakai logika sama seperti compute)
        last_penilaian = self.env['cdn.penilaian_quran'].search([
            ('siswa_id', '=', self.siswa_id.id),
            ('state', '=', 'done')
        ], order='tanggal desc, id desc', limit=1)

        if last_penilaian:
            if last_penilaian.tahfidz_line_ids:
                last_line = last_penilaian.tahfidz_line_ids.sorted(key=lambda r: (r.sequence or 0, r.id))[-1]
                self.last_surah_id = last_line.surah_id.id
                self.last_ayat_akhir = last_line.ayat_akhir.id

                # Tentukan ayat awal berikutnya
                surah = last_line.surah_id
                ayat_akhir = last_line.ayat_akhir.name if last_line.ayat_akhir else 0
                total_ayat = surah.jml_ayat if surah else 0

                if ayat_akhir and ayat_akhir < total_ayat:
                    # Lanjut surah sama
                    self.surah_id = surah.id
                    next_ayat_num = ayat_akhir + 1
                    next_ayat = self.env['cdn.ayat'].search([
                        ('surah_id', '=', surah.id),
                        ('name', '=', next_ayat_num)
                    ], limit=1)
                    self.ayat_awal = next_ayat.id
                else:
                    # Pindah surah berikutnya
                    next_surah = self.env['cdn.surah'].search([
                        ('number', '>', surah.number)
                    ], order='number', limit=1)
                    if next_surah:
                        self.surah_id = next_surah.id
                        ayat_1 = self.env['cdn.ayat'].search([
                            ('surah_id', '=', next_surah.id),
                            ('name', '=', 1)
                        ], limit=1)
                        self.ayat_awal = ayat_1.id
            else:
                # fallback kalau tidak ada line
                self.last_surah_id = last_penilaian.surah_id.id
                self.last_ayat_akhir = last_penilaian.ayat_akhir.id
        else:
            # Belum ada data → mulai dari Al-Fatihah
            surah_fatihah = self.env['cdn.surah'].search([('number', '=', 1)], limit=1)
            if surah_fatihah:
                self.surah_id = surah_fatihah.id
                ayat_1 = self.env['cdn.ayat'].search([
                    ('surah_id', '=', surah_fatihah.id),
                    ('name', '=', 1)
                ], limit=1)
                self.ayat_awal = ayat_1.id

    # === WORKFLOW ===
    def action_confirm(self):
        for rec in self:
            rec.state = 'done'
            rec._compute_last_tahfidz()  # pastikan langsung update surah terakhir

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    # === OTHER ===
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
    
class PenilaianQuranLine(models.Model):
    _name = 'cdn.penilaian_quran_line'
    _description = 'Detail Setoran Tahfidz'
    _order = 'sequence, id'

    penilaian_id = fields.Many2one('cdn.penilaian_quran', string='Penilaian', ondelete='cascade')
    sequence = fields.Integer(string='No', default=1)
    surah_id = fields.Many2one('cdn.surah', string='Surah', required=True)
    ayat_awal = fields.Many2one('cdn.ayat', string='Ayat Awal', domain="[('surah_id','=',surah_id)]")
    ayat_akhir = fields.Many2one('cdn.ayat', string='Ayat Akhir', domain="[('surah_id','=',surah_id)]")
    jml_baris = fields.Integer(string="Jumlah Maqra")
    nilai_hafalan = fields.Integer(string='Nilai Hafalan', default=75)

    predikat = fields.Char(string='Predikat', compute='_compute_predikat', store=True)
    keterangan = fields.Char(string='Keterangan')

    @api.depends('nilai_hafalan', 'penilaian_id.jenjang_display')
    def _compute_predikat(self):
        for rec in self:
            n = rec.nilai_hafalan or 0
            jenjang = (rec.penilaian_id.jenjang_display or '').lower()

            # === PAUD/TK ===
            if jenjang in ['paud', 'tk', 'tk/ra']:
                if n >= 90:
                    rec.predikat = 'BSB - Berkembang Sangat Bagus'
                elif n >= 75:
                    rec.predikat = 'BSA - Berkembang Sesuai Harapan'
                elif n >= 60:
                    rec.predikat = 'MB - Mulai Berkembang'
                else:
                    rec.predikat = 'BB - Belum Berkembang'

            # === SD ===
            elif jenjang in ['sd', 'sd/mi', 'sdmi']:
                if n >= 95:
                    rec.predikat = 'A+ (Mumtaz)'
                elif n >= 91:
                    rec.predikat = 'A (Jayyid Jiddan)'
                elif n >= 80:
                    rec.predikat = 'B+ (Jayyid)'
                elif n >= 70:
                    rec.predikat = 'B (Maqbul)'
                elif n >= 60:
                    rec.predikat = 'C (Dhaif)'
                else:
                    rec.predikat = 'D (Dhaif Jiddan)'

            # === SMP ===
            elif jenjang in ['smp', 'smp/mts', 'smpmts']:
                if n >= 90:
                    rec.predikat = 'A (Mumtaz)'
                elif n >= 80:
                    rec.predikat = 'B (Jayyid Jiddan)'
                elif n >= 70:
                    rec.predikat = 'C (Jayyid)'
                else:
                    rec.predikat = 'D (Mardud)'

            # === SMA ===
            elif jenjang in ['sma', 'ma', 'smama']:
                if n >= 96:
                    rec.predikat = 'A+ (Mumtaz)'
                elif n >= 90:
                    rec.predikat = 'A (Mumtaz)'
                elif n >= 80:
                    rec.predikat = 'B+ (Jayyid Jiddan)'
                elif n >= 75:
                    rec.predikat = 'B (Jayyid)'
                elif n >= 70:
                    rec.predikat = 'C (Maqbul)'
                elif n >= 60:
                    rec.predikat = 'D (Dhaif)'
                else:
                    rec.predikat = 'E (Dhaif Jiddan)'

            # === Default ===
            else:
                rec.predikat = False