from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ruang_kelas(models.Model):
    _name = "cdn.ruang_kelas"
    _description = "Tabel Data Ruang Kelas"

    name = fields.Many2one(
        comodel_name="cdn.master_kelas",  
        string="Rombongan Belajar", 
        required=True, 
        copy=False,
    )
    siswa_ids = fields.Many2many(
        'cdn.siswa', 
        'ruang_kelas_siswa_rel', 
        'ruang_kelas_id', 
        'siswa_id', 
        ondelete='cascade',
        string='Daftar Siswa', 
        domain=[('active', '=', True)]
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
        domain="[('jns_pegawai','=','guru')]"
    )
    jenjang = fields.Selection(
        selection=[('paud','PAUD'),('tk','TK/RA'),('sd','SD/MI'),
                   ('smp','SMP/MTS'),('sma','SMA/MA/SMK'), ('nonformal', 'Nonformal')],
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
    jurusan_id = fields.Many2one(
        comodel_name='cdn.master_jurusan', 
        string='Jurusan / Peminatan', 
        related='name.jurusan_id', 
        store=True,
        readonly=True
    )
    # Ubah readonly menjadi False dan tambahkan store=True
    nama_kelas = fields.Char(string="Nama Kelas", store=True)

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

    keterangan = fields.Char(string="Keterangan")

    _sql_constraints = [
        ('ruang_kelas_uniq', 'unique(name, tahunajaran_id)', 
         'Data Rombongan Belajar dan Tahun Pelajaran harus unik!')
    ]

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

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            self.tingkat = self.name.tingkat.id
            self.jurusan_id = self.name.jurusan_id.id
            self.nama_kelas = self.name.nama_kelas
    
    # Tambahkan method untuk memastikan nama_kelas selalu diisi dari name
    @api.model
    def create(self, vals):
        if vals.get('name'):
            kelas = self.env['cdn.master_kelas'].browse(vals.get('name'))
            if kelas and kelas.nama_kelas:
                vals['nama_kelas'] = kelas.nama_kelas
        return super(ruang_kelas, self).create(vals)
    
    def write(self, vals):
        if vals.get('name'):
            kelas = self.env['cdn.master_kelas'].browse(vals.get('name'))
            if kelas and kelas.nama_kelas:
                vals['nama_kelas'] = kelas.nama_kelas
        result = super(ruang_kelas, self).write(vals)
        return result

    def konfirmasi(self):
        for rec in self:
            # Pastikan nama_kelas diisi dari name jika kosong
            if rec.name and not rec.nama_kelas:
                rec.nama_kelas = rec.name.nama_kelas
                
            rec.status = 'konfirm'

            conflicting_students = [
                (s.name, s.ruang_kelas_id.name.name, s.ruang_kelas_id.tahunajaran_id.name)
                for s in rec.siswa_ids
                if s.ruang_kelas_id and s.ruang_kelas_id.id != rec.id and s.ruang_kelas_id.tahunajaran_id == rec.tahunajaran_id
            ]

            if conflicting_students:
                conflict_message = "\n".join(
                    ["Siswa atas nama %s sudah terdaftar di %s pada Tahun Ajaran %s!" % (name, kelas, tahun)
                     for name, kelas, tahun in conflicting_students]
                )
                raise UserError("Silakan hapus dulu data siswa yang bersangkutan dari kelas lain:\n\n%s" % conflict_message)

            # Set ruang_kelas_id pada siswa
            for siswa in rec.siswa_ids:
                siswa.ruang_kelas_id = rec.id

            # Reset siswa yang sebelumnya ada tapi sekarang tidak
            siswa_existing = self.env['cdn.siswa'].search([('ruang_kelas_id', '=', rec.id)])
            for siswa in siswa_existing:
                if siswa.id not in rec.siswa_ids.ids:
                    siswa.ruang_kelas_id = False

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

    def draft(self):
        for rec in self:
            rec.status = 'draft'

    @api.depends('siswa_ids')
    def _compute_jml_siswa(self):
        for record in self:
            record.jml_siswa = len(record.siswa_ids)

class MessageWizard(models.TransientModel):
    _name = 'message.wizard'

    message = fields.Text('Informasi', required=True)

    def action_ok(self):
        """ close wizard"""
        return {'type': 'ir.actions.act_window_close'}













# #!/usr/bin/python
# #-*- coding: utf-8 -*-

# from odoo import models, fields, api, _
# from odoo.exceptions import UserError

# class ruang_kelas(models.Model):

#     _name               = "cdn.ruang_kelas"
#     _description        = "Tabel Data Ruang Kelas"

#     name                = fields.Many2one(comodel_name="cdn.master_kelas",  string="Rombongan Belajar", required=True, copy=False, help="")
#     siswa_ids           = fields.Many2many('cdn.siswa','ruang_kelas_siswa_rel','ruang_kelas_id','siswa_id', string='Daftar Siswa', domain=[('active', '=', True)])
#     tahunajaran_id      = fields.Many2one(comodel_name="cdn.ref_tahunajaran",  string="Tahun Pelajaran", required=True, help="Tahun ajaran aktif saat ini" , default=lambda self: self.env.user.company_id.tahun_ajaran_aktif.id)
#     walikelas_id        = fields.Many2one(comodel_name="hr.employee",  string="Wali Kelas",  help="", domain="[('jns_pegawai','=','guru')]")
#     jenjang             = fields.Selection(selection=[('paud','PAUD'),('tk','TK/RA'),('sd','SD/MI'),('smp','SMP/MTS'),('sma','SMA/MA/SMK'), ('nonformal', 'Nonformal')],  string="Jenjang", related='name.jenjang', help="")
#     tingkat             = fields.Many2one(comodel_name="cdn.tingkat",  string="Tingkat", related='name.tingkat', help="")
#     jurusan_id          = fields.Many2one(comodel_name='cdn.master_jurusan', string='Jurusan / Peminatan', related='name.jurusan_id')
#     status              = fields.Selection(string='Status', selection=[('draft', 'Draft'), ('konfirm', 'Terkonfirmasi')], default="draft")
#     jml_siswa       = fields.Integer(string='Jumlah Siswa', compute='_compute_jml_siswa', store=True)
#     # ruang_kelas_lines   = fields.One2many(comodel_name='cdn.ruang_kelas_lines', inverse_name='ruang_kelas_id', string='')
    
#     aktif_tidak         = fields.Selection(selection=[
#         ('aktif', 'Aktif'),
#         ('tidak', 'Tidak Aktif'),
#     ], string="Aktif/Tidak", required=True, default='aktif', )
     

#     keterangan          = fields.Char( string="Keterangan",  help="")

#     _sql_constraints = [('ruang_kelas_uniq', 'unique(name, tahunajaran_id)', 'Data Rombongan Belajar dan Tahun Pelajaran harus unik !')]
    
    
#     def konfirmasi(self):
#         for rec in self:
#             rec.status = 'konfirm'
            
#             conflicting_students = []
#             for siswa in rec.siswa_ids:
#                 if siswa.ruang_kelas_id and siswa.ruang_kelas_id.id != rec.id and siswa.ruang_kelas_id.tahunajaran_id == rec.tahunajaran_id:
#                     conflicting_students.append((siswa.name, siswa.ruang_kelas_id.name.name, siswa.ruang_kelas_id.tahunajaran_id.name))

#             #Raise error saat santri yang ditambahkan sudah terdaftar di kelas lain
#             if conflicting_students:
#                 conflict_message = "\n".join(["Siswa atas nama %s Sudah Terdaftar di %s pada Tahun Ajaran %s!\n" % (name, kelas, tahun) for name, kelas, tahun in conflicting_students])
#                 raise UserError("Silakan dihapus dulu data siswa ybs di tersebut:\n\n%s" % conflict_message)
            
#             #buat field ruang_kelas_id jadi rec.id
#             for siswa in rec.siswa_ids:
#                 siswa.ruang_kelas_id = rec.id
                
#             siswa_existing = self.env['cdn.siswa'].search([('ruang_kelas_id', '=', rec.id)])
#             for siswa in siswa_existing:
#                 if siswa.id not in rec.siswa_ids.ids:
#                     siswa.ruang_kelas_id = False
                    
#             message_id = self.env['message.wizard'].create({'message': _("Update Ruang Kelas Siswa - SUKSES !!")})
#             return {
#                 'name': _('Successfull'),
#                 'type': 'ir.actions.act_window',
#                 'view_mode': 'form',
#                 'res_model': 'message.wizard',
#                 # pass the id
#                 'res_id': message_id.id,
#                 'target': 'new'
#             }
    
#     def draft(self):
#         for rec in self:
#             rec.status = 'draft'
    
#     @api.depends('siswa_ids')
#     def _compute_jml_siswa(self):
#         for record in self:
#             record.jml_siswa = len(record.siswa_ids)

# class MessageWizard(models.TransientModel):
#     _name = 'message.wizard'

#     message = fields.Text('Informasi', required=True)

#     def action_ok(self):
#         """ close wizard"""
#         return {'type': 'ir.actions.act_window_close'}
    
    
# from odoo import models, fields, api, _
# from odoo.exceptions import UserError

# class ruang_kelas(models.Model):
#     _name = "cdn.ruang_kelas"
#     _description = "Tabel Data Ruang Kelas"

#     name = fields.Many2one(
#         comodel_name="cdn.master_kelas",  
#         string="Rombongan Belajar", 
#         required=True, 
#         copy=False,
#     )
#     siswa_ids = fields.Many2many(
#         'cdn.siswa', 
#         'ruang_kelas_siswa_rel', 
#         'ruang_kelas_id', 
#         'siswa_id', 
#         ondelete='cascade',
#         string='Daftar Siswa', 
#         domain=[('active', '=', True)]
#     )
#     tahunajaran_id = fields.Many2one(
#         comodel_name="cdn.ref_tahunajaran",  
#         string="Tahun Pelajaran", 
#         required=True, 
#         default=lambda self: self.env.user.company_id.tahun_ajaran_aktif.id
#     )
#     walikelas_id = fields.Many2one(
#         comodel_name="hr.employee",  
#         string="Wali Kelas",  
#         domain="[('jns_pegawai','=','guru')]"
#     )
#     jenjang = fields.Selection(
#         selection=[('paud','PAUD'),('tk','TK/RA'),('sd','SD/MI'),
#                    ('smp','SMP/MTS'),('sma','SMA/MA/SMK'), ('nonformal', 'Nonformal')],
#         string="Jenjang", 
#         related='name.jenjang', 
#         store=True,
#         readonly=True
#     )
#     tingkat = fields.Many2one(
#         comodel_name="cdn.tingkat",  
#         string="Tingkat", 
#         related='name.tingkat', 
#         store=True,
#         readonly=True
#     )
#     jurusan_id = fields.Many2one(
#         comodel_name='cdn.master_jurusan', 
#         string='Jurusan / Peminatan', 
#         related='name.jurusan_id', 
#         store=True,
#         readonly=True
#     )
#     nama_kelas = fields.Char(string="Nama Kelas", readonly=True)

#     status = fields.Selection(
#         string='Status', 
#         selection=[('draft', 'Draft'), ('konfirm', 'Terkonfirmasi')], 
#         default="draft"
#     )
#     jml_siswa = fields.Integer(
#         string='Jumlah Siswa', 
#         compute='_compute_jml_siswa', 
#         store=True
#     )

#     aktif_tidak = fields.Selection([
#         ('aktif', 'Aktif'),
#         ('tidak', 'Tidak Aktif'),
#     ], string="Aktif/Tidak", required=True, default='aktif')

#     keterangan = fields.Char(string="Keterangan")

#     _sql_constraints = [
#         ('ruang_kelas_uniq', 'unique(name, tahunajaran_id)', 
#          'Data Rombongan Belajar dan Tahun Pelajaran harus unik!')
#     ]

#     @api.onchange('tingkat', 'jurusan_id', 'nama_kelas')
#     def _onchange_tingkat_jurusan_nama(self):
#         domain = []

#         # Filter berdasarkan tingkat
#         if self.tingkat:
#             domain.append(('tingkat', '=', self.tingkat.id))

#         # Filter jurusan hanya jika jenjang SMA
#         if self.jenjang == 'sma' and self.jurusan_id:
#             domain.append(('jurusan_id', '=', self.jurusan_id.id))

#         # Jika nama_kelas diisi, cari yang sesuai
#         if self.nama_kelas:
#             domain.append(('nama_kelas', 'ilike', self.nama_kelas.strip()))
#         else:
#             # Jika tidak ada nama_kelas, hanya ambil yang nama_kelas-nya kosong/null
#             domain.append(('nama_kelas', '=', ""))

#         # Jalankan pencarian berdasarkan domain
#         if domain:
#             kelas = self.env['cdn.master_kelas'].search(domain, limit=1)
#             self.name = kelas.id if kelas else False
#             return {'domain': {'name': domain}}
#         else:
#             self.name = False
#             return {}




#     @api.onchange('name')
#     def onchange_name(self):
#         if self.name:
#             self.tingkat = self.name.tingkat.id
#             self.jurusan_id = self.name.jurusan_id.id
#             self.nama_kelas = self.name.nama_kelas

#     def konfirmasi(self):
#         for rec in self:
#             rec.status = 'konfirm'

#             conflicting_students = [
#                 (s.name, s.ruang_kelas_id.name.name, s.ruang_kelas_id.tahunajaran_id.name)
#                 for s in rec.siswa_ids
#                 if s.ruang_kelas_id and s.ruang_kelas_id.id != rec.id and s.ruang_kelas_id.tahunajaran_id == rec.tahunajaran_id
#             ]

#             if conflicting_students:
#                 conflict_message = "\n".join(
#                     ["Siswa atas nama %s sudah terdaftar di %s pada Tahun Ajaran %s!" % (name, kelas, tahun)
#                      for name, kelas, tahun in conflicting_students]
#                 )
#                 raise UserError("Silakan hapus dulu data siswa yang bersangkutan dari kelas lain:\n\n%s" % conflict_message)

#             # Set ruang_kelas_id pada siswa
#             for siswa in rec.siswa_ids:
#                 siswa.ruang_kelas_id = rec.id

#             # Reset siswa yang sebelumnya ada tapi sekarang tidak
#             siswa_existing = self.env['cdn.siswa'].search([('ruang_kelas_id', '=', rec.id)])
#             for siswa in siswa_existing:
#                 if siswa.id not in rec.siswa_ids.ids:
#                     siswa.ruang_kelas_id = False

#             message_id = self.env['message.wizard'].create({
#                 'message': _("Update Ruang Kelas Siswa - SUKSES !!")
#             })
#             return {
#                 'name': _('Berhasil'),
#                 'type': 'ir.actions.act_window',
#                 'view_mode': 'form',
#                 'res_model': 'message.wizard',
#                 'res_id': message_id.id,
#                 'target': 'new'
#             }

#     def draft(self):
#         for rec in self:
#             rec.status = 'draft'

#     @api.depends('siswa_ids')
#     def _compute_jml_siswa(self):
#         for record in self:
#             record.jml_siswa = len(record.siswa_ids)
    
    
    
# #!/usr/bin/python
# #-*- coding: utf-8 -*-

# from odoo import models, fields, api, _
# from odoo.exceptions import UserError

# class ruang_kelas(models.Model):

#     _name               = "cdn.ruang_kelas"
#     _description        = "Tabel Data Ruang Kelas"

#     name                = fields.Many2one(comodel_name="cdn.master_kelas",  string="Rombongan Belajar", required=True, copy=False, help="")
#     siswa_ids           = fields.Many2many('cdn.siswa','ruang_kelas_siswa_rel','ruang_kelas_id','siswa_id', string='Daftar Siswa', domain=[('active', '=', True)])
#     tahunajaran_id      = fields.Many2one(comodel_name="cdn.ref_tahunajaran",  string="Tahun Pelajaran", required=True, help="Tahun ajaran aktif saat ini" , default=lambda self: self.env.user.company_id.tahun_ajaran_aktif.id)
#     walikelas_id        = fields.Many2one(comodel_name="hr.employee",  string="Wali Kelas",  help="", domain="[('jns_pegawai','=','guru')]")
#     jenjang             = fields.Selection(selection=[('paud','PAUD'),('tk','TK/RA'),('sd','SD/MI'),('smp','SMP/MTS'),('sma','SMA/MA/SMK'), ('nonformal', 'Nonformal')],  string="Jenjang", related='name.jenjang', help="")
#     tingkat             = fields.Many2one(comodel_name="cdn.tingkat",  string="Tingkat", related='name.tingkat', help="")
#     jurusan_id          = fields.Many2one(comodel_name='cdn.master_jurusan', string='Jurusan / Peminatan', related='name.jurusan_id')
#     status              = fields.Selection(string='Status', selection=[('draft', 'Draft'), ('konfirm', 'Terkonfirmasi')], default="draft")
#     jml_siswa           = fields.Integer(string='Jumlah Siswa', compute='_compute_jml_siswa', store=True)
#     # ruang_kelas_lines   = fields.One2many(comodel_name='cdn.ruang_kelas_lines', inverse_name='ruang_kelas_id', string='')
    
#     nama_kelas          = fields.Char( string="Nama Kelas")
    
#     aktif_tidak         = fields.Selection(selection=[
#         ('aktif', 'Aktif'),
#         ('tidak', 'Tidak Aktif'),
#     ], string="Aktif/Tidak", required=True, default='aktif', )

#     keterangan          = fields.Char( string="Keterangan",  help="")

#     _sql_constraints = [('ruang_kelas_uniq', 'unique(name, tahunajaran_id)', 'Data Rombongan Belajar dan Tahun Pelajaran harus unik !')]
     
#     @api.onchange('tingkat', 'jurusan_id', 'nama_kelas')
#     def _onchange_tingkat_jurusan_nama(self):
#         domain = []
        
#         if self.tingkat:
#             domain.append(('tingkat', '=', self.tingkat.id))
        
#         if self.jurusan_id:
#             domain.append(('jurusan_id', '=', self.jurusan_id.id))
        
#         if self.nama_kelas:
#             domain.append(('nama_kelas', 'ilike', self.nama_kelas.strip()))
        
#         if domain:
#             kelas = self.env['cdn.master_kelas'].search(domain, limit=1)
#             self.name = kelas.id if kelas else False
#             return {'domain': {'name': domain}}
#         else:
#             self.name = False
#             return {}

    
    
#     # @api.onchange('tingkat', 'jurusan_id')
#     # def onchange_tingkat(self):
       
#     #     if self.tingkat:
#     #         # Create domain with tingkat ID
#     #         domain = [('tingkat', '=', self.tingkat.id)]
            
#     #         # Add jurusan filter if it's set
#     #         if self.jurusan_id:
#     #             domain.append(('jurusan_id', '=', self.jurusan_id.id))
            
#     #         # Search for matching kelas
#     #         kelas = self.env['cdn.master_kelas'].search(domain, limit=1)
            
#     #         if kelas:
#     #             self.name = kelas.id
#     #         else:
#     #             self.name = False
                
#     #         # Return domain to limit dropdown options in the UI
#     #         return {'domain': {'name': domain}}
            
    
#     # @api.onchange('tingkat', 'jurusan_id')
#     # def onchange_tingkat(self):
#     #     """
#     #     Fungsi ini akan mengisi field name secara otomatis ketika field tingkat diisi
#     #     """
#     #     if self.tingkat:
#     #         domain = [('tingkat', '=', self.tingkat.id)]
            
#     #         if self.jurusan_id:
#     #             domain.append(('jurusan_id', '=', self.jurusan_id.id))
            
#     #         kelas = self.env['cdn.master_kelas'].search(domain)
            
#     #         if kelas:
#     #             # Jika hanya ada satu kelas yang sesuai, langsung pilih kelas tersebut
#     #             if len(kelas) == 1:
#     #                 self.name = kelas.id
#     #             # Jika ada lebih dari satu kelas, tampilkan domain untuk pilihan
#     #             else:
#     #                 return {'domain': {'name': domain}}
#     #         else:
#     #             # Jika tidak ada kelas yang sesuai, kosongkan field name dan berikan peringatan
#     #             self.name = False
#     #             return {'warning': {'title': 'Peringatan', 'message': 'Tidak ditemukan kelas dengan tingkat dan jurusan yang dipilih!'}}
    
#     @api.onchange('name')
#     def onchange_name(self):
#         """
#         Fungsi ini akan mengupdate field tingkat dan jurusan_id jika name dipilih langsung
#         """
#         if self.name:
#             self.tingkat = self.name.tingkat.id
#             self.jurusan_id = self.name.jurusan_id.id
#             self.nama_kelas = self.name.nama_kelas
            
    
#     def konfirmasi(self):
#         for rec in self:
#             rec.status = 'konfirm'
            
#             conflicting_students = []
#             for siswa in rec.siswa_ids:
#                 if siswa.ruang_kelas_id and siswa.ruang_kelas_id.id != rec.id and siswa.ruang_kelas_id.tahunajaran_id == rec.tahunajaran_id:
#                     conflicting_students.append((siswa.name, siswa.ruang_kelas_id.name.name, siswa.ruang_kelas_id.tahunajaran_id.name))

#             #Raise error saat santri yang ditambahkan sudah terdaftar di kelas lain
#             if conflicting_students:
#                 conflict_message = "\n".join(["Siswa atas nama %s Sudah Terdaftar di %s pada Tahun Ajaran %s!\n" % (name, kelas, tahun) for name, kelas, tahun in conflicting_students])
#                 raise UserError("Silakan dihapus dulu data siswa ybs di tersebut:\n\n%s" % conflict_message)
            
#             #buat field ruang_kelas_id jadi rec.id
#             for siswa in rec.siswa_ids:
#                 siswa.ruang_kelas_id = rec.id
                
#             siswa_existing = self.env['cdn.siswa'].search([('ruang_kelas_id', '=', rec.id)])
#             for siswa in siswa_existing:
#                 if siswa.id not in rec.siswa_ids.ids:
#                     siswa.ruang_kelas_id = False
                    
#             message_id = self.env['message.wizard'].create({'message': _("Update Ruang Kelas Siswa - SUKSES !!")})
#             return {
#                 'name': _('Successfull'),
#                 'type': 'ir.actions.act_window',
#                 'view_mode': 'form',
#                 'res_model': 'message.wizard',
#                 # pass the id
#                 'res_id': message_id.id,
#                 'target': 'new'
#             }
    
#     def draft(self):
#         for rec in self:
#             rec.status = 'draft'
    
#     @api.depends('siswa_ids')
#     def _compute_jml_siswa(self):
#         for record in self:
#             record.jml_siswa = len(record.siswa_ids)

class MessageWizard(models.TransientModel):
    _name = 'message.wizard'

    message = fields.Text('Informasi', required=True)

    def action_ok(self):
        """ close wizard"""
        return {'type': 'ir.actions.act_window_close'}