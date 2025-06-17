from odoo import api, fields, models
from datetime import date, datetime


class AbsensiEkskul(models.Model):
    _name               = 'cdn.absensi_ekskul'
    _inherit            = ['mail.thread', 'mail.activity.mixin']
    _description        = 'Data Absensi Ekskul'

    def _get_domain_guru(self):
        user = self.env.user
        if user.has_group('pesantren_guru.group_guru_manager'):
            return [('user_id', '=', self.env.user.id), ('jns_pegawai', '=', 'guru')]
        elif user.has_group('pesantren_guru.group_guru_staff'):
            user = self.env['hr.employee'].search([('user_id', '=', user.id)])
            return [('user_id', '=', self.env.user.id), ('jns_pegawai', '=', 'guru')]
        return [('id', '=', False)]
    
    def _get_default_guru(self):
        user = self.env.user
        if user.has_group('pesantren_guru.group_guru_staff'):
            user = self.env['hr.employee'].search([('user_id', '=', user.id)])  
            return user.id
        return False

    def _get_domain_ekskul(self):
        user = self.env.user
        return [
            ('penanggung_id', '=', user.name),
        ]

    search          = fields.Char(string="Ya Hooo")

    name            = fields.Date(string='Tgl Absen', required=True, default=fields.Date.context_today)
    fiscalyear_id   = fields.Many2one('cdn.ref_tahunajaran', string='Tahun Ajaran', readonly=True, default=lambda self:self.env.user.company_id.tahun_ajaran_aktif.id)
    guru            = fields.Many2one('hr.employee', string="Guru", required=True, 
                      domain=_get_domain_guru, default=_get_default_guru)
    ekskul_id       = fields.Many2one('cdn.pembagian_ekstra', required=True, domain=_get_domain_ekskul)
    absen_ids       = fields.One2many('cdn.absen_ekskul_line', 'absen_id', string='Daftar Absensi')
    states          = fields.Selection([
                        ('Proses', 'Proses'),
                        ('Done','Selesai'),
                    ], default='Proses', string='Status')
    
    @api.onchange('ekskul_id')
    def _onchange_ekskul_id(self):
        self.absen_ids = [(5, 0, 0)] 
        if self.ekskul_id:
            absen_list = []
            for siswa in self.ekskul_id.siswa_ids:
                absen_list.append((0, 0, {
                    'siswa_id': siswa.id,
                    'kehadiran': 'Hadir',
                }))
            self.absen_ids = absen_list
        
    def action_proses(self):
        self.states = 'Proses'
        
    def action_done(self):
        self.states = 'Done'
        
    # def _get_absen_line_context(self):
    #     return {'state_not_draft': self.states != 'Draft'}


class AbsenEkskulLine(models.Model):
    _name = 'cdn.absen_ekskul_line'
    _description = 'Tabel Absen Ekskul Line'

    absen_id = fields.Many2one('cdn.absensi_ekskul', string='Absen', ondelete='cascade')
    tanggal = fields.Date(string='Tgl Absen', related='absen_id.name', readonly=True, store=True)
    siswa_id = fields.Many2one('cdn.siswa', string='Siswa', ondelete='cascade', domain="[('id', 'in', allowed_siswa_ids)]")
    allowed_siswa_ids = fields.Many2many(
        comodel_name='cdn.siswa', 
        compute='_compute_allowed_siswa', 
        store=False
    )


    name = fields.Char(string='Nama', related='siswa_id.name', readonly=True, store=True)
    nis = fields.Char(string='NIS', related='siswa_id.nis', readonly=True, store=True)
    panggilan = fields.Char(string='Nama Panggilan', related='siswa_id.namapanggilan', readonly=True, store=True)
    keterangan_izin = fields.Binary(string='Foto', attachment=True, store=True)
    kehadiran = fields.Selection([
        ('Hadir', 'Hadir'),
        ('Izin', 'Izin'),
        ('keluar', 'Izin Keluar'),
        ('Sakit', 'Sakit'),
        ('Alpa', 'Alpa'),
    ], string='Kehadiran', required=True, default='Hadir')
    keterangan = fields.Char(string="Keterangan")
    guru = fields.Many2one('hr.employee',string="Guru", related='absen_id.guru')
    ekskul = fields.Many2one('cdn.pembagian_ekstra', related='absen_id.ekskul_id')
    
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


    @api.depends('absen_id.ekskul_id')
    def _compute_allowed_siswa(self):
        for record in self:
            if record.absen_id.ekskul_id:
                record.allowed_siswa_ids = record.absen_id.ekskul_id.siswa_ids.ids

                # Pengecekan perijinan untuk update kehadiran dan keterangan
                if record.siswa_id and record.tanggal:
                    permission = self.env['cdn.perijinan'].search([
                        ('siswa_id', '=', record.siswa_id.id),
                        ('state', '=', 'Permission')
                    ], limit=1)

                    if permission:
                        record.kehadiran = 'keluar'  # atau 'keluar' jika Anda menggunakan nilai itu
                        tanggal_str = record.tanggal.strftime('%d-%m-%Y') if record.tanggal else ''
                        keperluan_name = permission.keperluan.name if permission.keperluan else 'Tidak ada keterangan'
                        waktu_keluar = self.format_datetime_indonesia(permission.waktu_keluar) if permission.waktu_keluar else 'Tidak tercatat'
                        waktu_kembali = permission.waktu_kembali.strftime('%d-%m-%Y %H:%M') if permission.waktu_kembali else 'Belum kembali'

                        record.keterangan = f"Santri Keluar pada {waktu_keluar}, karena {keperluan_name}".encode()
            else:
                record.allowed_siswa_ids = []


    @api.onchange('siswa_id')
    def _onchange_siswa_id(self):
        """Check permission when student is selected"""
        if self.siswa_id and self.tanggal:
            permission = self.env['cdn.perijinan'].search([
                ('siswa_id', '=', self.siswa_id.id),
                ('state', '=', 'Permission')
            ], limit=1)
            
            if permission:
                self.kehadiran = 'keluar'
                
                # Format keterangan
                tanggal_str = self.tanggal.strftime('%d-%m-%Y') if self.tanggal else ''
                keperluan_name = permission.keperluan.name if permission.keperluan else 'Tidak ada keterangan'
                waktu_keluar = self.format_datetime_indonesia(permission.waktu_keluar) if permission.waktu_keluar else 'Tidak tercatat'

                waktu_kembali = permission.waktu_kembali.strftime('%d-%m-%Y %H:%M') if permission.waktu_kembali else 'Belum kembali'
                
                self.keterangan = f"Santri Keluar pada {waktu_keluar}, karena {keperluan_name}"
            else:
                self.kehadiran = 'Hadir'
                self.keterangan = False


    # @api.depends('absen_id.ekskul_id')
    # def _compute_allowed_siswa(self):
    #     for record in self:
    #         record.allowed_siswa_ids = record.absen_id.ekskul_id.siswa_ids.ids if record.absen_id.ekskul_id else []