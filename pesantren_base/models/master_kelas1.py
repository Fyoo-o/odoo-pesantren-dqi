# #!/usr/bin/python
# #-*- coding: utf-8 -*-

# from odoo import models, fields, api, _
# from odoo.exceptions import UserError
# import re

# class master_kelas(models.Model):

#     _name               = "cdn.master_kelas"
#     _description        = "Tabel Data Master Kelas"

#     name                = fields.Char(required=True, string="Nama Kelas",  help="",  copy=False)
#     jenjang             = fields.Selection(selection=[('paud','PAUD'),('tk','TK/RA'),('sd','SD/MI'),('smp','SMP/MTS'),('sma','SMA/MA'), ('nonformal', 'Nonformal')],  string="Jenjang", required=True, help="")
#     tingkat             = fields.Many2one(comodel_name="cdn.tingkat", string="Tingkat", required=True)
#     jurusan_id          = fields.Many2one(comodel_name='cdn.master_jurusan', string='Jurusan / Peminatan')
    
#     nama_kelas          = fields.Char(string="Nama Rombongan", required=True)
 
#     _sql_constraints = [('master_kelas_uniq', 'unique(name)', 'Master Data Kelas harus unik !')]

#     def _convert_to_roman(self, number):
#         roman =[(1000, 'M'),(900, 'CM'),(500, 'D'),(400, 'CD'),(100, 'C'),(90, 'XC'),(50, 'L'),(40, 'XL'),(10, 'X'),(9, 'IX'),(5, 'V'),(4, 'IV'),(1, 'I')]
#         result = ''
#         for value, letter in roman:
#             while number >= value:
#                 result += letter
#                 number -= value
#         return result

#     @api.onchange('tingkat','jurusan_id')
#     def onchange_tingkat(self):
#         suffix = re.search(r'-[a-zA-Z]{1}$', self.name) if self.name else False
#         name = ''
#         if self.tingkat and self.jurusan_id:
#             name = '%s-%s-' % (self._convert_to_roman(int(self.tingkat)), self.jurusan_id.name)
#         elif self.tingkat:
#             name = '%s-' % (self._convert_to_roman(int(self.tingkat)))
#         if suffix:
#             name += suffix.group(0)[1:].upper()
#         return {'value': {'name': name}}
        


# class master_jurusan(models.Model):
#     _name               = 'cdn.master_jurusan'
#     _description        = 'Tabel Master Data Jurusan SMA'

#     name                = fields.Char(string='Nama Bidang/Jurusan', required=True, copy=False)
#     active              = fields.Boolean(string='Aktif', default=True)
#     keterangan          = fields.Char(string='Keterangan')

#     _sql_constraints    = [('master_jurusan_uniq', 'unique(name)', 'Master Jurusan/Bidang Study harus unik !')]
    
    

#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import re

