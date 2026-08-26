# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime


class ruang_kelas(models.Model):
    _name = "cdn.ruang_kelas"
    _description = "Tabel Data Ruang Kelas"
    # Tambahan: urutan berdasarkan tingkat
    _order = "tingkat_urutan, nama_kelas, id"

    def _get_domain_guru(self):
        admin_user_ids = self.env.ref('base.group_system').users.ids

        return [
            '|',
            ('user_id', '=', admin_user_ids),
            ('jns_pegawai_ids.code', 'in', ['guru', 'walikelas', 'superadmin'])
        ]

    name = fields.Many2one(
        comodel_name="cdn.master_kelas",
        string="Rombongan Belajar",
        required=True,
        copy=False,
    )
    active = fields.Boolean(string="Active", default=True)

    siswa_ids = fields.Many2many(
        'cdn.siswa',
        'ruang_kelas_siswa_rel',
        'ruang_kelas_id',
        'siswa_id',
        ondelete='cascade',
        string='Daftar Siswa',
        domain="[('active', '=', True), ('jenjang', '=', jenjang)]"
    )

    tahunajaran_id = fields.Many2one(
        comodel_name="cdn.ref_tahunajaran",
        string="Tahun Pelajaran",
        required=True,
        default=lambda self: self.env.user.company_id.tahun_ajaran_aktif.id
    )
    walikelas_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Wali Kelas",
        # Memperluas domain untuk memasukkan musyrif
        domain=lambda self: self.env['cdn.ruang_kelas']._get_domain_guru()
    )
    jenjang = fields.Selection(
        selection=[
            ('paud', 'PAUD'),
            ('tk', 'TK/RA'),
            ('sd', 'SD/MI'),
            ('smp', 'SMP/MTS'),
            ('sma', 'SMA/MA/SMK'),
            ('nonformal', 'Non formal'),
            ('rtq', 'Rumah Tahfidz Quran')
        ],
        string="Jenjang",
        related='name.jenjang',
        store=True,
        readonly=True
    )
    tingkat = fields.Many2one(
        comodel_name="cdn.tingkat",
        string="Tingkat",
        related='name.tingkat',
        store=True,
        readonly=True
    )

    # Tambahan: field untuk menyimpan urutan tingkat sebagai integer
    tingkat_urutan = fields.Integer(
        string="Urutan Tingkat",
        compute='_compute_tingkat_urutan',
        store=True,
        help="Urutan numerik tingkat untuk sorting (1, 2, 3, dst)"
    )

    jurusan_id = fields.Many2one(
        comodel_name='cdn.master_jurusan',
        string='Jurusan / Peminatan',
        related='name.jurusan_id',
        store=True,
        readonly=True
    )
    # Ubah readonly menjadi False dan tambahkan store=True
    nama_kelas = fields.Char(
        string="Nama Kelas", store=True, help="Nama spesifik ruangan kelas.")

    status = fields.Selection(
        string='Status',
        selection=[('draft', 'Draft'), ('konfirm', 'Terkonfirmasi')],
        default="draft"
    )
    jml_siswa = fields.Integer(
        string='Jumlah Siswa',
        compute='_compute_jml_siswa',
        store=True
    )

    aktif_tidak = fields.Selection([
        ('aktif', 'Aktif'),
        ('tidak', 'Tidak Aktif'),
    ], string="Aktif/Tidak", required=True, default='aktif')

    keterangan = fields.Char(
        string="Keterangan", help="Keterangan tambahan terkait ruang kelas")

    angkatan_id = fields.Many2one(
        comodel_name="cdn.ref_tahunajaran",
        string="Angkatan",
        default=lambda self: self._get_default_angkatan(),
    )

    def _get_default_angkatan(self):
        today = date.today()
        tahun = today.year
        bulan = today.month

        # Tahun ajaran mulai dari 1 Juli
        if bulan >= 7:
            start_year = tahun
        else:
            start_year = tahun - 1

        nama_tahun_ajaran = f"{start_year}/{start_year + 1}"

        return self.env['cdn.ref_tahunajaran'].search([
            ('name', '=', nama_tahun_ajaran)
        ], limit=1)

    # Tambahan: compute method untuk menghitung urutan tingkat
    @api.depends('tingkat', 'jenjang')
    def _compute_tingkat_urutan(self):
        """
        Menghitung urutan numerik berdasarkan tingkat dan jenjang
        Mengambil angka dari nama tingkat atau menggunakan mapping default
        """
        for record in self:
            urutan = 999  # default value untuk tingkat yang tidak dikenali

            if record.tingkat:
                # Pastikan tingkat.name adalah string, jika tidak konversi dulu
                try:
                    if hasattr(record.tingkat, 'name') and record.tingkat.name:
                        tingkat_name = str(record.tingkat.name).strip().lower()
                    else:
                        # Jika tidak ada name, coba ambil dari display_name atau id
                        tingkat_name = str(
                            record.tingkat.display_name or record.tingkat.id).strip().lower()
                except (AttributeError, TypeError):
                    # Fallback jika ada masalah dengan akses tingkat
                    tingkat_name = ""

                if tingkat_name:
                    # Import regex di dalam try block untuk keamanan
                    import re

                    # Mapping berdasarkan jenjang
                    if record.jenjang == 'tk':
                        if 'a' in tingkat_name or '1' in tingkat_name:
                            urutan = 1
                        elif 'b' in tingkat_name or '2' in tingkat_name:
                            urutan = 2
                    elif record.jenjang in ['sd', 'smp', 'sma']:
                        # Ekstrak angka dari nama tingkat
                        numbers = re.findall(r'\d+', tingkat_name)
                        if numbers:
                            urutan = int(numbers[0])
                        else:
                            # Mapping manual untuk kelas yang menggunakan huruf romawi
                            tingkat_mapping = {
                                'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5, 'vi': 6,
                                'vii': 7, 'viii': 8, 'ix': 9, 'x': 10, 'xi': 11, 'xii': 12
                            }
                            for key, value in tingkat_mapping.items():
                                if key in tingkat_name:
                                    urutan = value
                                    break
                    elif record.jenjang == 'paud':
                        # Untuk PAUD, bisa disesuaikan dengan kebutuhan
                        if 'play' in tingkat_name or 'bermain' in tingkat_name:
                            urutan = 1
                        elif 'preparation' in tingkat_name or 'persiapan' in tingkat_name:
                            urutan = 2
                        else:
                            # Coba ekstrak angka
                            numbers = re.findall(r'\d+', tingkat_name)
                            if numbers:
                                urutan = int(numbers[0])

            record.tingkat_urutan = urutan

    @api.constrains('name', 'tahunajaran_id', 'status', 'aktif_tidak')
    def _check_duplicate_kelas_konfirm(self):
        """
        Validasi duplikat kelas:
        - Hanya berlaku untuk kelas yang aktif
        - Tidak boleh ada duplikat jika status terkonfirmasi
        - Boleh duplikat jika status draft
        """
        for record in self:
            if record.aktif_tidak == 'aktif' and record.status == 'konfirm':
                # Cek apakah ada kelas lain yang aktif dan terkonfirmasi dengan nama dan tahun ajaran yang sama
                duplicate = self.search([
                    ('id', '!=', record.id),
                    ('name', '=', record.name.id),
                    ('tahunajaran_id', '=', record.tahunajaran_id.id),
                    ('status', '=', 'konfirm'),
                    ('aktif_tidak', '=', 'aktif'),
                ], limit=1)

                if duplicate:
                    raise UserError(
                        _("Tidak boleh ada duplikat kelas yang aktif dan terkonfirmasi! "
                          "Kelas '%s' pada tahun ajaran '%s' sudah ada dengan status terkonfirmasi.") %
                        (record.name.name, record.tahunajaran_id.name)
                    )

    @api.onchange('tingkat', 'jurusan_id', 'nama_kelas')
    def _onchange_tingkat_jurusan_nama(self):
        domain = []

        # Filter berdasarkan tingkat
        if self.tingkat:
            domain.append(('tingkat', '=', self.tingkat.id))

        # Filter jurusan hanya jika jenjang SMA
        if self.jenjang == 'sma' and self.jurusan_id:
            domain.append(('jurusan_id', '=', self.jurusan_id.id))

        # Jika nama_kelas diisi, cari yang sesuai
        if self.nama_kelas:
            domain.append(('nama_kelas', 'ilike', self.nama_kelas.strip()))
        # Hapus kondisi else yang membatasi pencarian ke nama_kelas kosong

        # Jalankan pencarian berdasarkan domain
        if domain:
            kelas = self.env['cdn.master_kelas'].search(domain, limit=1)
            self.name = kelas.id if kelas else False
            return {'domain': {'name': domain}}
        else:
            self.name = False
            return {}

    @api.onchange('name', 'tahunajaran_id', 'aktif_tidak', 'status')
    def _onchange_detect_duplikat_kelas_aktif(self):
        """
        Peringatan duplikat dengan aturan baru:
        - Hanya peringatan untuk kelas aktif
        - Peringatan khusus jika akan membuat duplikat terkonfirmasi
        """
        if self.name and self.tahunajaran_id and self.aktif_tidak == 'aktif':
            # Cek duplikat dengan status terkonfirmasi
            duplikat_konfirm = self.env['cdn.ruang_kelas'].search([
                ('id', '!=', self.id),
                ('name', '=', self.name.id),
                ('tahunajaran_id', '=', self.tahunajaran_id.id),
                ('aktif_tidak', '=', 'aktif'),
                ('status', '=', 'konfirm'),
            ], limit=1)

            # Cek duplikat dengan status draft
            duplikat_draft = self.env['cdn.ruang_kelas'].search([
                ('id', '!=', self.id),
                ('name', '=', self.name.id),
                ('tahunajaran_id', '=', self.tahunajaran_id.id),
                ('aktif_tidak', '=', 'aktif'),
                ('status', '=', 'draft'),
            ], limit=1)

            if duplikat_konfirm and self.status == 'konfirm':
                return {
                    'warning': {
                        'title': "Error: Duplikat Kelas Terkonfirmasi",
                        'message': "Sudah ada kelas aktif yang terkonfirmasi dengan nama dan tahun ajaran yang sama. "
                                 "Tidak diperbolehkan memiliki duplikat kelas terkonfirmasi.",
                    }
                }

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            self.tingkat = self.name.tingkat.id
            self.jurusan_id = self.name.jurusan_id.id
            self.nama_kelas = self.name.nama_kelas
            self.walikelas_id = self.walikelas_id.id

    def _extract_siswa_ids_from_vals(self, vals_siswa_ids):
        """
        Mengekstrak ID siswa yang ditambahkan, dihapus, dan digantikan dari tuple commands Many2many Odoo
        """
        added_ids = set()
        removed_ids = set()
        replaced_ids = None

        if not vals_siswa_ids:
            return added_ids, removed_ids, replaced_ids

        for cmd in vals_siswa_ids:
            if not isinstance(cmd, (tuple, list)) or len(cmd) == 0:
                continue
            code = cmd[0]
            if code == 6:  # (6, 0, [ids])
                replaced_ids = set(cmd[2]) if len(cmd) > 2 and cmd[2] else set()
            elif code == 4:  # (4, id, 0)
                added_ids.add(cmd[1])
            elif code in (2, 3):  # (2, id, 0) or (3, id, 0)
                removed_ids.add(cmd[1])
            elif code == 5:  # (5, 0, 0)
                replaced_ids = set()

        return added_ids, removed_ids, replaced_ids

    def _sync_siswa_ruang_kelas(self, vals=None):
        """
        Sinkronisasi otomatis antara siswa_ids di cdn.ruang_kelas dan ruang_kelas_id di cdn.siswa
        """
        if self.env.context.get('skip_ruang_kelas_sync'):
            return

        for record in self:
            vals_siswa_ids = vals.get('siswa_ids') if vals else None
            added_ids, removed_ids, replaced_ids = self._extract_siswa_ids_from_vals(vals_siswa_ids)

            if replaced_ids is not None:
                current_ids = set(record.siswa_ids.ids)
                target_added_ids = replaced_ids - current_ids
                target_removed_ids = current_ids - replaced_ids
            else:
                target_added_ids = added_ids
                target_removed_ids = removed_ids

            # Jika tidak dari vals (misal call manual/bulk sync), hitung dari record.siswa_ids
            if vals is None:
                target_added_ids = set(record.siswa_ids.ids)
                siswa_removed = self.env['cdn.siswa'].search([('ruang_kelas_id', '=', record.id)])
                target_removed_ids = set(siswa_removed.ids) - target_added_ids

            # Update siswa yang ditambahkan
            if target_added_ids:
                added_siswa = self.env['cdn.siswa'].browse(list(target_added_ids))
                for siswa in added_siswa:
                    if siswa.ruang_kelas_id and siswa.ruang_kelas_id.id != record.id:
                        old_kelas = siswa.ruang_kelas_id
                        old_kelas.with_context(skip_ruang_kelas_sync=True).write({
                            'siswa_ids': [(3, siswa.id)]
                        })

                added_siswa.with_context(skip_ruang_kelas_sync=True).write({
                    'ruang_kelas_id': record.id,
                    'tahunajaran_id': record.tahunajaran_id.id if record.tahunajaran_id else False,
                })

            # Reset siswa yang dikeluarkan
            if target_removed_ids:
                removed_siswa = self.env['cdn.siswa'].browse(list(target_removed_ids))
                removed_siswa.with_context(skip_ruang_kelas_sync=True).write({
                    'ruang_kelas_id': False,
                })

    def _sync_walikelas_roles(self, old_walikelas_id=None, new_walikelas_id=None):
        role_walikelas = self.env['cdn.jenis_pegawai'].sudo().search([('code', '=', 'walikelas')], limit=1)
        if not role_walikelas:
            return

        # 1. Handle new walikelas: add role
        if new_walikelas_id:
            employee = self.env['hr.employee'].sudo().browse(new_walikelas_id)
            if employee and role_walikelas not in employee.jns_pegawai_ids:
                employee.write({
                    'jns_pegawai_ids': [(4, role_walikelas.id)]
                })

        # 2. Handle old walikelas: remove role if they don't have any other class bimbingan
        if old_walikelas_id and old_walikelas_id != new_walikelas_id:
            # Check if this old walikelas is still assigned to other classes
            other_classes = self.env['cdn.ruang_kelas'].search([
                ('walikelas_id', '=', old_walikelas_id),
                ('id', 'not in', self.ids)
            ])
            if not other_classes:
                employee = self.env['hr.employee'].sudo().browse(old_walikelas_id)
                if employee and role_walikelas in employee.jns_pegawai_ids:
                    employee.write({
                        'jns_pegawai_ids': [(3, role_walikelas.id)]
                    })

    # Tambahkan method untuk memastikan nama_kelas selalu diisi dari name
    @api.model
    def create(self, vals):
        if vals.get('name'):
            kelas = self.env['cdn.master_kelas'].browse(vals.get('name'))
            if kelas and kelas.nama_kelas:
                vals['nama_kelas'] = kelas.nama_kelas
        rec = super(ruang_kelas, self).create(vals)
        if rec.walikelas_id:
            rec._sync_walikelas_roles(new_walikelas_id=rec.walikelas_id.id)
        if 'siswa_ids' in vals:
            rec._sync_siswa_ruang_kelas(vals=vals)
        if rec.status == 'draft':
            rec.konfirmasi()
        return rec

    def write(self, vals):
        if vals.get('name'):
            kelas = self.env['cdn.master_kelas'].browse(vals.get('name'))
            if kelas and kelas.nama_kelas:
                vals['nama_kelas'] = kelas.nama_kelas

        # Keep track of old walikelas
        old_walikelas_by_rec = {}
        if 'walikelas_id' in vals:
            old_walikelas_by_rec = {rec.id: rec.walikelas_id.id for rec in self if rec.walikelas_id}

        # Sinkronkan profil siswa SEBELUM super().write agar constraint unique_siswa_per_tahunajaran tidak terganggu
        if 'siswa_ids' in vals or 'tahunajaran_id' in vals:
            self._sync_siswa_ruang_kelas(vals=vals)

        result = super(ruang_kelas, self).write(vals)

        # Pastikan sinkronisasi akhir beres
        if 'siswa_ids' in vals or 'tahunajaran_id' in vals:
            self._sync_siswa_ruang_kelas()

        if 'walikelas_id' in vals:
            for rec in self:
                old_id = old_walikelas_by_rec.get(rec.id)
                new_id = vals.get('walikelas_id')
                rec._sync_walikelas_roles(old_walikelas_id=old_id, new_walikelas_id=new_id)

        if 'status' not in vals:
            for rec in self:
                if rec.status == 'draft':
                    rec.konfirmasi()
        return result

    def unlink(self):
        # Keep track of walikelas before deletion
        walikelas_ids = [rec.walikelas_id.id for rec in self if rec.walikelas_id]
        
        result = super(ruang_kelas, self).unlink()
        
        # Check and remove roles
        role_walikelas = self.env['cdn.jenis_pegawai'].sudo().search([('code', '=', 'walikelas')], limit=1)
        if role_walikelas and walikelas_ids:
            for w_id in set(walikelas_ids):
                # check if they have other classes left
                other_classes = self.env['cdn.ruang_kelas'].search([('walikelas_id', '=', w_id)])
                if not other_classes:
                    employee = self.env['hr.employee'].sudo().browse(w_id)
                    if employee and role_walikelas in employee.jns_pegawai_ids:
                        employee.write({
                            'jns_pegawai_ids': [(3, role_walikelas.id)]
                        })
        return result

    def action_sync_all_ruang_kelas(self):
        """
        Action / Method untuk melakukan sinkronisasi massal seluruh data Ruang Kelas dan Santri
        """
        all_classes = self.search([])
        for kelas in all_classes:
            # Cari siswa aktif yang terdaftar di kelas ini
            siswa_in_kelas = self.env['cdn.siswa'].search([
                ('ruang_kelas_id', '=', kelas.id),
                ('active', '=', True)
            ])
            # Set siswa_ids agar persis sama dengan siswa aktif kelas tersebut
            kelas.with_context(skip_ruang_kelas_sync=True).write({
                'siswa_ids': [(6, 0, siswa_in_kelas.ids)]
            })
            kelas._compute_jml_siswa()

        # Dan pastikan semua santri aktif dengan ruang_kelas_id terisi disinkronkan
        all_siswa = self.env['cdn.siswa'].search([('ruang_kelas_id', '!=', False), ('active', '=', True)])
        for s in all_siswa:
            if s.ruang_kelas_id and s.id not in s.ruang_kelas_id.siswa_ids.ids:
                s.ruang_kelas_id.with_context(skip_ruang_kelas_sync=True).write({
                    'siswa_ids': [(4, s.id)]
                })
                s.ruang_kelas_id._compute_jml_siswa()

        # Otomatis aktifkan kembali status_akun & bersihkan alasan_keluar santri aktif yang dipulihkan dari Alumni
        active_siswa_to_fix = self.env['cdn.siswa'].search([
            ('active', '=', True),
            '|', ('alasan_keluar', '!=', False), ('status_akun', '=', 'blokir')
        ])
        for s in active_siswa_to_fix:
            fix_vals = {}
            if s.alasan_keluar:
                fix_vals['alasan_keluar'] = False
            if s.tanggal_keluar:
                fix_vals['tanggal_keluar'] = False
            if s.status_akun == 'blokir' and not getattr(s, 'alasan_akun', False):
                fix_vals['status_akun'] = 'aktif'
            if fix_vals:
                s.write(fix_vals)

        message_id = self.env['message.wizard'].create({
            'message': _("Sinkronisasi Data Santri, Ruang Kelas, & Pemulihan Kartu Berhasil !!")
        })
        return {
            'name': _('Berhasil'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'message.wizard',
            'res_id': message_id.id,
            'target': 'new'
        }

    def konfirmasi(self):
        for rec in self:
            # Pastikan nama_kelas diisi dari name jika kosong
            if rec.name and not rec.nama_kelas:
                rec.nama_kelas = rec.name.nama_kelas

            # Validasi duplikat sebelum konfirmasi (hanya untuk kelas aktif)
            if rec.aktif_tidak == 'aktif':
                duplicate_konfirm = self.env['cdn.ruang_kelas'].search([
                    ('id', '!=', rec.id),
                    ('name', '=', rec.name.id),
                    ('tahunajaran_id', '=', rec.tahunajaran_id.id),
                    ('status', '=', 'konfirm'),
                    ('aktif_tidak', '=', 'aktif'),
                ], limit=1)

                if duplicate_konfirm:
                    raise UserError(
                        _("Tidak dapat mengkonfirmasi kelas ini karena sudah ada kelas aktif yang terkonfirmasi "
                          "dengan nama '%s' pada tahun ajaran '%s'. "
                          "Silakan ubah status kelas lain menjadi draft terlebih dahulu atau nonaktifkan kelas tersebut.") %
                        (rec.name.name, rec.tahunajaran_id.name)
                    )

            rec.status = 'konfirm'

            conflicting_students = [
                (s.name, s.ruang_kelas_id.name.name,
                 s.ruang_kelas_id.tahunajaran_id.name)
                for s in rec.siswa_ids
                if s.ruang_kelas_id and s.ruang_kelas_id.id != rec.id and s.ruang_kelas_id.tahunajaran_id == rec.tahunajaran_id
            ]

            if conflicting_students:
                conflict_message = "\n".join(
                    ["Siswa atas nama %s sudah terdaftar di %s pada Tahun Ajaran %s!" % (name, kelas, tahun)
                     for name, kelas, tahun in conflicting_students]
                )
                raise UserError(
                    "Silakan hapus dulu data siswa yang bersangkutan dari kelas lain:\n\n%s" % conflict_message)

            # Set ruang_kelas_id dan tahunajaran_id pada siswa
            for siswa in rec.siswa_ids:
                siswa.write({
                    'ruang_kelas_id': rec.id,
                    'tahunajaran_id': rec.tahunajaran_id.id,  # Tambahan: set tahun ajaran siswa
                })

            # Reset siswa yang sebelumnya ada tapi sekarang tidak
            siswa_existing = self.env['cdn.siswa'].search(
                [('ruang_kelas_id', '=', rec.id)])
            for siswa in siswa_existing:
                if siswa.id not in rec.siswa_ids.ids:
                    siswa.write({
                        'ruang_kelas_id': False,
                        'tahunajaran_id': False,  # Tambahan: reset tahun ajaran juga
                    })

            message_id = self.env['message.wizard'].create({
                'message': _("Update Ruang Kelas Siswa - SUKSES !!")
            })
            return {
                'name': _('Berhasil'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'message.wizard',
                'res_id': message_id.id,
                'target': 'new'
            }

    @api.constrains('siswa_ids', 'tahunajaran_id')
    def _check_unique_siswa_per_tahunajaran(self):
        for rec in self:
            if not rec.tahunajaran_id or not rec.siswa_ids:
                continue
            conflicting_students = []
            for siswa in rec.siswa_ids:
                if siswa.ruang_kelas_id and siswa.ruang_kelas_id.id != rec.id and siswa.ruang_kelas_id.tahunajaran_id == rec.tahunajaran_id:
                    k_name = siswa.ruang_kelas_id.name.name if (siswa.ruang_kelas_id.name and hasattr(siswa.ruang_kelas_id.name, 'name')) else (siswa.ruang_kelas_id.nama_kelas or '-')
                    conflicting_students.append(f"• {siswa.name} (terdaftar di kelas: {k_name})")
            if conflicting_students:
                msg = "\n".join(conflicting_students)
                raise UserError(
                    f"⛔ Santri berikut sudah terdaftar di kelas lain pada Tahun Pelajaran {rec.tahunajaran_id.name}:\n\n{msg}\n\n"
                    f"Satu santri hanya boleh terdaftar di 1 kelas per Tahun Pelajaran. "
                    f"Silakan hapus/keluarkan santri tersebut dari kelas lama terlebih dahulu."
                )

    def draft(self):
        for rec in self:
            rec.status = 'draft'

    @api.depends('siswa_ids', 'siswa_ids.active', 'siswa_ids.ruang_kelas_id')
    def _compute_jml_siswa(self):
        for record in self:
            # Filter hanya siswa yang aktif dan memiliki ruang_kelas_id sesuai dengan kelas ini
            siswa_aktif = record.siswa_ids.filtered(
                lambda s: s.active and s.ruang_kelas_id and s.ruang_kelas_id.id == record.id
            )
            record.jml_siswa = len(siswa_aktif)


class MessageWizard(models.TransientModel):
    _name = 'message.wizard'

    message = fields.Text('Informasi', required=True)

    def action_ok(self):
        """ close wizard"""
        return {'type': 'ir.actions.act_window_close'}
