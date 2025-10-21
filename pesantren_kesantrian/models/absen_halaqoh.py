from odoo import api, fields, models
from datetime import date, datetime

class Absenhalaqoh(models.Model):
    _name           = 'cdn.absen_halaqoh'
    _description    = 'Tabel Halaqoh'

    #get domain 
    # def _domain_halaqoh_id(self):
    #     tahun_ajaran = self.env.user.company_id.tahun_ajaran_aktif.id
    #     user = self.env.user

    #     # Jika user adalah Manager Kesantrian -> lihat semua halaqoh di tahun ajaran aktif
    #     if self.env.user.has_group('pesantren_kesantrian.group_kesantrian_manager,pesantren_guruquran.group_guru_quran_staff'):
    #         return [
    #             ('fiscalyear_id', '=', tahun_ajaran)
    #         ]
    # # # Cari employee dari user
    # #     employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)

    # #     if employee:
    # #         # Guru Qur’an: hanya halaqoh yang dia pegang atau dia jadi pengganti
    # #         return [
    # #             ('fiscalyear_id', '=', tahun_ajaran),
    # #             '|',
    # #             ('penanggung_jawab_id', '=', employee.id),
    # #             ('pengganti_ids', 'in', [employee.id])
    # #         ]

    #     # Jika user bukan guru dan tidak punya employee
    #     return [('id', '=', 0)]
    
    def _domain_halaqoh_id(self):
        """Mengembalikan domain untuk field halaqoh_id berdasarkan tahun ajaran aktif."""
        tahun_ajaran = self.env.user.company_id.tahun_ajaran_aktif.id
        return [('fiscalyear_id', '=', tahun_ajaran)]

    def _get_domain_guru(self):
        return [
            ('jns_pegawai', 'in', ['guruquran','guru,guruquran', 'musyrif,guruquran', 'musyrif,guru,guruquran'])
        ]

    # def _get_default_guru(self):
    #     user = self.env.user
    #     if user.has_group('pesantren_guru.group_guru_staff'):
    #         employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
    #         if employee:
    #             return employee.id
    #     return False
    
    def _get_default_guru(self):
        user = self.env.user
        employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        return employee.id if employee else False

    name            = fields.Date(string='Tgl Absen', required=True, default=fields.Date.context_today, states={'Done': [('readonly', True)]})
    halaqoh_id      = fields.Many2one('cdn.halaqoh', string='Halaqoh', required=True, domain=_domain_halaqoh_id, states={'Done': [('readonly', True)]})
    # ustadz_id       = fields.Many2one('hr.employee', string='Ustadz',domain=_get_domain_guru, default=_get_default_guru ,required=True, states={'Done': [('readonly', True)]})
    ustadz_id = fields.Many2one(
        'hr.employee',
        string='Ustadz',
        domain=_get_domain_guru,
        default=_get_default_guru,
        required=True,
        states={'Done': [('readonly', True)]}
    )
    fiscalyear_id   = fields.Many2one('cdn.ref_tahunajaran', string='Tahun Ajaran', readonly=True, default=lambda self:self.env.user.company_id.tahun_ajaran_aktif.id, states={'Done': [('readonly', True)]})
    absen_ids       = fields.One2many('cdn.absen_halaqoh_line', 'absen_id', string='Absen', states={'Done': [('readonly', True)]})
    state           = fields.Selection([
        ('Draft', 'Draft'),
        ('Proses', 'Proses'),
        ('Done','Selesai'),
    ], default='Draft', string='Status')
    penanggung_jawab_id = fields.Many2one('hr.employee', string='Penanggung Jawab', related='halaqoh_id.penanggung_jawab_id', readonly=True, store=True)
    sesi_id         = fields.Many2one('cdn.sesi_halaqoh', string='Sesi', states={'Done': [('readonly', True)]})
    keterangan      = fields.Char(string='Keterangan')
    row_number      = fields.Integer(string='No', compute='_compute_row_number', store=False)

    def _compute_row_number(self):
        for index, record in enumerate(self):
            record.row_number = index + 1
    def action_proses(self):
        self.state = 'Proses'
        for absen in self.absen_ids:
            if absen.kehadiran == 'Hadir':
                halaqoh_vals = {
                    'tanggal': self.name,
                    'siswa_id': absen.siswa_id.id,
                    'halaqoh_id': self.halaqoh_id.id,
                    'ustadz_id': self.ustadz_id.id,
                    'sesi_id': self.sesi_id.id,
                    'state': 'draft',
                }
                self.env['cdn.penilaian_quran'].create(halaqoh_vals)

    def action_confirm(self):
        self.state = 'Done'
        
    def action_sync_penilaian(self):
        Penilaian = self.env['cdn.penilaian_quran']

        for record in self:
            for line in record.absen_ids.filtered(lambda l: l.kehadiran == 'Hadir'):
                # Cek apakah sudah ada penilaian dengan kombinasi yang sama
                existing = Penilaian.search([
                    ('tanggal', '=', record.name),
                    ('siswa_id', '=', line.siswa_id.id),
                    ('halaqoh_id', '=', record.halaqoh_id.id),
                    ('sesi_id', '=', record.sesi_id.id),
                ], limit=1)

                if not existing:
                    Penilaian.create({
                        'tanggal': record.name,
                        'siswa_id': line.siswa_id.id,
                        'halaqoh_id': record.halaqoh_id.id,
                        'ustadz_id': record.ustadz_id.id,
                        'sesi_id': record.sesi_id.id,
                        'state': 'draft',
                    })


    @staticmethod
    def format_datetime_indonesia(dt):
        bulan_dict = {
            '01': 'Januari', '02': 'Februari', '03': 'Maret', '04': 'April',
            '05': 'Mei', '06': 'Juni', '07': 'Juli', '08': 'Agustus',
            '09': 'September', '10': 'Oktober', '11': 'November', '12': 'Desember'
        }
        if dt:
            hari = dt.strftime('%d')
            bulan_angka = dt.strftime('%m')
            tahun = dt.strftime('%Y')
            jam_menit = dt.strftime('%H:%M')
            nama_bulan = bulan_dict.get(bulan_angka, bulan_angka)
            return f"{hari} {nama_bulan} {tahun} {jam_menit}"
        return 'Tidak tercatat'    

    # @api.onchange('halaqoh_id')
    # def _onchange_halaqoh_id(self):
    #     halaqoh = self.halaqoh_id
    #     if halaqoh:
    #         absen_ids = [(5, 0, 0)] 
    #         for siswa in halaqoh.siswa_ids:

    #             permission = self.env['cdn.perijinan'].search([
    #                 ('siswa_id', '=', siswa.id),
    #                 ('state', '=', 'Permission')
    #             ], limit=1)

    #             if permission:
    #                 keperluan_name = permission.keperluan.name if permission.keperluan else 'Tidak ada keterangan'
    #                 waktu_keluar = self.format_datetime_indonesia(permission.waktu_keluar) if permission.waktu_keluar else 'Tidak tercatat'
    #                 message = f"Santri Keluar pada {waktu_keluar}, karena {keperluan_name}".encode()

    #                 absen_ids.append((0,0, {
    #                     'siswa_id': siswa.id,
    #                     'kehadiran' : 'keluar',
    #                     'keterangan': message,
    #                 }))

    #             else:
    #                 absen_ids.append((0, 0, {
    #                     'siswa_id': siswa.id,
    #                     'kehadiran': 'Hadir'
    #                 }))
        
    #         ustadz = halaqoh.penanggung_jawab_id | halaqoh.pengganti_ids
            
    #         if not self.env.user.has_group('pesantren_kesantrian.group_kesantrian_manager'):
    #             ustadz = ustadz.filtered(lambda x: x.user_id == self.env.user)
            
    #         return {
    #             'domain': {
    #                 'ustadz_id': [('id', 'in', ustadz.ids)]
    #             },
    #             'value': {
    #                 'absen_ids': absen_ids,
    #                 'ustadz_id': ustadz[0].id if ustadz else False
    #             }
    #         }
    @api.onchange('halaqoh_id')
    def _onchange_halaqoh_id(self):
        """Mengisi absen_ids dan mengatur ustadz_id ke pengguna yang login untuk staff."""
        halaqoh = self.halaqoh_id
        if halaqoh:
            absen_ids = [(5, 0, 0)]
            for siswa in halaqoh.siswa_ids:
                permission = self.env['cdn.perijinan'].search([
                    ('siswa_id', '=', siswa.id),
                    ('state', '=', 'Permission')
                ], limit=1)
                if permission:
                    keperluan_name = permission.keperluan.name if permission.keperluan else 'Tidak ada keterangan'
                    waktu_keluar = self.format_datetime_indonesia(permission.waktu_keluar) if permission.waktu_keluar else 'Tidak tercatat'
                    message = f"Santri Keluar pada {waktu_keluar}, karena {keperluan_name}"
                    absen_ids.append((0, 0, {
                        'siswa_id': siswa.id,
                        'kehadiran': 'keluar',
                        'keterangan': message,
                    }))
                else:
                    absen_ids.append((0, 0, {
                        'siswa_id': siswa.id,
                        'kehadiran': 'Hadir'
                    }))
            user = self.env.user
            employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
            ustadz_id = employee.id if employee else False
            if self.env.user.has_group('pesantren_kesantrian.group_kesantrian_manager'):
                ustadz = halaqoh.penanggung_jawab_id | halaqoh.pengganti_ids
                return {
                    'domain': {
                        'ustadz_id': [('id', 'in', ustadz.ids)]
                    },
                    'value': {
                        'absen_ids': absen_ids,
                        'ustadz_id': ustadz[0].id if ustadz else False
                    }
                }
            return {
                'domain': {
                    'ustadz_id': [('id', '=', ustadz_id)] if ustadz_id else [('id', '=', False)]
                },
                'value': {
                    'absen_ids': absen_ids,
                    'ustadz_id': ustadz_id
                }
            }
    
    # @api.model
    # def default_get(self, fields_tree):
    #     tahun_ajaran = self.env['res.company'].search([('id', '=', self.env.ref('base.main_company').id)]).tahun_ajaran_aktif.id
    #     if not tahun_ajaran:
    #         raise models.ValidationError('Tahun ajaran belum di set')
    #     return super().default_get(fields_tree)
    @api.model
    def default_get(self, fields_list):
        """Memastikan tahun ajaran aktif diset."""
        res = super().default_get(fields_list)
        tahun_ajaran = self.env['res.company'].search([('id', '=', self.env.ref('base.main_company').id)]).tahun_ajaran_aktif.id
        if not tahun_ajaran:
            raise ValidationError('Tahun ajaran belum di set')
        return res
    
    @api.model
    def create(self, vals):
        """Membuat absensi tanpa batasan ustadz_id untuk staff."""
        return super().create(vals)
    
    
