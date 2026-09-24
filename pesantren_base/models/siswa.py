# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import json
import base64
from io import BytesIO
import qrcode
from odoo.exceptions import ValidationError
import random

import logging
_logger = logging.getLogger(__name__)


class res_partner(models.Model):
    _inherit = 'res.partner'

    jns_partner = fields.Selection(string='Jenis Partner', selection=[(
        'siswa', 'Siswa'), ('ortu', 'Orang Tua'), ('guru', 'Guru'), ('umum', 'Umum')])


class siswa(models.Model):

    _name = "cdn.siswa"
    _description = "Tabel siswa"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {"res.partner": "partner_id"}
    _sql_constraints = [
        ('nis_unique', 'unique(nis)', 'NIS sudah terdaftar! NIS harus unik untuk setiap santri.'),
    ]

    partner_id = fields.Many2one('res.partner', 'Partner', ondelete="cascade")
    active_id = fields.Many2one(
        'res.partner', string='Customer Active', compute="_compute_partner_id")
    qr_code_image = fields.Binary("QR Code", attachment=True)
    jenjang = fields.Selection(selection=[('paud', 'PAUD'), ('tk', 'TK/RA'), ('sd', 'SD/MI'), ('smp', 'SMP/MTS'), ('sma', 'SMA/MA/SMK'), ('nonformal',
                               'Non Formal'), ('rtq', 'Rumah Tahfidz Quran')],  string="Jenjang", related="ruang_kelas_id.name.jenjang", readonly=False, store=True, help="")
    nama_sekolah = fields.Selection(
        selection='_get_pilihan_nama_sekolah', string="Nama Sekolah", store=True, tracking=True)
    kamar_id = fields.Many2one('cdn.kamar_santri', string='Nama Kamar')
    ruang_kelas_id = fields.Many2one('cdn.ruang_kelas', string="Ruang Kelas")

    @api.model
    def _get_pilihan_nama_sekolah(self):
        pendidikan = self.env['ubig.pendidikan'].search([])
        return [(p.name, p.name) for p in pendidikan]

    @api.depends('partner_id', 'jenjang')
    def _compute_nama_sekolah(self):
        mapping_jenjang = {
            'paud': 'paud',
            'tk': 'tk',
            'sd': 'sdmi',
            'smp': 'smpmts',
            'sma': 'smama',
            'nonformal': 'nonformal'
        }

        for rec in self:
            nama_sekolah = False

            # 1. Coba dari pendaftaran
            pendaftaran = self.env['ubig.pendaftaran'].search([
                ('siswa_id', '=', rec.id)
            ], limit=1)

            if pendaftaran and pendaftaran.jenjang_id and pendaftaran.jenjang_id.name:
                nama_sekolah = pendaftaran.jenjang_id.name
            else:
                # 2. Alternatif dari partner
                partner_name = rec.partner_id.name
                alt_pendaftaran = self.env['ubig.pendaftaran'].search([
                    ('partner_id.name', '=', partner_name)
                ], limit=1)
                if alt_pendaftaran and alt_pendaftaran.jenjang_id and alt_pendaftaran.jenjang_id.name:
                    nama_sekolah = alt_pendaftaran.jenjang_id.name
                else:
                    # 3. Coba mapping dari jenjang
                    kode_jenjang = mapping_jenjang.get(rec.jenjang)
                    if kode_jenjang:
                        pendidikan = self.env['ubig.pendidikan'].search([
                            ('jenjang', '=', kode_jenjang)
                        ], limit=1)
                        nama_sekolah = pendidikan.name if pendidikan else False

            rec.nama_sekolah = nama_sekolah

    @api.onchange('nama_sekolah')
    def _onchange_nama_sekolah(self):
        """
        Update jenjang saat nama_sekolah berubah di form view.
        """
        # Mapping dari kode jenjang ke selection value
        mapping_kode_to_jenjang = {
            'paud': 'paud',
            'tk': 'tk',
            'sdmi': 'sd',
            'smpmts': 'smp',
            'smama': 'sma',
            'nonformal': 'nonformal'
        }

        if self.nama_sekolah:
            # Cari data pendidikan berdasarkan nama sekolah
            pendidikan = self.env['ubig.pendidikan'].search([
                ('name', '=', self.nama_sekolah)
            ], limit=1)

            if pendidikan and pendidikan.jenjang:
                # Mapping dari kode jenjang ke selection value
                jenjang_value = mapping_kode_to_jenjang.get(pendidikan.jenjang)
                if jenjang_value:
                    self.jenjang = jenjang_value
                else:
                    # Jika tidak ada mapping, coba langsung assign
                    self.jenjang = pendidikan.jenjang
            else:
                # Jika tidak ditemukan data pendidikan, reset jenjang
                self.jenjang = False
        else:
            # Jika nama_sekolah kosong, reset jenjang
            self.jenjang = False

    @api.model
    def update_nama_sekolah_all(self):
        """
        Method untuk memperbarui nama sekolah pada semua data santri
        yang dapat dipanggil dari shell Odoo
        """
        siswa_ids = self.search([])
        count = 0
        for siswa in siswa_ids:
            # Cari data pendaftaran yang punya siswa_id = siswa ini
            pendaftaran = self.env['ubig.pendaftaran'].search([
                ('siswa_id', '=', siswa.id)
            ], limit=1)

            if pendaftaran and pendaftaran.jenjang_id and pendaftaran.jenjang_id.name:
                siswa.nama_sekolah = pendaftaran.jenjang_id.name
                count += 1
            else:
                # Coba metode alternatif jika pendaftaran tidak ditemukan
                partner_name = siswa.partner_id.name
                alt_pendaftaran = self.env['ubig.pendaftaran'].search([
                    ('partner_id.name', '=', partner_name)
                ], limit=1)

                if alt_pendaftaran and alt_pendaftaran.jenjang_id and alt_pendaftaran.jenjang_id.name:
                    siswa.nama_sekolah = alt_pendaftaran.jenjang_id.name
                    count += 1

        _logger.info(f"Berhasil update {count} data nama sekolah santri")
        return True

    nis = fields.Char(string="NIS", help="Nomor Induk Siswa/Santri (Lokal)", copy=False)
    namapanggilan = fields.Char(string="Nama Panggilan")
    nisn = fields.Char(string="NISN",  help="Nomor Induk Siswa Nasional")
    tmp_lahir = fields.Char(string="Tempat Lahir",  help="")
    tgl_lahir = fields.Date(string="Tanggal Lahir",  help="")
    gol_darah = fields.Selection(selection=[(
        'A', 'A'), ('B', 'B'), ('AB', 'AB'), ('O', 'O')],  string="Golongan Darah",  help="")
    jns_kelamin = fields.Selection(selection=[(
        'L', 'Laki-laki'), ('P', 'Perempuan')],  string="Jenis Kelamin",  help="")

    rt_rw = fields.Char(string="RT/RW")
    propinsi_id = fields.Many2one(
        comodel_name="cdn.ref_propinsi",  string="Provinsi",  help="")
    kota_id = fields.Many2one(
        comodel_name="cdn.ref_kota",  string="Kota",  help="")
    kecamatan_id = fields.Many2one(
        comodel_name="cdn.ref_kecamatan",  string="Kecamatan",  help="")

    kewarganegaraan = fields.Selection(
        selection=[('wni', 'WNI'), ('wna', 'WNA')],  string="Kewarganegaraan",  help="Status Kewarganegaraan Siswa")
    agama = fields.Selection(selection=[('islam', 'Islam'), ('katolik', 'Katolik'), ('protestan', 'Protestan'), (
        'hindu', 'Hindu'), ('budha', 'Budha')],  string="Agama", default='islam', help="")
    panggilan = fields.Char(string="Nama Panggilan",  help="")

    nik = fields.Char(string="No Induk Keluarga",
                      help="Nomor Induk Kependudukan (Sesuai KK)")
    anak_ke = fields.Integer(string="Anak ke",  help="")
    jml_saudara_kandung = fields.Integer(
        string="Jml Saudara Kandung",  help="")
    bahasa = fields.Char(string="Bahasa Sehari-hari",  help="")
    hobi = fields.Many2one(comodel_name='cdn.ref_hobi', string='Hobi')
    cita_cita = fields.Char(string='Cita-Cita')

    email = fields.Char(string="Email", tracking=True,
                        store=True, readonly=False, related='orangtua_id.email')
    nomor_login = fields.Char(string="Nomor HP", help="Nomor HP/WhatsApp Untuk Login",
                              tracking=True, store=True, readonly=False, related='orangtua_id.phone')
    password = fields.Char(string="Kata Sandi", help="Kata Sandi Login",
                           tracking=True, store=True, readonly=False, related='orangtua_id.password')
    show_password_button = fields.Boolean(
        compute='_compute_show_password_button')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('terdaftar', 'Terdaftar'),
        ('seleksi', 'Seleksi'),
        ('diterima', 'Diterima'),
        ('ditolak', 'Ditolak'),
        ('batal', 'Batal'),
    ], string='Status', default='draft',
        track_visibility='onchange')
    status_akun = fields.Selection([
        ('aktif', 'Aktif'),
        ('nonaktif', 'Tidak Aktif'),
        ('blokir', 'Diblokir')
    ], string="Kartu", default='aktif')

    alasan_keluar = fields.Selection([
        ('lulus', 'Lulus'),
        ('pindah', 'Pindah Sekolah'),
        ('berhenti', 'Berhenti / Mengundurkan Diri'),
        ('dikeluarkan', 'Dikeluarkan (Pelanggaran)'),
        ('meninggal', 'Meninggal Dunia'),
        ('lainnya', 'Lainnya')
    ], string='Alasan Keluar', readonly=True)
    tanggal_keluar = fields.Date(string='Tanggal Keluar', readonly=True)

    # Jika `partner_id` field ada, atau bisa diubah ke field lain yang relevan
    @api.depends('partner_id')
    def _compute_partner_id(self):
        for record in self:
            if record.partner_id:
                # Mengisi active_id berdasarkan data partner_id
                # Bisa disesuaikan dengan field partner_id yang ingin digunakan
                record.active_id = record.partner_id
            else:
                record.active_id = 'No Partner'  # Nilai default jika partner_id kosong

    @api.model
    def default_get(self, fields_list):
        """Override default_get untuk set jns_partner"""
        res = super(siswa, self).default_get(fields_list)
        res['jns_partner'] = 'siswa'
        return res

    def _create_orangtua_from_akun(self):
        """Buat record orangtua baru dari data akun siswa"""
        self.ensure_one()

        if self.orangtua_id:
            return  # Sudah ada orangtua

        # Validasi: minimal harus ada email atau nomor_login
        if not self.email and not self.nomor_login:
            return

        # Siapkan data untuk membuat orangtua
        orangtua_vals = {
            'name': f"Orang Tua {self.name}",
            'email': self.email or False,
            'mobile': self.nomor_login or False,
            'phone': self.nomor_login or False,
            'password': self.password or (self.email[:8] if self.email else 'default123'),
        }

        # Tambahkan data ayah/ibu jika ada
        if self.ayah_nama:
            orangtua_vals.update({
                'ayah_nama': self.ayah_nama,
                'ayah_telp': self.ayah_telp,
                'ayah_email': self.ayah_email
            })

        if self.ibu_nama:
            orangtua_vals.update({
                'ibu_nama': self.ibu_nama,
                'ibu_telp': self.ibu_telp,
                'ibu_email': self.ibu_email
            })

        try:
            # Buat record orangtua baru
            orangtua = self.env['cdn.orangtua'].sudo().create(orangtua_vals)

            # Link ke siswa
            self.orangtua_id = orangtua.id
            self.orangtua_ids = [(4, orangtua.id)]

            _logger.info(f"Orangtua baru dibuat untuk siswa {self.name}")
            return orangtua

        except Exception as e:
            _logger.error(f"Error creating orangtua: {str(e)}")
            raise UserError(f"Gagal membuat akun orang tua: {str(e)}")

    def _generate_auto_nis(self, vals=None):
        vals = vals or {}
        jenjang = vals.get('jenjang') or (self.jenjang if self else False)
        tgl = vals.get('tanggal_daftar') or (self.tanggal_daftar if self else False) or fields.Date.today()

        try:
            tahun_daftar = tgl.strftime('%Y')[-2:]
        except AttributeError:
            tahun_daftar = fields.Date.today().strftime('%Y')[-2:]

        lembaga = {
            'paud': '01', 'tk': '02', 'sdmi': '03',
            'smpmts': '04', 'smama': '05', 'smk': '10', 'nonformal': '06',
        }.get(jenjang, '00')

        nomor_pendaftaran = vals.get('nomor_pendaftaran') or (self.nomor_pendaftaran if self else False)
        if nomor_pendaftaran and str(nomor_pendaftaran).isdigit():
            nomor = str(nomor_pendaftaran).zfill(4)
        else:
            nomor = str(random.randint(1000, 9999))

        nis_candidate = f"{lembaga}.{tahun_daftar}.{nomor}"

        rec_id = self.id if self else False
        domain = [('nis', '=', nis_candidate)]
        if rec_id:
            domain.append(('id', '!=', rec_id))

        count = 1
        final_nis = nis_candidate
        while self.with_context(active_test=False).search(domain, limit=1):
            final_nis = f"{lembaga}.{tahun_daftar}.{random.randint(1000, 9999)}"
            domain = [('nis', '=', final_nis)]
            if rec_id:
                domain.append(('id', '!=', rec_id))

        return final_nis

    def _validate_nama_nis(self, vals, record=None):
        """Validasi wajib: Nama tidak boleh kosong, NIS wajib & unik"""
        is_create = record is None

        # ---- Validasi NAMA ----
        name_val = vals.get('name')
        if name_val is not None:
            if not name_val or not str(name_val).strip():
                raise ValidationError('Nama santri wajib diisi dan tidak boleh kosong!')
        elif is_create and not vals.get('partner_id'):
            raise ValidationError('Nama santri wajib diisi!')

        # ---- Validasi NIS ----
        nis_val = vals.get('nis')
        if nis_val is not None and nis_val:
            nis_str = str(nis_val).strip()
            if not nis_str:
                raise ValidationError('NIS (Nomor Induk Santri) wajib diisi dan tidak boleh kosong!')
            # Cek keunikan NIS termasuk santri nonaktif
            domain = [('nis', '=', nis_str)]
            if record:
                domain += [('id', 'not in', record.ids)]
            exists = self.with_context(active_test=False).search(domain, limit=1)
            if exists:
                raise ValidationError(
                    f'NIS "{nis_str}" sudah terdaftar pada santri "{exists.name}". '
                    'NIS harus unik untuk setiap santri (aktif maupun nonaktif)!')

    @api.model
    def create(self, vals):
        """Override create untuk validasi Nama & NIS wajib + auto-create orangtua"""
        if vals.get('nis'):
            vals['nis'] = str(vals['nis']).strip()

        # Jika NIS tidak terisi saat create, otomatis buat NIS unik
        if not vals.get('nis') or not str(vals.get('nis')).strip():
            vals['nis'] = self._generate_auto_nis(vals)

        self._validate_nama_nis(vals, record=None)
        res = super(siswa, self).create(vals)

        # Sinkronisasi orangtua_id ke orangtua_ids jika diisi
        if res.orangtua_id and res.orangtua_id not in res.orangtua_ids:
            res.orangtua_ids = [(4, res.orangtua_id.id)]
        elif res.orangtua_ids and not res.orangtua_id:
            res.orangtua_id = res.orangtua_ids[0].id

        # Create orangtua jika data akun diisi tapi orangtua_id kosong
        if (vals.get('email') or vals.get('nomor_login')) and not vals.get('orangtua_id'):
            res._create_orangtua_from_akun()

        return res

    def write(self, vals):
        """Override write untuk validasi Nama & NIS, auto-create orangtua, dan auto-reactivate status_akun"""
        if 'nis' in vals and vals.get('nis'):
            vals['nis'] = str(vals['nis']).strip()

        # Validasi: NIS tidak boleh dikosongkan jika sebelumnya sudah terisi
        if 'nis' in vals:
            nis_val = vals.get('nis')
            if not nis_val or not str(nis_val).strip():
                for record in self:
                    if record.nis:
                        raise ValidationError(
                            f'NIS santri "{record.name}" tidak boleh dikosongkan! '
                            'NIS yang sudah ada tidak bisa dihapus.')

        # Validasi: Nama tidak boleh dikosongkan secara eksplisit
        if 'name' in vals:
            name_val = vals.get('name')
            if not name_val or not str(name_val).strip():
                raise ValidationError('Nama santri wajib diisi dan tidak boleh dikosongkan!')

        # Cek keunikan NIS jika NIS diubah
        if 'nis' in vals and vals.get('nis'):
            nis_str = str(vals['nis']).strip()
            domain = [('nis', '=', nis_str), ('id', 'not in', self.ids)]
            exists = self.with_context(active_test=False).search(domain, limit=1)
            if exists:
                raise ValidationError(
                    f'NIS "{nis_str}" sudah terdaftar pada santri "{exists.name}". '
                    'NIS harus unik untuk setiap santri (aktif maupun nonaktif)!')

        if vals.get('active') is True:
            if 'status_akun' not in vals:
                vals['status_akun'] = 'aktif'
            if 'alasan_keluar' not in vals:
                vals['alasan_keluar'] = False
            if 'tanggal_keluar' not in vals:
                vals['tanggal_keluar'] = False

        res = super(siswa, self).write(vals)

        # Sinkronisasi orangtua_id dan orangtua_ids
        if 'orangtua_id' in vals or 'orangtua_ids' in vals:
            for record in self:
                if record.orangtua_id and record.orangtua_id not in record.orangtua_ids:
                    record.orangtua_ids = [(4, record.orangtua_id.id)]
                elif record.orangtua_ids and not record.orangtua_id:
                    record.orangtua_id = record.orangtua_ids[0].id

        # Jika edit akun tapi belum ada orangtua, buat baru
        akun_fields = ['email', 'nomor_login', 'password']
        has_akun_changes = any(field in vals for field in akun_fields)

        if has_akun_changes:
            for record in self:
                if not record.orangtua_id and (record.email or record.nomor_login):
                    record._create_orangtua_from_akun()

        return res

    # Data Orang Tua
    ayah_nama = fields.Char(string="Nama Ayah",  help="")
    ayah_tmp_lahir = fields.Char(string="Tmp Lahir (Ayah)",  help="")
    ayah_tgl_lahir = fields.Date(string="Tgl Lahir (Ayah)",  help="")
    ayah_warganegara = fields.Selection(
        selection=[('wni', 'WNI'), ('wna', 'WNA')],  string="Warganegara (Ayah)",  help="")
    ayah_telp = fields.Char(string="No Telepon (Ayah)",  help="")
    ayah_email = fields.Char(string="Email (Ayah)",  help="")
    ayah_pekerjaan_id = fields.Many2one(
        comodel_name="cdn.ref_pekerjaan",  string="Pekerjaan (Ayah)",  help="")
    ayah_pendidikan_id = fields.Many2one(
        comodel_name="cdn.ref_pendidikan",  string="Pendidikan (Ayah)",  help="")
    ayah_kantor = fields.Char(string="Kantor (Ayah)",  help="")
    ayah_penghasilan = fields.Char(string="Penghasilan (Ayah)",  help="")
    ayah_agama = fields.Selection(selection=[('islam', 'Islam'), ('katolik', 'Katolik'), (
        'protestan', 'Protestan'), ('hindu', 'Hindu'), ('budha', 'Budha')],  string="Agama (Ayah)",  help="")

    ibu_nama = fields.Char(string="Nama Ibu",  help="")
    ibu_tmp_lahir = fields.Char(string="Tmp lahir (Ibu) ",  help="")
    ibu_tgl_lahir = fields.Date(string="Tgl lahir (Ibu)",  help="")
    ibu_warganegara = fields.Selection(
        selection=[('wni', 'WNI'), ('wna', 'WNA')],  string="Warganegara (Ibu)",  help="")
    ibu_telp = fields.Char(string="No Telepon (Ibu)",  help="")
    ibu_email = fields.Char(string="Email (Ibu)",  help="")
    ibu_pekerjaan_id = fields.Many2one(
        comodel_name="cdn.ref_pekerjaan",  string="Pekerjaan (Ibu)",  help="")
    ibu_pendidikan_id = fields.Many2one(
        comodel_name="cdn.ref_pendidikan",  string="Pendidikan (Ibu)",  help="")
    ibu_kantor = fields.Char(string="Kantor (Ibu)",  help="")
    ibu_penghasilan = fields.Char(string="Penghasilan (Ibu)",  help="")
    ibu_agama = fields.Selection(selection=[('islam', 'Islam'), ('katolik', 'Katolik'), (
        'protestan', 'Protestan'), ('hindu', 'Hindu'), ('budha', 'Budha')],  string="Agama (Ibu)",  help="")

    wali_nama = fields.Char(string="Nama Wali",  help="")
    wali_tmp_lahir = fields.Char(string="Tmp lahir (Wali)",  help="")
    wali_tgl_lahir = fields.Date(string="Tgl lahir (Wali)",  help="")
    wali_telp = fields.Char(string="No Telepon (Wali)",  help="")
    wali_email = fields.Char(string="Email (Wali)",  help="")
    wali_agama = fields.Selection(selection=[('islam', 'Islam'), ('katolik', 'Katolik'), (
        'protestan', 'Protestan'), ('hindu', 'Hindu'), ('budha', 'Budha')],  string="Agama (Wali)",  help="")
    wali_hubungan = fields.Char(string="Hubungan dengan Siswa",  help="")

    orangtua_id = fields.Many2one(
        comodel_name="cdn.orangtua",  string="Orang Tua Utama",  help="Akun orang tua utama (penanggung jawab)")
    orangtua_ids = fields.Many2many(
        comodel_name="cdn.orangtua",
        relation="cdn_siswa_orangtua_rel",
        column1="siswa_id",
        column2="orangtua_id",
        string="Akun Orang Tua / Wali",
        help="Daftar akun orang tua (ayah, ibu, wali) yang terhubung dengan santri ini"
    )
    tahunajaran_id = fields.Many2one(
        comodel_name="cdn.ref_tahunajaran",  string="Tahun Ajaran",  help="")
    ruang_kelas_id = fields.Many2one(
        comodel_name="cdn.ruang_kelas",  string="Ruang Kelas", help="")
    ekstrakulikuler_ids = fields.Many2many(
        "cdn.ekstrakulikuler", string="Ekstrakulikuler")

    centang = fields.Boolean(string="Naik/Tidak", default=True)

    def action_toggle_centang(self):
        """Toggle field centang dari list view (untuk Kenaikan Kelas)"""
        for rec in self:
            rec.centang = not rec.centang

    tingkat = fields.Many2one(comodel_name="cdn.tingkat",  string="Tingkat",
                              related="ruang_kelas_id.name.tingkat", readonly=True, store=True, help="")

    row_number = fields.Integer(
        string='No', compute='_compute_row_number', store=False)

    def _compute_row_number(self):
        for index, record in enumerate(self):
            record.row_number = index + 1

    # Data Pendaftaran
    tgl_daftar = fields.Date(string='Tgl Pendaftaran')
    asal_sekolah = fields.Char(string='Asal Sekolah')
    alamat_asal_sek = fields.Char(string='Alamat Sekolah Asal')
    telp_asal_sek = fields.Char(string='No Telp Sekolah Asal')
    kepsek_sekolah_asal = fields.Char(string='Nama Kepala Sekolah')
    status_sekolah_asal = fields.Selection(string='Status Sekolah Asal', selection=[
                                           ('swasta', 'Swasta'), ('negeri', 'Negeri'),])

    prestasi_sebelum = fields.Char(string='Prestasi Diraih')
    bakat = fields.Many2many(
        comodel_name='cdn.ref_bakat', string='Bakat Siswa')
    jalur_pendaftaran = fields.Many2one(
        comodel_name='cdn.jalur_pendaftaran', string='Jalur Pendaftaran')
    jurusan_sma = fields.Many2one(
        comodel_name='cdn.master_jurusan', string='Bidang/Jurusan')

    # Nilai Rata-rata Raport Kelas
    raport_4sd_1 = fields.Float(string='Raport 4 SD Smt 1')
    raport_4sd_2 = fields.Float(string='Raport 4 SD Smt 2')
    raport_5sd_1 = fields.Float(string='Raport 5 SD Smt 1')
    raport_5sd_2 = fields.Float(string='Raport 5 SD Smt 2')
    raport_6sd_1 = fields.Float(string='Raport 4 SD Smt 1')
    baca_quran = fields.Selection(string="Baca Qur'an", selection=[(
        'belumbisa', 'Belum Bisa'), ('kuranglancar', 'Kurang Lancar'), ('lancar', 'Lancar'), ('tartil', 'Tartil')])

    bebasbiaya = fields.Boolean(string='Bebas Biaya', default=False)
    harga_komponen = fields.One2many(
        comodel_name='cdn.harga_khusus', inverse_name='siswa_id', string='Harga Khusus')
    penetapan_tagihan_id = fields.Many2one(
        'cdn.penetapan_tagihan', string='penetapan_tagihan_id')
    nomor_pendaftaran = fields.Char(string="Nomor Pendfataran")
    tanggal_daftar = fields.Date(string="Tanggal Daftar")
    barcode_santri = fields.Char(string='Kartu Santri')

    @api.constrains('nik')
    def _check_nik_unique(self):
        for record in self:
            if record.nik:
                exists = self.search(
                    [('nik', '=', record.nik), ('id', '!=', record.id)], limit=1)
                if exists:
                    raise UserError(
                        'Data NIK tersebut sudah pernah terdaftar, pastikan NIK harus unik!')

    @api.constrains('nis')
    def _check_nis_unique(self):
        """Validasi keunikan NIS — termasuk santri yang sudah nonaktif/diarsipkan"""
        for record in self:
            if record.nis and record.nis.strip():
                nis_str = record.nis.strip()
                # Cek keunikan NIS termasuk santri nonaktif (active=False)
                exists = self.with_context(active_test=False).search(
                    [('nis', '=', nis_str), ('id', '!=', record.id)], limit=1)
                if exists:
                    raise ValidationError(
                        f'NIS "{nis_str}" sudah terdaftar pada santri "{exists.name}". '
                        'NIS harus unik untuk setiap santri (aktif maupun nonaktif)!')

    @api.depends('password')
    def _compute_show_password_button(self):
        for rec in self:
            rec.show_password_button = bool(rec.password)

    def action_show_password(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Kata Sandi',
            'res_model': 'lihat.password.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_password': self.password,
            }
        }

    def default_get(self, fields):
        res = super(siswa, self).default_get(fields)
        res['jns_partner'] = 'siswa'
        return res

    def _get_saldo_tagihan(self):
        saldo_invoice = self.env['account.move'].search(
            [('partner_id', '=', self.partner_id.id), ('state', '=', 'posted')])
        self.saldo_tagihan = sum(
            item.amount_residual for item in saldo_invoice)

    saldo_tagihan = fields.Float('Saldo Tagihan', compute='_get_saldo_tagihan')

    def open_tagihan(self):
        action = self.env.ref('action_tagihan_inherit_view').read()[0]
        action['domain'] = [('partner_id', '=', self.partner_id.id),
                            ('state', '=', 'posted'), ('move_type', '=', 'out_invoice')]
        return action

    @api.model
    def print_kartu_santri(self, additional_arg=None):
        return self.env.ref("pesantren_base.action_report_kartu_santri").report_action(self)

    @api.model
    def print_sertifikat_santri(self, additional_arg=None):
        return self.env.ref("pesantren_base.action_report_sertifikat_santri").report_action(self)

    def action_cetak_kts(self):
        ids = "&".join(f"id={rec.id}" for rec in self)
        return {
            'type': 'ir.actions.act_url',
            'url': f'/cetak_kts?{ids}',
            'target': 'new',
        }

    def action_recharge(self):
        partner_model = self.env['res.partner']
        return partner_model.action_recharge()

    def action_generate_nis(self):
        for rec in self:
            rec.nis = rec._generate_auto_nis()


    def action_recharge_wallet_mass(self):
        partner_model = self.env['res.partner']
        return partner_model.action_recharge_mass()

    def action_register(self):
        context = dict(self.env.context)
        active_ids = context.get('active_ids', [])

        return {
            'name': 'Register Kartu Santri',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.register.kartu',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'default_partner_ids': active_ids}
        }

    def name_get(self):
        result = []
        for siswa in self:
            name = f"{siswa.name} - {siswa.nis}" if siswa.nis else siswa.name
            result.append((siswa.id, name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """
        Kustomisasi pencarian untuk mendukung pencarian berdasarkan nama atau NIS
        """
        args = args or []
        domain = []
        if name:
            domain = [
                '|',
                ('name', operator, name),
                ('nis', operator, name)
            ]

        # Gabungkan domain tambahan jika ada
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()

    def action_generate_qr(self):
        for siswa in self:
            qr_data = f"NIS: {siswa.nis}\nNama: {siswa.name}\nKamar: {siswa.kamar_id.kamar_id.name}\nKelas: {siswa.ruang_kelas_id.name.name}"

            qr = qrcode.QRCode(
                version=1,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')

            siswa.qr_code_image = base64.b64encode(buffer.getvalue())

    def unlink(self):
        for record in self:
            related_modules = []

            # 1. Absensi Siswa (Kelas)
            if 'cdn.absensi_siswa_lines' in self.env and self.env['cdn.absensi_siswa_lines'].sudo().search([('siswa_id', '=', record.id)], limit=1):
                related_modules.append("Absensi Siswa")

            # 2. Absensi Halaqoh
            if 'cdn.absen_halaqoh_lines' in self.env and self.env['cdn.absen_halaqoh_lines'].sudo().search([('siswa_id', '=', record.id)], limit=1):
                related_modules.append("Absensi Halaqoh")

            # 3. Penilaian Al-Qur'an / Tahfidz
            if 'cdn.penilaian_quran' in self.env and self.env['cdn.penilaian_quran'].sudo().search([('siswa_id', '=', record.id)], limit=1):
                related_modules.append("Penilaian Al-Qur'an")
            elif 'cdn.penilaian_santri' in self.env and self.env['cdn.penilaian_santri'].sudo().search([('siswa_id', '=', record.id)], limit=1):
                related_modules.append("Penilaian Al-Qur'an")

            # 4. Penilaian Akademik
            if 'cdn.penilaian_siswa' in self.env and self.env['cdn.penilaian_siswa'].sudo().search([('siswa_id', '=', record.id)], limit=1):
                related_modules.append("Penilaian Akademik")

            # 5. Perizinan Santri
            if 'cdn.perijinan' in self.env and self.env['cdn.perijinan'].sudo().search([('siswa_id', '=', record.id)], limit=1):
                related_modules.append("Perizinan Santri")

            # 6. Pelanggaran Santri
            if 'cdn.pelanggaran' in self.env and self.env['cdn.pelanggaran'].sudo().search([('siswa_id', '=', record.id)], limit=1):
                related_modules.append("Pelanggaran Santri")

            # 7. Kesehatan Santri
            if 'cdn.kesehatan' in self.env and self.env['cdn.kesehatan'].sudo().search([('siswa_id', '=', record.id)], limit=1):
                related_modules.append("Kesehatan Santri")

            if related_modules:
                msg_modules = ", ".join(related_modules)
                raise UserError(
                    f"⛔ Gagal Menghapus Data Santri!\n\n"
                    f"Data Santri \"{record.name}\" tidak dapat dihapus karena sudah tercatat dalam riwayat: {msg_modules}.\n\n"
                    f"Saran: Ubah status santri menjadi Non-Aktif / Keluar / Alumni."
                )
        return super(siswa, self).unlink()

    def init(self):
        super().init()
        # Migrasi data: pastikan semua data orangtua_id yang sudah ada tercatat di relasi Many2many cdn_siswa_orangtua_rel
        try:
            self._cr.execute("""
                CREATE TABLE IF NOT EXISTS cdn_siswa_orangtua_rel (
                    siswa_id INTEGER NOT NULL,
                    orangtua_id INTEGER NOT NULL,
                    PRIMARY KEY (siswa_id, orangtua_id)
                );
                INSERT INTO cdn_siswa_orangtua_rel (siswa_id, orangtua_id)
                SELECT s.id, s.orangtua_id 
                FROM cdn_siswa s
                WHERE s.orangtua_id IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1 FROM cdn_siswa_orangtua_rel r 
                      WHERE r.siswa_id = s.id AND r.orangtua_id = s.orangtua_id
                  );
            """)
        except Exception as e:
            _logger.warning("Auto-migration cdn_siswa_orangtua_rel failed: %s", e)

