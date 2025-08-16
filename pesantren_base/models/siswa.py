#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests, json
import base64
from io import BytesIO
import qrcode
from odoo.exceptions import ValidationError
import random

import logging
_logger = logging.getLogger(__name__)

class res_partner(models.Model):
    _inherit = 'res.partner'

    jns_partner = fields.Selection(string='Jenis Partner', selection=[('siswa', 'Siswa'), ('ortu', 'Orang Tua'), ('guru', 'Guru'), ('umum', 'Umum')])

class siswa(models.Model):

    _name               = "cdn.siswa"
    _description        = "Tabel siswa"
    _inherit            = ['mail.thread', 'mail.activity.mixin']
    _inherits           = {"res.partner": "partner_id"}

    partner_id          = fields.Many2one('res.partner', 'Partner', ondelete="cascade")
    active_id           = fields.Many2one('res.partner', string='Customer Active', compute="_compute_partner_id")
    qr_code_image       = fields.Binary("QR Code", attachment=True)

    jenjang             = fields.Selection(selection=[('paud','PAUD'),('tk','TK/RA'),('sd','SD/MI'),('smp','SMP/MTS'),('sma','SMA/MA/SMK'), ('nonformal', 'Nonformal')],  string="Jenjang", related="ruang_kelas_id.name.jenjang", readonly=False, store=True, help="")
    nama_sekolah        = fields.Selection(selection='_get_pilihan_nama_sekolah',string="Nama Sekolah",store=True,tracking=True)
    kamar_id            = fields.Many2one('cdn.kamar_santri', string='Nama Kamar')
    ruang_kelas_id      = fields.Many2one('cdn.ruang_kelas', string="Ruang Kelas")


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

    # @api.onchange('jenjang')
    # def _onchange_jenjang(self):
    #     """
    #     Update nama_sekolah saat jenjang berubah di form view.
    #     """
    #     mapping_jenjang = {
    #         'paud': 'paud',
    #         'tk': 'tk',
    #         'sd': 'sdmi',
    #         'smp': 'smpmts',
    #         'sma': 'smama',
    #         'nonformal': 'nonformal'
    #     }

    #     kode_jenjang = mapping_jenjang.get(self.jenjang)
    #     if kode_jenjang:
    #         pendidikan = self.env['ubig.pendidikan'].search([
    #             ('jenjang', '=', kode_jenjang)
    #         ], limit=1)
    #         self.nama_sekolah = pendidikan.name if pendidikan else False
    #     else:
    #         self.nama_sekolah = False

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


    # nama_sekolah        = fields.Char(string="Nama Sekolah", readonly=False, store=True)
    
    # @api.onchange('jenjang')
    # def _onchange_jenjang(self):
    #     if self.jenjang:
    #         # Cari pendaftaran yang cocok dengan nama dan jenjang
    #         pendaftaran = self.env['ubig.pendaftaran'].search([
    #             ('jenjang', '=', self.jenjang)
    #         ], limit=1)

    #         if pendaftaran:
    #             self.nama_sekolah = pendaftaran.ini_nama
    #         else:
    #             self.nama_sekolah = False


    nis                 = fields.Char( string="NIS",  help="")
    namapanggilan       = fields.Char(string="Nama Panggilan")
    nisn                = fields.Char( string="NISN",  help="")
    tmp_lahir           = fields.Char( string="Tempat Lahir",  help="")
    tgl_lahir           = fields.Date( string="Tgl Lahir",  help="")
    gol_darah           = fields.Selection(selection=[('A','A'),('B','B'),('AB','AB'),('O','O')],  string="Golongan Darah",  help="")
    jns_kelamin         = fields.Selection(selection=[('L','Laki-laki'),('P','Perempuan')],  string="Jenis Kelamin",  help="")

    rt_rw               = fields.Char(string="RT/RW")
    propinsi_id         = fields.Many2one(comodel_name="cdn.ref_propinsi",  string="Provinsi",  help="")
    kota_id             = fields.Many2one(comodel_name="cdn.ref_kota",  string="Kota",  help="")
    kecamatan_id        = fields.Many2one(comodel_name="cdn.ref_kecamatan",  string="Kecamatan",  help="")


    kewarganegaraan     = fields.Selection(selection=[('wni','WNI'),('wna','WNA')],  string="Kewarganegaraan",  help="")
    agama               = fields.Selection(selection=[('islam', 'Islam'), ('katolik', 'Katolik'), ('protestan', 'Protestan'), ('hindu', 'Hindu'), ('budha', 'Budha')],  string="Agama", default='islam', help="")
    panggilan           = fields.Char( string="Nama Panggilan",  help="")
    
    nik                 = fields.Char( string="No Induk Keluarga",  help="")
    anak_ke             = fields.Integer( string="Anak ke",  help="")
    jml_saudara_kandung = fields.Integer( string="Jml Saudara Kandung",  help="")
    bahasa              = fields.Char( string="Bahasa Sehari-hari",  help="")
    hobi                = fields.Many2one(comodel_name='cdn.ref_hobi', string='Hobi')
    cita_cita           = fields.Char(string='Cita-Cita')

    status_akun = fields.Selection([
        ('aktif', 'Aktif'),
        ('nonaktif', 'Tidak Aktif'),
        ('blokir', 'Diblokir')
    ], string="Kartu", default='aktif')
    #Data Tempat Tinggal
    # tinggal_di          = fields.Selection(string='Tinggal di', selection=[('rumah', 'Rumah'), ('pondok', 'Pondok Pesantren'),], default='rumah')
    # pesantren_id        = fields.Many2one(comodel_name='res.partner', string='Nama Pesantren', domain="[('is_pesantren','=',True)]")
    # pesantren_alamat    = fields.Char(string='Alamat Pesantren', related='pesantren_id.street')
    # pesantren_telp      = fields.Char(string='No Telp Pesantren', related='pesantren_id.phone')

    @api.depends('partner_id')  # Jika `partner_id` field ada, atau bisa diubah ke field lain yang relevan
    def _compute_partner_id(self):
        for record in self:
            if record.partner_id:
                # Mengisi active_id berdasarkan data partner_id
                record.active_id = record.partner_id  # Bisa disesuaikan dengan field partner_id yang ingin digunakan
            else:
                record.active_id = 'No Partner'  # Nilai default jika partner_id kosong
    
    # Data Orang Tua
    ayah_nama           = fields.Char( string="Nama Ayah",  help="")
    ayah_tmp_lahir      = fields.Char( string="Tmp Lahir (Ayah)",  help="")
    ayah_tgl_lahir      = fields.Date( string="Tgl Lahir (Ayah)",  help="")
    ayah_warganegara    = fields.Selection(selection=[('wni','WNI'),('wna','WNA')],  string="Warganegara (Ayah)",  help="")
    ayah_telp           = fields.Char( string="No Telepon (Ayah)",  help="")
    ayah_email          = fields.Char( string="Email (Ayah)",  help="")
    ayah_pekerjaan_id   = fields.Many2one(comodel_name="cdn.ref_pekerjaan",  string="Pekerjaan (Ayah)",  help="")
    ayah_pendidikan_id  = fields.Many2one(comodel_name="cdn.ref_pendidikan",  string="Pendidikan (Ayah)",  help="")
    ayah_kantor         = fields.Char( string="Kantor (Ayah)",  help="")
    ayah_penghasilan    = fields.Char( string="Penghasilan (Ayah)",  help="")
    ayah_agama          = fields.Selection(selection=[('islam', 'Islam'), ('katolik', 'Katolik'), ('protestan', 'Protestan'), ('hindu', 'Hindu'), ('budha', 'Budha')],  string="Agama (Ayah)",  help="")
    
    ibu_nama            = fields.Char( string="Nama Ibu",  help="")
    ibu_tmp_lahir       = fields.Char( string="Tmp lahir (Ibu) ",  help="")
    ibu_tgl_lahir       = fields.Date( string="Tgl lahir (Ibu)",  help="")
    ibu_warganegara     = fields.Selection(selection=[('wni','WNI'),('wna','WNA')],  string="Warganegara (Ibu)",  help="")
    ibu_telp            = fields.Char( string="No Telepon (Ibu)",  help="")
    ibu_email           = fields.Char( string="Email (Ibu)",  help="")
    ibu_pekerjaan_id    = fields.Many2one(comodel_name="cdn.ref_pekerjaan",  string="Pekerjaan (Ibu)",  help="")
    ibu_pendidikan_id   = fields.Many2one(comodel_name="cdn.ref_pendidikan",  string="Pendidikan (Ibu)",  help="")
    ibu_kantor          = fields.Char( string="Kantor (Ibu)",  help="")
    ibu_penghasilan     = fields.Char( string="Penghasilan (Ibu)",  help="")
    ibu_agama           = fields.Selection(selection=[('islam', 'Islam'), ('katolik', 'Katolik'), ('protestan', 'Protestan'), ('hindu', 'Hindu'), ('budha', 'Budha')],  string="Agama (Ibu)",  help="")
    
    wali_nama           = fields.Char( string="Nama Wali",  help="")
    wali_tmp_lahir      = fields.Char( string="Tmp lahir (Wali)",  help="")
    wali_tgl_lahir      = fields.Date( string="Tgl lahir (Wali)",  help="")
    wali_telp           = fields.Char( string="No Telepon (Wali)",  help="")
    wali_email          = fields.Char( string="Email (Wali)",  help="")
    wali_agama          = fields.Selection(selection=[('islam', 'Islam'), ('katolik', 'Katolik'), ('protestan', 'Protestan'), ('hindu', 'Hindu'), ('budha', 'Budha')],  string="Agama (Wali)",  help="")
    wali_hubungan       = fields.Char( string="Hubungan dengan Siswa",  help="")
 
    orangtua_id         = fields.Many2one(comodel_name="cdn.orangtua",  string="Orangtua",  help="")
    tahunajaran_id      = fields.Many2one(comodel_name="cdn.ref_tahunajaran",  string="Thn Ajaran",  help="")
    ruang_kelas_id      = fields.Many2one(comodel_name="cdn.ruang_kelas",  string="Ruang Kelas", help="")
    ekstrakulikuler_ids = fields.Many2many("cdn.ekstrakulikuler",string="Ekstrakulikuler")
    
    centang             = fields.Boolean(string="", default=True)

    # jenjang_id_moki          = fields.Many2one(comodel_name='ubig.pendaftaran', string='Sekolah')
    
    
    tingkat             = fields.Many2one(comodel_name="cdn.tingkat",  string="Tingkat", related="ruang_kelas_id.name.tingkat", readonly=True, store=True, help="")


    # @api.model
    # def _get_jenjang_from_ubig(self):
    #     """
    #     Fungsi untuk mendapatkan nilai jenjang dari model ubig.pendidikan
    #     """
    #     # Daftar asli selection
    #     jenjang_list = [
    #         ('paud', 'PAUD'),
    #         ('tk', 'TK/RA'),
    #         ('sd', 'SD/MI'),
    #         ('smp', 'SMP/MTS'),
    #         ('sma', 'SMA/MA/SMK')
    #     ]
        
    #     # Mencari semua data di tabel ubig.pendidikan
    #     ubig_pendidikan = self.env['ubig.pendidikan'].search([])
    #     result = []
        
    #     # Mapping yang menyesuaikan nilai jenjang di cdn.siswa dengan ubig.pendidikan
    #     mapping = {
    #         'paud': 'paud',
    #         'tk': 'tk',
    #         'sd': 'sdmi',
    #         'smp': 'smpmts',
    #         'sma': 'smama',  # Untuk SMA
    #     }
        
    #     # Menambahkan nilai SMK jika diperlukan
    #     # Ada perbedaan antara kedua model, SMK terpisah di ubig.pendidikan
    #     mapping_tambahan = {
    #         'sma': 'smk'  # Untuk SMK
    #     }
        
    #     # Untuk setiap nilai jenjang di daftar asli
    #     for key, label in jenjang_list:
    #         records = []
            
    #         # Cari data di ubig.pendidikan yang cocok dengan jenjang saat ini
    #         if key in mapping:
    #             records = ubig_pendidikan.filtered(lambda r: r.jenjang == mapping[key])
            
    #         # Untuk kasus SMA, kita juga perlu memeriksa SMK
    #         if key == 'sma':
    #             smk_records = ubig_pendidikan.filtered(lambda r: r.jenjang == 'smk')
    #             records += smk_records
            
    #         if records:
    #             # Jika ada data yang cocok, gunakan nama dari ubig.pendidikan
    #             for record in records:
    #                 result.append((key, record.name))
    #         else:
    #             # Jika tidak ada yang cocok, gunakan label asli
    #             result.append((key, label))
        
    #     return result


    # Data Pendaftaran
    tgl_daftar          = fields.Date(string='Tgl Pendaftaran')
    asal_sekolah        = fields.Char(string='Asal Sekolah')
    alamat_asal_sek     = fields.Char(string='Alamat Sekolah Asal')
    telp_asal_sek       = fields.Char(string='No Telp Sekolah Asal')
    kepsek_sekolah_asal = fields.Char(string='Nama Kepala Sekolah')
    status_sekolah_asal = fields.Selection(string='Status Sekolah Asal', selection=[('swasta', 'Swasta'), ('negeri', 'Negeri'),])
    
    prestasi_sebelum    = fields.Char(string='Prestasi Diraih')
    bakat               = fields.Many2many(comodel_name='cdn.ref_bakat', string='Bakat Siswa')
    jalur_pendaftaran   = fields.Many2one(comodel_name='cdn.jalur_pendaftaran', string='Jalur Pendaftaran')
    jurusan_sma         = fields.Many2one(comodel_name='cdn.master_jurusan', string='Bidang/Jurusan')
    
    #Nilai Rata-rata Raport Kelas
    raport_4sd_1 = fields.Float(string='Raport 4 SD Smt 1')
    raport_4sd_2 = fields.Float(string='Raport 4 SD Smt 2')
    raport_5sd_1 = fields.Float(string='Raport 5 SD Smt 1')
    raport_5sd_2 = fields.Float(string='Raport 5 SD Smt 2')
    raport_6sd_1 = fields.Float(string='Raport 4 SD Smt 1')
    baca_quran   = fields.Selection(string="Baca Qur'an", selection=[('belumbisa', 'Belum Bisa'), ('kuranglancar', 'Kurang Lancar'),('lancar','Lancar'),('tartil','Tartil')])
    

    bebasbiaya          = fields.Boolean(string='Bebas Biaya', default=False)
    harga_komponen      = fields.One2many(comodel_name='cdn.harga_khusus', inverse_name='siswa_id', string='Harga Khusus')
    penetapan_tagihan_id = fields.Many2one('cdn.penetapan_tagihan', string='penetapan_tagihan_id')
    nomor_pendaftaran   = fields.Char(string="Nomor Pendfataran")
    tanggal_daftar      = fields.Date(string="Tanggal Daftar")
    barcode_santri      = fields.Char(string='Kartu Santri')    
    
    # @api.model
    # def create(self, vals):
    #     if not vals.get('barcode_santri'):
    #         vals['barcode_santri'] = self._generate_unique_barcode()
        
    #     record = super(siswa, self).create(vals)
        
    #     if record.barcode_santri:
    #         record.partner_id.barcode = record.barcode_santri
        
    #     return record
    
    # def _generate_unique_barcode(self):
    #     """Generate a random numeric barcode (10 digits)."""
    #     return f"{random.randint(1000000000000000, 9999999999999999)}"

    # _sql_constraints = [('nis_uniq', 'unique(nis)', 'Data NIS tersebut sudah pernah terdaftar, pastikan NIS harus unik !'),
    #                     ('nisn_uniq', 'unique(nisn)', 'Data NISN tersebut sudah pernah terdaftar, pastikan NISN harus unik !'),
    #                     ('nik_uniq', 'unique(nik)', 'Data NIK tersebut sudah pernah terdaftar, pastikan NIK harus unik !')]
    _sql_constraints = [('nik_uniq', 'unique(nik)', 'Data NIK tersebut sudah pernah terdaftar, pastikan NIK harus unik !')]
    
    # @api.model
    # def create(self, vals):
    #     # Update barcode_santri in res.partner before creation
    #     if 'barcode_santri' in vals:
    #         partner = self.env['res.partner'].browse(vals['partner_id'])
    #         partner.write({'barcode_santri': vals['barcode_santri']})
    #     return super(siswa, self).create(vals)
    
    

    def write(self, vals):
        # Update barcode_santri in res.partner on record update
        if 'barcode_santri' in vals:
            for record in self:
                record.partner_id.write({'barcode_santri': vals['barcode_santri']})
        return super(siswa, self).write(vals)
    
    @api.model
    def default_get(self, fields):
       res = super(siswa,self).default_get(fields)
       res['jns_partner'] = 'siswa'
       return res

    def _get_saldo_tagihan(self):
        saldo_invoice       = self.env['account.move'].search([('partner_id','=',self.partner_id.id),('state','=','posted')])
        self.saldo_tagihan  = sum(item.amount_residual for item in saldo_invoice)

    saldo_tagihan           = fields.Float('Saldo Tagihan', compute='_get_saldo_tagihan')

    def open_tagihan(self):
        # return {
        #     'name'          : _('Tagihan'),
        #     'domain'        : [('partner_id','=',self.partner_id.id),('state','=','posted'),('move_type','=','out_invoice')],
        #     # 'view_type' : 'form',
        #     'res_model'     : 'account.move',
        #     'view_id'       : False,
        #     'view_mode'     : 'list,form',
        #     'context': "{'default_move_type': 'out_invoice'}",
        #     'type'          :'ir.actions.act_window'
        # }
        action = self.env.ref('action_tagihan_inherit_view').read()[0]
        action['domain'] = [('partner_id','=',self.partner_id.id),('state','=','posted'),('move_type','=','out_invoice')]
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
        if not self.nomor_pendaftaran or not self.tanggal_daftar:
            _logger.warning("NIS tidak bisa dibuat: Tanggal pendaftaran atau jenjang kosong.")
            return False

        # Mapping Kode Lembaga
        lembaga = {
            'paud': '01', 'tk': '02', 'sdmi': '03',
            'smpmts': '04', 'smama': '05', 'smk': '10', 'nonformal': '06',
        }.get(self.jenjang, '00')  # Default '00' jika tidak cocok

        # Konversi Tahun Daftar
        try:
            tahun_daftar = self.tanggal_daftar.strftime('%Y')[-2:]
        except AttributeError:
            tahun_daftar = '00'
 
        # Gunakan nomor_pendaftaran sebagai bagian dari NIS
        nomor = self.nomor_pendaftaran if self.nomor_pendaftaran and self.nomor_pendaftaran.isdigit() else "000"

        # Format NIS
        nis = f"{lembaga}.{tahun_daftar}.{nomor}"
        _logger.info(f"NIS yang dihasilkan: {nis}")  
        self.nis = nis
        # return nis

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
            # 'context': {'default_id': self.id}
        }
        # wizard_model = self.env['wizard.register.kartu']
        # return wizard_model.action_register()



    # def name_get(self):
    #     """
    #     Kustomisasi tampilan nama untuk menampilkan nama dan NIS
    #     """
    #     result = []
    #     for record in self:
    #         # Gabungkan nama dan NIS dalam satu tampilan
    #         name = f"{record.name} - {record.nis}"
    #         result.append((record.id, name))
    #     return result

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
