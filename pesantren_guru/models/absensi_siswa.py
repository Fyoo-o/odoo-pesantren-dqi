# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging
import base64
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AbsensiSiswa(models.Model):
    _name = 'cdn.absensi_siswa'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Data Absensi Siswa'
    _order = 'tanggal desc'

    def _get_domain_guru(self):
        user = self.env.user
        guru_domain = [('jns_pegawai_ids.code', 'in', ['guru'])]
        if user.has_group('pesantren_guru.group_guru_manager'):
            return [('user_id', '=', self.env.user.id)] + guru_domain
        elif user.has_group('pesantren_guru.group_guru_staff'):
            user = self.env['hr.employee'].search([('user_id', '=', user.id)])
            return [('user_id', '=', self.env.user.id)] + guru_domain
        return [('id', '=', False)]

    def _get_default_guru(self):
        user = self.env.user
        if user.has_group('pesantren_guru.group_guru_staff'):
            user = self.env['hr.employee'].search([('user_id', '=', user.id)])
            return user.id
        return False

    name = fields.Char(string='Nama', readonly=True,
                       compute='_compute_name', store=True)
    tanggal = fields.Date(string='Tanggal Absen', required=True,
                          default=lambda self: fields.Date.context_today(self))
    hari = fields.Selection([
        ('1', 'Senin'),
        ('2', 'Selasa'),
        ('3', 'Rabu'),
        ('4', 'Kamis'),
        ('5', 'Jumat'),
        ('6', 'Sabtu'),
        ('7', 'Minggu'),
    ], string='Hari', readonly=True, compute='_compute_hari', store=True)
    jampelajaran_id = fields.Many2many(
        comodel_name='cdn.ref_jam_pelajaran', string='Jam Ke', required=True)
    start_time = fields.Float(
        string='Start Time', related='jampelajaran_id.start_time', readonly=True, store=True)
    end_time = fields.Float(
        string='End Time', related='jampelajaran_id.end_time', readonly=True, store=True)
    kelas_id = fields.Many2one(
        comodel_name='cdn.ruang_kelas', string='Kelas', required=True)
    tingkat_id = fields.Many2one(comodel_name='cdn.tingkat', string='Tingkat',
                                 related='kelas_id.tingkat', readonly=True, store=True)
    walikelas_id = fields.Many2one(comodel_name='hr.employee', string='Wali Kelas',
                                   related='kelas_id.walikelas_id', readonly=True, store=True)
    tahunajaran_id = fields.Many2one(comodel_name='cdn.ref_tahunajaran', string='Tahun Ajaran',
                                     related='kelas_id.tahunajaran_id', readonly=True, store=True)
    semester = fields.Selection(selection=[(
        '1', 'Ganjil'), ('2', 'Genap')], string='Semester', readonly=True, store=True)
    guru_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Guru',
        required=True,
        default=_get_default_guru,
        domain=lambda self: self.env['cdn.absensi_siswa']._domain_guru()
    )
    pertemuan_ke = fields.Integer(
        string='Pertemuan Ke', readonly=True, compute='_compute_pertemuan_ke', store=True)
    mapel_id = fields.Many2one(
        comodel_name='cdn.mata_pelajaran', string='Mata pelajaran', required=True)
    rpp_id = fields.Many2one(comodel_name='cdn.master_rpp', string='RPP')
    dokumen = fields.Binary(
        string='Dokumen', related='rpp_id.dokumen', readonly=True, store=True)
    tema = fields.Char(string='Tema', required=True)
    materi = fields.Text(string='Materi', required=True)
    state = fields.Selection(
        selection=[('draft', 'Draft'), ('done', 'Done')], string='State', default='done')
    absensi_ids = fields.One2many(
        comodel_name='cdn.absensi_siswa_lines', inverse_name='absensi_id', string='Absensi Siswa')
    row_number = fields.Integer(
        string='No', compute='_compute_row_number', store=False)
    company_id = fields.Many2one(
        'res.company', string='Lembaga', default=lambda self: self.env.company)
    jml_jampelajaran = fields.Integer(
        string='Jumlah JP', compute='_compute_jml_jampelajaran', store=True, help='Jumlah Jam Pelajaran')
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
        related='kelas_id.jenjang',
        store=True,
        readonly=True
    )
    is_guru_pengganti = fields.Boolean(
        string='Guru Pengganti',
        default=False,
        help='Centang jika Anda bertindak sebagai guru pengganti'
    )
    keterangan = fields.Char(string='Catatan')

    def _domain_guru(self):
        admin_user_ids = self.env.ref('base.group_system').users.ids

        return [
            '|',
            ('user_id', 'in', admin_user_ids),
            ('jns_pegawai_ids.code', 'in', ['guru', 'superadmin'])
        ]

    def _compute_row_number(self):
        for index, record in enumerate(self):
            record.row_number = index + 1

    def action_draft(self):
        self.state = 'draft'

    def action_done(self):
        self.state = 'done'

    def action_sort_siswa(self):
        for record in self:
            sorted_lines = record.absensi_ids.sorted(key=lambda l: (l.siswa_id.name or '').lower())
            record.absensi_ids = [(6, 0, sorted_lines.ids)]

    @api.constrains('kelas_id', 'tanggal', 'jampelajaran_id')
    def _check_name(self):
        for record in self:
            if record.kelas_id and record.tanggal and record.jampelajaran_id:
                existing = self.search([
                    ('kelas_id', '=', record.kelas_id.id),
                    ('tanggal', '=', record.tanggal),
                    ('jampelajaran_id', 'in', record.jampelajaran_id.ids),
                    ('id', '!=', record.id)
                ], limit=1)
                if existing:
                    guru_name = existing.guru_id.name if existing.guru_id else 'Tidak diketahui'
                    user_name = existing.create_uid.name if existing.create_uid else 'Tidak diketahui'
                    kelas_name = existing.kelas_id.display_name if existing.kelas_id else '-'
                    jam_names = ", ".join(existing.jampelajaran_id.mapped('name')) if existing.jampelajaran_id else '-'
                    tgl = existing.tanggal.strftime('%d-%m-%Y') if existing.tanggal else '-'
                    raise UserError(
                        f"Absensi Siswa untuk Kelas '{kelas_name}' Tanggal {tgl} (Jam: {jam_names}) "
                        f"sudah diisi oleh Guru: {guru_name} (User: {user_name}). "
                        f"Silakan berkoordinasi langsung dengan yang bersangkutan."
                    )

    @api.depends('tanggal')
    def _compute_hari(self):
        for record in self:
            record.hari = str(record.tanggal.weekday() + 1)

    @api.depends('kelas_id', 'tanggal', 'jampelajaran_id')
    def _compute_name(self):
        for record in self:
            jam_names = ", ".join(record.jampelajaran_id.mapped(
                'name')) if record.jampelajaran_id else "-"
            kelas_name = record.kelas_id.name.name if record.kelas_id and record.kelas_id.name else "Baru"
            tanggal = record.tanggal or "-"
            record.name = "%s/%s/%s" % (
                kelas_name,
                tanggal,
                jam_names
            )

    @api.depends('jampelajaran_id')
    def _compute_jml_jampelajaran(self):
        for record in self:
            record.jml_jampelajaran = len(record.jampelajaran_id)

    @api.depends('mapel_id', 'kelas_id')
    def _compute_pertemuan_ke(self):
        for record in self:
            if record.kelas_id and record.mapel_id:
                rid = record.id if type(record.id) == int else False
                record.pertemuan_ke = self.env['cdn.absensi_siswa'].search_count([
                    ('mapel_id', '=', record.mapel_id.id),
                    ('kelas_id', '=', record.kelas_id.id),
                    ('id', '!=', rid),
                ]) + 1

    @api.model
    def _get_company_id_for_jenjang(self, jenjang):
        """Mendapatkan company_id (Lembaga) yang sesuai dengan jenjang kelas."""
        mapping = {
            'smp': 'SMP Tahfizh Bilingual',
            'sma': 'MA Tahfizh Bilingual',
            'sd': 'SD Tahfizh Bilingual',
            'tk': 'TK Tahfizh Baby-Qu',
            'paud': 'KB Tahfizh Baby-Qu',
            'kb': 'KB Tahfizh Baby-Qu',
            'rtq': "Rumah Tahfizh Al-Qur'an",
        }
        target_name = mapping.get(jenjang)
        if not target_name:
            return False
        comp = self.env['res.company'].sudo().search([
            ('name', 'ilike', target_name),
            ('name', 'not ilike', '%backup%')
        ], limit=1)
        return comp.id if comp else False

    def _register_hook(self):
        super()._register_hook()
        try:
            self._auto_sync_guru_company(self.env.cr)
        except Exception as e:
            _logger.warning("Auto-sync guru company in _register_hook failed: %s", e)

    @classmethod
    def _auto_sync_guru_company(cls, cr):
        """Sinkronisasi otomatis saat server Odoo start / restart:
        1. Menyelaraskan company_id cdn_absensi_siswa agar sesuai dengan jenjang kelasnya.
        2. Menyelaraskan company_id cdn_absensi_siswa_lines.
        3. Memberikan akses semua unit lembaga pesantren di res_company_users_rel untuk seluruh akun guru.
        4. Mengarahkan Default Company (res_users.company_id) guru ke unit tempat mengajarnya.
        """
        _logger.info("Checking & running auto-sync for guru company and absensi records...")
        try:
            cr.execute("""
                SELECT id, name FROM res_company 
                WHERE (parent_id = 1 OR id = 1) AND name NOT ILIKE '%backup%'
            """)
            comps = cr.fetchall()
            if not comps:
                return

            company_mapping = {}
            edu_comp_ids = [c[0] for c in comps]

            for cid, name in comps:
                lname = name.lower()
                if 'smp' in lname:
                    company_mapping['smp'] = cid
                elif 'ma tahfizh' in lname or 'sma' in lname:
                    company_mapping['sma'] = cid
                elif 'sd tahfizh' in lname:
                    company_mapping['sd'] = cid
                elif 'tk tahfizh' in lname:
                    company_mapping['tk'] = cid
                elif 'kb tahfizh' in lname or 'paud' in lname:
                    company_mapping['paud'] = cid
                    company_mapping['kb'] = cid

            # 1. Update cdn_absensi_siswa agar company_id sesuai jenjang kelasnya
            total_absensi = 0
            for jenjang, target_cid in company_mapping.items():
                cr.execute("""
                    UPDATE cdn_absensi_siswa a
                    SET company_id = %s
                    FROM cdn_ruang_kelas k
                    WHERE a.kelas_id = k.id AND k.jenjang = %s AND (a.company_id IS NULL OR a.company_id != %s)
                """, (target_cid, jenjang, target_cid))
                total_absensi += cr.rowcount

            # 2. Update lines company_id
            cr.execute("""
                UPDATE cdn_absensi_siswa_lines l
                SET company_id = a.company_id
                FROM cdn_absensi_siswa a
                WHERE l.absensi_id = a.id AND (l.company_id IS NULL OR l.company_id != a.company_id)
            """)
            total_lines = cr.rowcount
            if total_absensi > 0 or total_lines > 0:
                _logger.info("Auto-sync: %d absensi records and %d lines aligned to class unit.", total_absensi, total_lines)

            # 3. Tambahkan allowed companies untuk semua akun guru (res_company_users_rel)
            total_allowed = 0
            for cid in edu_comp_ids:
                cr.execute("""
                    INSERT INTO res_company_users_rel (user_id, cid)
                    SELECT DISTINCT u.id, %s
                    FROM res_users u
                    WHERE u.id IN (
                        SELECT DISTINCT user_id FROM hr_employee WHERE user_id IS NOT NULL
                        UNION
                        SELECT DISTINCT p.user_id FROM cdn_guru g JOIN res_partner p ON g.partner_id = p.id WHERE p.user_id IS NOT NULL
                        UNION
                        SELECT DISTINCT create_uid FROM cdn_absensi_siswa WHERE create_uid IS NOT NULL
                    )
                    AND u.active = true
                    ON CONFLICT DO NOTHING
                """, (cid,))
                total_allowed += cr.rowcount
            if total_allowed > 0:
                _logger.info("Auto-sync: Granted %d allowed company accesses to teacher accounts.", total_allowed)

            # 4. Set default company_id untuk guru yang masih 1 (Yayasan) sesuai jenjang utama mengajar
            total_default = 0
            for jenjang, target_cid in company_mapping.items():
                cr.execute("""
                    WITH teacher_primary_jenjang AS (
                        SELECT DISTINCT ON (e.user_id) e.user_id, k.jenjang
                        FROM cdn_absensi_siswa a
                        JOIN hr_employee e ON a.guru_id = e.id
                        JOIN cdn_ruang_kelas k ON a.kelas_id = k.id
                        WHERE e.user_id IS NOT NULL
                        GROUP BY e.user_id, k.jenjang
                        ORDER BY e.user_id, count(*) DESC
                    )
                    UPDATE res_users u
                    SET company_id = %s
                    FROM teacher_primary_jenjang tp
                    WHERE u.id = tp.user_id AND tp.jenjang = %s AND u.company_id = 1
                """, (target_cid, jenjang))
                total_default += cr.rowcount

            # 5. Fallback berdasarkan department employee jika belum ter-set
            for jenjang, target_cid in company_mapping.items():
                cr.execute("""
                    UPDATE res_users u
                    SET company_id = %s
                    FROM hr_employee e
                    LEFT JOIN hr_department d ON e.department_id = d.id
                    WHERE e.user_id = u.id 
                      AND u.company_id = 1 
                      AND (d.name->>'en_US' ILIKE %s OR d.name->>'id_ID' ILIKE %s)
                """, (target_cid, f'%{jenjang}%', f'%{jenjang}%'))
                total_default += cr.rowcount

            if total_default > 0:
                _logger.info("Auto-sync: Set default company for %d teacher users.", total_default)

            # 6. Update legacy draft records to done
            cr.execute("UPDATE cdn_absensi_siswa SET state = 'done' WHERE state = 'draft';")
            if cr.rowcount > 0:
                _logger.info("Auto-sync: Set %d draft absensi records to done.", cr.rowcount)

            # 7. Update view arch_db in ir_ui_view to remove Confirm & Set to Draft buttons
            cr.execute("""
                UPDATE ir_ui_view 
                SET arch_db = jsonb_set(
                    arch_db, 
                    '{en_US}', 
                    to_jsonb(
                        regexp_replace(
                            regexp_replace(
                                arch_db->>'en_US', 
                                '<button name="action_done"[^>]*/>\\s*', '', 'g'
                            ),
                            '<button name="action_draft"[^>]*/>\\s*', '', 'g'
                        )
                    )
                )
                WHERE name = 'cdn.absensi_siswa.view.form'
                  AND (arch_db->>'en_US' LIKE '%action_done%' OR arch_db->>'en_US' LIKE '%action_draft%');
            """)

            # 8. Update multi-company ir_rule agar mematuhi company selector (KB hanya tampil KB, dsb)
            domain_force_comp = "['|', ('company_id', '=', False), ('company_id', 'child_of', company_ids)]"
            cr.execute("""
                UPDATE ir_rule 
                SET domain_force = %s
                WHERE id IN (
                    SELECT res_id FROM ir_model_data 
                    WHERE module = 'pesantren_guru' 
                      AND name IN (
                          'absensi_siswa_company_rule', 'absensi_siswa_line_company_rule',
                          'absensi_ekskul_company_rule', 'absensi_ekskul_line_company_rule',
                          'penugasan_company_rule', 'penugasan_line_company_rule',
                          'penilaian_company_rule', 'penilaian_lines_company_rule',
                          'penilaian_akhir_guru_company_rule', 'penilaian_akhir_company_rule'
                      )
                ) OR name IN (
                    'Absensi Siswa companies', 'Absensi Siswa Line companies',
                    'Absensi Ekskul companies', 'Absensi Ekskul Line companies',
                    'Penugasan companies', 'Penugasan Line companies',
                    'Penilaian companies', 'Penilaian Lines companies',
                    'Penilaian Akhir Guru companies', 'Penilaian Akhir Wali Kelas companies'
                );
            """, (domain_force_comp,))

            # 9. Update ir_rule agar guru hanya melihat absensi miliknya atau yang dibuatnya (guru pengganti)
            domain_force_hdr = "['|', ('guru_id.user_id', '=', user.id), ('create_uid', '=', user.id)]"
            cr.execute("""
                UPDATE ir_rule 
                SET domain_force = %s
                WHERE id IN (
                    SELECT res_id FROM ir_model_data 
                    WHERE module = 'pesantren_guru' 
                      AND name IN ('absensi_siswa_rule_guru_user', 'absensi_siswa_rule_guru_staff')
                ) OR TRIM(name) IN ('Absensi Siswa - Guru Akademik User', 'Absensi Siswa - Guru Akademik Staff');
            """, (domain_force_hdr,))

            domain_force_line = "['|', ('guru.user_id', '=', user.id), ('create_uid', '=', user.id)]"
            cr.execute("""
                UPDATE ir_rule 
                SET domain_force = %s
                WHERE id IN (
                    SELECT res_id FROM ir_model_data 
                    WHERE module = 'pesantren_guru' 
                      AND name = 'absensi_siswa_line_rule_guru_user'
                ) OR TRIM(name) = 'Absensi Siswa Line - Guru Akademik User';
            """, (domain_force_line,))

            # 10. Update string label baris keterangan -> Catatan pada form view absensi_siswa
            cr.execute("""
                UPDATE ir_ui_view
                SET arch_db = jsonb_set(
                    arch_db,
                    '{en_US}',
                    to_jsonb(
                        replace(
                            arch_db->>'en_US',
                            '<field name="keterangan" placeholder="Alasan penggantian',
                            '<field name="keterangan" string="Catatan" placeholder="Alasan penggantian'
                        )
                    )
                )
                WHERE name = 'cdn.absensi_siswa.view.form'
                  AND arch_db->>'en_US' LIKE '%<field name="keterangan" placeholder="Alasan penggantian%'
                  AND arch_db->>'en_US' NOT LIKE '%string="Catatan"%';
            """)
            cr.execute("""
                UPDATE ir_model_fields 
                SET field_description = jsonb_set(field_description, '{en_US}', '"Catatan"')
                WHERE model = 'cdn.absensi_siswa' AND name = 'keterangan' 
                  AND pg_typeof(field_description) = 'jsonb'::regtype;
            """)

            # 11. Pastikan view publik absensi siswa (Sekolah -> Absensi) tidak menampilkan tombol Baru/Edit
            cr.execute("""
                UPDATE ir_ui_view
                SET arch_db = jsonb_set(
                    arch_db,
                    '{en_US}',
                    to_jsonb(
                        replace(
                            replace(arch_db->>'en_US', '<list>', '<list create="false">'),
                            '<form string="">', '<form string="" create="false" edit="false" delete="false">'
                        )
                    )
                )
                WHERE name IN ('cdn.absensi_siswa.view.list.public', 'cdn.absensi_siswa.view.form.public')
                  AND arch_db->>'en_US' NOT LIKE '%create="false"%';
            """)
            cr.execute("""
                UPDATE ir_act_window
                SET context = '{"create": False, "edit": False, "delete": False}'
                WHERE res_model = 'cdn.absensi_siswa'
                  AND id IN (
                      SELECT res_id FROM ir_model_data 
                      WHERE module = 'pesantren_guru' AND name = 'cdn_absensi_siswa_action_public'
                  );
            """)

            # Commit seluruh perubahan auto-sync agar langsung tersimpan di database
            cr.commit()
            _logger.info("Auto-sync: Successfully completed all guru multi-company and permissions sync.")

        except Exception as e:
            _logger.warning("Error in _auto_sync_guru_company: %s", e)

    @api.onchange('guru_id')
    def _onchange_guru_id(self):
        if not self._origin.guru_id and self.guru_id:
            pass

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['state'] = 'done'
            if vals.get('kelas_id') and not vals.get('company_id'):
                kelas = self.env['cdn.ruang_kelas'].sudo().browse(vals['kelas_id'])
                if kelas.exists() and kelas.jenjang:
                    target_cid = self._get_company_id_for_jenjang(kelas.jenjang)
                    if target_cid:
                        vals['company_id'] = target_cid

        records = super(AbsensiSiswa, self).create(vals_list)
        for rec in records:
            if rec.tanggal:
                for line in rec.absensi_ids:
                    if line.kehadiran == 'Hadir' and line.siswa_id:
                        malam_line = self.env['cdn.absensi_malam_line'].sudo().search([
                            ('siswa_id', '=', line.siswa_id.id),
                            ('tanggal', '=', rec.tanggal)
                        ], limit=1)
                        if malam_line and malam_line.kehadiran_absen != 'Hadir':
                            sync_val = malam_line.kehadiran_absen
                            if sync_val in dict(line._fields['kehadiran'].selection):
                                msg = malam_line.keterangan or f"Absen Kamar ({sync_val})"
                                line.write({'kehadiran': sync_val, 'keterangan': msg})
        return records

    @api.onchange('kelas_id')
    def _onchange_kelas_id(self):
        """Mengisi absensi_ids berdasarkan kelas dan menyelaraskan company_id dengan jenjang kelas."""
        if self.kelas_id:
            if self.kelas_id.jenjang:
                comp_id = self._get_company_id_for_jenjang(self.kelas_id.jenjang)
                if comp_id:
                    self.company_id = comp_id

        if self.kelas_id and (not self.absensi_ids or self._origin.kelas_id != self.kelas_id):
            # Hapus semua baris hanya jika perlu mengisi ulang
            absensi_ids = [(5, 0, 0)]
            siswa_domain = ['|', ('ruang_kelas_id', '=', self.kelas_id.id), ('id', 'in', self.kelas_id.siswa_ids.ids)]
            siswa_list = self.env['cdn.siswa'].search(siswa_domain, order='name asc')
            if not siswa_list:
                return {
                    'warning': {
                        'title': 'Perhatian',
                        'message': 'Tidak ada siswa yang ditemukan di kelas tersebut.'
                    },
                    'value': {'absensi_ids': [(5, 0, 0)]}
                }
            for siswa in siswa_list:
                permission = self.env['cdn.perijinan'].search([
                    ('siswa_id', '=', siswa.id),
                    ('state', '=', 'Permission')
                ], limit=1)
                if permission:
                    keperluan_name = permission.keperluan.name if permission.keperluan else 'Tidak ada keterangan'
                    waktu_keluar = self.format_datetime_indonesia(
                        permission.waktu_keluar) if permission.waktu_keluar else 'Tidak tercatat'
                    message = f"Santri Keluar pada {waktu_keluar}, karena {keperluan_name}"
                    foto_bukti = False
                    try:
                        if permission.foto_bukti:
                            base64.b64decode(
                                permission.foto_bukti, validate=True)
                            foto_bukti = permission.foto_bukti
                    except Exception as e:
                        _logger.error(
                            f"Invalid foto_bukti for permission {permission.id} (siswa: {siswa.name}): {str(e)}"
                        )
                        foto_bukti = False
                    if permission and permission.foto_bukti_filename:
                        nama_file = permission.foto_bukti_filename
                    elif permission and foto_bukti:
                        nama_file = f"Bukti_Izin_{siswa.nis}_{siswa.name}_{permission.name}.jpg"
                    else:
                        nama_file = False
                    absensi_ids.append((0, 0, {
                        'siswa_id': siswa.id,
                        'kehadiran': 'Pulang-Izin',
                        'keterangan': message,
                        'keterangan_izin': foto_bukti,
                        'keterangan_izin_filename': nama_file,
                        'company_id': self.company_id.id,
                    }))
                else:
                    tgl_absen = self.tanggal or fields.Date.today()
                    malam_line = self.env['cdn.absensi_malam_line'].sudo().search([
                        ('siswa_id', '=', siswa.id),
                        ('tanggal', '=', tgl_absen)
                    ], limit=1)
                    if malam_line and malam_line.kehadiran_absen != 'Hadir':
                        msg_kamar = malam_line.keterangan or f"Absen Kamar ({malam_line.kehadiran_absen})"
                        absensi_ids.append((0, 0, {
                            'siswa_id': siswa.id,
                            'kehadiran': malam_line.kehadiran_absen,
                            'keterangan': msg_kamar,
                            'company_id': self.company_id.id,
                        }))
                    else:
                        absensi_ids.append((0, 0, {
                            'siswa_id': siswa.id,
                            'kehadiran': 'Hadir',
                            'company_id': self.company_id.id,
                        }))
            return {'value': {'absensi_ids': absensi_ids}}
        return {}

    @api.onchange('tanggal', 'kelas_id', 'guru_id', 'jampelajaran_id', 'is_guru_pengganti')
    def _onchange_tanggal(self):
        """Mengatur domain dan mapel_id berdasarkan jadwal, tanpa menimpa absensi_ids yang sudah ada."""
        if self.is_guru_pengganti:
            return {
                'domain': {
                    'kelas_id': [],
                    'jampelajaran_id': []
                }
            }
        if self.tanggal and self.guru_id:
            jadwal = self.env['cdn.jadwal_pelajaran_lines'].search([
                ('guru_id', '=', self.guru_id.id),
                ('name', '=', self.hari)
            ])
            if jadwal:
                mapel = False
                if self.hari and self.kelas_id and self.guru_id and self.jampelajaran_id:
                    m = self.env['cdn.jadwal_pelajaran_lines'].search([
                        ('name', '=', self.hari),
                        ('kelas_id', '=', self.kelas_id.id),
                        ('guru_id', '=', self.guru_id.id),
                        ('jampelajaran_id', '=', self.jampelajaran_id.id)
                    ])
                    mapel = m.matapelajaran_id.id if m else False
                return {
                    'domain': {
                        'kelas_id': [('id', 'in', jadwal.mapped('kelas_id').ids)],
                        'jampelajaran_id': [('id', 'in', jadwal.mapped('jampelajaran_id').ids)]
                    },
                    'value': {
                        'mapel_id': mapel,
                    }
                }
        return {}

    @api.onchange('kelas_id', 'tanggal')
    def _onchange_guru_domain(self):
        return {
            'domain': {
                'guru_id': [('jns_pegawai_ids.code', 'in', ['guru'])]
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


class AbsensiSiswaLine(models.Model):
    _name = 'cdn.absensi_siswa_lines'
    _description = 'Data Absensi Siswa Lines'
    _order = 'name asc, id asc'

    absensi_id = fields.Many2one(
        comodel_name='cdn.absensi_siswa', string='Absensi Siswa', ondelete='cascade')
    mapel_id = fields.Many2one(comodel_name='cdn.mata_pelajaran',
                               string='Mata pelajaran', related='absensi_id.mapel_id')
    tanggal = fields.Date(
        string='Tgl Absen', related='absensi_id.tanggal', readonly=True, store=True)
    kelas_id = fields.Many2one(comodel_name='cdn.ruang_kelas', string='Kelas',
                               related='absensi_id.kelas_id', readonly=True, store=True)
    siswa_id = fields.Many2one(
        comodel_name='cdn.siswa',
        string='Siswa',
        required=True,
        domain="[('id', 'in', allowed_siswa_ids)]",
        ondelete='cascade'
    )
    allowed_siswa_ids = fields.Many2many(
        comodel_name='cdn.siswa',
        compute='_compute_allowed_siswa',
        store=False
    )
    name = fields.Char(string='Nama', related='siswa_id.name',
                       readonly=True, store=True)
    nis = fields.Char(string='NIS', related='siswa_id.nis',
                      readonly=True, store=True)
    kehadiran = fields.Selection([
        ('Hadir', 'Hadir'),
        ('Sakit', 'Sakit'),
        ('Izin', 'Izin'),
        ('Alpa', 'Alpa'),
        ('Pulang-Sakit', 'Pulang-Sakit'),
        ('Pulang-Izin', 'Pulang-Izin'),
        ('Pulang-Alpa', 'Pulang-Alpa'),
    ], string='Kehadiran', default='Hadir')

    keterangan_izin = fields.Binary(string='Foto', attachment=True)
    keterangan_izin_filename = fields.Char(string="Nama File Foto")
    keterangan = fields.Char(string='Keterangan')
    panggilan = fields.Char(
        string='Nama Panggilan', related='siswa_id.namapanggilan', readonly=True, store=True)
    guru = fields.Many2one('hr.employee', string="Guru",
                           related='absensi_id.guru_id')
    row_number = fields.Integer(
        string='No', compute='_compute_row_number', store=False)
    company_id = fields.Many2one('res.company', string='Lembaga',
                                 related='absensi_id.company_id', readonly=True, store=True)
    jml_jampelajaran = fields.Integer(
        string='Jumlah JP', related='absensi_id.jml_jampelajaran', store=True, help='Jumlah Jam Pelajaran')

    def _compute_row_number(self):
        for index, record in enumerate(self):
            record.row_number = index + 1

    @api.depends('absensi_id.kelas_id')
    def _compute_allowed_siswa(self):
        for record in self:
            if record.absensi_id.kelas_id:
                siswa_domain = ['|', ('ruang_kelas_id', '=', record.absensi_id.kelas_id.id), ('id', 'in', record.absensi_id.kelas_id.siswa_ids.ids)]
                record.allowed_siswa_ids = self.env['cdn.siswa'].search(siswa_domain).ids
            else:
                record.allowed_siswa_ids = []

    @api.onchange('siswa_id')
    def _onchange_siswa_id(self):
        """Check permission and absen kamar when student is selected"""
        if self.siswa_id and self.tanggal:
            permission = self.env['cdn.perijinan'].search([
                ('siswa_id', '=', self.siswa_id.id),
                ('state', '=', 'Permission')
            ], limit=1)
            if permission:
                self.kehadiran = 'Pulang-Izin'
                keperluan_name = permission.keperluan.name if permission.keperluan else 'Tidak ada keterangan'
                waktu_keluar = self.format_datetime_indonesia(
                    permission.waktu_keluar) if permission.waktu_keluar else 'Tidak tercatat'
                self.keterangan = f"Santri Keluar pada {waktu_keluar}, karena {keperluan_name}"
            else:
                malam_line = self.env['cdn.absensi_malam_line'].sudo().search([
                    ('siswa_id', '=', self.siswa_id.id),
                    ('tanggal', '=', self.tanggal)
                ], limit=1)
                if malam_line and malam_line.kehadiran_absen != 'Hadir':
                    self.kehadiran = malam_line.kehadiran_absen
                    self.keterangan = malam_line.keterangan or f"Absen Kamar ({malam_line.kehadiran_absen})"
                else:
                    self.kehadiran = 'Hadir'
                    self.keterangan = False

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
                    'title': '❌ Tidak Dapat Menemukan Data!',
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


class Kbm_Siswa(models.Model):
    _inherit = 'cdn.siswa'
    _description = 'Kbm_Siswa'
    kbm_id = fields.One2many(
        string='Kegiatan Belajar Mengajar',
        comodel_name='cdn.absensi_siswa_lines',
        inverse_name='siswa_id',
    )
