from odoo import api, fields, models
from datetime import date, datetime
from odoo.exceptions import UserError


class Absenhalaqoh(models.Model):
    _name = 'cdn.absen_halaqoh'
    _description = 'Tabel Halaqoh'

    def _domain_halaqoh_id(self):
        """Mengembalikan domain untuk field halaqoh_id berdasarkan tahun ajaran aktif.

        Menampilkan seluruh halaqoh pada tahun ajaran aktif agar guru utama
        maupun guru pengganti dapat memilih halaqoh yang sesuai.
        """
        tahun_ajaran = self.env.company.tahun_ajaran_aktif.id or self.env.user.company_id.tahun_ajaran_aktif.id
        return [('fiscalyear_id', '=', tahun_ajaran)]

    def _get_domain_guru(self):
        admin_user_ids = self.env.ref('base.group_system').users.ids

        return [
            '|',
            ('user_id', '=', admin_user_ids),
            ('jns_pegawai_ids.code', 'in', ['guruquran', 'superadmin'])
        ]

    def _get_default_guru(self):
        user = self.env.user
        employee = self.env['hr.employee'].search(
            [('user_id', '=', user.id)], limit=1)
        return employee.id if employee else False

    name = fields.Date(string='Tgl Absen', required=True,
                       default=fields.Date.context_today, states={'Done': [('readonly', True)]})
    halaqoh_id = fields.Many2one('cdn.halaqoh', string='Halaqoh', required=True,
                                 domain=_domain_halaqoh_id, ondelete='cascade', states={'Done': [('readonly', True)]})
    ustadz_id = fields.Many2one(
        'hr.employee',
        string='Ustadz',
        domain=lambda self: self.env['cdn.absen_halaqoh']._get_domain_guru(),
        default=_get_default_guru,
        required=True,
        states={'Done': [('readonly', True)]}
    )
    fiscalyear_id = fields.Many2one('cdn.ref_tahunajaran', string='Tahun Ajaran', readonly=True,
                                    default=lambda self: self.env.user.company_id.tahun_ajaran_aktif.id, states={'Done': [('readonly', True)]})
    absen_ids = fields.One2many('cdn.absen_halaqoh_line', 'absen_id', string='Absen', states={
                                'Done': [('readonly', True)]})
    state = fields.Selection([
        ('Draft', 'Draft'),
        ('Done', 'Selesai'),
    ], default='Draft', string='Status')
    penanggung_jawab_id = fields.Many2one(
        'hr.employee', string='Penanggung Jawab', related='halaqoh_id.penanggung_jawab_id', readonly=True, store=True)
    sesi_id = fields.Many2one('cdn.sesi_halaqoh', string='Sesi', states={
                              'Done': [('readonly', True)]})
    keterangan = fields.Char(string='Keterangan')
    is_guru_pengganti = fields.Boolean(
        string='Guru Pengganti',
        default=False,
        help='Centang kotak disamping jika anda sebagai guru pengganti'
    )
    row_number = fields.Integer(
        string='No', compute='_compute_row_number', store=False)
    company_id = fields.Many2one(
        'res.company', string='Lembaga', default=lambda self: self.env.company)

    def _compute_row_number(self):
        for index, record in enumerate(self):
            record.row_number = index + 1

    def _sync_penilaian_records(self):
        """Metode presisi untuk menyelaraskan data penilaian halaqoh dengan absensi:
        1. Membuat cdn.penilaian_quran baru untuk santri yang berstatus 'Hadir' (jika belum ada).
        2. Membersihkan cdn.penilaian_quran 'draft' yang masih kosong jika santri diubah menjadi selain 'Hadir'.
        """
        Penilaian = self.env['cdn.penilaian_quran'].with_context(from_guru_quran=True)
        for record in self:
            if not record.name or not record.halaqoh_id:
                continue

            # 1. Proses santri yang HADIR (case-insensitive check)
            hadir_lines = record.absen_ids.filtered(lambda l: (l.kehadiran or '').strip().lower() == 'hadir')
            for line in hadir_lines:
                existing = Penilaian.search([
                    ('tanggal', '=', record.name),
                    ('siswa_id', '=', line.siswa_id.id),
                    ('halaqoh_id', '=', record.halaqoh_id.id),
                ], limit=1)
                if not existing:
                    Penilaian.create({
                        'tanggal': record.name,
                        'siswa_id': line.siswa_id.id,
                        'halaqoh_id': record.halaqoh_id.id,
                        'ustadz_id': record.ustadz_id.id if record.ustadz_id else False,
                        'sesi_id': record.sesi_id.id if record.sesi_id else False,
                        'state': 'draft',
                        'company_id': record.company_id.id if record.company_id else False,
                    })
                else:
                    vals_to_update = {}
                    if record.ustadz_id and existing.ustadz_id != record.ustadz_id:
                        vals_to_update['ustadz_id'] = record.ustadz_id.id
                    if record.sesi_id and existing.sesi_id != record.sesi_id:
                        vals_to_update['sesi_id'] = record.sesi_id.id
                    if record.company_id and existing.company_id != record.company_id:
                        vals_to_update['company_id'] = record.company_id.id
                    if vals_to_update:
                        vals_to_update['state'] = existing.state
                        existing.with_context(from_guru_quran=True).write(vals_to_update)

            # 2. Proses santri yang TIDAK HADIR (Izin, Sakit, Alpa, Pulang, dll)
            non_hadir_siswa_ids = record.absen_ids.filtered(
                lambda l: (l.kehadiran or '').strip().lower() != 'hadir'
            ).mapped('siswa_id').ids
            if non_hadir_siswa_ids:
                orphan_penilaians = Penilaian.search([
                    ('tanggal', '=', record.name),
                    ('siswa_id', 'in', non_hadir_siswa_ids),
                    ('halaqoh_id', '=', record.halaqoh_id.id),
                    ('state', '=', 'draft'),
                ])
                for pen in orphan_penilaians:
                    is_empty = (
                        not pen.tahfidz_line_ids and
                        not pen.buku_harian_id and
                        not pen.buku_ujian_id and
                        not pen.juz_murajaah and
                        not pen.surah_id_ujian_tahfidz
                    )
                    if is_empty:
                        pen.unlink()

    def action_proses(self):
        self.state = 'Done'
        self._sync_penilaian_records()

    def action_confirm(self):
        self.state = 'Done'

    def action_draft(self):
        self.state = 'Draft'

    def action_sync_penilaian(self):
        self._sync_penilaian_records()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '✅ Sinkronisasi Berhasil',
                'message': 'Data penilaian Qur’an telah diperbarui.',
                'type': 'success',
                'sticky': False,
            }
        }

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

    @api.onchange('halaqoh_id')
    def _onchange_halaqoh_id(self):
        """Mengisi absen_ids dan mengatur ustadz_id ke pengguna yang login untuk staff."""
        halaqoh = self.halaqoh_id
        if halaqoh:
            absen_ids = [(5, 0, 0)]
            for siswa in halaqoh.siswa_ids.sorted(key=lambda s: (s.name or '').lower()):
                permission = self.env['cdn.perijinan'].search([
                    ('siswa_id', '=', siswa.id),
                    ('state', '=', 'Permission')
                ], limit=1)
                if permission:
                    keperluan_name = permission.keperluan.name if permission.keperluan else 'Tidak ada keterangan'
                    waktu_keluar = self.format_datetime_indonesia(
                        permission.waktu_keluar) if permission.waktu_keluar else 'Tidak tercatat'
                    message = f"Santri Keluar pada {waktu_keluar}, karena {keperluan_name}"

                    # PERBAIKAN: Ambil foto bukti dari perijinan
                    foto_bukti = permission.foto_bukti if permission.foto_bukti else False

                    # Ambil nama file asli dari perijinan, atau generate jika kosong
                    if permission.foto_bukti_filename:
                        nama_file = permission.foto_bukti_filename
                    elif foto_bukti:
                        # Generate nama file jika tidak ada
                        nama_file = f"Bukti_Izin_{siswa.nis}_{siswa.name}_{permission.name}.jpg"
                    else:
                        nama_file = False

                    absen_ids.append((0, 0, {
                        'siswa_id': siswa.id,
                        'kehadiran': 'Pulang-Izin',
                        'keterangan': message,
                        'keterangan_izin': foto_bukti,  # Auto-fill foto bukti
                        'keterangan_izin_filename': nama_file,  # Auto-fill nama file
                    }))
                else:
                    absen_ids.append((0, 0, {
                        'siswa_id': siswa.id,
                        'kehadiran': 'Hadir'
                    }))
            user = self.env.user
            employee = self.env['hr.employee'].search(
                [('user_id', '=', user.id)], limit=1)
            ustadz_id = employee.id if employee else False
            if self.env.user.has_group('pesantren_kesantrian.group_kesantrian_manager'):
                ustadz = halaqoh.penanggung_jawab_id | halaqoh.pengganti_ids
                selected_ustadz = employee.id if (employee and employee.id in ustadz.ids) else (ustadz[0].id if ustadz else ustadz_id)
                return {
                    'domain': {
                        'ustadz_id': [('id', 'in', ustadz.ids)]
                    },
                    'value': {
                        'absen_ids': absen_ids,
                        'ustadz_id': selected_ustadz,
                        'company_id': halaqoh.company_id.id,
                    }
                }
            return {
                'domain': {
                    'ustadz_id': [('id', '=', ustadz_id)] if ustadz_id else [('id', '=', False)]
                },
                'value': {
                    'absen_ids': absen_ids,
                    'ustadz_id': ustadz_id,
                    'company_id': halaqoh.company_id.id,
                }
            }

    @api.model
    def default_get(self, fields_list):
        """Memastikan tahun ajaran aktif diset dari company yang sedang aktif."""
        res = super().default_get(fields_list)

        # PERBAIKAN: Gunakan company aktif user, bukan selalu main_company
        current_company = self.env.company  # Company yang sedang aktif
        tahun_ajaran = current_company.tahun_ajaran_aktif

        if not tahun_ajaran:
            raise UserError(
                f'Tahun ajaran belum diset untuk {current_company.name}. '
                'Silakan set tahun ajaran aktif di menu Settings > Companies.'
            )

        # Optional: Set fiscalyear_id di res jika diperlukan
        if 'fiscalyear_id' in fields_list:
            res['fiscalyear_id'] = tahun_ajaran.id

        return res

    def unlink(self):
        """Saat dokumen Absensi Halaqoh dihapus, bersihkan record Penilaian Quran
        yang berstatus 'draft' dan masih kosong agar tidak menjadi data mengambang (orphan data).
        """
        Penilaian = self.env['cdn.penilaian_quran'].with_context(from_guru_quran=True)
        for record in self:
            if record.name and record.halaqoh_id:
                siswa_ids = record.absen_ids.mapped('siswa_id').ids
                if siswa_ids:
                    orphan_penilaians = Penilaian.search([
                        ('tanggal', '=', record.name),
                        ('siswa_id', 'in', siswa_ids),
                        ('halaqoh_id', '=', record.halaqoh_id.id),
                        ('state', '=', 'draft'),
                    ])
                    for pen in orphan_penilaians:
                        is_empty = (
                            not pen.tahfidz_line_ids and
                            not pen.buku_harian_id and
                            not pen.buku_ujian_id and
                            not pen.juz_murajaah and
                            not pen.surah_id_ujian_tahfidz
                        )
                        if is_empty:
                            pen.unlink()
        return super().unlink()

    @api.model
    def create(self, vals):
        """Membuat absensi tanpa batasan ustadz_id untuk staff."""
        rec = super().create(vals)
        if rec.state in ('Draft', 'Proses'):
            rec.action_proses()
            rec.action_confirm()
        return rec

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if rec.state in ('Draft', 'Proses'):
                rec.action_proses()
                rec.action_confirm()
            else:
                rec._sync_penilaian_records()
        return res


