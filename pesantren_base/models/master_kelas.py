#!/usr/bin/python
#-*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import re

class master_kelas(models.Model):

    _name               = "cdn.master_kelas"
    _description        = "Tabel Data Master Kelas"
    _order              = "tingkat_urutan, jurusan_id, nama_kelas, id"  # Tambahan: urutan berdasarkan tingkat

    name                = fields.Char(required=True, string="Nama Kelas", help="", copy=False, readonly=True)
    jenjang             = fields.Selection(selection=[('paud','PAUD'),('tk','TK/RA'),('sd','SD/MI'),('smp','SMP/MTS'),('sma','SMA/MA'), ('nonformal', 'Nonformal')],  string="Jenjang", required=True, help="")
    tingkat             = fields.Many2one(comodel_name="cdn.tingkat", string="Tingkat", required=True)
    jurusan_id          = fields.Many2one(comodel_name='cdn.master_jurusan', string='Jurusan / Peminatan')
    
    nama_kelas          = fields.Char(string="Nama Kelas", required=False)
    
    # Tambahan: field untuk menyimpan urutan tingkat sebagai integer
    tingkat_urutan      = fields.Integer(
        string="Urutan Tingkat",
        compute='_compute_tingkat_urutan',
        store=True,
        help="Urutan numerik tingkat untuk sorting (1, 2, 3, dst)"
    )
 
    _sql_constraints = [('master_kelas_uniq', 'unique(name)', 'Master Data Kelas harus unik !')]

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
                        tingkat_name = str(record.tingkat.display_name or record.tingkat.id).strip().lower()
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