class AbsenTahsinQuranLine(models.Model):
    _name = 'cdn.absen_halaqoh_line'
    _description = 'Tabel Absen Halaqoh Line'

    absen_id = fields.Many2one('cdn.absen_halaqoh', string='Absen', ondelete='cascade')
    tanggal = fields.Date(string='Tgl Absen', related='absen_id.name', readonly=True, store=True)
    halaqoh_id = fields.Many2one('cdn.halaqoh', string='Halaqoh', related='absen_id.halaqoh_id', readonly=True, store=True)
    siswa_id = fields.Many2one('cdn.siswa', string='Siswa', ondelete='cascade')
    name = fields.Char(string='Nama', related='siswa_id.name', readonly=True, store=True)
    nis = fields.Char(string='NIS', related='siswa_id.nis', readonly=True, store=True)
    panggilan = fields.Char(string='Nama Panggilan', related='siswa_id.namapanggilan', readonly=True, store=True)
    keterangan = fields.Char(string='Keterangan')
    keterangan_izin = fields.Char(string='Foto', store=True)
    kehadiran = fields.Selection([
        ('Hadir', 'Hadir'),
        ('Izin', 'Izin'),
        ('keluar', 'Izin Keluar'),
        ('Sakit', 'Sakit'),
        ('Alpa', 'Alpa'),
    ], string='Kehadiran', required=True)
    penanggung_jawab_id = fields.Many2one('hr.employee', string='Penanggung Jawab', related='halaqoh_id.penanggung_jawab_id', readonly=True, store=True)
    row_number      = fields.Integer(string='No', compute='_compute_row_number', store=False)
    ustadz_id = fields.Many2one(
        'hr.employee',
        string='Ustadz',
        related='absen_id.ustadz_id',
        readonly=True,
        store=True
    )

    def _compute_row_number(self):
        for index, record in enumerate(self):
            record.row_number = index + 1
    def action_view_permission(self):
        """Open permission form for this student"""
        if not self.siswa_id or not self.tanggal:
            return
            
        permission = self.env['cdn.perijinan'].search([
            ('siswa_id', '=', self.siswa_id.id),
            ('state', '=', 'Permission')
        ], limit=1)
        
        if not permission:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title' : '❌ Tidak Dapat Menemukan Data !',
                    'message': 'Data perizinan tidak ditemukan, mungkin santri telah kembali.',
                    'type': 'danger',
                    'sticky': False,
                }
            }
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Detail Perijinan',
            'res_model': 'cdn.perijinan',
            'res_id': permission.id,
            'view_mode': 'form',
            'target': 'current',
        }

