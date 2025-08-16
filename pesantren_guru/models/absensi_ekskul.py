from odoo import api, fields, models


class AbsensiEkskul(models.Model):
    _name = 'cdn.absensi_ekskul'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Data Absensi Ekstrakurikuler'

    # Default & Domain Helper
    def _get_default_guru(self):
        user = self.env.user
        if user.has_group('pesantren_guru.group_guru_staff') or user.has_group('pesantren_guru.group_guru_manager'):
            employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
            return employee.id if employee else False
        return False

    def _get_domain_ekskul(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return [('penanggung_id', '=', employee.id)] if employee else [('id', '=', False)]

    # Fields
    search = fields.Char(string="Pencarian")

    name = fields.Date(
        string='Tanggal Absen',
        required=True,
        default=fields.Date.context_today
    )
    fiscalyear_id = fields.Many2one(
        'cdn.ref_tahunajaran',
        string='Tahun Ajaran',
        readonly=True,
        default=lambda self: self.env.user.company_id.tahun_ajaran_aktif.id
    )
    guru = fields.Many2one(
        'hr.employee',
        string="Guru Pengampu",
        required=True,
        default=_get_default_guru,
        compute='_compute_guru',
        readonly=True,
        store=True
    )

    @api.depends('ekskul_id')
    def _compute_guru(self):
        for record in self:
            if record.ekskul_id and record.ekskul_id.penanggung_id:
                record.guru = record.ekskul_id.penanggung_id.id
            else:
                record.guru = False
                
        
    penanggung_id = fields.Many2one(
        "hr.employee",
        string="Penanggung Jawab",
        readonly=True,
        help="Penanggung jawab ekskul, diisi otomatis dari ekskul"
    )
    ekskul_id = fields.Many2one(
        'cdn.pembagian_ekstra',
        string="Ekstrakurikuler",
        required=True,
        domain=lambda self: self._get_domain_ekskul()
    )
    absen_ids = fields.One2many(
        'cdn.absen_ekskul_line',
        'absen_id',
        string='Daftar Absensi'
    )
    states = fields.Selection([
        ('Proses', 'Proses'),
        ('Done', 'Selesai'),
    ], default='Proses', string='Status', tracking=True)

    # Onchange: Filter ekskul berdasarkan guru
    @api.onchange('guru')
    def _onchange_guru(self):
        if self.guru:
            return {
                'domain': {
                    'ekskul_id': [('penanggung_id', '=', self.guru.id)]
                }
            }
        else:
            return {
                'domain': {
                    'ekskul_id': []
                }
            }

    # Onchange: Saat ekskul dipilih, isi siswa & sinkronkan guru/penanggung
    @api.onchange('ekskul_id')
    def _onchange_ekskul_id(self):
        # Hapus semua baris absensi lama
        self.absen_ids = [(5, 0, 0)]

        if self.ekskul_id:
            # Isi penanggung jawab dan pastikan guru terisi
            self.penanggung_id = self.ekskul_id.penanggung_id.id
            if not self.guru:
                self.guru = self.ekskul_id.penanggung_id.id

            # Isi daftar siswa ekskul
            absen_list = []
            for siswa in self.ekskul_id.siswa_ids:
                absen_list.append((0, 0, {
                    'siswa_id': siswa.id,
                    'kehadiran': 'Hadir',
                }))
            self.absen_ids = absen_list

    # Button Actions
    def action_proses(self):
        self.states = 'Proses'

    def action_done(self):
        self.states = 'Done'

    # Opsional: Cegah edit jika sudah Done
    def write(self, vals):
        for rec in self:
            if rec.states == 'Done' and any(field in vals for field in ['ekskul_id', 'absen_ids']):
                raise models.UserError("Tidak dapat mengubah absensi yang sudah Selesai.")
        return super(AbsensiEkskul, self).write(vals)


class AbsenEkskulLine(models.Model):
    _name = 'cdn.absen_ekskul_line'
    _description = 'Baris Absensi Ekstrakurikuler'

    absen_id = fields.Many2one('cdn.absensi_ekskul', string='Absen', ondelete='cascade')
    tanggal = fields.Date(string='Tanggal', related='absen_id.name', readonly=True, store=True)
    siswa_id = fields.Many2one(
        'cdn.siswa',
        string='Siswa',
        ondelete='cascade',
        domain="[('id', 'in', allowed_siswa_ids)]"
    )
    allowed_siswa_ids = fields.Many2many(
        'cdn.siswa',
        compute='_compute_allowed_siswa',
        string='Siswa yang Diizinkan'
    )
    name = fields.Char(string='Nama', related='siswa_id.name', readonly=True, store=True)
    nis = fields.Char(string='NIS', related='siswa_id.nis', readonly=True, store=True)
    panggilan = fields.Char(string='Nama Panggilan', related='siswa_id.namapanggilan', readonly=True, store=True)
    keterangan_izin = fields.Binary(string='Foto Bukti', attachment=True)
    kehadiran = fields.Selection([
        ('Hadir', 'Hadir'),
        ('Izin', 'Izin'),
        ('keluar', 'Izin Keluar'),
        ('Sakit', 'Sakit'),
        ('Alpa', 'Alpa'),
    ], string='Kehadiran', required=True, default='Hadir')
    keterangan = fields.Char(string="Keterangan")
    guru = fields.Many2one('hr.employee', string="Guru", related='absen_id.guru')
    ekskul = fields.Many2one('cdn.pembagian_ekstra', string="Ekskul", related='absen_id.ekskul_id')

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
        """Buka form perijinan aktif siswa"""
        self.ensure_one()
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
                    'title': '❌ Tidak Ditemukan',
                    'message': 'Santri tidak dalam status izin keluar.',
                    'type': 'warning',
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
                # Ambil siswa dari ekskul
                siswa_ids = record.absen_id.ekskul_id.siswa_ids.ids
                record.allowed_siswa_ids = [(6, 0, siswa_ids)]

                # Cek perijinan aktif
                if record.siswa_id:
                    permission = self.env['cdn.perijinan'].search([
                        ('siswa_id', '=', record.siswa_id.id),
                        ('state', '=', 'Permission')
                    ], limit=1)
                    if permission:
                        record.kehadiran = 'keluar'
                        keperluan = permission.keperluan.name or 'Tidak ada keterangan'
                        waktu_keluar = self.format_datetime_indonesia(permission.waktu_keluar)
                        record.keterangan = f"Santri Keluar pada {waktu_keluar}, karena {keperluan}"
                    else:
                        record.keterangan = False
            else:
                record.allowed_siswa_ids = [(5,)]

    @api.onchange('siswa_id')
    def _onchange_siswa_id(self):
        """Cek perijinan saat siswa dipilih"""
        if self.siswa_id:
            permission = self.env['cdn.perijinan'].search([
                ('siswa_id', '=', self.siswa_id.id),
                ('state', '=', 'Permission')
            ], limit=1)
            if permission:
                self.kehadiran = 'keluar'
                keperluan = permission.keperluan.name or 'Tidak ada keterangan'
                waktu_keluar = self.format_datetime_indonesia(permission.waktu_keluar)
                self.keterangan = f"Santri Keluar pada {waktu_keluar}, karena {keperluan}"
            else:
                self.kehadiran = 'Hadir'
                self.keterangan = False