class master_kelas(models.Model):

    _name               = "cdn.master_kelas"
    _description        = "Tabel Data Master Kelas"

    name                = fields.Char(required=True, string="Nama Kelas", help="", copy=False, readonly=True)
    jenjang             = fields.Selection(selection=[('paud','PAUD'),('tk','TK/RA'),('sd','SD/MI'),('smp','SMP/MTS'),('sma','SMA/MA'), ('nonformal', 'Nonformal')],  string="Jenjang", required=True, help="")
    tingkat             = fields.Many2one(comodel_name="cdn.tingkat", string="Tingkat", required=True)
    jurusan_id          = fields.Many2one(comodel_name='cdn.master_jurusan', string='Jurusan / Peminatan')
    
    nama_kelas          = fields.Char(string="Nama Kelas", required=False)
 
    _sql_constraints = [('master_kelas_uniq', 'unique(name)', 'Master Data Kelas harus unik !')]

    def _convert_to_roman(self, number):
        roman =[(1000, 'M'),(900, 'CM'),(500, 'D'),(400, 'CD'),(100, 'C'),(90, 'XC'),(50, 'L'),(40, 'XL'),(10, 'X'),(9, 'IX'),(5, 'V'),(4, 'IV'),(1, 'I')]
        result = ''
        for value, letter in roman:
            while number >= value:
                result += letter
                number -= value
        return result

    @api.onchange('tingkat', 'jurusan_id', 'nama_kelas')
    def onchange_tingkat_nama_kelas(self):
        """
        Fungsi ini akan memperbarui field name berdasarkan tingkat, jurusan, dan nama_kelas
        Format: [Tingkat (Roman)]-[Jurusan (jika ada)]-[Nama Kelas]
        """
        if self.tingkat:
            # Dapatkan tingkat dalam angka romawi
            tingkat_romawi = self._convert_to_roman(int(self.tingkat.name))
            
            # Buat format nama kelas
            if self.jurusan_id and self.nama_kelas:
                # Format dengan jurusan dan nama kelas
                self.name = f"{tingkat_romawi} - {self.jurusan_id.name} - {self.nama_kelas}"
            elif self.jurusan_id:
                # Format dengan jurusan saja
                self.name = f"{tingkat_romawi} - {self.jurusan_id.name}"
            elif self.nama_kelas:
                # Format dengan nama kelas saja
                self.name = f"{tingkat_romawi} - {self.nama_kelas}"
            else:
                # Format dengan tingkat saja
                self.name = f"{tingkat_romawi}"

    @api.model
    def create(self, vals):
        """
        Override create method untuk memastikan name terbentuk dengan benar saat record dibuat
        """
        if 'tingkat' in vals and ('name' not in vals or not vals['name']):
            tingkat = self.env['cdn.tingkat'].browse(vals['tingkat'])
            tingkat_romawi = self._convert_to_roman(int(tingkat.name))

            jurusan_name = ''
            nama_kelas = ''

            if 'jurusan_id' in vals and vals['jurusan_id']:
                jurusan = self.env['cdn.master_jurusan'].browse(vals['jurusan_id'])
                jurusan_name = jurusan.name

            if 'nama_kelas' in vals and vals['nama_kelas']:
                nama_kelas = vals['nama_kelas']

            # Susun berdasarkan ketersediaan field
            name_parts = [tingkat_romawi]
            if jurusan_name:
                name_parts.append(jurusan_name)
            if nama_kelas:
                name_parts.append(nama_kelas)

            vals['name'] = " - ".join(name_parts)

        return super(master_kelas, self).create(vals)



    # @api.model
    # def create(self, vals):
    #     """
    #     Override create method untuk memastikan name terbentuk dengan benar saat record dibuat
    #     """
    #     # Jika tingkat dan nama_kelas disediakan tapi name tidak
    #     if ('tingkat' in vals and 'nama_kelas' in vals) and ('name' not in vals or not vals['name']):
    #         tingkat = self.env['cdn.tingkat'].browse(vals['tingkat'])
    #         tingkat_romawi = self._convert_to_roman(int(tingkat.name))
            
    #         if 'jurusan_id' in vals and vals['jurusan_id']:
    #             jurusan = self.env['cdn.master_jurusan'].browse(vals['jurusan_id'])
    #             vals['name'] = f"{tingkat_romawi} - {jurusan.name} - {vals['nama_kelas']}"
    #         else:
    #             vals['name'] = f"{tingkat_romawi} - {vals['nama_kelas']}"
                
    #     return super(master_kelas, self).create(vals)

    def write(self, vals):
        """
        Override write method untuk memastikan name diperbarui saat field lain diubah
        """
        res = super(master_kelas, self).write(vals)
        
        # Jika tingkat, jurusan_id, atau nama_kelas diubah, perbarui name
        if 'tingkat' in vals or 'jurusan_id' in vals or 'nama_kelas' in vals:
            for record in self:
                tingkat_romawi = self._convert_to_roman(int(record.tingkat.name))
                
                if record.jurusan_id and record.nama_kelas:
                    name = f"{tingkat_romawi} - {record.jurusan_id.name} - {record.nama_kelas}"
                elif record.jurusan_id:
                    name = f"{tingkat_romawi} - {record.jurusan_id.name}"
                elif record.nama_kelas:
                    name = f"{tingkat_romawi} - {record.nama_kelas}"
                else:
                    name = f"{tingkat_romawi}"
                
                # Perbarui name tanpa memicu rekursi
                if name != record.name:
                    record.with_context(no_name_update=True).write({'name': name})
                    
        return res
    
class master_jurusan(models.Model):
    _name               = 'cdn.master_jurusan'
    _description        = 'Tabel Master Data Jurusan SMA'

    # name                = fields.Char(string='Nama Bidang/Jurusan', required=True, copy=False)
    name                = fields.Char(string='Nama Bidang/Jurusan', required=True, )

    active              = fields.Boolean(string='Aktif', default=True)
    keterangan          = fields.Char(string='Keterangan')

    # _sql_constraints    = [('master_jurusan_uniq', 'unique(name)', 'Master Jurusan/Bidang Study harus unik !')]