class AbsenTahsinQuranLine(models.Model):
    _name = 'cdn.absen_halaqoh_line'
    _description = 'Tabel Absen Halaqoh Line'
    _order = 'name asc, id asc'

    absen_id = fields.Many2one(
        'cdn.absen_halaqoh', string='Absen', ondelete='cascade')
    tanggal = fields.Date(string='Tgl Absen',
                          related='absen_id.name', readonly=True, store=True)
    halaqoh_id = fields.Many2one('cdn.halaqoh', string='Halaqoh',
                                 related='absen_id.halaqoh_id', readonly=True, store=True)
    siswa_id = fields.Many2one('cdn.siswa', string='Siswa', ondelete='cascade')

    name = fields.Char(string='Nama', related='siswa_id.name',
                       readonly=True, store=True)
    nis = fields.Char(string='NIS', related='siswa_id.nis',
                      readonly=True, store=True)
    panggilan = fields.Char(
        string='Nama Panggilan', related='siswa_id.namapanggilan', readonly=True, store=True)
    keterangan = fields.Char(string='Keterangan')
    keterangan_izin = fields.Binary(string='Foto', attachment=True)
    keterangan_izin_filename = fields.Char(string="Nama File Foto")
    company_id = fields.Many2one('res.company', string='Lembaga',
                                 related='absen_id.company_id', readonly=True, store=True)
    kehadiran = fields.Selection([
        ('Hadir', 'Hadir'),
        ('Sakit', 'Sakit'),
        ('Izin', 'Izin'),
        ('Alpa', 'Alpa'),
        ('Pulang-Sakit', 'Pulang-Sakit'),
        ('Pulang-Izin', 'Pulang-Izin'),
        ('Pulang-Alpa', 'Pulang-Alpa'),
    ], string='Kehadiran', required=True, default='Hadir')
    penanggung_jawab_id = fields.Many2one(
        'hr.employee', string='Penanggung Jawab', related='halaqoh_id.penanggung_jawab_id', readonly=True, store=True)
    row_number = fields.Integer(
        string='No', compute='_compute_row_number', store=False)
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
                    'title': '❌ Tidak Dapat Menemukan Data !',
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
