from odoo import api, fields, models


class PenilaianAkhirGuru(models.Model):
    _name = 'cdn.penilaian_akhir_guru'
    _description = 'Penilaian Akhir Guru'
    _rec_name = 'guru_id'
    _sql_constraints = [
        ('penilaian_akhir_guru_uniq', 'unique(tahunajaran_id, semester, kelas_id, mapel_id)', 'Penilaian Akhir Guru sudah ada!')
    ]

    # Default Methods
    def _get_default_guru(self):
        emp = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        if not emp:
            emp = self.env['hr.employee'].search([('jns_pegawai', '=', 'guru')], limit=1)
        return emp.id if emp else False

    def _get_default_semester(self):
        tahun_ajaran = self.env.user.company_id.tahun_ajaran_aktif
        if not tahun_ajaran or not tahun_ajaran.term_akademik_ids:
            return False
        today = fields.Date.today()
        for term in tahun_ajaran.term_akademik_ids:
            if term.term_start_date <= today <= term.term_end_date:
                return term.name.split(' ')[1]
        return '1'  # fallback ke semester 1

    # Domain Methods
    def _get_domain_guru(self):
        user = self.env.user
        if user.has_group('pesantren_guru.group_guru_manager'):
            return [('jns_pegawai', '=', 'guru')]
        elif user.has_group('pesantren_guru.group_guru_staff'):
            employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
            return ['|', ('id', '=', employee.id), ('jns_pegawai', '=', 'guru')]
        return [('id', '=', False)]

    def _get_domain_kelas(self):
        guru = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        if not guru:
            return []
        kelas_ids = self.env['cdn.jadwal_pelajaran_lines'].search([
            ('guru_id', '=', guru.id)
        ]).mapped('kelas_id').ids
        return [('id', 'in', kelas_ids)]

    # Fields
    guru_id = fields.Many2one(
        'hr.employee',
        string='Guru',
        required=True,
        domain=_get_domain_guru,
        default=_get_default_guru
    )
    kelas_id = fields.Many2one(
        'cdn.ruang_kelas',
        string='Kelas',
        required=True,
        domain=_get_domain_kelas
    )
    tahunajaran_id = fields.Many2one(
        'cdn.ref_tahunajaran',
        string='Tahun Ajaran',
        required=True,
        default=lambda self: self.env.user.company_id.tahun_ajaran_aktif.id
    )
    semester = fields.Selection(
        string='Semester',
        selection=[
            ('1', 'Semester 1'),
            ('2', 'Semester 2'),
        ],
        required=True,
        default=_get_default_semester
    )
    mapel_id = fields.Many2one(
        'cdn.mata_pelajaran',
        string='Mata Pelajaran',
        required=True
    )
    state = fields.Selection(
        string='Status',
        selection=[
            ('draft', 'Draft'),
            ('confirm', 'Confirm'),
        ],
        default='draft'
    )
    penilaian_ids = fields.One2many(
        'cdn.penilaian_akhir_lines',
        inverse_name='penilaianguru_id',
        string='Penilaian Siswa'
    )

    # Actions
    def act_confirm(self):
        self.state = 'confirm'
        for nilai in self.penilaian_ids:
            penilaianakhir_id = self.env['cdn.penilaian_akhir'].search([
                ('siswa_id', '=', nilai.siswa_id.id),
                ('tahunajaran_id', '=', self.tahunajaran_id.id),
                ('semester', '=', self.semester)
            ])
            if penilaianakhir_id:
                nilai.penilaianakhir_id = penilaianakhir_id.id

    def act_draft(self):
        self.state = 'draft'


    @api.onchange('guru_id')
    def _onchange_guru_id(self):
        if self.guru_id:
            kelas_ids = self.env['cdn.jadwal_pelajaran_lines'].search([
                ('guru_id', '=', self.guru_id.id)
            ]).mapped('kelas_id').ids
            return {
                'domain': {'kelas_id': [('id', 'in', kelas_ids)]},
                'value': {'kelas_id': False, 'mapel_id': False}  # Reset kelas & mapel
            }
        return {
            'domain': {'kelas_id': [], 'mapel_id': []},
            'value': {'kelas_id': False, 'mapel_id': False}
        }

    @api.onchange('guru_id', 'kelas_id')
    def _onchange_guru_kelas(self):
        if self.guru_id and self.kelas_id:
            # Cari jadwal yang sesuai
            jadwal_lines = self.env['cdn.jadwal_pelajaran_lines'].search([
                ('guru_id', '=', self.guru_id.id),
                ('kelas_id', '=', self.kelas_id.id)
            ])
            mapel_ids = jadwal_lines.mapped('matapelajaran_id').ids
            return {
                'domain': {'mapel_id': [('id', 'in', mapel_ids)]},
                'value': {'mapel_id': False}  # Reset jika sebelumnya pilih mapel lain
            }
        else:
            return {
                'domain': {'mapel_id': [('id', 'in', [])]},  # Kosongkan jika belum lengkap
                'value': {'mapel_id': False}
            }

    # Default Get
    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if not self.env.user.company_id.tahun_ajaran_aktif:
            raise models.ValidationError("Tahun ajaran aktif belum diatur di pengaturan perusahaan.")
        return defaults