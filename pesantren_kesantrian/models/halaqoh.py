from odoo import api, fields, models
from odoo.exceptions import UserError


class Halaqoh(models.Model):
    _name = 'cdn.halaqoh'
    _description = 'Model untuk Pembagian Kelas Halaqoh'

    name = fields.Char(string='Nama Halaqoh', required=True)
    keterangan = fields.Char(string='Keterangan')
    fiscalyear_id = fields.Many2one('cdn.ref_tahunajaran', string='Tahun Ajaran', required=True, default=lambda self: self.env.user.company_id.tahun_ajaran_aktif.id)
    # siswa_ids       = fields.Many2many(
    #     comodel_name='cdn.siswa', 
    #     string='Siswa', 
    #     ondelete='cascade',
    #     domain="[('active', '=', True), '|', ('halaqoh_id', '=', False), ('halaqoh_id', '=', id)]"
    # ) 
    siswa_ids = fields.Many2many(
        'cdn.siswa',
        'cdn_siswa_halaqoh_rel',
        'halaqoh_m2m_id', 'siswa_id',
        string='Siswa'
    )   
    penanggung_jawab_id = fields.Many2one('hr.employee', string='Penanggung jawab', required=True)
    pengganti_ids = fields.Many2many('hr.employee', string='Ustadz Pengganti')
    status          = fields.Selection(string='Status', selection=[('draft', 'Draft'), ('konfirm', 'Terkonfirmasi')], default="draft")
    jml_siswa       = fields.Integer(string='Jumlah Siswa', compute='_compute_jml_siswa', store=True)


    #test
    # def unlink(self):
    #     for siswa in self.siswa_ids:
    #         siswa.halaqoh_id = False
    #     return super(Halaqoh, self).unlink()
    def unlink(self):
        for rec in self:
            for siswa in rec.siswa_ids:
                siswa.halaqoh_ids = [(3, rec.id)]  # hapus relasi M2M
                if siswa.halaqoh_id == rec:
                    siswa.halaqoh_id = False        # reset Many2one jika sama
        return super().unlink()
    # def konfirmasi(self):
    #     for rec in self:
    #         rec.status = 'konfirm'
            
    #         conflicting_students = []
    #         for siswa in rec.siswa_ids:
    #             if siswa.halaqoh_id and siswa.halaqoh_id.id != rec.id and siswa.halaqoh_id.fiscalyear_id == rec.fiscalyear_id:
    #                 conflicting_students.append((siswa.name, siswa.halaqoh_id.name, siswa.kamar_id.fiscalyear_id.name))

    #         #Raise error saat santri yang ditambahkan sudah terdaftar di halaqoh lain
    #         if conflicting_students:
    #             conflict_message = "\n".join(["Siswa atas nama %s Sudah Terdaftar di halaqoh %s pada Tahun Ajaran %s!\n" % (name, halaqoh, tahun) for name, halaqoh, tahun in conflicting_students])
    #             raise UserError("Silakan dihapus dulu data siswa ybs di halaqoh tersebut:\n\n%s" % conflict_message)
            
    #         for siswa in rec.siswa_ids:
    #             siswa.halaqoh_id = rec.id
                
    #         siswa_existing = self.env['cdn.siswa'].search([('halaqoh_id', '=', rec.id)])
    #         for siswa in siswa_existing:
    #             if siswa.id not in rec.siswa_ids.ids:
    #                 siswa.halaqoh_id = False
    def konfirmasi(self):
        for rec in self:
            rec.status = 'konfirm'

            conflicting_students = []
            for siswa in rec.siswa_ids:

                # Cek bentrok tahun ajaran via Many2many
                if rec.fiscalyear_id in siswa.halaqoh_ids.mapped('fiscalyear_id') and rec not in siswa.halaqoh_ids:
                    conflicting_students.append((
                        siswa.name,
                        ', '.join(siswa.halaqoh_ids.mapped('name')),
                        rec.fiscalyear_id.name
                    ))

            # Raise error kalau ada konflik
            if conflicting_students:
                conflict_message = "\n".join([
                    "Siswa %s sudah terdaftar di halaqoh %s pada Tahun Ajaran %s!"
                    % (name, halaqoh, tahun)
                    for name, halaqoh, tahun in conflicting_students
                ])
                raise UserError(
                    "Silakan hapus dulu data siswa yang bersangkutan di halaqoh lain:\n\n%s"
                    % conflict_message
                )

            # Tambahkan siswa ke M2M + set halaqoh utama (Many2one)
            for siswa in rec.siswa_ids:
                siswa.halaqoh_ids = [(4, rec.id)]  # tambahkan ke M2M
                if not siswa.halaqoh_id:
                    siswa.halaqoh_id = rec          # isi halaqoh utama kalau kosong        
    def draft(self):
        for rec in self:
            rec.status = 'draft'
    
    @api.depends('siswa_ids')
    def _compute_jml_siswa(self):
        for record in self:
            record.jml_siswa = len(record.siswa_ids)
            
    # _sql_constraints = [
    #     ('unique_halaqoh_name', 'unique(name)', 'Nama Halaqoh sudah ada!')
    # ]
    @api.constrains('name', 'fiscalyear_id')
    def _check_unique_name_per_tahun(self):
        for rec in self:
            if self.search_count([
                ('name', '=', rec.name),
                ('fiscalyear_id', '=', rec.fiscalyear_id.id),
                ('id', '!=', rec.id)
            ]) > 0:
                raise UserError(
                    "Nama Halaqoh '%s' sudah ada pada Tahun Ajaran %s. "
                    "Silakan gunakan nama lain atau pilih tahun ajaran berbeda."
                    % (rec.name, rec.fiscalyear_id.name)
                )
