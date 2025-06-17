from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

class KenaikanKelasLine(models.Model):
    _name = 'cdn.kenaikan_kelas.line'
    _description = 'Detail santri dalam proses kenaikan kelas'

    kenaikan_id = fields.Many2one('cdn.kenaikan_kelas', string='Header')
    siswa_id = fields.Many2one('cdn.siswa', string='Santri')
    nis = fields.Char(related='siswa_id.nis', string='NIS', store=False)
    kelas_sekarang_id = fields.Many2one(related='siswa_id.ruang_kelas_id', string='Kelas Sekarang', store=False)
    next_class_id = fields.Many2one('cdn.master_kelas', string='Kelas Selanjutnya')


class KenaikanKelas(models.Model):
    _name           = 'cdn.kenaikan_kelas'
    _description    = 'Menu POP UP untuk mengatur kenaikan kelas dan kelas yang lulus'
    _rec_name       = 'tahunajaran_id'

    # def _default_tahunajaran(self):
    #    return self.env['res.company'].search([('id','=',1)]).tahun_ajaran_aktif

    jenjang             = fields.Selection(
        selection=[('paud', 'PAUD'), ('tk', 'TK/RA'), ('sd', 'SD/MI'),
                   ('smp', 'SMP/MTS'), ('sma', 'SMA/MA/SMK'), ('nonformal', 'Nonformal')],
        string="Jenjang", 
        store=True, 
        related='kelas_id.jenjang', 
    )
    
    # tahunajaran_id      = fields.Many2one(comodel_name="cdn.ref_tahunajaran", string="Tahun Ajaran", default=_default_tahunajaran, readonly=False, store=True)

    tahunajaran_id      = fields.Many2one(comodel_name="cdn.ref_tahunajaran", string="Tahun Ajaran", readonly=False, store=True)
    kelas_id            = fields.Many2one('cdn.ruang_kelas', string='Kelas', domain="[('tahunajaran_id','=',tahunajaran_id), ('aktif_tidak','=','aktif'), ('status','=','konfirm')]")
    partner_ids         = fields.Many2many('cdn.siswa', 'kenaikan_santri_rel', 'kenaikan_id', 'santri_id', 'Santri')
    
    tingkat_id          = fields.Many2one('cdn.tingkat', string="Tingkat", store=True, readonly=False)    

    walikelas_id = fields.Many2one(
        comodel_name="hr.employee",  
        string="Wali Kelas",  
        domain="[('jns_pegawai','=','guru')]"
    )
    
    status = fields.Selection(
        selection=[('naik', 'Naik Kelas'), ('tidak_naik', 'Tidak Naik'), ('lulus', 'Lulus'), ('tidak_lulus', 'Tidak Lulus'), ],
        string="Status",
    )

    # Field baru untuk menampilkan kelas selanjutnya
    next_class = fields.Many2one(
        comodel_name='cdn.master_kelas',
        string='Kelas Selanjutnya',
        compute='_compute_next_class',
        store=True,
        help="Kelas selanjutnya berdasarkan tingkat, nama kelas, dan jurusan"
    )
    
    # Field untuk menampilkan hasil proses
    message_result = fields.Text(string="Hasil Proses", readonly=True)
        
    angkatan_id = fields.Many2one(related="kelas_id.angkatan_id", string="Angkatan", readoly=True)    
    
    partner_lines = fields.One2many('cdn.kenaikan_kelas.line', 'kenaikan_id', string='Santri')
    
    filtered_santri_ids = fields.Many2many(
        'cdn.siswa',
        'kenaikan_filtered_santri_rel',
        'kenaikan_id',
        'santri_id',
        string='Santri',
        domain="[('ruang_kelas_id', '=', kelas_id)]",
        help="Hanya menampilkan santri yang berada di kelas yang dipilih"
    )
    
    # Tambahkan field ini setelah field tahunajaran_id
    next_tahunajaran_id = fields.Many2one(
        comodel_name="cdn.ref_tahunajaran",
        string="Tahun Ajaran Berikutnya",
        compute='_compute_next_tahunajaran',
        store=True,
        readonly=True,
        help="Tahun ajaran berikutnya yang akan digunakan untuk kenaikan kelas"
    )

    # Tambahkan field untuk menampilkan nama tahun ajaran berikutnya dalam format text
    next_tahunajaran_name = fields.Char(
        string="Tahun Ajaran Berikutnya",
        compute='_compute_next_tahunajaran',
        store=True,
        readonly=True,
        help="Nama tahun ajaran berikutnya"
    )


    # Tambahkan method compute untuk menghitung tahun ajaran berikutnya
    @api.depends('tahunajaran_id')
    def _compute_next_tahunajaran(self):
        """
        Compute tahun ajaran berikutnya berdasarkan tahun ajaran saat ini
        Jika tidak ada di database, akan membuat preview berdasarkan logic pembuatan tahun ajaran baru
        """
        for record in self:
            if not record.tahunajaran_id:
                record.next_tahunajaran_id = False
                record.next_tahunajaran_name = ""
                continue
                
            try:
                # Ekstrak tahun dari nama tahun ajaran saat ini
                current_year = int(record.tahunajaran_id.name.split('/')[0])
                next_year = current_year + 1
                next_ta_name = f"{next_year}/{next_year+1}"
                
                # Cari tahun ajaran berikutnya yang sudah ada
                existing_next_ta = self.env['cdn.ref_tahunajaran'].search([
                    ('name', '=', next_ta_name)
                ], limit=1)
                
                if existing_next_ta:
                    # Jika sudah ada, gunakan yang sudah ada
                    record.next_tahunajaran_id = existing_next_ta.id
                    record.next_tahunajaran_name = existing_next_ta.name
                else:
                    # Jika belum ada, tampilkan preview nama tahun ajaran yang akan dibuat
                    record.next_tahunajaran_id = False
                    record.next_tahunajaran_name = next_ta_name
                                        
            except (ValueError, IndexError) as e:
                # Jika format tahun ajaran tidak sesuai
                _logger.warning(f"Format tahun ajaran tidak valid untuk record {record.id}: {e}")
                record.next_tahunajaran_id = False
                record.next_tahunajaran_name = "Format tahun ajaran tidak valid"
            except Exception as e:
                _logger.error(f"Error computing next tahun ajaran for record {record.id}: {e}")
                record.next_tahunajaran_id = False
                record.next_tahunajaran_name = "Error menghitung tahun ajaran berikutnya"

    # Method untuk mendapatkan atau membuat tahun ajaran berikutnya
    def get_or_create_next_tahunajaran(self):
        """
        Method untuk mendapatkan tahun ajaran berikutnya
        Jika belum ada, akan membuatnya menggunakan fungsi _create_next_tahun_ajaran
        
        Returns:
            cdn.ref_tahunajaran: Record tahun ajaran berikutnya
        """
        self.ensure_one()
        
        if not self.tahunajaran_id:
            raise UserError("Tahun ajaran saat ini belum dipilih")
        
        # Cek apakah sudah ada tahun ajaran berikutnya
        if self.next_tahunajaran_id:
            return self.next_tahunajaran_id
        
        # Jika belum ada, buat tahun ajaran baru
        try:
            next_ta = self._create_next_tahun_ajaran(self.tahunajaran_id)
            
            # Update field computed untuk refresh tampilan
            self._compute_next_tahunajaran()
            
            return next_ta
            
        except Exception as e:
            _logger.error(f"Gagal membuat tahun ajaran berikutnya: {str(e)}")
            raise UserError(f"Gagal membuat tahun ajaran berikutnya: {str(e)}")

    # Method untuk refresh data tahun ajaran berikutnya (opsional, untuk button)
    def action_refresh_next_tahunajaran(self):
        """
        Action untuk merefresh data tahun ajaran berikutnya
        Berguna jika ada perubahan data tahun ajaran
        """
        self._compute_next_tahunajaran()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
        
    
    def _create_next_tahun_ajaran(self, current_ta):
        """
        Fungsi untuk membuat tahun ajaran berikutnya jika belum ada
        Disesuaikan dengan sistem pendidikan di Indonesia (Juli-Juni)
        
        Args:
            current_ta: Tahun ajaran saat ini
            
        Returns:
            cdn.ref_tahunajaran: Tahun ajaran baru yang dibuat
        """
        try:
            _logger.info(f"Mencoba membuat tahun ajaran baru setelah {current_ta.name}")
            
            # Ekstrak tahun dari nama tahun ajaran saat ini
            current_year = int(current_ta.name.split('/')[0])
            next_year = current_year + 1
            next_ta_name = f"{next_year}/{next_year+1}"
            
            _logger.info(f"Tahun yang diekstrak: {current_year}, Tahun berikutnya: {next_year}")
            _logger.info(f"Nama tahun ajaran baru: {next_ta_name}")
            
            # Tentukan tanggal mulai dan akhir sesuai sistem pendidikan Indonesia
            start_date = datetime(next_year, 7, 1).date()
            end_date = datetime(next_year + 1, 6, 30).date()
            
            _logger.info(f"Tanggal mulai: {start_date}, Tanggal akhir: {end_date}")
            
            # Cek apakah sudah ada tahun ajaran dengan nama tersebut
            existing_ta_by_name = self.env['cdn.ref_tahunajaran'].search([
                ('name', '=', next_ta_name)
            ], limit=1)
            
            if existing_ta_by_name:
                _logger.info(f"Tahun ajaran dengan nama {next_ta_name} sudah ada")
                return existing_ta_by_name
                
            # Cek apakah sudah ada tahun ajaran dengan rentang waktu tersebut
            existing_ta = self.env['cdn.ref_tahunajaran'].search([
                ('start_date', '=', start_date),
                ('end_date', '=', end_date)
            ], limit=1)
            
            if existing_ta:
                _logger.info(f"Tahun ajaran dengan rentang {start_date} - {end_date} sudah ada")
                return existing_ta
            
            _logger.info(f"Membuat tahun ajaran baru: {next_ta_name}")
            
            # Ambil data tambahan dari tahun ajaran saat ini
            create_vals = {
                'name': next_ta_name,
                'start_date': start_date,
                'end_date': end_date,
                'keterangan': f"Dibuat otomatis dari proses kenaikan kelas pada {fields.Date.today()}"
            }
            
            # Copy field yang ada dari tahun ajaran saat ini
            if hasattr(current_ta, 'term_structure') and current_ta.term_structure:
                create_vals['term_structure'] = current_ta.term_structure
                
            if hasattr(current_ta, 'company_id') and current_ta.company_id:
                create_vals['company_id'] = current_ta.company_id.id
            
            # Buat tahun ajaran baru dengan sudo untuk memastikan hak akses
            new_ta = self.env['cdn.ref_tahunajaran'].sudo().create(create_vals)
            
            # Verifikasi record telah dibuat
            if not new_ta:
                raise UserError(f"Gagal membuat tahun ajaran baru {next_ta_name}")
            
            # Commit transaksi untuk memastikan data tersimpan
            self.env.cr.commit()
            
            # Buat termin akademik dan periode tagihan jika method tersedia
            if hasattr(new_ta, 'term_create'):
                try:
                    new_ta.term_create()
                except Exception as e:
                    _logger.warning(f"Gagal membuat termin untuk tahun ajaran {next_ta_name}: {str(e)}")
            
            _logger.info(f"Tahun ajaran baru berhasil dibuat: {new_ta.name} ({new_ta.start_date} - {new_ta.end_date})")
            
            return new_ta
        except Exception as e:
            _logger.error(f"Gagal membuat tahun ajaran baru: {str(e)}")
            raise UserError(f"Gagal membuat tahun ajaran baru: {str(e)}")

    @api.depends('kelas_id', 'kelas_id.nama_kelas', 'kelas_id.jurusan_id', 'kelas_id.tingkat', 'status')
    def _compute_next_class(self):
        """Compute kelas selanjutnya berdasarkan kelas yang dipilih dan status"""
        for record in self:
            if not record.kelas_id:
                record.next_class = False
                continue
            
            # Jika status adalah tidak_naik atau tidak_lulus, 
            # maka next_class tetap menampilkan kelas yang sama
            if record.status in ['tidak_naik', 'tidak_lulus']:
                # Cari master kelas yang sesuai dengan kelas_id saat ini
                current_class = record.kelas_id
                current_tingkat = current_class.tingkat
                current_nama_kelas = current_class.nama_kelas
                current_jurusan = current_class.jurusan_id
                
                if not current_tingkat:
                    record.next_class = False
                    continue
                
                # Cari master kelas yang cocok dengan kelas saat ini
                domain = [('tingkat', '=', current_tingkat.id)]
                
                # Filter berdasarkan nama kelas jika ada
                if current_nama_kelas:
                    domain.append(('nama_kelas', '=', current_nama_kelas))
                
                # Filter berdasarkan jurusan jika ada
                if current_jurusan:
                    domain.append(('jurusan_id', '=', current_jurusan.id))
                
                # Cari master kelas yang cocok dengan kelas saat ini
                current_master_class = self.env['cdn.master_kelas'].search(domain, limit=1)
                
                # Jika tidak ditemukan dengan nama_kelas, coba tanpa nama_kelas (hanya tingkat dan jurusan)
                if not current_master_class and current_jurusan:
                    domain_alternative = [
                        ('tingkat', '=', current_tingkat.id),
                        ('jurusan_id', '=', current_jurusan.id)
                    ]
                    current_master_class = self.env['cdn.master_kelas'].search(domain_alternative, limit=1)
                
                # Jika masih tidak ditemukan, coba hanya berdasarkan tingkat
                if not current_master_class:
                    domain_simple = [('tingkat', '=', current_tingkat.id)]
                    current_master_class = self.env['cdn.master_kelas'].search(domain_simple, limit=1)
                
                record.next_class = current_master_class.id if current_master_class else False
                continue
            
                        # Untuk status naik, cari kelas selanjutnya
            # Ambil data kelas saat ini
            current_class = record.kelas_id
            current_tingkat = current_class.tingkat
            current_nama_kelas = current_class.nama_kelas
            current_jurusan = current_class.jurusan_id
            
            if not current_tingkat:
                record.next_class = False
                continue
            
            # Cari tingkat selanjutnya
            next_tingkat = record._get_next_tingkat(current_tingkat)
            if not next_tingkat:
                record.next_class = False
                continue
            
            # Cari master kelas yang cocok dengan kriteria:
            # 1. Tingkat = tingkat selanjutnya
            # 2. nama_kelas = sama dengan kelas saat ini (jika ada)
            # 3. jurusan_id = sama dengan kelas saat ini (jika ada)
            domain = [('tingkat', '=', next_tingkat.id)]
            
            # Filter berdasarkan nama kelas jika ada
            if current_nama_kelas:
                domain.append(('nama_kelas', '=', current_nama_kelas))
            
            # Filter berdasarkan jurusan jika ada
            if current_jurusan:
                domain.append(('jurusan_id', '=', current_jurusan.id))
            
            # Cari master kelas yang cocok
            next_master_class = self.env['cdn.master_kelas'].search(domain, limit=1)
            
            # Jika tidak ditemukan dengan nama_kelas, coba tanpa nama_kelas (hanya tingkat dan jurusan)
            if not next_master_class and current_jurusan:
                domain_alternative = [
                    ('tingkat', '=', next_tingkat.id),
                    ('jurusan_id', '=', current_jurusan.id)
                ]
                next_master_class = self.env['cdn.master_kelas'].search(domain_alternative, limit=1)
            
            # Jika masih tidak ditemukan, coba hanya berdasarkan tingkat
            if not next_master_class:
                domain_simple = [('tingkat', '=', next_tingkat.id)]
                next_master_class = self.env['cdn.master_kelas'].search(domain_simple, limit=1)
            
            record.next_class = next_master_class.id if next_master_class else False
            
        
    def _get_next_tingkat(self, current_tingkat):
        """Mendapatkan tingkat selanjutnya berdasarkan tingkat saat ini"""
        if not current_tingkat:
            return False
        
        # Coba ambil urutan tingkat
        current_order = None
        
        # Cara 1: Berdasarkan field urutan
        if hasattr(current_tingkat, 'urutan') and current_tingkat.urutan:
            current_order = current_tingkat.urutan
        
        # Cara 2: Berdasarkan field level
        elif hasattr(current_tingkat, 'level') and current_tingkat.level:
            current_order = current_tingkat.level
        
        # Cara 3: Extract dari nama tingkat
        elif hasattr(current_tingkat, 'name') and current_tingkat.name:
            current_order = self._extract_tingkat_number(current_tingkat.name)
        
        if not current_order:
            return False
        
        next_order = current_order + 1
        
        # Cari tingkat dengan urutan selanjutnya
        # Prioritas pencarian: urutan -> level -> nama
        next_tingkat = None
        
        # Cari berdasarkan urutan
        if hasattr(current_tingkat, 'urutan'):
            next_tingkat = self.env['cdn.tingkat'].search([('urutan', '=', next_order)], limit=1)
        
        # Jika tidak ditemukan, cari berdasarkan level
        if not next_tingkat and hasattr(current_tingkat, 'level'):
            next_tingkat = self.env['cdn.tingkat'].search([('level', '=', next_order)], limit=1)
        
        # Jika tidak ditemukan, cari berdasarkan nama
        if not next_tingkat:
            # Cari berdasarkan angka
            next_tingkat = self.env['cdn.tingkat'].search([
                '|', '|',
                ('name', 'ilike', str(next_order)),
                ('name', 'ilike', self._number_to_roman(next_order)),
                ('name', 'ilike', self._number_to_word(next_order))
            ], limit=1)
        
        return next_tingkat

    def _extract_tingkat_number(self, tingkat_name):
        """Extract nomor tingkat dari nama tingkat"""
        if not tingkat_name:
            return None
        
        tingkat_name = str(tingkat_name).upper()
        
        # Dictionary untuk konversi angka romawi ke angka
        roman_to_num = {
            'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6,
            'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10, 'XI': 11, 'XII': 12,
            'XIII': 13, 'XIV': 14, 'XV': 15, 'XVI': 16, 'XVII': 17, 'XVIII': 18
        }
        
        # Dictionary untuk konversi kata ke angka
        word_to_num = {
            'SATU': 1, 'DUA': 2, 'TIGA': 3, 'EMPAT': 4, 'LIMA': 5, 'ENAM': 6,
            'TUJUH': 7, 'DELAPAN': 8, 'SEMBILAN': 9, 'SEPULUH': 10, 
            'SEBELAS': 11, 'DUABELAS': 12, 'TIGABELAS': 13, 'EMPATBELAS': 14
        }
        
        # Cari angka langsung
        import re
        numbers = re.findall(r'\d+', tingkat_name)
        if numbers:
            return int(numbers[0])
        
        # Cari angka romawi
        for roman, num in roman_to_num.items():
            if roman in tingkat_name:
                return num
        
        # Cari kata
        for word, num in word_to_num.items():
            if word in tingkat_name:
                return num
        
        return None

    def _number_to_roman(self, num):
        """Convert number to roman numeral"""
        roman_numerals = {
            1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI',
            7: 'VII', 8: 'VIII', 9: 'IX', 10: 'X', 11: 'XI', 12: 'XII',
            13: 'XIII', 14: 'XIV', 15: 'XV', 16: 'XVI', 17: 'XVII', 18: 'XVIII'
        }
        return roman_numerals.get(num, str(num))

    def _number_to_word(self, num):
        """Convert number to Indonesian word"""
        word_numerals = {
            1: 'SATU', 2: 'DUA', 3: 'TIGA', 4: 'EMPAT', 5: 'LIMA', 6: 'ENAM',
            7: 'TUJUH', 8: 'DELAPAN', 9: 'SEMBILAN', 10: 'SEPULUH',
            11: 'SEBELAS', 12: 'DUABELAS', 13: 'TIGABELAS', 14: 'EMPATBELAS'
        }
        return word_numerals.get(num, str(num))            


    def _reset_kelas_related_fields(self):
        """Helper method untuk reset semua field yang terkait dengan kelas"""
        self.tingkat_id = False
        self.walikelas_id = False
        self.status = False
        self.partner_ids = [(5, 0, 0)]  # kosongkan M2M
        self.partner_lines = [(5, 0, 0)]  # kosongkan One2many
        self.filtered_santri_ids = [(5, 0, 0)]  # kosongkan filtered santri
        self.next_class = False
        self.message_result = False

    @api.onchange('kelas_id')
    def _onchange_kelas_id(self):
        """Auto-fill tingkat_id, walikelas_id, status, partner_ids, dan partner_lines berdasarkan kelas"""
        # RESET SEMUA FIELD TERLEBIH DAHULU
        self._reset_kelas_related_fields()
        
        if self.kelas_id:
            # Ambil data kelas
            kelas = self.kelas_id

            # Set tingkat_id - coba beberapa kemungkinan nama field
            if hasattr(kelas, 'tingkat_id') and kelas.tingkat_id:
                self.tingkat_id = kelas.tingkat_id.id
            elif hasattr(kelas, 'tingkat') and kelas.tingkat:
                self.tingkat_id = kelas.tingkat.id

            # Set walikelas_id
            if hasattr(kelas, 'walikelas_id') and kelas.walikelas_id:
                self.walikelas_id = kelas.walikelas_id.id

            # Set status otomatis berdasarkan tingkat (pastikan method ini ada)
            if hasattr(self, '_set_status_by_tingkat'):
                self._set_status_by_tingkat(kelas)

            # Cari siswa yang berada di kelas yang dipilih
            santri = self.env['cdn.siswa'].search([('ruang_kelas_id', '=', self.kelas_id.id)])
            
            # Set semua field santri jika ada data
            if santri:
                santri.write({'centang': True})
                self.partner_ids = [(6, 0, santri.ids)]
                # self.filtered_santri_ids = [(6, 0, santri.ids)]
                
                # Buat partner_lines baru
                lines = []
                for s in santri:
                    lines.append((0, 0, {
                        'siswa_id': s.id,
                        'next_class_id': self.next_class.id if self.next_class else False, 
                    }))
                self.partner_lines = lines
                
            # Trigger compute untuk next_class jika perlu
            self._compute_next_class()



    def _set_status_by_tingkat(self, kelas):
        """Set status berdasarkan tingkat kelas"""
        if not kelas.tingkat:
            self.status = 'naik'  # Default jika tidak ada tingkat
            return
        
        # Ambil data tingkat
        tingkat = kelas.tingkat
        
        # Cek apakah tingkat 12 (kelas SMA/MA/SMK)
        is_tingkat_12 = self._is_tingkat_12(tingkat)
        if is_tingkat_12:
            # Untuk tingkat 12, cek apakah ada kelas selanjutnya
            has_next_class = self._check_next_class_exists(kelas)
            if has_next_class:
                self.status = 'naik'
            else:
                self.status = 'lulus'
            return
        
        # Cara 1: Cek berdasarkan nama tingkat (jika ada field nama/name)
        if hasattr(tingkat, 'name'):
            tingkat_name = str(tingkat.name).lower()
            # Cek apakah tingkat 6 atau 9
            if '6' in tingkat_name or 'vi' in tingkat_name or 'enam' in tingkat_name:
                self.status = 'lulus'
            elif '9' in tingkat_name or 'ix' in tingkat_name or 'sembilan' in tingkat_name:
                self.status = 'lulus'
            else:
                self.status = 'naik'
        
        # Cara 2: Cek berdasarkan field urutan (jika ada)
        elif hasattr(tingkat, 'urutan'):
            if tingkat.urutan in [6, 9]:
                self.status = 'lulus'
            else:
                self.status = 'naik'
        
        # Cara 3: Cek berdasarkan field level (jika ada)
        elif hasattr(tingkat, 'level'):
            if tingkat.level in [6, 9]:
                self.status = 'lulus'
            else:
                self.status = 'naik'
        
        # Cara 4: Cek berdasarkan jenjang dan tingkat
        elif hasattr(kelas, 'jenjang'):
            # Untuk SD/MI: tingkat 6 = lulus
            if kelas.jenjang in ['sd'] and hasattr(tingkat, 'name'):
                if '6' in str(tingkat.name) or 'vi' in str(tingkat.name).lower():
                    self.status = 'lulus'
                else:
                    self.status = 'naik'
            # Untuk SMP/MTS: tingkat 9 = lulus  
            elif kelas.jenjang in ['smp'] and hasattr(tingkat, 'name'):
                if '9' in str(tingkat.name) or 'ix' in str(tingkat.name).lower():
                    self.status = 'lulus'
                else:
                    self.status = 'naik'
            else:
                self.status = 'naik'
        
        else:
            # Default jika tidak bisa menentukan
            self.status = 'naik'

    @api.onchange('tingkat_id')
    def _onchange_tingkat_id(self):
        """Update status ketika tingkat_id diubah manual"""
        if self.tingkat_id and self.kelas_id:
            # Buat object kelas sementara untuk menggunakan method yang sama
            class MockKelas:
                def __init__(self, tingkat, jenjang):
                    self.tingkat = tingkat
                    self.jenjang = jenjang
            
            mock_kelas = MockKelas(self.tingkat_id, self.jenjang)
            self._set_status_by_tingkat(mock_kelas)

    def _is_tingkat_12(self, tingkat):
        """Cek apakah tingkat adalah kelas 12"""
        if hasattr(tingkat, 'name'):
            tingkat_name = str(tingkat.name).lower()
            if '12' in tingkat_name or 'xii' in tingkat_name or 'duabelas' in tingkat_name:
                return True
        
        if hasattr(tingkat, 'urutan'):
            if tingkat.urutan == 12:
                return True
        
        if hasattr(tingkat, 'level'):
            if tingkat.level == 12:
                return True
                
        return False

    def _check_next_class_exists(self, kelas):
        """Cek apakah ada kelas selanjutnya setelah tingkat 12 di cdn.master_kelas"""
        try:
            # Ambil tingkat saat ini
            current_tingkat = kelas.tingkat
            if not current_tingkat:
                return False
            
            # Ambil jenjang dan jurusan dari kelas saat ini
            current_jenjang = kelas.jenjang if hasattr(kelas, 'jenjang') else None
            current_jurusan = None
            
            # Coba ambil jurusan dari kelas saat ini
            if hasattr(kelas, 'jurusan_id'):
                current_jurusan = kelas.jurusan_id
            elif hasattr(kelas, 'name') and hasattr(kelas.name, 'jurusan_id'):
                current_jurusan = kelas.name.jurusan_id
            
            # Tentukan tingkat selanjutnya yang mungkin (13, 14, dst)
            next_tingkat_numbers = [13, 14, 15, 16]  # Bisa disesuaikan
            
            # Cari tingkat selanjutnya di cdn.tingkat
            next_tingkat_ids = []
            for num in next_tingkat_numbers:
                tingkat_domain = []
                
                # Cari berdasarkan nama
                tingkat_records = self.env['cdn.tingkat'].search([
                    '|', '|', '|',
                    ('name', 'ilike', str(num)),
                    ('name', 'ilike', self._number_to_roman(num)),
                    ('urutan', '=', num),
                    ('level', '=', num)
                ])
                
                if tingkat_records:
                    next_tingkat_ids.extend(tingkat_records.ids)
            
            if not next_tingkat_ids:
                return False
            
            # Cari di cdn.master_kelas apakah ada kelas dengan tingkat selanjutnya
            master_kelas_domain = [('tingkat', 'in', next_tingkat_ids)]
            
            # Filter berdasarkan jenjang jika ada
            if current_jenjang:
                master_kelas_domain.append(('jenjang', '=', current_jenjang))
            
            # Filter berdasarkan jurusan jika ada
            if current_jurusan:
                master_kelas_domain.append(('jurusan_id', '=', current_jurusan.id))
            
            next_classes = self.env['cdn.master_kelas'].search(master_kelas_domain, limit=1)
            
            return bool(next_classes)
            
        except Exception as e:
            # Jika terjadi error, default ke False (lulus)
            _logger.warning(f"Error checking next class: {str(e)}")
            return False


    # def action_proses_kenaikan_kelas(self):
    #     """
    #     Aksi untuk memproses kenaikan kelas dengan memperbarui data siswa
    #     pada kelas yang sudah ada (tidak membuat kelas baru)
    #     """
    #     _logger.info(f"Memulai proses kenaikan kelas untuk tahun ajaran: {self.tahunajaran_id.name}")
        
    #     if not self.partner_ids:
    #         raise UserError("Belum ada santri yang dipilih!")
        
    #     if not self.kelas_id:
    #         raise UserError("Belum ada kelas yang dipilih!")
        
    #     self.ensure_one()
    #     message = ""
    #     count_siswa_naik = 0
    #     count_siswa_tidak_naik = 0
    #     count_siswa_lulus = 0
    #     count_siswa_tidak_lulus = 0
        
    #     # Mendapatkan tahun ajaran berikutnya
    #     try:
    #         current_year = int(self.tahunajaran_id.name.split('/')[0])
    #         next_year = current_year + 1
    #         next_ta_name = f"{next_year}/{next_year+1}"
            
    #         _logger.info(f"Current year: {current_year}, Next year: {next_year}")
    #         _logger.info(f"Mencari tahun ajaran dengan nama: {next_ta_name}")
            
    #         # Cari tahun ajaran berikutnya
    #         tahun_ajaran_berikutnya = self.env['cdn.ref_tahunajaran'].search([
    #             ('name', '=', next_ta_name)
    #         ], limit=1)
            
    #         _logger.info(f"Hasil pencarian tahun ajaran berikutnya: {tahun_ajaran_berikutnya.name if tahun_ajaran_berikutnya else 'Tidak ditemukan'}")
            
    #     except (ValueError, IndexError) as e:
    #         _logger.error(f"Format tahun ajaran tidak valid: {str(e)}")
    #         raise UserError(f"Format tahun ajaran tidak valid: {self.tahunajaran_id.name}. Format yang diharapkan: YYYY/YYYY")
        
    #     # Jika tahun ajaran berikutnya tidak ditemukan, buat yang baru
    #     if not tahun_ajaran_berikutnya:
    #         message += f"Tahun ajaran {next_ta_name} tidak ditemukan. Mencoba membuat tahun ajaran baru...\n"
    #         try:
    #             tahun_ajaran_berikutnya = self._create_next_tahun_ajaran(self.tahunajaran_id)
    #             message += f"Berhasil membuat tahun ajaran baru: {tahun_ajaran_berikutnya.name}\n\n"
    #         except Exception as e:
    #             message += f"Gagal membuat tahun ajaran baru: {str(e)}\n\n"
    #             raise UserError(f"Gagal membuat tahun ajaran baru: {str(e)}")
        
    #     # Update data kelas berdasarkan status kenaikan kelas
    #     try:
    #         # Cek status kenaikan kelas dan update kelas yang lama
    #         if self.status == 'naik':
    #             # Siswa naik kelas - ubah name dan tahun_ajaran kelas lama
    #             if self.next_class:
    #                 # Update kelas lama dengan kelas baru dan tahun ajaran baru
    #                 self.kelas_id.write({
    #                     'name': self.next_class.id,
    #                     'tahunajaran_id': tahun_ajaran_berikutnya.id,
    #                     'walikelas_id': self.walikelas_id.id,
    #                 })
    #                 message += f"Kelas {self.kelas_id.nama_kelas} berhasil diupdate ke {self.next_class.name} untuk tahun ajaran {tahun_ajaran_berikutnya.name}\n"
                    
    #                 # Update status siswa
    #                 for siswa in self.partner_ids:
    #                     siswa.write({
    #                         'tahun_ajaran_id': tahun_ajaran_berikutnya.id,
    #                         'walikelas_id': self.walikelas_id.id,
    #                     })
    #                     count_siswa_naik += 1
                        
    #                 message += f"Total {len(self.partner_ids)} siswa naik kelas ke {self.next_class.name}\n"
    #             else:
    #                 message += "Gagal naik kelas - kelas selanjutnya tidak ditentukan\n"
                    
    #         elif self.status == 'tidak_naik':
    #             # Siswa tidak naik kelas - hanya ubah tahun_ajaran
    #             self.kelas_id.write({
    #                 'tahunajaran_id': tahun_ajaran_berikutnya.id,
    #                 'walikelas_id': self.walikelas_id.id,
    #             })
    #             message += f"Kelas {self.kelas_id.nama_kelas} diupdate ke tahun ajaran {tahun_ajaran_berikutnya.name} (tidak naik kelas)\n"
                
    #             # Update status siswa
    #             for siswa in self.partner_ids:
    #                 siswa.write({
    #                     'tahun_ajaran_id': tahun_ajaran_berikutnya.id,
    #                     'walikelas_id': self.walikelas_id.id,
    #                 })
    #                 count_siswa_tidak_naik += 1
                    
    #             message += f"Total {len(self.partner_ids)} siswa tidak naik kelas\n"
                    
    #         elif self.status == 'lulus':
    #             # Siswa lulus - ubah aktif_tidak menjadi 'tidak'
    #             self.kelas_id.write({
    #                 'aktif_tidak': 'tidak',
    #                 # 'tahunajaran_id': tahun_ajaran_berikutnya.id,
    #             })
    #             message += f"Kelas {self.kelas_id.nama_kelas} dinonaktifkan karena siswa lulus\n"
                
    #             # Update status siswa
    #             for siswa in self.partner_ids:
    #                 siswa.write({
    #                     'status_kelulusan': 'lulus',
    #                     'tahun_lulus': tahun_ajaran_berikutnya.name,
    #                     # 'tahun_ajaran_id': tahun_ajaran_berikutnya.id,
    #                 })
    #                 count_siswa_lulus += 1
                    
    #             message += f"Total {len(self.partner_ids)} siswa lulus\n"
                
    #         elif self.status == 'tidak_lulus':
    #             # Siswa tidak lulus - hanya ubah tahun_ajaran
    #             self.kelas_id.write({
    #                 'tahunajaran_id': tahun_ajaran_berikutnya.id,
    #                 'walikelas_id': self.walikelas_id.id,
    #             })
    #             message += f"Kelas {self.kelas_id.nama_kelas} diupdate ke tahun ajaran {tahun_ajaran_berikutnya.name} (tidak lulus)\n"
                
    #             # Update status siswa
    #             for siswa in self.partner_ids:
    #                 siswa.write({
    #                     'tahun_ajaran_id': tahun_ajaran_berikutnya.id,
    #                     'status_kelulusan': 'tidak_lulus',
    #                     'walikelas_id': self.walikelas_id.id,
    #                 })
    #                 count_siswa_tidak_lulus += 1
                    
    #             message += f"Total {len(self.partner_ids)} siswa tidak lulus\n"
                
    #     except Exception as e:
    #         error_msg = f"ERROR memproses kenaikan kelas: {str(e)}"
    #         message += f"- {error_msg}\n"
    #         _logger.error(error_msg)
        
    #     # Commit perubahan
    #     try:
    #         self.env.cr.commit()
    #         _logger.info("Perubahan berhasil di-commit ke database")
    #     except Exception as e:
    #         _logger.error(f"Gagal melakukan commit perubahan: {str(e)}")
    #         raise UserError(f"Gagal menyimpan perubahan: {str(e)}")
        
    #     # Buat summary hasil proses
    #     result_message = f"Proses Kenaikan Kelas berhasil dilakukan!\n\n"
    #     result_message += f"Ringkasan Hasil:\n"
    #     result_message += f"- Siswa naik kelas: {count_siswa_naik}\n"
    #     result_message += f"- Siswa tidak naik: {count_siswa_tidak_naik}\n"
    #     result_message += f"- Siswa lulus: {count_siswa_lulus}\n"
    #     result_message += f"- Siswa tidak lulus: {count_siswa_tidak_lulus}\n"
    #     result_message += f"Total siswa diproses: {len(self.partner_ids)}\n\n"
    #     result_message += f"Detail Proses:\n{message}"
        
    #     _logger.info(f"Proses kenaikan kelas selesai dengan hasil: {result_message}")
        
    #     # Update field message_result
    #     self.message_result = result_message
        
    #     # Buat notification message
    #     notification_message = f'Proses kenaikan kelas berhasil! Total {len(self.partner_ids)} siswa diproses.'


    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Kenaikan Kelas',
    #         'res_model': 'cdn.kenaikan_kelas',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': {
    #             'default_message_result': result_message,
    #             # Kosongkan field lain sesuai kebutuhan
    #             'default_kelas_id': False,
    #             'default_status': False,
    #             'default_partner_ids': [],
    #             'default_next_class': False,
    #         }
    #     }

    # def action_proses_kenaikan_kelas(self):
    #     """
    #     Aksi untuk memproses kenaikan kelas dengan memperbarui data siswa
    #     berdasarkan status centang masing-masing siswa
    #     """
    #     _logger.info(f"Memulai proses kenaikan kelas untuk tahun ajaran: {self.tahunajaran_id.name}")
        
    #     if not self.partner_ids:
    #         raise UserError("Belum ada santri yang dipilih!")
        
    #     if not self.kelas_id:
    #         raise UserError("Belum ada kelas yang dipilih!")
        
    #     self.ensure_one()
    #     message = ""
    #     count_siswa_naik = 0
    #     count_siswa_tidak_naik = 0
    #     count_siswa_lulus = 0
    #     count_siswa_tidak_lulus = 0
        
    #     # Mendapatkan tahun ajaran berikutnya
    #     try:
    #         current_year = int(self.tahunajaran_id.name.split('/')[0])
    #         next_year = current_year + 1
    #         next_ta_name = f"{next_year}/{next_year+1}"
            
    #         _logger.info(f"Current year: {current_year}, Next year: {next_year}")
    #         _logger.info(f"Mencari tahun ajaran dengan nama: {next_ta_name}")
            
    #         # Cari tahun ajaran berikutnya
    #         tahun_ajaran_berikutnya = self.env['cdn.ref_tahunajaran'].search([
    #             ('name', '=', next_ta_name)
    #         ], limit=1)
            
    #         _logger.info(f"Hasil pencarian tahun ajaran berikutnya: {tahun_ajaran_berikutnya.name if tahun_ajaran_berikutnya else 'Tidak ditemukan'}")
            
    #     except (ValueError, IndexError) as e:
    #         _logger.error(f"Format tahun ajaran tidak valid: {str(e)}")
    #         raise UserError(f"Format tahun ajaran tidak valid: {self.tahunajaran_id.name}. Format yang diharapkan: YYYY/YYYY")
        
    #     # Jika tahun ajaran berikutnya tidak ditemukan, buat yang baru
    #     if not tahun_ajaran_berikutnya:
    #         message += f"Tahun ajaran {next_ta_name} tidak ditemukan. Mencoba membuat tahun ajaran baru...\n"
    #         try:
    #             tahun_ajaran_berikutnya = self._create_next_tahun_ajaran(self.tahunajaran_id)
    #             message += f"Berhasil membuat tahun ajaran baru: {tahun_ajaran_berikutnya.name}\n\n"
    #         except Exception as e:
    #             message += f"Gagal membuat tahun ajaran baru: {str(e)}\n\n"
    #             raise UserError(f"Gagal membuat tahun ajaran baru: {str(e)}")
        
    #     # Pisahkan santri berdasarkan status centang
    #     santri_naik = self.partner_ids.filtered(lambda s: getattr(s, 'centang', False) is True)
    #     santri_tidak_naik = self.partner_ids.filtered(lambda s: not getattr(s, 'centang', False))

    #     _logger.info(f"Santri naik kelas (centang=True): {len(santri_naik)} - {[s.name for s in santri_naik]}")
    #     _logger.info(f"Santri tidak naik kelas (centang=False): {len(santri_tidak_naik)} - {[s.name for s in santri_tidak_naik]}")
        
    #     try:
    #         # ===== SIMPAN DATA KELAS LAMA LANGSUNG DARI DATABASE SEBELUM DIUPDATE =====
    #         kelas_lama_db = self.env['cdn.ruang_kelas'].browse(self.kelas_id.id)
    #         tingkat_lama = kelas_lama_db.tingkat_id.id if hasattr(kelas_lama_db, 'tingkat_id') and kelas_lama_db.tingkat_id else None
    #         name_lama = kelas_lama_db.name.id if hasattr(kelas_lama_db.name, 'id') else kelas_lama_db.name
    #         jurusan_lama = kelas_lama_db.jurusan_id.id if hasattr(kelas_lama_db, 'jurusan_id') and kelas_lama_db.jurusan_id else None
    #         jenjang_lama = kelas_lama_db.jenjang

    #         # ===== PROSES SANTRI YANG TIDAK NAIK KELAS (TIDAK DICENTANG) =====
    #         if santri_tidak_naik:
    #             message += f"\n=== PROSES SANTRI TIDAK NAIK KELAS ({len(santri_tidak_naik)} siswa) ===\n"
    #             # Cari kelas dengan nama, jurusan, tingkat sama di tahun ajaran berikutnya
    #             domain_kelas_tujuan = [
    #                 ('name', '=', name_lama),
    #                 ('tahunajaran_id', '=', tahun_ajaran_berikutnya.id),
    #                 ('jenjang', '=', jenjang_lama),
    #             ]
    #             if tingkat_lama:
    #                 domain_kelas_tujuan.append(('tingkat', '=', tingkat_lama))
    #             if jurusan_lama:
    #                 domain_kelas_tujuan.append(('jurusan_id', '=', jurusan_lama))
    #             kelas_tujuan = self.env['cdn.ruang_kelas'].search(domain_kelas_tujuan, limit=1)
    #             if kelas_tujuan:
    #                 message += f"Menggunakan kelas tidak naik existing: {kelas_tujuan.nama_kelas}\n"
    #             else:
    #                 # Buat kelas baru dengan nama, jurusan, tingkat sama untuk tahun ajaran berikutnya
    #                 kelas_tujuan_vals = {
    #                     'name': name_lama,
    #                     'tahunajaran_id': tahun_ajaran_berikutnya.id,
    #                     'walikelas_id': self.walikelas_id.id if self.walikelas_id else False,
    #                     'aktif_tidak': 'aktif',
    #                     'status': 'konfirm',
    #                     'angkatan_id': kelas_lama.angkatan_id.id if kelas_lama.angkatan_id else False,
    #                     'jenjang': jenjang_lama,
    #                 }
    #                 if tingkat_lama:
    #                     kelas_tujuan_vals['tingkat_id'] = tingkat_lama
    #                 if jurusan_lama:
    #                     kelas_tujuan_vals['jurusan_id'] = jurusan_lama
    #                 kelas_tujuan = self.env['cdn.ruang_kelas'].create(kelas_tujuan_vals)
    #                 message += f"Membuat kelas tidak naik baru: {kelas_tujuan.nama_kelas}\n"
    #             # Log detail kelas_tujuan
    #             _logger.info(f"Kelas tujuan (tinggal kelas): id={kelas_tujuan.id}, nama={kelas_tujuan.nama_kelas}, tahunajaran={kelas_tujuan.tahunajaran_id.name}, tingkat={kelas_tujuan.tingkat_id.name if hasattr(kelas_tujuan, 'tingkat_id') and kelas_tujuan.tingkat_id else '-'}, jurusan={kelas_tujuan.jurusan_id.name if hasattr(kelas_tujuan, 'jurusan_id') and kelas_tujuan.jurusan_id else '-'}")
    #             # Update siswa yang tidak naik kelas
    #             for siswa in santri_tidak_naik:
    #                 _logger.info(f"Update siswa tidak naik: {siswa.name} -> kelas tujuan: {kelas_tujuan.nama_kelas} (id={kelas_tujuan.id}), tahunajaran={tahun_ajaran_berikutnya.name}")
    #                 siswa.write({
    #                     'ruang_kelas_id': kelas_tujuan.id,  # Kelas tujuan = kelas tinggal kelas, tingkat sama
    #                     'tahunajaran_id': tahun_ajaran_berikutnya.id,  # Tahun ajaran naik
    #                 })
    #                 count_siswa_tidak_naik += 1
    #             message += f"Total {len(santri_tidak_naik)} siswa tidak naik kelas ke {kelas_tujuan.nama_kelas}\n"

    #         # ===== PROSES SANTRI YANG NAIK KELAS (DICENTANG) =====
    #         if santri_naik:
    #             message += f"\n=== PROSES SANTRI NAIK KELAS ({len(santri_naik)} siswa) ===\n"
                
    #             if self.status == 'naik':
    #                 # Siswa naik kelas hanya update tingkat dan tahun ajaran kelas lama
    #                 if self.next_class:
    #                     # Update kelas lama dengan tingkat baru dan tahun ajaran baru
    #                     self.kelas_id.write({
    #                         'name': self.next_class.id,
    #                         'tahunajaran_id': tahun_ajaran_berikutnya.id,
    #                         'walikelas_id': self.walikelas_id.id if self.walikelas_id else False,
    #                     })
    #                     message += f"Kelas {self.kelas_id.nama_kelas} berhasil diupdate ke {self.next_class.name} untuk tahun ajaran {tahun_ajaran_berikutnya.name}\n"
    #                     # Update siswa yang naik kelas
    #                     for siswa in santri_naik:
    #                         siswa.write({
    #                             'ruang_kelas_id': self.kelas_id.id,
    #                             'tahunajaran_id': tahun_ajaran_berikutnya.id,
    #                         })
    #                         count_siswa_naik += 1
    #                     message += f"Total {len(santri_naik)} siswa naik kelas ke {self.next_class.name}\n"
    #                 else:
    #                     message += "Gagal naik kelas - kelas selanjutnya tidak ditentukan\n"
                        
    #             elif self.status == 'lulus':
    #                 # Siswa lulus - tidak perlu kelas baru
    #                 for siswa in santri_naik:
    #                     siswa.write({
    #                         'status_kelulusan': 'lulus',
    #                         'tahun_lulus': tahun_ajaran_berikutnya.name,
    #                         'ruang_kelas_id': False,  # Siswa lulus tidak memiliki kelas
    #                     })
    #                     count_siswa_lulus += 1
                        
    #                 message += f"Total {len(santri_naik)} siswa lulus\n"
            
    #         # ===== PROSES SANTRI YANG TIDAK NAIK KELAS (TIDAK DICENTANG) =====
    #         if santri_tidak_naik:
    #             message += f"\n=== PROSES SANTRI TIDAK NAIK KELAS ({len(santri_tidak_naik)} siswa) ===\n"
    #             # Cari kelas dengan nama dan jurusan sama di tahun ajaran berikutnya
    #             kelas_lama = self.kelas_id
    #             # Pastikan pencarian nama kelas sesuai tipe field
    #             if hasattr(kelas_lama.name, 'id'):
    #                 name_val = kelas_lama.name.id
    #             else:
    #                 name_val = kelas_lama.name
    #             domain_kelas_tujuan = [
    #                 ('name', '=', name_val),
    #                 ('tahunajaran_id', '=', tahun_ajaran_berikutnya.id),
    #                 ('jenjang', '=', kelas_lama.jenjang),
    #             ]
    #             # Tambahkan filter tingkat (tingkat_id atau tingkat)
    #             if hasattr(kelas_lama, 'tingkat_id') and kelas_lama.tingkat_id:
    #                 domain_kelas_tujuan.append(('tingkat_id', '=', kelas_lama.tingkat_id.id))
    #             elif hasattr(kelas_lama, 'tingkat') and kelas_lama.tingkat:
    #                 domain_kelas_tujuan.append(('tingkat', '=', kelas_lama.tingkat.id))
    #             if hasattr(kelas_lama, 'jurusan_id') and kelas_lama.jurusan_id:
    #                 domain_kelas_tujuan.append(('jurusan_id', '=', kelas_lama.jurusan_id.id))
    #             # Cek jika kelas sudah ada
    #             kelas_tujuan = self.env['cdn.ruang_kelas'].search(domain_kelas_tujuan, limit=1)
    #             if kelas_tujuan:
    #                 message += f"Menggunakan kelas tidak naik existing: {kelas_tujuan.nama_kelas}\n"
    #             else:
    #                 # Buat kelas baru dengan nama dan jurusan sama untuk tahun ajaran berikutnya
    #                 kelas_tujuan_vals = {
    #                     'name': kelas_lama.name.id if hasattr(kelas_lama.name, 'id') else kelas_lama.name,
    #                     'tahunajaran_id': tahun_ajaran_berikutnya.id,
    #                     'walikelas_id': self.walikelas_id.id if self.walikelas_id else False,
    #                     'aktif_tidak': 'aktif',
    #                     'status': 'konfirm',
    #                     'angkatan_id': kelas_lama.angkatan_id.id if kelas_lama.angkatan_id else False,
    #                     'jenjang': kelas_lama.jenjang,
    #                 }
    #                 # Pastikan tingkat sama dengan kelas_lama
    #                 if hasattr(kelas_lama, 'tingkat_id') and kelas_lama.tingkat_id:
    #                     kelas_tujuan_vals['tingkat_id'] = kelas_lama.tingkat_id.id
    #                 elif hasattr(kelas_lama, 'tingkat') and kelas_lama.tingkat:
    #                     kelas_tujuan_vals['tingkat'] = kelas_lama.tingkat.id
    #                 if hasattr(kelas_lama, 'jurusan_id') and kelas_lama.jurusan_id:
    #                     kelas_tujuan_vals['jurusan_id'] = kelas_lama.jurusan_id.id
    #                 kelas_tujuan = self.env['cdn.ruang_kelas'].create(kelas_tujuan_vals)
    #                 message += f"Membuat kelas tidak naik baru: {kelas_tujuan.nama_kelas}\n"
    #             # Log detail kelas_tujuan
    #             _logger.info(f"Kelas tujuan (tinggal kelas): id={kelas_tujuan.id}, nama={kelas_tujuan.nama_kelas}, tahunajaran={kelas_tujuan.tahunajaran_id.name}, tingkat={kelas_tujuan.tingkat_id.name if hasattr(kelas_tujuan, 'tingkat_id') and kelas_tujuan.tingkat_id else '-'}, jurusan={kelas_tujuan.jurusan_id.name if hasattr(kelas_tujuan, 'jurusan_id') and kelas_tujuan.jurusan_id else '-'}")
    #             # Update siswa yang tidak naik kelas
    #             for siswa in santri_tidak_naik:
    #                 _logger.info(f"Update siswa tidak naik: {siswa.name} -> kelas tujuan: {kelas_tujuan.nama_kelas} (id={kelas_tujuan.id}), tahunajaran={tahun_ajaran_berikutnya.name}")
    #                 siswa.write({
    #                     'ruang_kelas_id': kelas_tujuan.id,  # Kelas tujuan = kelas tinggal kelas, tingkat sama
    #                     'tahunajaran_id': tahun_ajaran_berikutnya.id,  # Tahun ajaran naik
    #                 })
    #                 count_siswa_tidak_naik += 1
    #             message += f"Total {len(santri_tidak_naik)} siswa tidak naik kelas ke {kelas_tujuan.nama_kelas}\n"
            
    #         # ===== UPDATE STATUS KELAS LAMA =====
    #         # Nonaktifkan kelas lama jika semua siswa sudah dipindah
    #         # Nonaktifkan kelas lama hanya jika semua siswa lulus
    #         if self.status == 'lulus' and len(santri_naik) == len(self.partner_ids):
    #             self.kelas_id.write({'aktif_tidak': 'tidak'})
    #             message += f"\nKelas lama {self.kelas_id.nama_kelas} dinonaktifkan (semua siswa lulus)\n"
    #         elif len(santri_tidak_naik) > 0:
    #             message += f"\nKelas lama {self.kelas_id.nama_kelas} tetap aktif (ada siswa yang tinggal kelas)\n"
                    
    #     except Exception as e:
    #         error_msg = f"ERROR memproses kenaikan kelas: {str(e)}"
    #         message += f"- {error_msg}\n"
    #         _logger.error(error_msg)
    #         raise UserError(error_msg)
        
    #     # Commit perubahan
    #     try:
    #         self.env.cr.commit()
    #         _logger.info("Perubahan berhasil di-commit ke database")
    #     except Exception as e:
    #         _logger.error(f"Gagal melakukan commit perubahan: {str(e)}")
    #         raise UserError(f"Gagal menyimpan perubahan: {str(e)}")
        
    #     # Buat summary hasil proses
    #     result_message = f"Proses Kenaikan Kelas berhasil dilakukan!\n\n"
    #     result_message += f"Ringkasan Hasil:\n"
    #     result_message += f"- Siswa naik kelas: {count_siswa_naik}\n"
    #     result_message += f"- Siswa tidak naik: {count_siswa_tidak_naik}\n"
    #     result_message += f"- Siswa lulus: {count_siswa_lulus}\n"
    #     result_message += f"- Siswa tidak lulus: {count_siswa_tidak_lulus}\n"
    #     result_message += f"Total siswa diproses: {len(self.partner_ids)}\n\n"
    #     result_message += f"Detail Proses:\n{message}"
        
    #     _logger.info(f"Proses kenaikan kelas selesai dengan hasil: {result_message}")
        
    #     # Update field message_result
    #     self.message_result = result_message
        
    #     # Reset field centang semua siswa
    #     self.partner_ids.write({'centang': False})
        
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Hasil Kenaikan Kelas',
    #         'res_model': 'cdn.kenaikan_kelas',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': {
    #             'default_message_result': result_message,
    #             'default_kelas_id': False,
    #             'default_status': False,
    #             'default_partner_ids': [],
    #             'default_next_class': False,
    #         }
    #     }

    # def action_proses_kenaikan_kelas(self):
    #     """
    #     Aksi untuk memproses kenaikan kelas dengan memperbarui data siswa
    #     berdasarkan status centang masing-masing siswa
    #     """
    #     _logger.info(f"Memulai proses kenaikan kelas untuk tahun ajaran: {self.tahunajaran_id.name}")
        
    #     if not self.partner_ids:
    #         raise UserError("Belum ada santri yang dipilih!")
        
    #     if not self.kelas_id:
    #         raise UserError("Belum ada kelas yang dipilih!")
        
    #     self.ensure_one()
    #     message = ""
    #     count_siswa_naik = 0
    #     count_siswa_tidak_naik = 0
    #     count_siswa_lulus = 0
    #     count_siswa_tidak_lulus = 0
        
    #     # Mendapatkan tahun ajaran berikutnya
    #     try:
    #         current_year = int(self.tahunajaran_id.name.split('/')[0])
    #         next_year = current_year + 1
    #         next_ta_name = f"{next_year}/{next_year+1}"
            
    #         _logger.info(f"Current year: {current_year}, Next year: {next_year}")
    #         _logger.info(f"Mencari tahun ajaran dengan nama: {next_ta_name}")
            
    #         # Cari tahun ajaran berikutnya
    #         tahun_ajaran_berikutnya = self.env['cdn.ref_tahunajaran'].search([
    #             ('name', '=', next_ta_name)
    #         ], limit=1)
            
    #         _logger.info(f"Hasil pencarian tahun ajaran berikutnya: {tahun_ajaran_berikutnya.name if tahun_ajaran_berikutnya else 'Tidak ditemukan'}")
            
    #     except (ValueError, IndexError) as e:
    #         _logger.error(f"Format tahun ajaran tidak valid: {str(e)}")
    #         raise UserError(f"Format tahun ajaran tidak valid: {self.tahunajaran_id.name}. Format yang diharapkan: YYYY/YYYY")
        
    #     # Jika tahun ajaran berikutnya tidak ditemukan, buat yang baru
    #     if not tahun_ajaran_berikutnya:
    #         message += f"Tahun ajaran {next_ta_name} tidak ditemukan. Mencoba membuat tahun ajaran baru...\n"
    #         try:
    #             tahun_ajaran_berikutnya = self._create_next_tahun_ajaran(self.tahunajaran_id)
    #             message += f"Berhasil membuat tahun ajaran baru: {tahun_ajaran_berikutnya.name}\n\n"
    #         except Exception as e:
    #             message += f"Gagal membuat tahun ajaran baru: {str(e)}\n\n"
    #             raise UserError(f"Gagal membuat tahun ajaran baru: {str(e)}")
        
    #     # Pisahkan santri berdasarkan status centang
    #     santri_naik = self.partner_ids.filtered(lambda s: s.centang == True)
    #     santri_tidak_naik = self.partner_ids.filtered(lambda s: s.centang == False)
        
    #     _logger.info(f"Santri naik kelas: {len(santri_naik)}")
    #     _logger.info(f"Santri tidak naik kelas: {len(santri_tidak_naik)}")
        
    #     try:
    #         # ====== SIMPAN DATA KELAS LAMA SEBELUM DIUPDATE ======
    #         kelas_lama_db = self.env['cdn.ruang_kelas'].browse(self.kelas_id.id)
    #         tingkat_lama_id = kelas_lama_db.tingkat.id if hasattr(kelas_lama_db, 'tingkat') and kelas_lama_db.tingkat else None
    #         name_lama = kelas_lama_db.name.id if hasattr(kelas_lama_db.name, 'id') else kelas_lama_db.name
    #         jurusan_lama_id = kelas_lama_db.jurusan_id.id if hasattr(kelas_lama_db, 'jurusan_id') and kelas_lama_db.jurusan_id else None
    #         jenjang_lama = kelas_lama_db.jenjang

    #         # ===== PROSES SANTRI YANG NAIK KELAS (DICENTANG) =====
    #         if santri_naik:
    #             message += f"\n=== PROSES SANTRI NAIK KELAS ({len(santri_naik)} siswa) ===\n"
    #             if self.status == 'naik':
    #                 # Hanya update tingkat dan tahun ajaran pada kelas lama, siswa tetap di kelas lama
    #                 if self.next_class:
    #                     self.kelas_id.write({
    #                         'name': self.next_class.id,
    #                         'tingkat': self.next_class.tingkat_id.id if hasattr(self.next_class, 'tingkat_id') and self.next_class.tingkat_id else None,
    #                         'tahunajaran_id': tahun_ajaran_berikutnya.id,
    #                         'walikelas_id': self.walikelas_id.id if self.walikelas_id else False,
    #                     })
    #                     message += f"Kelas {self.kelas_id.nama_kelas} berhasil diupdate ke {self.next_class.name} untuk tahun ajaran {tahun_ajaran_berikutnya.name}\n"
    #                     for siswa in santri_naik:
    #                         siswa.write({
    #                             'ruang_kelas_id': self.kelas_id.id,
    #                             'tahunajaran_id': tahun_ajaran_berikutnya.id,
    #                         })
    #                         count_siswa_naik += 1
    #                     message += f"Total {len(santri_naik)} siswa naik kelas ke {self.next_class.name}\n"
    #                 else:
    #                     message += "Gagal naik kelas - kelas selanjutnya tidak ditentukan\n"
                        
    #             elif self.status == 'lulus':
    #                 # Siswa lulus - tidak perlu kelas baru
    #                 for siswa in santri_naik:
    #                     siswa.write({
    #                         'status_kelulusan': 'lulus',
    #                         'tahun_lulus': tahun_ajaran_berikutnya.name,
    #                         'ruang_kelas_id': False,  # Siswa lulus tidak memiliki kelas
    #                     })
    #                     count_siswa_lulus += 1
                        
    #                 message += f"Total {len(santri_naik)} siswa lulus\n"
            
    #         # ===== PROSES SANTRI YANG TIDAK NAIK KELAS (TIDAK DICENTANG) =====
    #         if santri_tidak_naik:
    #             message += f"\n=== PROSES SANTRI TIDAK NAIK KELAS ({len(santri_tidak_naik)} siswa) ===\n"
                
    #             # Buat kelas tinggal kelas untuk santri yang tidak naik
    #             kelas_tinggal_vals = {
    #                 'name': self.kelas_id.name.id,  # Tetap di master kelas yang sama
    #                 'tahunajaran_id': tahun_ajaran_berikutnya.id,  # Tapi tahun ajaran baru
    #                 'walikelas_id': self.walikelas_id.id if self.walikelas_id else False,
    #                 'aktif_tidak': 'aktif',
    #                 'status': 'konfirm',
    #                 'angkatan_id': self.kelas_id.angkatan_id.id if self.kelas_id.angkatan_id else False,
    #                 'jenjang': self.kelas_id.jenjang,
    #                 'tingkat': tingkat_lama_id,
    #             }
                
    #             # Cek apakah kelas tinggal kelas sudah ada
    #             existing_tinggal_kelas = self.env['cdn.ruang_kelas'].search([
    #                 ('name', '=', self.kelas_id.name.id),
    #                 ('tahunajaran_id', '=', tahun_ajaran_berikutnya.id),
    #             ], limit=1)
                
    #             if existing_tinggal_kelas:
    #                 kelas_tinggal = existing_tinggal_kelas
    #                 message += f"Menggunakan kelas tinggal kelas existing: {kelas_tinggal.nama_kelas}\n"
    #             else:
    #                 kelas_tinggal = self.env['cdn.ruang_kelas'].create(kelas_tinggal_vals)
    #                 message += f"Membuat kelas tinggal kelas: {kelas_tinggal.nama_kelas}\n"
                
    #             # Update siswa yang tidak naik kelas
    #             for siswa in santri_tidak_naik:
    #                 if self.status == 'lulus':  # Seharusnya lulus tapi tidak naik = tidak lulus
    #                     siswa.write({
    #                         'ruang_kelas_id': kelas_tinggal.id,
    #                         'tahun_ajaran_id': tahun_ajaran_berikutnya.id,
    #                         'status_kelulusan': 'tidak_lulus',
    #                         'walikelas_id': self.walikelas_id.id if self.walikelas_id else False,
    #                     })
    #                     count_siswa_tidak_lulus += 1
    #                 else:  # Status naik tapi tidak naik = tidak naik kelas
    #                     siswa.write({
    #                         'ruang_kelas_id': kelas_tinggal.id,
    #                         'tahunajaran_id': tahun_ajaran_berikutnya.id,
                            
    #                     })
    #                     count_siswa_tidak_naik += 1
                
    #             if self.status == 'lulus':
    #                 message += f"Total {len(santri_tidak_naik)} siswa tidak lulus (tinggal kelas)\n"
    #             else:
    #                 message += f"Total {len(santri_tidak_naik)} siswa tidak naik kelas (tinggal kelas)\n"
            
    #         # ===== UPDATE STATUS KELAS LAMA =====
    #         # Nonaktifkan kelas lama jika semua siswa sudah dipindah
    #         if len(santri_naik) == len(self.partner_ids):
    #             # Semua siswa naik/lulus, nonaktifkan kelas lama
    #             self.kelas_id.write({'aktif_tidak': 'tidak'})
    #             message += f"\nKelas lama {self.kelas_id.nama_kelas} dinonaktifkan (semua siswa naik/lulus)\n"
    #         elif len(santri_tidak_naik) > 0:
    #             # Ada siswa yang tinggal kelas, kelas lama tetap aktif untuk tahun ini
    #             # Tapi tahun ajarannya tidak diubah karena masih digunakan untuk siswa yang tidak naik
    #             message += f"\nKelas lama {self.kelas_id.nama_kelas} tetap aktif (ada siswa yang tinggal kelas)\n"
                    
    #     except Exception as e:
    #         error_msg = f"ERROR memproses kenaikan kelas: {str(e)}"
    #         message += f"- {error_msg}\n"
    #         _logger.error(error_msg)
    #         raise UserError(error_msg)
        
    #     # Commit perubahan
    #     try:
    #         self.env.cr.commit()
    #         _logger.info("Perubahan berhasil di-commit ke database")
    #     except Exception as e:
    #         _logger.error(f"Gagal melakukan commit perubahan: {str(e)}")
    #         raise UserError(f"Gagal menyimpan perubahan: {str(e)}")
        
    #     # Buat summary hasil proses
    #     result_message = f"Proses Kenaikan Kelas berhasil dilakukan!\n\n"
    #     result_message += f"Ringkasan Hasil:\n"
    #     result_message += f"- Siswa naik kelas: {count_siswa_naik}\n"
    #     result_message += f"- Siswa tidak naik: {count_siswa_tidak_naik}\n"
    #     result_message += f"- Siswa lulus: {count_siswa_lulus}\n"
    #     result_message += f"- Siswa tidak lulus: {count_siswa_tidak_lulus}\n"
    #     result_message += f"Total siswa diproses: {len(self.partner_ids)}\n\n"
    #     result_message += f"Detail Proses:\n{message}"
        
    #     _logger.info(f"Proses kenaikan kelas selesai dengan hasil: {result_message}")
        
    #     # Update field message_result
    #     self.message_result = result_message
        
    #     # Reset field centang semua siswa
    #     self.partner_ids.write({'centang': False})
        
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Hasil Kenaikan Kelas',
    #         'res_model': 'cdn.kenaikan_kelas',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': {
    #             'default_message_result': result_message,
    #             'default_kelas_id': False,
    #             'default_status': False,
    #             'default_partner_ids': [],
    #             'default_next_class': False,
    #         }
    #     }

    def action_proses_kenaikan_kelas(self):
        """
        Aksi untuk memproses kenaikan kelas dengan memperbarui data siswa
        Membedakan siswa yang naik kelas dan tidak naik kelas berdasarkan centang
        """
        _logger.info(f"Memulai proses kenaikan kelas untuk tahun ajaran: {self.tahunajaran_id.name}")
        
        if not self.partner_ids:
            raise UserError("Belum ada santri yang dipilih!")
        
        if not self.kelas_id:
            raise UserError("Belum ada kelas yang dipilih!")
        
        self.ensure_one()
        message = ""
        count_siswa_naik = 0
        count_siswa_tidak_naik = 0
        count_siswa_lulus = 0
        count_siswa_tidak_lulus = 0
        
        # Mendapatkan tahun ajaran berikutnya
        try:
            current_year = int(self.tahunajaran_id.name.split('/')[0])
            next_year = current_year + 1
            next_ta_name = f"{next_year}/{next_year+1}"
            
            _logger.info(f"Current year: {current_year}, Next year: {next_year}")
            _logger.info(f"Mencari tahun ajaran dengan nama: {next_ta_name}")
            
            # Cari tahun ajaran berikutnya
            tahun_ajaran_berikutnya = self.env['cdn.ref_tahunajaran'].search([
                ('name', '=', next_ta_name)
            ], limit=1)
            
            _logger.info(f"Hasil pencarian tahun ajaran berikutnya: {tahun_ajaran_berikutnya.name if tahun_ajaran_berikutnya else 'Tidak ditemukan'}")
            
        except (ValueError, IndexError) as e:
            _logger.error(f"Format tahun ajaran tidak valid: {str(e)}")
            raise UserError(f"Format tahun ajaran tidak valid: {self.tahunajaran_id.name}. Format yang diharapkan: YYYY/YYYY")
        
        # Jika tahun ajaran berikutnya tidak ditemukan, buat yang baru
        if not tahun_ajaran_berikutnya:
            message += f"Tahun ajaran {next_ta_name} tidak ditemukan. Mencoba membuat tahun ajaran baru...\n"
            try:
                tahun_ajaran_berikutnya = self._create_next_tahun_ajaran(self.tahunajaran_id)
                message += f"Berhasil membuat tahun ajaran baru: {tahun_ajaran_berikutnya.name}\n\n"
            except Exception as e:
                message += f"Gagal membuat tahun ajaran baru: {str(e)}\n\n"
                raise UserError(f"Gagal membuat tahun ajaran baru: {str(e)}")
        
        # Pisahkan siswa berdasarkan centang (naik/tidak naik)
        siswa_naik = self.partner_ids.filtered(lambda s: s.centang == True)
        siswa_tidak_naik = self.partner_ids.filtered(lambda s: s.centang == False)
        
        _logger.info(f"Siswa naik kelas: {len(siswa_naik)}")
        _logger.info(f"Siswa tidak naik kelas: {len(siswa_tidak_naik)}")
        
        try:
            # ===== PROSES SISWA YANG NAIK KELAS =====
            if siswa_naik:
                if self.status in ['naik', 'lulus']:
                    if self.status == 'naik' and self.next_class:
                        # Update kelas lama dengan kelas baru dan tahun ajaran baru
                        self.kelas_id.write({
                            'name': self.next_class.id,
                            'tahunajaran_id': tahun_ajaran_berikutnya.id,
                            'walikelas_id': self.walikelas_id.id,
                        })
                        message += f"Kelas {self.kelas_id.nama_kelas} berhasil diupdate ke {self.next_class.name} untuk tahun ajaran {tahun_ajaran_berikutnya.name}\n"
                        
                        # Update status siswa yang naik
                        for siswa in siswa_naik:
                            siswa.write({
                                'tahunajaran_id': tahun_ajaran_berikutnya.id,
                                
                            })
                            count_siswa_naik += 1
                            
                        message += f"Total {len(siswa_naik)} siswa naik kelas ke {self.next_class.name}\n"
                        
                    elif self.status == 'lulus':
                        # Siswa lulus - kelas dinonaktifkan
                        self.kelas_id.write({
                            'aktif_tidak': 'tidak',
                        })
                        message += f"Kelas {self.kelas_id.nama_kelas} dinonaktifkan karena siswa lulus\n"
                        
                        # Update status siswa yang lulus
                        for siswa in siswa_naik:
                            siswa.write({
                                'status_kelulusan': 'lulus',
                                'tahun_lulus': tahun_ajaran_berikutnya.name,
                            })
                            count_siswa_lulus += 1
                            
                        message += f"Total {len(siswa_naik)} siswa lulus\n"
                    else:
                        message += "Gagal naik kelas - kelas selanjutnya tidak ditentukan\n"
            
            # ===== PROSES SISWA YANG TIDAK NAIK KELAS =====
            if siswa_tidak_naik:
                # Cari atau buat kelas untuk siswa yang tidak naik
                kelas_tidak_naik = self._get_or_create_class_for_repeat_students(
                    self.kelas_id, tahun_ajaran_berikutnya
                )
                
                if kelas_tidak_naik:
                    # Pindahkan siswa yang tidak naik ke kelas baru/yang sudah ada
                    for siswa in siswa_tidak_naik:
                        siswa.write({
                            'ruang_kelas_id': kelas_tidak_naik.id,
                            'tahunajaran_id': tahun_ajaran_berikutnya.id,
                        
                        })
                        count_siswa_tidak_naik += 1
                    
                    message += f"Total {len(siswa_tidak_naik)} siswa tidak naik kelas, dipindah ke kelas {kelas_tidak_naik.nama_kelas}\n"
                else:
                    message += f"Gagal memproses {len(siswa_tidak_naik)} siswa yang tidak naik kelas - tidak dapat membuat/menemukan kelas\n"
                    
        except Exception as e:
            error_msg = f"ERROR memproses kenaikan kelas: {str(e)}"
            message += f"- {error_msg}\n"
            _logger.error(error_msg)
            raise UserError(error_msg)
        
        # Commit perubahan
        try:
            self.env.cr.commit()
            _logger.info("Perubahan berhasil di-commit ke database")
        except Exception as e:
            _logger.error(f"Gagal melakukan commit perubahan: {str(e)}")
            raise UserError(f"Gagal menyimpan perubahan: {str(e)}")
        
        # Buat summary hasil proses
        total_siswa = len(self.partner_ids)
        result_message = f"Proses Kenaikan Kelas berhasil dilakukan!\n\n"
        result_message += f"Ringkasan Hasil:\n"
        result_message += f"- Siswa naik kelas: {count_siswa_naik}\n"
        result_message += f"- Siswa tidak naik: {count_siswa_tidak_naik}\n"
        result_message += f"- Siswa lulus: {count_siswa_lulus}\n"
        result_message += f"- Siswa tidak lulus: {count_siswa_tidak_lulus}\n"
        result_message += f"Total siswa diproses: {total_siswa}\n\n"
        result_message += f"Detail Proses:\n{message}"
        
        _logger.info(f"Proses kenaikan kelas selesai dengan hasil: {result_message}")
        
        # Update field message_result
        self.message_result = result_message
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Hasil Kenaikan Kelas',
            'res_model': 'cdn.kenaikan_kelas',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_message_result': result_message,
                'default_kelas_id': False,
                'default_status': False,
                'default_partner_ids': [],
                'default_next_class': False,
            }
        }


    def _get_or_create_class_for_repeat_students(self, current_class, next_tahun_ajaran):
        """
        Mencari atau membuat kelas untuk siswa yang tidak naik kelas
        Kelas harus memiliki tingkat yang sama dengan kelas saat ini
        """
        try:
            # Cari kelas yang sudah ada dengan kriteria yang sama di tahun ajaran berikutnya
            existing_class = self.env['cdn.ruang_kelas'].search([
                ('tahunajaran_id', '=', next_tahun_ajaran.id),
                ('tingkat', '=', current_class.tingkat.id if current_class.tingkat else False),
                ('nama_kelas', '=', current_class.nama_kelas),
                ('jurusan_id', '=', current_class.jurusan_id.id if current_class.jurusan_id else False),
                ('aktif_tidak', '=', 'aktif'),
            ], limit=1)
            
            if existing_class:
                _logger.info(f"Menggunakan kelas yang sudah ada: {existing_class.nama_kelas}")
                return existing_class
            
            # Jika tidak ada, buat kelas baru
            _logger.info(f"Membuat kelas baru untuk siswa yang tidak naik")
            
            # Siapkan data untuk kelas baru
            new_class_vals = {
                'name': current_class.name.id if current_class.name else False,  # Master kelas yang sama
                'tahunajaran_id': next_tahun_ajaran.id,
                'tingkat': current_class.tingkat.id if current_class.tingkat else False,
                'nama_kelas': current_class.nama_kelas,
                'jurusan_id': current_class.jurusan_id.id if current_class.jurusan_id else False,
                'angkatan_id': current_class.angkatan_id.id if current_class.angkatan_id else False,
                'walikelas_id': current_class.walikelas_id.id if current_class.walikelas_id else False,
                'jenjang': current_class.jenjang,
                'aktif_tidak': 'aktif',
                'status': 'konfirm',
                'keterangan': f'Kelas untuk siswa yang tidak naik dari {current_class.nama_kelas} tahun {current_class.tahunajaran_id.name}'
            }
            
            # Hapus field None/False yang tidak perlu
            new_class_vals = {k: v for k, v in new_class_vals.items() if v is not False}
            
            # Buat kelas baru
            new_class = self.env['cdn.ruang_kelas'].sudo().create(new_class_vals)
            
            if new_class:
                _logger.info(f"Berhasil membuat kelas baru: {new_class.nama_kelas} untuk tahun {next_tahun_ajaran.name}")
                return new_class
            else:
                _logger.error("Gagal membuat kelas baru")
                return False
                
        except Exception as e:
            _logger.error(f"Error dalam _get_or_create_class_for_repeat_students: {str(e)}")
            return False



# from odoo import fields, models, api, _
# from odoo.exceptions import UserError
# from datetime import datetime, timezone, timedelta
# from dateutil.relativedelta import relativedelta
# import logging

# _logger = logging.getLogger(__name__)

# class KenaikanKelas(models.Model):
#     _name           = 'cdn.kenaikan_kelas'
#     _description    = 'Menu POP UP untuk mengatur kenaikan kelas dan kelas yang lulus'
#     _rec_name       = 'tahunajaran_id'

#     # def _default_tahunajaran(self):
#     #    return self.env['res.company'].search([('id','=',1)]).tahun_ajaran_aktif

#     def _default_tahunajaran(self):
#         """
#         Menentukan tahun ajaran default berdasarkan tanggal Indonesia (WIB)
#         """
#         # Zona waktu Indonesia (WIB = UTC+7) tanpa pytz
#         indonesia_tz = timezone(timedelta(hours=7))
        
#         # Dapatkan waktu saat ini di Indonesia
#         now_indonesia = datetime.now(indonesia_tz)
        
#         current_year = now_indonesia.year
#         current_month = now_indonesia.month
        
#         # Logika tahun ajaran Indonesia (Juli - Juni)
#         if current_month <= 6:  # Januari - Juni
#             start_year = current_year - 1
#             end_year = current_year
#         else:  # Juli - Desember  
#             start_year = current_year
#             end_year = current_year + 1
        
#         # Format tahun ajaran
#         tahun_ajaran_string = f"{start_year}/{end_year}"
        
#         # Debug info (bisa dihapus di production)
#         import logging
#         _logger = logging.getLogger(__name__)
#         _logger.info(f"Waktu Indonesia: {now_indonesia.strftime('%Y-%m-%d %H:%M:%S %Z')}")
#         _logger.info(f"Tahun Ajaran: {tahun_ajaran_string}")
        
#         # Cari atau buat record tahun ajaran
#         tahun_ajaran = self.env['cdn.ref_tahunajaran'].search([
#             ('name', '=', tahun_ajaran_string)
#         ], limit=1)
        
#         if tahun_ajaran:
#             return tahun_ajaran.id
#         else:
#             # Auto-create jika belum ada
#             try:
#                 new_tahun_ajaran = self.env['cdn.ref_tahunajaran'].create({
#                     'name': tahun_ajaran_string,
#                     'aktif': True,
#                     # Sesuaikan field lain dengan model Anda
#                 })
#                 _logger.info(f"Auto-created tahun ajaran: {tahun_ajaran_string}")
#                 return new_tahun_ajaran.id
#             except Exception as e:
#                 _logger.error(f"Gagal create tahun ajaran {tahun_ajaran_string}: {e}")
#                 return False

#     def _get_indonesia_time(self):
#         """Helper function untuk mendapatkan waktu Indonesia"""
#         indonesia_tz = pytz.timezone('Asia/Jakarta')
#         return datetime.now(indonesia_tz)
    
#     def _default_tahunajaran_advanced(self):
#         """
#         Versi advanced dengan multiple timezone Indonesia dan tanggal cut-off custom
#         """
#         # Indonesia punya 3 zona waktu:
#         # WIB (UTC+7): Jakarta, Sumatera, Jawa, Kalimantan Barat & Tengah
#         # WITA (UTC+8): Bali, NTB, NTT, Kalimantan Timur & Selatan, Sulawesi
#         # WIT (UTC+9): Maluku, Papua
        
#         # Default menggunakan WIB (Jakarta) karena ini zona waktu paling umum
#         # indonesia_tz = pytz.timezone('Asia/Jakarta')  # WIB
#         indonesia_tz = pytz.timezone('Asia/Makassar')  # WITA
#         # indonesia_tz = pytz.timezone('Asia/Jayapura')  # WIT
        
#         now_indonesia = datetime.now(indonesia_tz)
        
#         # Bisa custom tanggal cut-off (misalnya 15 Juli)
#         cut_off_month = 7
#         cut_off_day = 15
        
#         current_year = now_indonesia.year
#         current_month = now_indonesia.month
#         current_day = now_indonesia.day
        
#         # Cek apakah sudah lewat cut-off date
#         if (current_month < cut_off_month) or \
#            (current_month == cut_off_month and current_day < cut_off_day):
#             # Masih tahun ajaran lama
#             start_year = current_year - 1
#             end_year = current_year
#         else:
#             # Sudah tahun ajaran baru
#             start_year = current_year
#             end_year = current_year + 1
        
#         tahun_ajaran_string = f"{start_year}/{end_year}"
        
#         # Log untuk debugging
#         import logging
#         _logger = logging.getLogger(__name__)
#         _logger.info(f"Indonesia Time ({indonesia_tz.zone}): {now_indonesia.strftime('%Y-%m-%d %H:%M:%S')}")
#         _logger.info(f"Cut-off: {cut_off_day}/{cut_off_month}, Current: {current_day}/{current_month}")
#         _logger.info(f"Tahun Ajaran: {tahun_ajaran_string}")
        
#         # Cari record tahun ajaran
#         tahun_ajaran = self.env['cdn.ref_tahunajaran'].search([
#             ('name', '=', tahun_ajaran_string)
#         ], limit=1)
        
#         return tahun_ajaran.id if tahun_ajaran else False

#     # Method untuk testing timezone
#     @api.model
#     def test_timezone_info(self):
#         """Method untuk testing - bisa dipanggil dari external API atau cron"""
#         indonesia_tz = pytz.timezone('Asia/Jakarta')
#         utc_now = datetime.utcnow()
#         indonesia_now = datetime.now(indonesia_tz)
        
#         return {
#             'utc_time': utc_now.strftime('%Y-%m-%d %H:%M:%S UTC'),
#             'indonesia_time': indonesia_now.strftime('%Y-%m-%d %H:%M:%S %Z'),
#             'timezone': str(indonesia_tz),
#             'current_academic_year': self._get_current_academic_year_string()
#         }
    
#     def _get_current_academic_year_string(self):
#         """Helper untuk mendapatkan string tahun ajaran saat ini"""
#         indonesia_tz = pytz.timezone('Asia/Jakarta')
#         now = datetime.now(indonesia_tz)
        
#         if now.month <= 6:
#             return f"{now.year-1}/{now.year}"
#         else:
#             return f"{now.year}/{now.year+1}"


#     jenjang             = fields.Selection(
#         selection=[('paud', 'PAUD'), ('tk', 'TK/RA'), ('sd', 'SD/MI'),
#                    ('smp', 'SMP/MTS'), ('sma', 'SMA/MA/SMK'), ('nonformal', 'Nonformal')],
#         string="Jenjang", 
#         store=True, 
#         related='kelas_id.jenjang', 
#     )
    
#     tahunajaran_id      = fields.Many2one(comodel_name="cdn.ref_tahunajaran", string="Tahun Ajaran", default=_default_tahunajaran, readonly=False, store=True)
#     kelas_id            = fields.Many2one('cdn.ruang_kelas', string='Kelas', domain="[('tahunajaran_id','=',tahunajaran_id), ('aktif_tidak','=','aktif'), ('status','=','konfirm')]")
#     partner_ids         = fields.Many2many('cdn.siswa', 'kenaikan_santri_rel', 'kenaikan_id', 'santri_id', 'Santri')
    
#     tingkat_id          = fields.Many2one('cdn.tingkat', string="Tingkat", store=True, readonly=False)    

#     walikelas_id = fields.Many2one(
#         comodel_name="hr.employee",  
#         string="Wali Kelas",  
#         domain="[('jns_pegawai','=','guru')]"
#     )
    
#     status = fields.Selection(
#         selection=[('naik', 'Naik Kelas'), ('tidak_naik', 'Tidak Naik'), ('lulus', 'Lulus'), ('tidak_lulus', 'Tidak Lulus'), ],
#         string="Status",
#     )

#     # Field baru untuk menampilkan kelas selanjutnya
#     next_class = fields.Many2one(
#         comodel_name='cdn.master_kelas',
#         string='Kelas Selanjutnya',
#         compute='_compute_next_class',
#         store=True,
#         help="Kelas selanjutnya berdasarkan tingkat, nama kelas, dan jurusan"
#     )
    
#     # Field untuk menampilkan hasil proses
#     message_result = fields.Text(string="Hasil Proses", readonly=True)
        
#     angkatan_id = fields.Many2one(related="kelas_id.angkatan_id", string="Angkatan", readoly=True)    
    

#     @api.onchange('tahunajaran_id')
#     def _onchange_tahunajaran_id(self):
#         """
#         Reset semua field ketika tahun ajaran berubah
#         """
#         if self.tahunajaran_id:
#             # Reset semua field yang terkait
#             self.kelas_id = False
#             self.partner_ids = [(5, 0, 0)]  # Clear all many2many records
#             self.tingkat_id = False
#             self.walikelas_id = False
#             self.status = False
#             self.next_class = False
#             self.message_result = False
            
#             # Return domain update untuk kelas_id
#             return {
#                 'domain': {
#                     'kelas_id': [
#                         ('tahunajaran_id', '=', self.tahunajaran_id.id),
#                         ('aktif_tidak', '=', 'aktif'),
#                         ('status', '=', 'konfirm')
#                     ]
#                 }
#             }
#         else:
#             # Jika tahun ajaran dikosongkan, reset semua
#             self.kelas_id = False
#             self.partner_ids = [(5, 0, 0)]
#             self.tingkat_id = False
#             self.walikelas_id = False
#             self.status = False
#             self.next_class = False
#             self.message_result = False
            
#             return {
#                 'domain': {
#                     'kelas_id': [('id', '=', False)]  # Empty domain
#                 }
#             }

    

#     @api.depends('kelas_id', 'kelas_id.nama_kelas', 'kelas_id.jurusan_id', 'kelas_id.tingkat', 'status')
#     def _compute_next_class(self):
#         """Compute kelas selanjutnya berdasarkan kelas yang dipilih dan status"""
#         for record in self:
#             if not record.kelas_id:
#                 record.next_class = False
#                 continue
            
#             # Jika status adalah tidak_naik atau tidak_lulus, 
#             # maka next_class tetap menampilkan kelas yang sama
#             if record.status in ['tidak_naik', 'tidak_lulus']:
#                 # Cari master kelas yang sesuai dengan kelas_id saat ini
#                 current_class = record.kelas_id
#                 current_tingkat = current_class.tingkat
#                 current_nama_kelas = current_class.nama_kelas
#                 current_jurusan = current_class.jurusan_id
                
#                 if not current_tingkat:
#                     record.next_class = False
#                     continue
                
#                 # Cari master kelas yang cocok dengan kelas saat ini
#                 domain = [('tingkat', '=', current_tingkat.id)]
                
#                 # Filter berdasarkan nama kelas jika ada
#                 if current_nama_kelas:
#                     domain.append(('nama_kelas', '=', current_nama_kelas))
                
#                 # Filter berdasarkan jurusan jika ada
#                 if current_jurusan:
#                     domain.append(('jurusan_id', '=', current_jurusan.id))
                
#                 # Cari master kelas yang cocok dengan kelas saat ini
#                 current_master_class = self.env['cdn.master_kelas'].search(domain, limit=1)
                
#                 # Jika tidak ditemukan dengan nama_kelas, coba tanpa nama_kelas (hanya tingkat dan jurusan)
#                 if not current_master_class and current_jurusan:
#                     domain_alternative = [
#                         ('tingkat', '=', current_tingkat.id),
#                         ('jurusan_id', '=', current_jurusan.id)
#                     ]
#                     current_master_class = self.env['cdn.master_kelas'].search(domain_alternative, limit=1)
                
#                 # Jika masih tidak ditemukan, coba hanya berdasarkan tingkat
#                 if not current_master_class:
#                     domain_simple = [('tingkat', '=', current_tingkat.id)]
#                     current_master_class = self.env['cdn.master_kelas'].search(domain_simple, limit=1)
                
#                 record.next_class = current_master_class.id if current_master_class else False
#                 continue
            
#                         # Untuk status naik, cari kelas selanjutnya
#             # Ambil data kelas saat ini
#             current_class = record.kelas_id
#             current_tingkat = current_class.tingkat
#             current_nama_kelas = current_class.nama_kelas
#             current_jurusan = current_class.jurusan_id
            
#             if not current_tingkat:
#                 record.next_class = False
#                 continue
            
#             # Cari tingkat selanjutnya
#             next_tingkat = record._get_next_tingkat(current_tingkat)
#             if not next_tingkat:
#                 record.next_class = False
#                 continue
            
#             # Cari master kelas yang cocok dengan kriteria:
#             # 1. Tingkat = tingkat selanjutnya
#             # 2. nama_kelas = sama dengan kelas saat ini (jika ada)
#             # 3. jurusan_id = sama dengan kelas saat ini (jika ada)
#             domain = [('tingkat', '=', next_tingkat.id)]
            
#             # Filter berdasarkan nama kelas jika ada
#             if current_nama_kelas:
#                 domain.append(('nama_kelas', '=', current_nama_kelas))
            
#             # Filter berdasarkan jurusan jika ada
#             if current_jurusan:
#                 domain.append(('jurusan_id', '=', current_jurusan.id))
            
#             # Cari master kelas yang cocok
#             next_master_class = self.env['cdn.master_kelas'].search(domain, limit=1)
            
#             # Jika tidak ditemukan dengan nama_kelas, coba tanpa nama_kelas (hanya tingkat dan jurusan)
#             if not next_master_class and current_jurusan:
#                 domain_alternative = [
#                     ('tingkat', '=', next_tingkat.id),
#                     ('jurusan_id', '=', current_jurusan.id)
#                 ]
#                 next_master_class = self.env['cdn.master_kelas'].search(domain_alternative, limit=1)
            
#             # Jika masih tidak ditemukan, coba hanya berdasarkan tingkat
#             if not next_master_class:
#                 domain_simple = [('tingkat', '=', next_tingkat.id)]
#                 next_master_class = self.env['cdn.master_kelas'].search(domain_simple, limit=1)
            
#             record.next_class = next_master_class.id if next_master_class else False
            
        
#     def _get_next_tingkat(self, current_tingkat):
#         """Mendapatkan tingkat selanjutnya berdasarkan tingkat saat ini"""
#         if not current_tingkat:
#             return False
        
#         # Coba ambil urutan tingkat
#         current_order = None
        
#         # Cara 1: Berdasarkan field urutan
#         if hasattr(current_tingkat, 'urutan') and current_tingkat.urutan:
#             current_order = current_tingkat.urutan
        
#         # Cara 2: Berdasarkan field level
#         elif hasattr(current_tingkat, 'level') and current_tingkat.level:
#             current_order = current_tingkat.level
        
#         # Cara 3: Extract dari nama tingkat
#         elif hasattr(current_tingkat, 'name') and current_tingkat.name:
#             current_order = self._extract_tingkat_number(current_tingkat.name)
        
#         if not current_order:
#             return False
        
#         next_order = current_order + 1
        
#         # Cari tingkat dengan urutan selanjutnya
#         # Prioritas pencarian: urutan -> level -> nama
#         next_tingkat = None
        
#         # Cari berdasarkan urutan
#         if hasattr(current_tingkat, 'urutan'):
#             next_tingkat = self.env['cdn.tingkat'].search([('urutan', '=', next_order)], limit=1)
        
#         # Jika tidak ditemukan, cari berdasarkan level
#         if not next_tingkat and hasattr(current_tingkat, 'level'):
#             next_tingkat = self.env['cdn.tingkat'].search([('level', '=', next_order)], limit=1)
        
#         # Jika tidak ditemukan, cari berdasarkan nama
#         if not next_tingkat:
#             # Cari berdasarkan angka
#             next_tingkat = self.env['cdn.tingkat'].search([
#                 '|', '|',
#                 ('name', 'ilike', str(next_order)),
#                 ('name', 'ilike', self._number_to_roman(next_order)),
#                 ('name', 'ilike', self._number_to_word(next_order))
#             ], limit=1)
        
#         return next_tingkat

#     def _extract_tingkat_number(self, tingkat_name):
#         """Extract nomor tingkat dari nama tingkat"""
#         if not tingkat_name:
#             return None
        
#         tingkat_name = str(tingkat_name).upper()
        
#         # Dictionary untuk konversi angka romawi ke angka
#         roman_to_num = {
#             'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6,
#             'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10, 'XI': 11, 'XII': 12,
#             'XIII': 13, 'XIV': 14, 'XV': 15, 'XVI': 16, 'XVII': 17, 'XVIII': 18
#         }
        
#         # Dictionary untuk konversi kata ke angka
#         word_to_num = {
#             'SATU': 1, 'DUA': 2, 'TIGA': 3, 'EMPAT': 4, 'LIMA': 5, 'ENAM': 6,
#             'TUJUH': 7, 'DELAPAN': 8, 'SEMBILAN': 9, 'SEPULUH': 10, 
#             'SEBELAS': 11, 'DUABELAS': 12, 'TIGABELAS': 13, 'EMPATBELAS': 14
#         }
        
#         # Cari angka langsung
#         import re
#         numbers = re.findall(r'\d+', tingkat_name)
#         if numbers:
#             return int(numbers[0])
        
#         # Cari angka romawi
#         for roman, num in roman_to_num.items():
#             if roman in tingkat_name:
#                 return num
        
#         # Cari kata
#         for word, num in word_to_num.items():
#             if word in tingkat_name:
#                 return num
        
#         return None

#     def _number_to_roman(self, num):
#         """Convert number to roman numeral"""
#         roman_numerals = {
#             1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI',
#             7: 'VII', 8: 'VIII', 9: 'IX', 10: 'X', 11: 'XI', 12: 'XII',
#             13: 'XIII', 14: 'XIV', 15: 'XV', 16: 'XVI', 17: 'XVII', 18: 'XVIII'
#         }
#         return roman_numerals.get(num, str(num))

#     def _number_to_word(self, num):
#         """Convert number to Indonesian word"""
#         word_numerals = {
#             1: 'SATU', 2: 'DUA', 3: 'TIGA', 4: 'EMPAT', 5: 'LIMA', 6: 'ENAM',
#             7: 'TUJUH', 8: 'DELAPAN', 9: 'SEMBILAN', 10: 'SEPULUH',
#             11: 'SEBELAS', 12: 'DUABELAS', 13: 'TIGABELAS', 14: 'EMPATBELAS'
#         }
#         return word_numerals.get(num, str(num))

#     @api.onchange('kelas_id')
#     def _onchange_kelas_id(self):
#         """Auto-fill tingkat_id, walikelas_id, status, dan daftar santri berdasarkan kelas yang dipilih"""
#         if self.kelas_id:
#             kelas = self.env['cdn.ruang_kelas'].browse(self.kelas_id.id)
            
#             # Set tingkat_id
#             try:
#                 self.tingkat_id = kelas.tingkat.id if kelas.tingkat else False
#             except AttributeError:
#                 if hasattr(kelas, 'tingkat_id'):
#                     self.tingkat_id = kelas.tingkat_id.id if kelas.tingkat_id else False
#                 else:
#                     self.tingkat_id = False
            
#             # Set walikelas_id
#             try:
#                 self.walikelas_id = kelas.walikelas_id.id if kelas.walikelas_id else False
#             except AttributeError:
#                 if hasattr(kelas, 'wali_kelas_id'):
#                     self.walikelas_id = kelas.wali_kelas_id.id if kelas.wali_kelas_id else False
#                 else:
#                     self.walikelas_id = False

#             # Set status berdasarkan tingkat
#             self._set_status_by_tingkat(kelas)

#             # Set daftar santri dari ruang kelas
#             if hasattr(kelas, 'siswa_ids'):
#                 self.partner_ids = [(6, 0, kelas.siswa_ids.ids)]
#             else:
#                 self.partner_ids = False

#         else:
#             self.tingkat_id = False
#             self.walikelas_id = False
#             self.status = False
#             self.partner_ids = False

#     def _set_status_by_tingkat(self, kelas):
#         """Set status berdasarkan tingkat kelas"""
#         if not kelas.tingkat:
#             self.status = 'naik'  # Default jika tidak ada tingkat
#             return
        
#         # Ambil data tingkat
#         tingkat = kelas.tingkat
        
#         # Cek apakah tingkat 12 (kelas SMA/MA/SMK)
#         is_tingkat_12 = self._is_tingkat_12(tingkat)
#         if is_tingkat_12:
#             # Untuk tingkat 12, cek apakah ada kelas selanjutnya
#             has_next_class = self._check_next_class_exists(kelas)
#             if has_next_class:
#                 self.status = 'naik'
#             else:
#                 self.status = 'lulus'
#             return
        
#         # Cara 1: Cek berdasarkan nama tingkat (jika ada field nama/name)
#         if hasattr(tingkat, 'name'):
#             tingkat_name = str(tingkat.name).lower()
#             # Cek apakah tingkat 6 atau 9
#             if '6' in tingkat_name or 'vi' in tingkat_name or 'enam' in tingkat_name:
#                 self.status = 'lulus'
#             elif '9' in tingkat_name or 'ix' in tingkat_name or 'sembilan' in tingkat_name:
#                 self.status = 'lulus'
#             else:
#                 self.status = 'naik'
        
#         # Cara 2: Cek berdasarkan field urutan (jika ada)
#         elif hasattr(tingkat, 'urutan'):
#             if tingkat.urutan in [6, 9]:
#                 self.status = 'lulus'
#             else:
#                 self.status = 'naik'
        
#         # Cara 3: Cek berdasarkan field level (jika ada)
#         elif hasattr(tingkat, 'level'):
#             if tingkat.level in [6, 9]:
#                 self.status = 'lulus'
#             else:
#                 self.status = 'naik'
        
#         # Cara 4: Cek berdasarkan jenjang dan tingkat
#         elif hasattr(kelas, 'jenjang'):
#             # Untuk SD/MI: tingkat 6 = lulus
#             if kelas.jenjang in ['sd'] and hasattr(tingkat, 'name'):
#                 if '6' in str(tingkat.name) or 'vi' in str(tingkat.name).lower():
#                     self.status = 'lulus'
#                 else:
#                     self.status = 'naik'
#             # Untuk SMP/MTS: tingkat 9 = lulus  
#             elif kelas.jenjang in ['smp'] and hasattr(tingkat, 'name'):
#                 if '9' in str(tingkat.name) or 'ix' in str(tingkat.name).lower():
#                     self.status = 'lulus'
#                 else:
#                     self.status = 'naik'
#             else:
#                 self.status = 'naik'
        
#         else:
#             # Default jika tidak bisa menentukan
#             self.status = 'naik'

#     @api.onchange('tingkat_id')
#     def _onchange_tingkat_id(self):
#         """Update status ketika tingkat_id diubah manual"""
#         if self.tingkat_id and self.kelas_id:
#             # Buat object kelas sementara untuk menggunakan method yang sama
#             class MockKelas:
#                 def __init__(self, tingkat, jenjang):
#                     self.tingkat = tingkat
#                     self.jenjang = jenjang
            
#             mock_kelas = MockKelas(self.tingkat_id, self.jenjang)
#             self._set_status_by_tingkat(mock_kelas)

#     def _is_tingkat_12(self, tingkat):
#         """Cek apakah tingkat adalah kelas 12"""
#         if hasattr(tingkat, 'name'):
#             tingkat_name = str(tingkat.name).lower()
#             if '12' in tingkat_name or 'xii' in tingkat_name or 'duabelas' in tingkat_name:
#                 return True
        
#         if hasattr(tingkat, 'urutan'):
#             if tingkat.urutan == 12:
#                 return True
        
#         if hasattr(tingkat, 'level'):
#             if tingkat.level == 12:
#                 return True
                
#         return False

#     def _check_next_class_exists(self, kelas):
#         """Cek apakah ada kelas selanjutnya setelah tingkat 12 di cdn.master_kelas"""
#         try:
#             # Ambil tingkat saat ini
#             current_tingkat = kelas.tingkat
#             if not current_tingkat:
#                 return False
            
#             # Ambil jenjang dan jurusan dari kelas saat ini
#             current_jenjang = kelas.jenjang if hasattr(kelas, 'jenjang') else None
#             current_jurusan = None
            
#             # Coba ambil jurusan dari kelas saat ini
#             if hasattr(kelas, 'jurusan_id'):
#                 current_jurusan = kelas.jurusan_id
#             elif hasattr(kelas, 'name') and hasattr(kelas.name, 'jurusan_id'):
#                 current_jurusan = kelas.name.jurusan_id
            
#             # Tentukan tingkat selanjutnya yang mungkin (13, 14, dst)
#             next_tingkat_numbers = [13, 14, 15, 16]  # Bisa disesuaikan
            
#             # Cari tingkat selanjutnya di cdn.tingkat
#             next_tingkat_ids = []
#             for num in next_tingkat_numbers:
#                 tingkat_domain = []
                
#                 # Cari berdasarkan nama
#                 tingkat_records = self.env['cdn.tingkat'].search([
#                     '|', '|', '|',
#                     ('name', 'ilike', str(num)),
#                     ('name', 'ilike', self._number_to_roman(num)),
#                     ('urutan', '=', num),
#                     ('level', '=', num)
#                 ])
                
#                 if tingkat_records:
#                     next_tingkat_ids.extend(tingkat_records.ids)
            
#             if not next_tingkat_ids:
#                 return False
            
#             # Cari di cdn.master_kelas apakah ada kelas dengan tingkat selanjutnya
#             master_kelas_domain = [('tingkat', 'in', next_tingkat_ids)]
            
#             # Filter berdasarkan jenjang jika ada
#             if current_jenjang:
#                 master_kelas_domain.append(('jenjang', '=', current_jenjang))
            
#             # Filter berdasarkan jurusan jika ada
#             if current_jurusan:
#                 master_kelas_domain.append(('jurusan_id', '=', current_jurusan.id))
            
#             next_classes = self.env['cdn.master_kelas'].search(master_kelas_domain, limit=1)
            
#             return bool(next_classes)
            
#         except Exception as e:
#             # Jika terjadi error, default ke False (lulus)
#             _logger.warning(f"Error checking next class: {str(e)}")
#             return False



#     def _create_next_tahun_ajaran(self, current_ta):
#         """
#         Fungsi untuk membuat tahun ajaran berikutnya jika belum ada
#         Disesuaikan dengan sistem pendidikan di Indonesia (Juli-Juni)
        
#         Args:
#             current_ta: Tahun ajaran saat ini
            
#         Returns:
#             cdn.ref_tahunajaran: Tahun ajaran baru yang dibuat
#         """
#         try:
#             _logger.info(f"Mencoba membuat tahun ajaran baru setelah {current_ta.name}")
            
#             # Ekstrak tahun dari nama tahun ajaran saat ini
#             current_year = int(current_ta.name.split('/')[0])
#             next_year = current_year + 1
#             next_ta_name = f"{next_year}/{next_year+1}"
            
#             _logger.info(f"Tahun yang diekstrak: {current_year}, Tahun berikutnya: {next_year}")
#             _logger.info(f"Nama tahun ajaran baru: {next_ta_name}")
            
#             # Tentukan tanggal mulai dan akhir sesuai sistem pendidikan Indonesia
#             start_date = datetime(next_year, 7, 1).date()
#             end_date = datetime(next_year + 1, 6, 30).date()
            
#             _logger.info(f"Tanggal mulai: {start_date}, Tanggal akhir: {end_date}")
            
#             # Cek apakah sudah ada tahun ajaran dengan nama tersebut
#             existing_ta_by_name = self.env['cdn.ref_tahunajaran'].search([
#                 ('name', '=', next_ta_name)
#             ], limit=1)
            
#             if existing_ta_by_name:
#                 _logger.info(f"Tahun ajaran dengan nama {next_ta_name} sudah ada")
#                 return existing_ta_by_name
                
#             # Cek apakah sudah ada tahun ajaran dengan rentang waktu tersebut
#             existing_ta = self.env['cdn.ref_tahunajaran'].search([
#                 ('start_date', '=', start_date),
#                 ('end_date', '=', end_date)
#             ], limit=1)
            
#             if existing_ta:
#                 _logger.info(f"Tahun ajaran dengan rentang {start_date} - {end_date} sudah ada")
#                 return existing_ta
            
#             _logger.info(f"Membuat tahun ajaran baru: {next_ta_name}")
            
#             # Ambil data tambahan dari tahun ajaran saat ini
#             create_vals = {
#                 'name': next_ta_name,
#                 'start_date': start_date,
#                 'end_date': end_date,
#                 'keterangan': f"Dibuat otomatis dari proses kenaikan kelas pada {fields.Date.today()}"
#             }
            
#             # Copy field yang ada dari tahun ajaran saat ini
#             if hasattr(current_ta, 'term_structure') and current_ta.term_structure:
#                 create_vals['term_structure'] = current_ta.term_structure
                
#             if hasattr(current_ta, 'company_id') and current_ta.company_id:
#                 create_vals['company_id'] = current_ta.company_id.id
            
#             # Buat tahun ajaran baru dengan sudo untuk memastikan hak akses
#             new_ta = self.env['cdn.ref_tahunajaran'].sudo().create(create_vals)
            
#             # Verifikasi record telah dibuat
#             if not new_ta:
#                 raise UserError(f"Gagal membuat tahun ajaran baru {next_ta_name}")
            
#             # Commit transaksi untuk memastikan data tersimpan
#             self.env.cr.commit()
            
#             # Buat termin akademik dan periode tagihan jika method tersedia
#             if hasattr(new_ta, 'term_create'):
#                 try:
#                     new_ta.term_create()
#                 except Exception as e:
#                     _logger.warning(f"Gagal membuat termin untuk tahun ajaran {next_ta_name}: {str(e)}")
            
#             _logger.info(f"Tahun ajaran baru berhasil dibuat: {new_ta.name} ({new_ta.start_date} - {new_ta.end_date})")
            
#             return new_ta
#         except Exception as e:
#             _logger.error(f"Gagal membuat tahun ajaran baru: {str(e)}")
#             raise UserError(f"Gagal membuat tahun ajaran baru: {str(e)}")


#     def action_proses_kenaikan_kelas(self):
#         """
#         Aksi untuk memproses kenaikan kelas dengan memperbarui data siswa
#         pada kelas yang sudah ada (tidak membuat kelas baru)
#         """
#         _logger.info(f"Memulai proses kenaikan kelas untuk tahun ajaran: {self.tahunajaran_id.name}")
        
#         if not self.partner_ids:
#             raise UserError("Belum ada santri yang dipilih!")
        
#         if not self.kelas_id:
#             raise UserError("Belum ada kelas yang dipilih!")
        
#         self.ensure_one()
#         message = ""
#         count_siswa_naik = 0
#         count_siswa_tidak_naik = 0
#         count_siswa_lulus = 0
#         count_siswa_tidak_lulus = 0
        
#         # Mendapatkan tahun ajaran berikutnya
#         try:
#             current_year = int(self.tahunajaran_id.name.split('/')[0])
#             next_year = current_year + 1
#             next_ta_name = f"{next_year}/{next_year+1}"
            
#             _logger.info(f"Current year: {current_year}, Next year: {next_year}")
#             _logger.info(f"Mencari tahun ajaran dengan nama: {next_ta_name}")
            
#             # Cari tahun ajaran berikutnya
#             tahun_ajaran_berikutnya = self.env['cdn.ref_tahunajaran'].search([
#                 ('name', '=', next_ta_name)
#             ], limit=1)
            
#             _logger.info(f"Hasil pencarian tahun ajaran berikutnya: {tahun_ajaran_berikutnya.name if tahun_ajaran_berikutnya else 'Tidak ditemukan'}")
            
#         except (ValueError, IndexError) as e:
#             _logger.error(f"Format tahun ajaran tidak valid: {str(e)}")
#             raise UserError(f"Format tahun ajaran tidak valid: {self.tahunajaran_id.name}. Format yang diharapkan: YYYY/YYYY")
        
#         # Jika tahun ajaran berikutnya tidak ditemukan, buat yang baru
#         if not tahun_ajaran_berikutnya:
#             message += f"Tahun ajaran {next_ta_name} tidak ditemukan. Mencoba membuat tahun ajaran baru...\n"
#             try:
#                 tahun_ajaran_berikutnya = self._create_next_tahun_ajaran(self.tahunajaran_id)
#                 message += f"Berhasil membuat tahun ajaran baru: {tahun_ajaran_berikutnya.name}\n\n"
#             except Exception as e:
#                 message += f"Gagal membuat tahun ajaran baru: {str(e)}\n\n"
#                 raise UserError(f"Gagal membuat tahun ajaran baru: {str(e)}")
        
#         # Update data kelas berdasarkan status kenaikan kelas
#         try:
#             # Cek status kenaikan kelas dan update kelas yang lama
#             if self.status == 'naik':
#                 # Siswa naik kelas - ubah name dan tahun_ajaran kelas lama
#                 if self.next_class:
#                     # Update kelas lama dengan kelas baru dan tahun ajaran baru
#                     self.kelas_id.write({
#                         'name': self.next_class.id,
#                         'tahunajaran_id': tahun_ajaran_berikutnya.id,
#                         'walikelas_id': self.walikelas_id.id,
#                     })
#                     message += f"Kelas {self.kelas_id.nama_kelas} berhasil diupdate ke {self.next_class.name} untuk tahun ajaran {tahun_ajaran_berikutnya.name}\n"
                    
#                     # Update status siswa
#                     for siswa in self.partner_ids:
#                         siswa.write({
#                             'tahun_ajaran_id': tahun_ajaran_berikutnya.id,
#                             'walikelas_id': self.walikelas_id.id,
#                         })
#                         count_siswa_naik += 1
                        
#                     message += f"Total {len(self.partner_ids)} siswa naik kelas ke {self.next_class.name}\n"
#                 else:
#                     message += "Gagal naik kelas - kelas selanjutnya tidak ditentukan\n"
                    
#             elif self.status == 'tidak_naik':
#                 # Siswa tidak naik kelas - hanya ubah tahun_ajaran
#                 self.kelas_id.write({
#                     'tahunajaran_id': tahun_ajaran_berikutnya.id,
#                     'walikelas_id': self.walikelas_id.id,
#                 })
#                 message += f"Kelas {self.kelas_id.nama_kelas} diupdate ke tahun ajaran {tahun_ajaran_berikutnya.name} (tidak naik kelas)\n"
                
#                 # Update status siswa
#                 for siswa in self.partner_ids:
#                     siswa.write({
#                         'tahun_ajaran_id': tahun_ajaran_berikutnya.id,
#                         'walikelas_id': self.walikelas_id.id,
#                     })
#                     count_siswa_tidak_naik += 1
                    
#                 message += f"Total {len(self.partner_ids)} siswa tidak naik kelas\n"
                    
#             elif self.status == 'lulus':
#                 # Siswa lulus - ubah aktif_tidak menjadi 'tidak'
#                 self.kelas_id.write({
#                     'aktif_tidak': 'tidak',
#                     # 'tahunajaran_id': tahun_ajaran_berikutnya.id,
#                 })
#                 message += f"Kelas {self.kelas_id.nama_kelas} dinonaktifkan karena siswa lulus\n"
                
#                 # Update status siswa
#                 for siswa in self.partner_ids:
#                     siswa.write({
#                         'status_kelulusan': 'lulus',
#                         'tahun_lulus': tahun_ajaran_berikutnya.name,
#                         # 'tahun_ajaran_id': tahun_ajaran_berikutnya.id,
#                     })
#                     count_siswa_lulus += 1
                    
#                 message += f"Total {len(self.partner_ids)} siswa lulus\n"
                
#             elif self.status == 'tidak_lulus':
#                 # Siswa tidak lulus - hanya ubah tahun_ajaran
#                 self.kelas_id.write({
#                     'tahunajaran_id': tahun_ajaran_berikutnya.id,
#                     'walikelas_id': self.walikelas_id.id,
#                 })
#                 message += f"Kelas {self.kelas_id.nama_kelas} diupdate ke tahun ajaran {tahun_ajaran_berikutnya.name} (tidak lulus)\n"
                
#                 # Update status siswa
#                 for siswa in self.partner_ids:
#                     siswa.write({
#                         'tahun_ajaran_id': tahun_ajaran_berikutnya.id,
#                         'status_kelulusan': 'tidak_lulus',
#                         'walikelas_id': self.walikelas_id.id,
#                     })
#                     count_siswa_tidak_lulus += 1
                    
#                 message += f"Total {len(self.partner_ids)} siswa tidak lulus\n"
                
#         except Exception as e:
#             error_msg = f"ERROR memproses kenaikan kelas: {str(e)}"
#             message += f"- {error_msg}\n"
#             _logger.error(error_msg)
        
#         # Commit perubahan
#         try:
#             self.env.cr.commit()
#             _logger.info("Perubahan berhasil di-commit ke database")
#         except Exception as e:
#             _logger.error(f"Gagal melakukan commit perubahan: {str(e)}")
#             raise UserError(f"Gagal menyimpan perubahan: {str(e)}")
        
#         # Buat summary hasil proses
#         result_message = f"Proses Kenaikan Kelas berhasil dilakukan!\n\n"
#         result_message += f"Ringkasan Hasil:\n"
#         result_message += f"- Siswa naik kelas: {count_siswa_naik}\n"
#         result_message += f"- Siswa tidak naik: {count_siswa_tidak_naik}\n"
#         result_message += f"- Siswa lulus: {count_siswa_lulus}\n"
#         result_message += f"- Siswa tidak lulus: {count_siswa_tidak_lulus}\n"
#         result_message += f"Total siswa diproses: {len(self.partner_ids)}\n\n"
#         result_message += f"Detail Proses:\n{message}"
        
#         _logger.info(f"Proses kenaikan kelas selesai dengan hasil: {result_message}")
        
#         # Update field message_result
#         self.message_result = result_message
        
#         # Buat notification message
#         notification_message = f'Proses kenaikan kelas berhasil! Total {len(self.partner_ids)} siswa diproses.'


#         return {
#             'type': 'ir.actions.act_window',
#             'name': 'Kenaikan Kelas',
#             'res_model': 'cdn.kenaikan_kelas',
#             'view_mode': 'form',
#             'target': 'new',
#             'context': {
#                 'default_message_result': result_message,
#                 # Kosongkan field lain sesuai kebutuhan
#                 'default_kelas_id': False,
#                 'default_status': False,
#                 'default_partner_ids': [],
#                 'default_next_class': False,
#             }
#         }



        
#         # # Return action untuk reload form dengan notifikasi
#         # return {
#         #     'type': 'ir.actions.act_window',
#         #     'name': 'Kenaikan Kelas',
#         #     'res_model': 'cdn.kenaikan_kelas',
#         #     'res_id': self.id,
#         #     'view_mode': 'form',
#         #     'target': 'new',
#         #     'context': dict(self.env.context, **{
#         #         'default_message_result': result_message,
#         #     }),
#         # }





#     # def _create_next_tahun_ajaran(self, current_ta):
#     #     """
#     #     Fungsi untuk membuat tahun ajaran berikutnya jika belum ada
#     #     Disesuaikan dengan sistem pendidikan di Indonesia (Juli-Juni)
        
#     #     Args:
#     #         current_ta: Tahun ajaran saat ini
            
#     #     Returns:
#     #         cdn.ref_tahunajaran: Tahun ajaran baru yang dibuat
#     #     """
#     #     try:
#     #         print(f"DEBUG - Mencoba membuat tahun ajaran baru setelah {current_ta.name}")
            
#     #         # Ekstrak tahun dari nama tahun ajaran saat ini
#     #         current_year = int(current_ta.name.split('/')[0])
#     #         next_year = current_year + 1
#     #         next_ta_name = f"{next_year}/{next_year+1}"
            
#     #         print(f"DEBUG - Tahun yang diekstrak: {current_year}, Tahun berikutnya: {next_year}")
#     #         print(f"DEBUG - Nama tahun ajaran baru: {next_ta_name}")
            
#     #         # Tentukan tanggal mulai dan akhir sesuai sistem pendidikan Indonesia
#     #         # Tahun ajaran di Indonesia umumnya Juli-Juni
#     #         today = fields.Date.from_string(fields.Date.today())
            
#     #         # Untuk pembuatan tahun ajaran baru, selalu gunakan tahun +1 dari current year
#     #         start_date = datetime(next_year, 7, 1).date()
#     #         end_date = datetime(next_year + 1, 6, 30).date()
            
#     #         print(f"DEBUG - Tanggal mulai: {start_date}, Tanggal akhir: {end_date}")
            
#     #         # Cek apakah sudah ada tahun ajaran dengan nama tersebut
#     #         existing_ta_by_name = self.env['cdn.ref_tahunajaran'].search([
#     #             ('name', '=', next_ta_name)
#     #         ], limit=1)
            
#     #         if existing_ta_by_name:
#     #             print(f"DEBUG - Tahun ajaran dengan nama {next_ta_name} sudah ada")
#     #             return existing_ta_by_name
                
#     #         # Cek apakah sudah ada tahun ajaran dengan rentang waktu tersebut
#     #         existing_ta = self.env['cdn.ref_tahunajaran'].search([
#     #             ('start_date', '=', start_date),
#     #             ('end_date', '=', end_date)
#     #         ], limit=1)
            
#     #         if existing_ta:
#     #             print(f"DEBUG - Tahun ajaran dengan rentang {start_date} - {end_date} sudah ada")
#     #             return existing_ta
            
#     #         print(f"DEBUG - Membuat tahun ajaran baru: {next_ta_name}")
            
#     #         # Buat tahun ajaran baru dengan sudo untuk memastikan hak akses
#     #         new_ta = self.env['cdn.ref_tahunajaran'].sudo().create({
#     #             'name': next_ta_name,
#     #             'start_date': start_date,
#     #             'end_date': end_date,
#     #             'term_structure': current_ta.term_structure,
#     #             'company_id': current_ta.company_id.id,
#     #             'keterangan': f"Dibuat otomatis dari proses kenaikan kelas pada {fields.Date.today()}"
#     #         })
            
#     #         # Verifikasi record telah dibuat
#     #         if not new_ta:
#     #             raise UserError(f"Gagal membuat tahun ajaran baru {next_ta_name}")
            
#     #         # Commit transaksi untuk memastikan data tersimpan
#     #         self.env.cr.commit()
            
#     #         # Buat termin akademik dan periode tagihan
#     #         new_ta.term_create()
            
#     #         # Log untuk debug
#     #         print(f"DEBUG - Tahun ajaran baru berhasil dibuat: {new_ta.name} ({new_ta.start_date} - {new_ta.end_date})")
            
#     #         return new_ta
#     #     except Exception as e:
#     #         print(f"ERROR - Gagal membuat tahun ajaran baru: {str(e)}")
#     #         # Re-raise supaya bisa dilihat di UI
#     #         raise UserError(f"Gagal membuat tahun ajaran baru: {str(e)}") 

#     # def action_proses_kenaikan_kelas(self):
#     #     """
#     #     Aksi untuk memproses kenaikan kelas dengan hanya memperbarui kelas yang sudah ada
#     #     """

#     #     # Ganti return statement dengan ini untuk reload form sekaligus notifikasi
#     #     return {
#     #         'type': 'ir.actions.act_window',
#     #         'name': 'Kenaikan Kelas',
#     #         'res_model': 'cdn.kenaikan_kelas',
#     #         'view_mode': 'form',
#     #         'target': 'new',
#     #     }








#     # def action_proses_kenaikan_kelas(self):
#     #     """
#     #     Aksi untuk memproses kenaikan kelas dengan hanya memperbarui kelas yang sudah ada
#     #     """
#     #     try:
#     #         # Validasi input
#     #         if not self.kelas_id:
#     #             raise UserError("Silakan pilih kelas terlebih dahulu!")
            
#     #         if not self.partner_ids:
#     #             raise UserError("Silakan pilih siswa yang akan diproses!")
            
#     #         if not self.status:
#     #             raise UserError("Silakan pilih status kenaikan kelas!")
            
#     #         # Ambil tahun ajaran saat ini
#     #         current_ta = self.tahunajaran_id
#     #         if not current_ta:
#     #             raise UserError("Tahun ajaran tidak ditemukan!")
            
#     #         messages = []
#     #         processed_count = 0
            
#     #         # Buat tahun ajaran baru menggunakan fungsi yang sudah ada
#     #         try:
#     #             next_ta = self._create_next_tahun_ajaran(current_ta)
#     #             messages.append(f"✓ Tahun ajaran baru: {next_ta.name}")
#     #         except Exception as e:
#     #             raise UserError(f"Gagal membuat tahun ajaran baru: {str(e)}")
            
#     #         # Proses setiap siswa yang dipilih
#     #         for siswa in self.partner_ids:
#     #             try:
#     #                 if self.status in ['naik', 'lulus']:
#     #                     # Siswa naik kelas atau lulus - cari kelas berikutnya
#     #                     next_class = self._find_next_class(siswa, next_ta)
                        
#     #                     if next_class:
#     #                         # Pindahkan siswa ke kelas berikutnya
#     #                         self._move_student_to_next_class(siswa, next_class)
#     #                         processed_count += 1
#     #                         messages.append(f"✓ {siswa.name} dipindah ke {next_class.nama_kelas} ({next_ta.name})")
#     #                     else:
#     #                         # Jika tidak ada kelas berikutnya (lulus dari tingkat tertinggi)
#     #                         if self.status == 'lulus':
#     #                             self._graduate_student(siswa)
#     #                             processed_count += 1
#     #                             messages.append(f"✓ {siswa.name} dinyatakan lulus")
#     #                         else:
#     #                             messages.append(f"⚠ {siswa.name} - Kelas berikutnya tidak ditemukan")
                    
#     #                 elif self.status in ['tidak_naik', 'tidak_lulus']:
#     #                     # Siswa tidak naik/tidak lulus - tetap di kelas yang sama dengan tahun ajaran baru
#     #                     current_class = self._find_same_class_next_year(siswa, next_ta)
                        
#     #                     if current_class:
#     #                         self._move_student_to_next_class(siswa, current_class)
#     #                         processed_count += 1
#     #                         messages.append(f"✓ {siswa.name} tetap di {current_class.nama_kelas} ({next_ta.name})")
#     #                     else:
#     #                         messages.append(f"⚠ {siswa.name} - Kelas yang sama untuk tahun ajaran baru tidak ditemukan")
                            
#     #             except Exception as e:
#     #                 messages.append(f"✗ Error memproses {siswa.name}: {str(e)}")
            
#     #         # Update message hasil
#     #         result_message = f"Proses Kenaikan Kelas Selesai\n"
#     #         result_message += f"Total siswa diproses: {processed_count}/{len(self.partner_ids)}\n\n"
#     #         result_message += "\n".join(messages)
            
#     #         self.message_result = result_message
            
#     #         # Commit perubahan
#     #         self.env.cr.commit()
            
#     #         # Show notification
#     #         if processed_count > 0:
#     #             return {
#     #                 'type': 'ir.actions.client',
#     #                 'tag': 'display_notification',
#     #                 'params': {
#     #                     'title': 'Sukses!',
#     #                     'message': f'Berhasil memproses {processed_count} siswa',
#     #                     'type': 'success',
#     #                     'sticky': False,
#     #                 }
#     #             }
#     #         else:
#     #             return {
#     #                 'type': 'ir.actions.client',
#     #                 'tag': 'display_notification',
#     #                 'params': {
#     #                     'title': 'Peringatan!',
#     #                     'message': 'Tidak ada siswa yang berhasil diproses',
#     #                     'type': 'warning',
#     #                     'sticky': False,
#     #                 }
#     #             }
                
#     #     except UserError as e:
#     #         # Update message dengan error
#     #         self.message_result = f"Error: {str(e)}"
#     #         raise
#     #     except Exception as e:
#     #         error_msg = f"Terjadi kesalahan tidak terduga: {str(e)}"
#     #         self.message_result = error_msg
#     #         raise UserError(error_msg)

#     # def _find_next_class(self, siswa, next_tahun_ajaran):
#     #     """
#     #     Mencari kelas berikutnya untuk siswa berdasarkan tingkat saat ini
#     #     """
#     #     try:
#     #         # Ambil kelas saat ini dari siswa
#     #         current_class = self.kelas_id
#     #         current_tingkat = current_class.tingkat
#     #         current_jenjang = current_class.jenjang
#     #         current_jurusan = current_class.jurusan_id
            
#     #         # Cari tingkat berikutnya
#     #         next_tingkat = self.env['cdn.tingkat'].search([
#     #             ('jenjang', '=', current_jenjang),
#     #             ('urutan', '>', current_tingkat.urutan)
#     #         ], order='urutan asc', limit=1)
            
#     #         if not next_tingkat:
#     #             # Tidak ada tingkat berikutnya, siswa lulus
#     #             return None
            
#     #         # Cari master kelas untuk tingkat berikutnya
#     #         domain = [
#     #             ('tingkat', '=', next_tingkat.id),
#     #             ('jenjang', '=', current_jenjang),
#     #         ]
            
#     #         # Tambahkan filter jurusan jika ada
#     #         if current_jurusan:
#     #             domain.append(('jurusan_id', '=', current_jurusan.id))
            
#     #         master_kelas = self.env['cdn.master_kelas'].search(domain, limit=1)
            
#     #         if not master_kelas:
#     #             print(f"DEBUG - Master kelas tidak ditemukan untuk tingkat {next_tingkat.name}")
#     #             return None
            
#     #         # Cari ruang kelas yang ada untuk tingkat berikutnya di tahun ajaran saat ini
#     #         ruang_kelas = self.env['cdn.ruang_kelas'].search([
#     #             ('name', '=', master_kelas.id),
#     #             ('tahunajaran_id', '=', self.tahunajaran_id.id),  # Gunakan tahun ajaran saat ini
#     #             ('aktif_tidak', '=', 'aktif')
#     #         ], limit=1)
            
#     #         if ruang_kelas:
#     #             # Update tahun ajaran pada ruang kelas yang ada
#     #             ruang_kelas.write({
#     #                 'tahunajaran_id': next_tahun_ajaran.id,
#     #                 'keterangan': f'Diupdate dari proses kenaikan kelas pada {fields.Date.today()}'
#     #             })
            
#     #         return ruang_kelas
            
#     #     except Exception as e:
#     #         print(f"ERROR - _find_next_class: {str(e)}")
#     #         return None

#     # def _find_same_class_next_year(self, siswa, next_tahun_ajaran):
#     #     """
#     #     Mencari kelas yang sama untuk tahun ajaran berikutnya (untuk siswa yang tidak naik)
#     #     """
#     #     try:
#     #         current_class = self.kelas_id
#     #         master_kelas = current_class.name
            
#     #         # Cari ruang kelas yang sama untuk tahun ajaran saat ini
#     #         ruang_kelas = self.env['cdn.ruang_kelas'].search([
#     #             ('name', '=', master_kelas.id),
#     #             ('tahunajaran_id', '=', self.tahunajaran_id.id),  # Gunakan tahun ajaran saat ini
#     #             ('aktif_tidak', '=', 'aktif')
#     #         ], limit=1)
            
#     #         if ruang_kelas:
#     #             # Update tahun ajaran pada ruang kelas yang ada
#     #             ruang_kelas.write({
#     #                 'tahunajaran_id': next_tahun_ajaran.id,
#     #                 'keterangan': f'Diupdate dari proses kenaikan kelas pada {fields.Date.today()}'
#     #             })
            
#     #         return ruang_kelas
            
#     #     except Exception as e:
#     #         print(f"ERROR - _find_same_class_next_year: {str(e)}")
#     #         return None

#     # def _update_ruang_kelas_tahun_ajaran(self, ruang_kelas, next_tahun_ajaran):
#     #     """
#     #     Update tahun ajaran pada ruang kelas yang sudah ada
#     #     """
#     #     try:
#     #         ruang_kelas.write({
#     #             'tahunajaran_id': next_tahun_ajaran.id,
#     #             'keterangan': f'Diupdate dari proses kenaikan kelas pada {fields.Date.today()}'
#     #         })
            
#     #         print(f"DEBUG - Ruang kelas {ruang_kelas.nama_kelas} diupdate ke TA {next_tahun_ajaran.name}")
#     #         return ruang_kelas
            
#     #     except Exception as e:
#     #         print(f"ERROR - _update_ruang_kelas_tahun_ajaran: {str(e)}")
#     #         raise UserError(f"Gagal mengupdate tahun ajaran ruang kelas: {str(e)}")

#     # def _move_student_to_next_class(self, siswa, target_class):
#     #     """
#     #     Memindahkan siswa ke kelas baru
#     #     """
#     #     try:
#     #         # Jangan hapus siswa dari kelas lama, cukup update tahun ajaran pada kelas yang ada
#     #         # Update informasi siswa jika diperlukan
#     #         siswa.write({
#     #             'kelas_id': target_class.id,
#     #             'tingkat_id': target_class.tingkat.id if target_class.tingkat else False,
#     #         })
            
#     #         print(f"DEBUG - Siswa {siswa.name} dipindah ke {target_class.nama_kelas}")
            
#     #     except Exception as e:
#     #         print(f"ERROR - _move_student_to_next_class: {str(e)}")
#     #         raise UserError(f"Gagal memindahkan siswa {siswa.name}: {str(e)}")

#     # def _graduate_student(self, siswa):
#     #     """
#     #     Memproses siswa yang lulus (tidak ada kelas berikutnya)
#     #     Menonaktifkan kelas saat ini dengan mengubah aktif_tidak menjadi 'tidak'
#     #     """
#     #     try:
#     #         # Cari kelas saat ini untuk siswa yang lulus
#     #         current_classes = self.env['cdn.ruang_kelas'].search([
#     #             ('siswa_ids', 'in', [siswa.id]),
#     #             ('tahunajaran_id', '=', self.tahunajaran_id.id)
#     #         ])
            
#     #         # Menonaktifkan kelas (bukan menghapus siswa)
#     #         for current_class in current_classes:
#     #             current_class.write({
#     #                 'aktif_tidak': 'tidak',
#     #                 'keterangan': f'Dinonaktifkan karena siswa lulus pada {fields.Date.today()}'
#     #             })
#     #             print(f"DEBUG - Kelas {current_class.nama_kelas} dinonaktifkan untuk siswa lulus")
            
#     #         # Update status siswa sebagai lulus
#     #         siswa.write({
#     #             'status_siswa': 'lulus',  # Jika ada field ini
#     #             'tanggal_lulus': fields.Date.today(),  # Jika ada field ini
#     #         })
            
#     #         print(f"DEBUG - Siswa {siswa.name} dinyatakan lulus")
            
#     #     except Exception as e:
#     #         print(f"ERROR - _graduate_student: {str(e)}")
#     #         raise UserError(f"Gagal memproses kelulusan siswa {siswa.name}: {str(e)}")
            







#     # @api.depends('kelas_id', 'kelas_id.nama_kelas', 'kelas_id.jurusan_id', 'kelas_id.tingkat', 'status')
#     # def _compute_next_class(self):
#     #     """Compute kelas selanjutnya berdasarkan kelas yang dipilih dan status"""
#     #     for record in self:
#     #         if not record.kelas_id:
#     #             record.next_class = False
#     #             continue
            
#     #         # Jika status adalah tidak_naik atau tidak_lulus, 
#     #         # maka next_class tetap menampilkan kelas yang sama
#     #         if record.status in ['tidak_naik', 'tidak_lulus']:
#     #             # Cari master kelas yang sesuai dengan kelas_id saat ini
#     #             current_class = record.kelas_id
#     #             current_tingkat = current_class.tingkat
#     #             current_nama_kelas = current_class.nama_kelas
#     #             current_jurusan = current_class.jurusan_id
                
#     #             if not current_tingkat:
#     #                 record.next_class = False
#     #                 continue
                
#     #             # Cari master kelas yang cocok dengan kelas saat ini
#     #             domain = [('tingkat', '=', current_tingkat.id)]
                
#     #             # Filter berdasarkan nama kelas jika ada
#     #             if current_nama_kelas:
#     #                 domain.append(('nama_kelas', '=', current_nama_kelas))
                
#     #             # Filter berdasarkan jurusan jika ada
#     #             if current_jurusan:
#     #                 domain.append(('jurusan_id', '=', current_jurusan.id))
                
#     #             # Cari master kelas yang cocok dengan kelas saat ini
#     #             current_master_class = self.env['cdn.master_kelas'].search(domain, limit=1)
                
#     #             # Jika tidak ditemukan dengan nama_kelas, coba tanpa nama_kelas (hanya tingkat dan jurusan)
#     #             if not current_master_class and current_jurusan:
#     #                 domain_alternative = [
#     #                     ('tingkat', '=', current_tingkat.id),
#     #                     ('jurusan_id', '=', current_jurusan.id)
#     #                 ]
#     #                 current_master_class = self.env['cdn.master_kelas'].search(domain_alternative, limit=1)
                
#     #             # Jika masih tidak ditemukan, coba hanya berdasarkan tingkat
#     #             if not current_master_class:
#     #                 domain_simple = [('tingkat', '=', current_tingkat.id)]
#     #                 current_master_class = self.env['cdn.master_kelas'].search(domain_simple, limit=1)
                
#     #             record.next_class = current_master_class.id if current_master_class else False
#     #             continue
            
#     #         # Untuk status naik dan lulus, cari kelas selanjutnya seperti biasa
#     #         # Ambil data kelas saat ini
#     #         current_class = record.kelas_id
#     #         current_tingkat = current_class.tingkat
#     #         current_nama_kelas = current_class.nama_kelas
#     #         current_jurusan = current_class.jurusan_id
            
#     #         if not current_tingkat:
#     #             record.next_class = False
#     #             continue
            
#     #         # Cari tingkat selanjutnya
#     #         next_tingkat = record._get_next_tingkat(current_tingkat)
#     #         if not next_tingkat:
#     #             record.next_class = False
#     #             continue
            
#     #         # Cari master kelas yang cocok dengan kriteria:
#     #         # 1. Tingkat = tingkat selanjutnya
#     #         # 2. nama_kelas = sama dengan kelas saat ini (jika ada)
#     #         # 3. jurusan_id = sama dengan kelas saat ini (jika ada)
#     #         domain = [('tingkat', '=', next_tingkat.id)]
            
#     #         # Filter berdasarkan nama kelas jika ada
#     #         if current_nama_kelas:
#     #             domain.append(('nama_kelas', '=', current_nama_kelas))
            
#     #         # Filter berdasarkan jurusan jika ada
#     #         if current_jurusan:
#     #             domain.append(('jurusan_id', '=', current_jurusan.id))
            
#     #         # Cari master kelas yang cocok
#     #         next_master_class = self.env['cdn.master_kelas'].search(domain, limit=1)
            
#     #         # Jika tidak ditemukan dengan nama_kelas, coba tanpa nama_kelas (hanya tingkat dan jurusan)
#     #         if not next_master_class and current_jurusan:
#     #             domain_alternative = [
#     #                 ('tingkat', '=', next_tingkat.id),
#     #                 ('jurusan_id', '=', current_jurusan.id)
#     #             ]
#     #             next_master_class = self.env['cdn.master_kelas'].search(domain_alternative, limit=1)
            
#     #         # Jika masih tidak ditemukan, coba hanya berdasarkan tingkat
#     #         if not next_master_class:
#     #             domain_simple = [('tingkat', '=', next_tingkat.id)]
#     #             next_master_class = self.env['cdn.master_kelas'].search(domain_simple, limit=1)
            
#     #         record.next_class = next_master_class.id if next_master_class else False




#     # def action_proses_naik_kelas(self):
#     #     """
#     #     Aksi untuk memproses kenaikan kelas dengan menangani berbagai status siswa
#     #     """
#     #     # Logging awal
#     #     print(f"DEBUG - Memulai proses kenaikan kelas untuk tahun ajaran: {self.tahunajaran_id.name}")
        
#     #     if not self.partner_ids:
#     #         raise UserError("Belum ada santri yang dipilih!")
        
#     #     if not self.status:
#     #         raise UserError("Status kenaikan harus dipilih terlebih dahulu!")
        
#     #     # Mencatat aktifitas untuk sistem log    
#     #     self.ensure_one()
#     #     message = ""
#     #     count_siswa = 0
#     #     count_siswa_filtered = 0
#     #     count_lulus = 0
#     #     count_tidak_naik = 0
#     #     count_kelas_nonaktif = 0
        
#     #     # Definisikan tingkat akhir untuk setiap jenjang
#     #     tingkat_akhir_map = {
#     #         'sd': 6,
#     #         'mi': 6,
#     #         'smp': 9,
#     #         'mts': 9,
#     #         'sma': 12,
#     #         'ma': 12,
#     #         'smk': 12,
#     #         'tk': 2,  # TK B
#     #         'paud': 1  # PAUD biasanya hanya 1 tingkat
#     #     }
        
#     #     # Mendapatkan tahun ajaran berikutnya (hanya diperlukan untuk status 'naik')
#     #     tahun_ajaran_berikutnya = None
#     #     if self.status == 'naik':
#     #         try:
#     #             current_year = int(self.tahunajaran_id.name.split('/')[0])
#     #             next_year = current_year + 1
#     #             next_ta_name = f"{next_year}/{next_year+1}"
                
#     #             print(f"DEBUG - Current year: {current_year}, Next year: {next_year}")
#     #             print(f"DEBUG - Mencari tahun ajaran dengan nama: {next_ta_name}")
                
#     #             # Cari tahun ajaran berikutnya dengan nama yang tepat
#     #             tahun_ajaran_berikutnya = self.env['cdn.ref_tahunajaran'].search([
#     #                 ('name', '=', next_ta_name)
#     #             ], limit=1)
                
#     #             print(f"DEBUG - Hasil pencarian tahun ajaran berikutnya: {tahun_ajaran_berikutnya.name if tahun_ajaran_berikutnya else 'Tidak ditemukan'}")
                
#     #         except (ValueError, IndexError) as e:
#     #             print(f"ERROR - Format tahun ajaran tidak valid: {str(e)}")
#     #             raise UserError(f"Format tahun ajaran tidak valid: {self.tahunajaran_id.name}. Format yang diharapkan: YYYY/YYYY")
            
#     #         # Jika tahun ajaran berikutnya tidak ditemukan, buat yang baru
#     #         if not tahun_ajaran_berikutnya:
#     #             message += f"Tahun ajaran {next_ta_name} tidak ditemukan. Mencoba membuat tahun ajaran baru...\n"
#     #             try:
#     #                 tahun_ajaran_berikutnya = self._create_next_tahun_ajaran(self.tahunajaran_id)
#     #                 message += f"Berhasil membuat tahun ajaran baru: {tahun_ajaran_berikutnya.name}\n\n"
#     #             except Exception as e:
#     #                 message += f"Gagal membuat tahun ajaran baru: {str(e)}\n\n"
#     #                 raise UserError(f"Gagal membuat tahun ajaran baru: {str(e)}")
        
#     #     # Proses berdasarkan status
#     #     if self.status == 'naik':
#     #         # === MODIFIKASI UTAMA: Pindahkan kelas dari tingkat 10 ke 11 ===
#     #         kelas_sekarang = self.kelas_id
#     #         if not kelas_sekarang.tingkat:
#     #             raise UserError("Kelas tidak memiliki tingkat yang valid!")
            
#     #         tingkat_sekarang = kelas_sekarang.tingkat
#     #         jenjang_lower = (kelas_sekarang.jenjang or '').lower()
#     #         tingkat_akhir = tingkat_akhir_map.get(jenjang_lower)
            
#     #         print(f"DEBUG - Memeriksa kelas: {kelas_sekarang.name.name}, Tingkat: {tingkat_sekarang.name}, Jenjang: {jenjang_lower}, Tingkat Akhir: {tingkat_akhir}")
            
#     #         # Cek apakah ini sudah tingkat akhir sebelum mencari tingkat berikutnya
#     #         tingkat_sekarang_int = int(tingkat_sekarang.name)
#     #         if tingkat_akhir and tingkat_sekarang_int >= tingkat_akhir:
#     #             # Ini sudah tingkat akhir, jadi nonaktifkan tanpa mencari tingkat berikutnya
#     #             print(f"DEBUG - Kelas {kelas_sekarang.name.name} sudah mencapai tingkat akhir ({tingkat_sekarang.name}), akan dinonaktifkan")
                
#     #             try:
#     #                 kelas_sekarang.write({'aktif_tidak': 'tidak'})
                    
#     #                 count_kelas_nonaktif = len(self.partner_ids)
#     #                 message += f"Kelas {kelas_sekarang.name.name} dinonaktifkan karena sudah mencapai tingkat akhir ({tingkat_sekarang.name}). {count_kelas_nonaktif} santri tetap berada di kelas ini.\n"
                    
#     #             except Exception as e:
#     #                 raise UserError(f"Gagal menonaktifkan kelas {kelas_sekarang.name.name}: {str(e)}")
#     #         else:
#     #             # === PERUBAHAN: Pindah kelas dari tingkat sekarang ke tingkat berikutnya ===
#     #             tingkat_berikutnya = self.env['cdn.tingkat'].search([
#     #                 ('name', '=', tingkat_sekarang_int + 1),
#     #                 ('jenjang', '=', self.jenjang) if self.jenjang else ('id', '!=', False)
#     #             ], limit=1)

#     #             if not tingkat_berikutnya:
#     #                 # Tingkat berikutnya tidak ditemukan, nonaktifkan kelas
#     #                 print(f"DEBUG - Tingkat berikutnya ({tingkat_sekarang_int + 1}) tidak ditemukan, menonaktifkan kelas")
                    
#     #                 try:
#     #                     kelas_sekarang.write({'aktif_tidak': 'tidak'})
                        
#     #                     count_kelas_nonaktif = len(self.partner_ids)
#     #                     message += f"Kelas {kelas_sekarang.name.name} dinonaktifkan karena tingkat berikutnya ({tingkat_sekarang_int + 1}) tidak ditemukan. {count_kelas_nonaktif} santri tetap berada di kelas ini.\n"
                        
#     #                 except Exception as e:
#     #                     raise UserError(f"Gagal menonaktifkan kelas {kelas_sekarang.name.name}: {str(e)}")
#     #             else:
#     #                 # Cari atau buat kelas baru untuk tingkat berikutnya
#     #                 domain_kelas_baru = [
#     #                     ('tingkat', '=', tingkat_berikutnya.id),
#     #                     ('jenjang', '=', kelas_sekarang.jenjang),
#     #                     ('tahunajaran_id', '=', tahun_ajaran_berikutnya.id)
#     #                 ]
                    
#     #                 # Tambahkan filter jurusan jika ada
#     #                 if hasattr(kelas_sekarang.name, 'jurusan_id') and kelas_sekarang.name.jurusan_id:
#     #                     domain_kelas_baru.append(('name.jurusan_id', '=', kelas_sekarang.name.jurusan_id.id))
                    
#     #                 # Tambahkan filter nama kelas jika ada
#     #                 if hasattr(kelas_sekarang.name, 'nama_kelas') and kelas_sekarang.name.nama_kelas:
#     #                     domain_kelas_baru.append(('name.nama_kelas', '=', kelas_sekarang.name.nama_kelas))
                    
#     #                 kelas_tujuan = self.env['cdn.ruang_kelas'].search(domain_kelas_baru, limit=1)
                    
#     #                 if not kelas_tujuan:
#     #                     raise UserError(f"Kelas untuk tingkat {tingkat_berikutnya.name}, jurusan '{kelas_sekarang.name.jurusan_id.name if kelas_sekarang.name.jurusan_id else '-'}', dan nama kelas '{kelas_sekarang.name.nama_kelas}' belum dibuat di tahun ajaran {tahun_ajaran_berikutnya.name}. Silakan buat terlebih dahulu.")

                    
#     #                 # if not kelas_tujuan:
#     #                 #     # Buat kelas baru untuk tingkat berikutnya
#     #                 #     try:
#     #                 #         # Cari master kelas yang sesuai
#     #                 #         domain_master_kelas = [
#     #                 #             ('tingkat', '=', tingkat_berikutnya.id),
#     #                 #             ('jenjang', '=', kelas_sekarang.jenjang)
#     #                 #         ]
                            
#     #                 #         if hasattr(kelas_sekarang.name, 'jurusan_id') and kelas_sekarang.name.jurusan_id:
#     #                 #             domain_master_kelas.append(('jurusan_id', '=', kelas_sekarang.name.jurusan_id.id))
                            
#     #                 #         if hasattr(kelas_sekarang.name, 'nama_kelas') and kelas_sekarang.name.nama_kelas:
#     #                 #             domain_master_kelas.append(('nama_kelas', '=', kelas_sekarang.name.nama_kelas))
                            
#     #                 #         master_kelas_baru = self.env['cdn.master_kelas'].search(domain_master_kelas, limit=1)
                            
#     #                 #         if not master_kelas_baru:
#     #                 #             raise UserError(f"Master kelas untuk tingkat {tingkat_berikutnya.name} tidak ditemukan!")
                            
#     #                 #         # Buat kelas baru
#     #                 #         kelas_tujuan = self.env['cdn.ruang_kelas'].create({
#     #                 #             'name': master_kelas_baru.id,
#     #                 #             'tahunajaran_id': tahun_ajaran_berikutnya.id,
#     #                 #             'aktif_tidak': 'aktif'
#     #                 #         })
                            
#     #                 #         print(f"DEBUG - Berhasil membuat kelas baru: {kelas_tujuan.name.name}")
#     #                 #         message += f"Kelas baru {kelas_tujuan.name.name} berhasil dibuat untuk tingkat {tingkat_berikutnya.name}\n"
                            
#     #                 #     except Exception as e:
#     #                 #         raise UserError(f"Gagal membuat kelas baru: {str(e)}")
                    
#     #                 # Pindahkan siswa ke kelas tujuan
#     #                 siswa_valid = []
#     #                 siswa_difilter = []
                    
#     #                 for siswa in self.partner_ids:
#     #                     # Filter siswa berdasarkan kesesuaian jika ada kelas_selanjutnya_id
#     #                     if hasattr(siswa, 'kelas_selanjutnya_id') and siswa.kelas_selanjutnya_id:
#     #                         nama_kelas_selanjutnya = getattr(siswa, 'nama_kelas_selanjutnya', '') or ''
#     #                         jurusan_selanjutnya = getattr(siswa, 'jurusan_selanjutnya', None)
                            
#     #                         nama_kelas_ruang = kelas_tujuan.nama_kelas or ''
#     #                         jurusan_ruang = kelas_tujuan.jurusan_id
                            
#     #                         # Cek kesesuaian
#     #                         nama_kelas_cocok = nama_kelas_selanjutnya == nama_kelas_ruang
#     #                         jurusan_cocok = (
#     #                             (jurusan_selanjutnya and jurusan_ruang and jurusan_selanjutnya.id == jurusan_ruang.id) or
#     #                             (not jurusan_selanjutnya and not jurusan_ruang)
#     #                         )
                            
#     #                         if not (nama_kelas_cocok and jurusan_cocok):
#     #                             siswa_difilter.append({
#     #                                 'siswa': siswa,
#     #                                 'nama_kelas_selanjutnya': nama_kelas_selanjutnya,
#     #                                 'jurusan_selanjutnya': jurusan_selanjutnya.name if jurusan_selanjutnya else 'Tidak ada',
#     #                                 'nama_kelas_ruang': nama_kelas_ruang,
#     #                                 'jurusan_ruang': jurusan_ruang.name if jurusan_ruang else 'Tidak ada'
#     #                             })
#     #                             continue
                        
#     #                     siswa_valid.append(siswa)
                    
#     #                 # Log siswa yang difilter
#     #                 if siswa_difilter:
#     #                     count_siswa_filtered = len(siswa_difilter)
#     #                     message += f"{count_siswa_filtered} siswa dikeluarkan dari proses kenaikan kelas karena ketidaksesuaian:\n"
#     #                     for item in siswa_difilter:
#     #                         siswa_info = item['siswa']
#     #                         message += f"- {siswa_info.name}: Kelas selanjutnya '{item['nama_kelas_selanjutnya']}' - Jurusan '{item['jurusan_selanjutnya']}' tidak sesuai dengan kelas tujuan '{item['nama_kelas_ruang']}' - Jurusan '{item['jurusan_ruang']}'\n"
                    
#     #                 # Pindahkan siswa yang valid ke kelas tujuan
#     #                 count_siswa = len(siswa_valid)
#     #                 if count_siswa > 0:
#     #                     for siswa in siswa_valid:
#     #                         siswa.write({'ruang_kelas_id': kelas_tujuan.id})
                        
#     #                     siswa_count_info = f"{count_siswa} siswa"
#     #                     if siswa_difilter:
#     #                         siswa_count_info += f" (dari {len(self.partner_ids)} siswa total, {count_siswa_filtered} difilter)"
                        
#     #                     message += f"Berhasil memindahkan {siswa_count_info} dari kelas {kelas_sekarang.name.name} (tingkat {tingkat_sekarang.name}) ke kelas {kelas_tujuan.name.name} (tingkat {tingkat_berikutnya.name}).\n"
            
#     #     elif self.status == 'lulus':
#     #         # === MODIFIKASI: Nonaktifkan kelas ketika siswa lulus ===
#     #         kelas_sekarang = self.kelas_id
            
#     #         # Hapus siswa dari kelas
#     #         for siswa in self.partner_ids:
#     #             siswa.write({'ruang_kelas_id': False})  # Hapus dari kelas
#     #             count_lulus += 1
            
#     #         # Nonaktifkan kelas
#     #         try:
#     #             kelas_sekarang.write({'aktif_tidak': 'tidak'})
#     #             message += f"Kelas {kelas_sekarang.name.name} dinonaktifkan karena siswa telah lulus.\n"
#     #             print(f"DEBUG - Kelas {kelas_sekarang.name.name} berhasil dinonaktifkan")
#     #         except Exception as e:
#     #             raise UserError(f"Gagal menonaktifkan kelas {kelas_sekarang.name.name}: {str(e)}")
            
#     #         message += f"Berhasil meluluskan {count_lulus} siswa dari kelas {kelas_sekarang.name.name}.\n"
            
#     #     elif self.status == 'tidak_naik':
#     #         # Siswa tetap di kelas yang sama
#     #         count_tidak_naik = len(self.partner_ids)
#     #         message += f"{count_tidak_naik} siswa tidak naik kelas dan tetap di kelas {self.kelas_id.name.name}.\n"
            
#     #     elif self.status == 'tidak_lulus':
#     #         # Siswa tetap di kelas yang sama
#     #         count_tidak_naik = len(self.partner_ids)
#     #         message += f"{count_tidak_naik} siswa tidak lulus dan tetap di kelas {self.kelas_id.name.name}.\n"
        
#     #     # Commit perubahan
#     #     try:
#     #         self.env.cr.commit()
#     #         print("DEBUG - Perubahan berhasil di-commit ke database")
#     #     except Exception as e:
#     #         print(f"ERROR - Gagal melakukan commit perubahan: {str(e)}")
        
#     #     # Siapkan pesan hasil
#     #     result_message = f"Proses Kenaikan Kelas berhasil dilakukan!\n\n"
        
#     #     if self.status == 'naik':
#     #         if count_kelas_nonaktif > 0:
#     #             result_message += f"Kelas dinonaktifkan (tingkat akhir): {count_kelas_nonaktif} santri tetap di kelas\n"
#     #         else:
#     #             result_message += f"Total siswa naik kelas: {count_siswa}\n"
#     #             if count_siswa_filtered > 0:
#     #                 result_message += f"Total siswa difilter: {count_siswa_filtered}\n"
#     #     elif self.status == 'lulus':
#     #         result_message += f"Total siswa lulus: {count_lulus}\n"
#     #         result_message += f"Kelas dinonaktifkan\n"
#     #     elif self.status in ['tidak_naik', 'tidak_lulus']:
#     #         result_message += f"Total siswa {self.status.replace('_', ' ')}: {count_tidak_naik}\n"
        
#     #     result_message += f"\n{message}"
        
#     #     # Simpan hasil ke field message_result
#     #     self.message_result = result_message
        
#     #     # Buat notification message
#     #     if self.status == 'naik':
#     #         if count_kelas_nonaktif > 0:
#     #             notification_message = f'Kelas dinonaktifkan karena sudah tingkat akhir! {count_kelas_nonaktif} santri tetap di kelas.'
#     #         else:
#     #             notification_message = f'Proses kenaikan kelas berhasil! Total {count_siswa} siswa naik kelas.'
#     #             if count_siswa_filtered > 0:
#     #                 notification_message += f' {count_siswa_filtered} siswa difilter.'
#     #     elif self.status == 'lulus':
#     #         notification_message = f'Proses kelulusan berhasil! Total {count_lulus} siswa lulus dan kelas dinonaktifkan.'
#     #     else:
#     #         notification_message = f'Proses berhasil! Total {count_tidak_naik} siswa {self.status.replace("_", " ")}.'
        
#     #     print(f"DEBUG - Proses kenaikan kelas selesai dengan pesan: {result_message}")
        
#     #     # Return untuk reload form dengan notifikasi
#     #     return {
#     #         'type': 'ir.actions.act_window',
#     #         'name': 'Kenaikan Kelas',
#     #         'res_model': 'cdn.kenaikan_kelas',
#     #         'view_mode': 'form',
#     #         'target': 'new',
#     #         'context': dict(self.env.context, **{
#     #             'notification': {
#     #                 'title': 'Kenaikan Kelas',
#     #                 'message': notification_message,
#     #                 'type': 'success'
#     #             }
#     #         }),
#     #     }


#     # def action_proses_naik_kelas(self):
#     #     """
#     #     Aksi untuk memproses kenaikan kelas dengan menangani berbagai status siswa
#     #     """
#     #     # Logging awal
#     #     print(f"DEBUG - Memulai proses kenaikan kelas untuk tahun ajaran: {self.tahunajaran_id.name}")
        
#     #     if not self.partner_ids:
#     #         raise UserError("Belum ada santri yang dipilih!")
        
#     #     if not self.status:
#     #         raise UserError("Status kenaikan harus dipilih terlebih dahulu!")
        
#     #     # Mencatat aktifitas untuk sistem log    
#     #     self.ensure_one()
#     #     message = ""
#     #     count_siswa = 0
#     #     count_siswa_filtered = 0
#     #     count_lulus = 0
#     #     count_tidak_naik = 0
#     #     count_kelas_nonaktif = 0
        
#     #     # Definisikan tingkat akhir untuk setiap jenjang
#     #     tingkat_akhir_map = {
#     #         'sd': 6,
#     #         'mi': 6,
#     #         'smp': 9,
#     #         'mts': 9,
#     #         'sma': 12,
#     #         'ma': 12,
#     #         'smk': 12,
#     #         'tk': 2,  # TK B
#     #         'paud': 1  # PAUD biasanya hanya 1 tingkat
#     #     }
        
#     #     # Mendapatkan tahun ajaran berikutnya (hanya diperlukan untuk status 'naik')
#     #     tahun_ajaran_berikutnya = None
#     #     if self.status == 'naik':
#     #         try:
#     #             current_year = int(self.tahunajaran_id.name.split('/')[0])
#     #             next_year = current_year + 1
#     #             next_ta_name = f"{next_year}/{next_year+1}"
                
#     #             print(f"DEBUG - Current year: {current_year}, Next year: {next_year}")
#     #             print(f"DEBUG - Mencari tahun ajaran dengan nama: {next_ta_name}")
                
#     #             # Cari tahun ajaran berikutnya dengan nama yang tepat
#     #             tahun_ajaran_berikutnya = self.env['cdn.ref_tahunajaran'].search([
#     #                 ('name', '=', next_ta_name)
#     #             ], limit=1)
                
#     #             print(f"DEBUG - Hasil pencarian tahun ajaran berikutnya: {tahun_ajaran_berikutnya.name if tahun_ajaran_berikutnya else 'Tidak ditemukan'}")
                
#     #         except (ValueError, IndexError) as e:
#     #             print(f"ERROR - Format tahun ajaran tidak valid: {str(e)}")
#     #             raise UserError(f"Format tahun ajaran tidak valid: {self.tahunajaran_id.name}. Format yang diharapkan: YYYY/YYYY")
            
#     #         # Jika tahun ajaran berikutnya tidak ditemukan, buat yang baru
#     #         if not tahun_ajaran_berikutnya:
#     #             message += f"Tahun ajaran {next_ta_name} tidak ditemukan. Mencoba membuat tahun ajaran baru...\n"
#     #             try:
#     #                 tahun_ajaran_berikutnya = self._create_next_tahun_ajaran(self.tahunajaran_id)
#     #                 message += f"Berhasil membuat tahun ajaran baru: {tahun_ajaran_berikutnya.name}\n\n"
#     #             except Exception as e:
#     #                 message += f"Gagal membuat tahun ajaran baru: {str(e)}\n\n"
#     #                 raise UserError(f"Gagal membuat tahun ajaran baru: {str(e)}")
        
#     #     # Proses berdasarkan status
#     #     if self.status == 'naik':
#     #         # Proses kenaikan kelas
#     #         kelas_sekarang = self.kelas_id
#     #         if not kelas_sekarang.tingkat:
#     #             raise UserError("Kelas tidak memiliki tingkat yang valid!")
            
#     #         tingkat_sekarang = kelas_sekarang.tingkat
#     #         jenjang_lower = (kelas_sekarang.jenjang or '').lower()
#     #         tingkat_akhir = tingkat_akhir_map.get(jenjang_lower)
            
#     #         print(f"DEBUG - Memeriksa kelas: {kelas_sekarang.name.name}, Tingkat: {tingkat_sekarang.name}, Jenjang: {jenjang_lower}, Tingkat Akhir: {tingkat_akhir}")
            
#     #         # *** PERBAIKAN UTAMA - Sesuai dengan kode referensi ***
#     #         # Cek apakah ini sudah tingkat akhir sebelum mencari tingkat berikutnya
#     #         tingkat_sekarang_int = int(tingkat_sekarang.name)
#     #         if tingkat_akhir and tingkat_sekarang_int >= tingkat_akhir:
#     #             # Ini sudah tingkat akhir, jadi nonaktifkan tanpa mencari tingkat berikutnya
#     #             print(f"DEBUG - Kelas {kelas_sekarang.name.name} sudah mencapai tingkat akhir ({tingkat_sekarang.name}), akan dinonaktifkan")
                
#     #             try:
#     #                 kelas_sekarang.write({'aktif_tidak': 'tidak'})
                    
#     #                 count_kelas_nonaktif = len(self.partner_ids)
#     #                 message += f"Kelas {kelas_sekarang.name.name} dinonaktifkan karena sudah mencapai tingkat akhir ({tingkat_sekarang.name}). {count_kelas_nonaktif} santri tetap berada di kelas ini.\n"
                    
#     #             except Exception as e:
#     #                 raise UserError(f"Gagal menonaktifkan kelas {kelas_sekarang.name.name}: {str(e)}")
#     #         else:
#     #             # Belum tingkat akhir, cari tingkat berikutnya
#     #             tingkat_berikutnya = self.env['cdn.tingkat'].search([
#     #                 ('name', '=', tingkat_sekarang_int + 1),
#     #                 ('jenjang', '=', self.jenjang) if self.jenjang else ('id', '!=', False)
#     #             ], limit=1)

#     #             if not tingkat_berikutnya:
#     #                 # Tingkat berikutnya tidak ditemukan, tapi belum mencapai tingkat akhir teoritis
#     #                 # Ini bisa terjadi jika data tingkat tidak lengkap - nonaktifkan kelas
#     #                 print(f"DEBUG - Tingkat berikutnya ({tingkat_sekarang_int + 1}) tidak ditemukan, menonaktifkan kelas")
                    
#     #                 try:
#     #                     kelas_sekarang.write({'aktif_tidak': 'tidak'})
                        
#     #                     count_kelas_nonaktif = len(self.partner_ids)
#     #                     message += f"Kelas {kelas_sekarang.name.name} dinonaktifkan karena tingkat berikutnya ({tingkat_sekarang_int + 1}) tidak ditemukan. {count_kelas_nonaktif} santri tetap berada di kelas ini.\n"
                        
#     #                 except Exception as e:
#     #                     raise UserError(f"Gagal menonaktifkan kelas {kelas_sekarang.name.name}: {str(e)}")
#     #             else:
#     #                 # Ada tingkat berikutnya, cari master kelas untuk tingkat berikutnya
#     #                 domain_master_kelas = [
#     #                     ('tingkat', '=', tingkat_berikutnya.id),
#     #                     ('jenjang', '=', kelas_sekarang.jenjang)
#     #                 ]
                    
#     #                 # Tambahkan filter jurusan jika ada
#     #                 if hasattr(kelas_sekarang.name, 'jurusan_id') and kelas_sekarang.name.jurusan_id:
#     #                     domain_master_kelas.append(('jurusan_id', '=', kelas_sekarang.name.jurusan_id.id))
                    
#     #                 # Tambahkan filter nama kelas jika ada
#     #                 if hasattr(kelas_sekarang.name, 'nama_kelas') and kelas_sekarang.name.nama_kelas:
#     #                     domain_master_kelas.append(('nama_kelas', '=', kelas_sekarang.name.nama_kelas))
                    
#     #                 master_kelas_baru = self.env['cdn.master_kelas'].search(domain_master_kelas, limit=1)
                    
#     #                 if not master_kelas_baru:
#     #                     message += f"Master kelas untuk tingkat {tingkat_berikutnya.name} tidak ditemukan untuk kelas {kelas_sekarang.name.name}!\n"
#     #                     return
                    
#     #                 # Update kelas yang sudah ada ke tingkat berikutnya
#     #                 try:
#     #                     print(f"DEBUG - Memperbarui kelas: {kelas_sekarang.name.name}, Dari tingkat {tingkat_sekarang.name} ke {tingkat_berikutnya.name}")
                        
#     #                     # Update kelas ke tingkat berikutnya
#     #                     kelas_sekarang.write({
#     #                         'name': master_kelas_baru.id,
#     #                         'tahunajaran_id': tahun_ajaran_berikutnya.id,
#     #                         # Tingkat akan terupdate otomatis karena related field dari master_kelas
#     #                     })
                        
#     #                     message += f"Kelas {kelas_sekarang.name.name} berhasil diperbarui dari tingkat {tingkat_sekarang.name} ke tingkat {tingkat_berikutnya.name} untuk tahun ajaran {tahun_ajaran_berikutnya.name}\n"
                        
#     #                 except Exception as e:
#     #                     raise UserError(f"Gagal memperbarui kelas {kelas_sekarang.name.name}: {str(e)}")
            
#     #         # Proses filtering siswa hanya jika kelas naik (bukan kelas yang di-nonaktifkan)
#     #         if count_kelas_nonaktif == 0:  # Kelas naik normal
#     #             siswa_valid = []
#     #             siswa_difilter = []
                
#     #             for siswa in self.partner_ids:
#     #                 # Filter siswa berdasarkan kesesuaian jika ada kelas_selanjutnya_id
#     #                 if hasattr(siswa, 'kelas_selanjutnya_id') and siswa.kelas_selanjutnya_id:
#     #                     nama_kelas_selanjutnya = getattr(siswa, 'nama_kelas_selanjutnya', '') or ''
#     #                     jurusan_selanjutnya = getattr(siswa, 'jurusan_selanjutnya', None)
                        
#     #                     nama_kelas_ruang = kelas_sekarang.nama_kelas or ''
#     #                     jurusan_ruang = kelas_sekarang.jurusan_id
                        
#     #                     # Cek kesesuaian
#     #                     nama_kelas_cocok = nama_kelas_selanjutnya == nama_kelas_ruang
#     #                     jurusan_cocok = (
#     #                         (jurusan_selanjutnya and jurusan_ruang and jurusan_selanjutnya.id == jurusan_ruang.id) or
#     #                         (not jurusan_selanjutnya and not jurusan_ruang)
#     #                     )
                        
#     #                     if not (nama_kelas_cocok and jurusan_cocok):
#     #                         siswa_difilter.append({
#     #                             'siswa': siswa,
#     #                             'nama_kelas_selanjutnya': nama_kelas_selanjutnya,
#     #                             'jurusan_selanjutnya': jurusan_selanjutnya.name if jurusan_selanjutnya else 'Tidak ada',
#     #                             'nama_kelas_ruang': nama_kelas_ruang,
#     #                             'jurusan_ruang': jurusan_ruang.name if jurusan_ruang else 'Tidak ada'
#     #                         })
#     #                         continue
                    
#     #                 siswa_valid.append(siswa)
                
#     #             # Log siswa yang difilter
#     #             if siswa_difilter:
#     #                 count_siswa_filtered = len(siswa_difilter)
#     #                 message += f"{count_siswa_filtered} siswa dikeluarkan dari proses kenaikan kelas karena ketidaksesuaian:\n"
#     #                 for item in siswa_difilter:
#     #                     siswa_info = item['siswa']
#     #                     message += f"- {siswa_info.name}: Kelas selanjutnya '{item['nama_kelas_selanjutnya']}' - Jurusan '{item['jurusan_selanjutnya']}' tidak sesuai dengan kelas tujuan '{item['nama_kelas_ruang']}' - Jurusan '{item['jurusan_ruang']}'\n"
                
#     #             # Siswa yang valid tetap di kelas yang sama (yang sudah diupdate)
#     #             if count_siswa == 0:  # Hitung ulang jika belum dihitung
#     #                 count_siswa = len(siswa_valid)
                
#     #             siswa_count_info = f"{count_siswa} siswa"
#     #             if siswa_difilter:
#     #                 siswa_count_info += f" (dari {len(self.partner_ids)} siswa total, {count_siswa_filtered} difilter)"
                
#     #             if count_siswa > 0:
#     #                 message += f"Berhasil menaikkan {siswa_count_info} dari kelas {kelas_sekarang.name.name}.\n"
            
#     #     elif self.status == 'lulus':
#     #         # Proses kelulusan - hapus siswa dari kelas
#     #         for siswa in self.partner_ids:
#     #             siswa.write({'ruang_kelas_id': True})  # Hapus dari kelas
#     #             count_lulus += 1
            
#     #         message += f"Berhasil meluluskan {count_lulus} siswa dari kelas {self.kelas_id.name.name}.\n"
            
#     #     elif self.status == 'tidak_naik':
#     #         # Siswa tetap di kelas yang sama
#     #         count_tidak_naik = len(self.partner_ids)
#     #         message += f"{count_tidak_naik} siswa tidak naik kelas dan tetap di kelas {self.kelas_id.name.name}.\n"
            
#     #     elif self.status == 'tidak_lulus':
#     #         # Siswa tetap di kelas yang sama
#     #         count_tidak_naik = len(self.partner_ids)
#     #         message += f"{count_tidak_naik} siswa tidak lulus dan tetap di kelas {self.kelas_id.name.name}.\n"
        
#     #     # Commit perubahan
#     #     try:
#     #         self.env.cr.commit()
#     #         print("DEBUG - Perubahan berhasil di-commit ke database")
#     #     except Exception as e:
#     #         print(f"ERROR - Gagal melakukan commit perubahan: {str(e)}")
        
#     #     # Siapkan pesan hasil
#     #     result_message = f"Proses Kenaikan Kelas berhasil dilakukan!\n\n"
        
#     #     if self.status == 'naik':
#     #         if count_kelas_nonaktif > 0:
#     #             result_message += f"Kelas dinonaktifkan (tingkat akhir): {count_kelas_nonaktif} santri tetap di kelas\n"
#     #         else:
#     #             result_message += f"Total siswa naik kelas: {count_siswa}\n"
#     #             if count_siswa_filtered > 0:
#     #                 result_message += f"Total siswa difilter: {count_siswa_filtered}\n"
#     #     elif self.status == 'lulus':
#     #         result_message += f"Total siswa lulus: {count_lulus}\n"
#     #     elif self.status in ['tidak_naik', 'tidak_lulus']:
#     #         result_message += f"Total siswa {self.status.replace('_', ' ')}: {count_tidak_naik}\n"
        
#     #     result_message += f"\n{message}"
        
#     #     # Simpan hasil ke field message_result
#     #     self.message_result = result_message
        
#     #     # Buat notification message
#     #     if self.status == 'naik':
#     #         if count_kelas_nonaktif > 0:
#     #             notification_message = f'Kelas dinonaktifkan karena sudah tingkat akhir! {count_kelas_nonaktif} santri tetap di kelas.'
#     #         else:
#     #             notification_message = f'Proses kenaikan kelas berhasil! Total {count_siswa} siswa naik kelas.'
#     #             if count_siswa_filtered > 0:
#     #                 notification_message += f' {count_siswa_filtered} siswa difilter.'
#     #     elif self.status == 'lulus':
#     #         notification_message = f'Proses kelulusan berhasil! Total {count_lulus} siswa lulus.'
#     #     else:
#     #         notification_message = f'Proses berhasil! Total {count_tidak_naik} siswa {self.status.replace("_", " ")}.'
        
#     #     print(f"DEBUG - Proses kenaikan kelas selesai dengan pesan: {result_message}")
        
#     #     # Return untuk reload form dengan notifikasi
#     #     return {
#     #         'type': 'ir.actions.act_window',
#     #         'name': 'Kenaikan Kelas',
#     #         'res_model': 'cdn.kenaikan_kelas',
#     #         'view_mode': 'form',
#     #         'target': 'new',
#     #         'context': dict(self.env.context, **{
#     #             'notification': {
#     #                 'title': 'Kenaikan Kelas',
#     #                 'message': notification_message,
#     #                 'type': 'success'
#     #             }
#     #         }),
#     #     }

  
    
    
    
    



#     # @api.onchange('kelas_id')
#     # def _onchange_kelas_id(self):
#     #     """Auto-fill tingkat_id, walikelas_id dan status berdasarkan kelas yang dipilih"""
#     #     if self.kelas_id:
#     #         # Pastikan kelas record sudah di-load dengan field yang dibutuhkan
#     #         kelas = self.env['cdn.ruang_kelas'].browse(self.kelas_id.id)
            
#     #         # Set tingkat_id
#     #         try:
#     #             self.tingkat_id = kelas.tingkat.id if kelas.tingkat else False
#     #         except AttributeError:
#     #             # Jika field tingkat tidak ada, coba nama field lain
#     #             if hasattr(kelas, 'tingkat_id'):
#     #                 self.tingkat_id = kelas.tingkat_id.id if kelas.tingkat_id else False
#     #             else:
#     #                 self.tingkat_id = False
            
#     #         # Set walikelas_id
#     #         try:
#     #             self.walikelas_id = kelas.walikelas_id.id if kelas.walikelas_id else False
#     #         except AttributeError:
#     #             # Jika field walikelas_id tidak ada, coba nama field lain
#     #             if hasattr(kelas, 'wali_kelas_id'):
#     #                 self.walikelas_id = kelas.wali_kelas_id.id if kelas.wali_kelas_id else False
#     #             else:
#     #                 self.walikelas_id = False
            
#     #         # Set status berdasarkan tingkat
#     #         self._set_status_by_tingkat(kelas)
            
#     #     else:
#     #         self.tingkat_id = False
#     #         self.walikelas_id = False
#     #         self.status = False





# # class KenaikanKelas(models.Model):
# #     _name           = 'cdn.kenaikan_kelas'
# #     _description    = 'Menu POP UP untuk mengatur kenaikan kelas dan kelas yang lulus'
# #     _rec_name       = 'tahunajaran_id'

# #     def _default_tahunajaran(self):
# #        return self.env['res.company'].search([('id','=',1)]).tahun_ajaran_aktif

# #     jenjang             = fields.Selection(
# #         selection=[('paud', 'PAUD'), ('tk', 'TK/RA'), ('sd', 'SD/MI'),
# #                    ('smp', 'SMP/MTS'), ('sma', 'SMA/MA/SMK'), ('nonformal', 'Nonformal')],
# #         string="Jenjang", 
# #         store=True, 
# #         related='kelas_id.jenjang', 
# #     )
    
# #     tahunajaran_id      = fields.Many2one(comodel_name="cdn.ref_tahunajaran", string="Tahun Ajaran", default=_default_tahunajaran, readonly=False, store=True)
# #     kelas_id            = fields.Many2one('cdn.ruang_kelas', string='Kelas', domain="[('tahunajaran_id','=',tahunajaran_id), ('aktif_tidak','=','aktif'), ('status','=','konfirm')]")
# #     partner_ids         = fields.Many2many('cdn.siswa', 'kenaikan_santri_rel', 'kenaikan_id', 'santri_id', 'Santri')
    
# #     tingkat_id          = fields.Many2one('cdn.tingkat', string="Tingkat", store=True, readonly=False)    

# #     walikelas_id = fields.Many2one(
# #         comodel_name="hr.employee",  
# #         string="Wali Kelas",  
# #         domain="[('jns_pegawai','=','guru')]"
# #     )
    
# #     status = fields.Selection(
# #         selection=[('naik', 'Naik Kelas'), ('tidak_naik', 'Tidak Naik Kelas'), ('lulus', 'Lulus'), ('tidak_lulus', 'Tidak Lulus'), ],
# #         string="Status",
# #     )

# #     @api.onchange('kelas_id')
# #     def _onchange_kelas_id(self):
# #         """Auto-fill tingkat_id, walikelas_id dan status berdasarkan kelas yang dipilih"""
# #         if self.kelas_id:
# #             # Pastikan kelas record sudah di-load dengan field yang dibutuhkan
# #             kelas = self.env['cdn.ruang_kelas'].browse(self.kelas_id.id)
            
# #             # Set tingkat_id
# #             try:
# #                 self.tingkat_id = kelas.tingkat.id if kelas.tingkat else False
# #             except AttributeError:
# #                 # Jika field tingkat tidak ada, coba nama field lain
# #                 if hasattr(kelas, 'tingkat_id'):
# #                     self.tingkat_id = kelas.tingkat_id.id if kelas.tingkat_id else False
# #                 else:
# #                     self.tingkat_id = False
            
# #             # Set walikelas_id
# #             try:
# #                 self.walikelas_id = kelas.walikelas_id.id if kelas.walikelas_id else False
# #             except AttributeError:
# #                 # Jika field walikelas_id tidak ada, coba nama field lain
# #                 if hasattr(kelas, 'wali_kelas_id'):
# #                     self.walikelas_id = kelas.wali_kelas_id.id if kelas.wali_kelas_id else False
# #                 else:
# #                     self.walikelas_id = False
            
# #             # Set status berdasarkan tingkat
# #             self._set_status_by_tingkat(kelas)
            
# #         else:
# #             self.tingkat_id = False
# #             self.walikelas_id = False
# #             self.status = False

# #     def _set_status_by_tingkat(self, kelas):
# #         """Set status berdasarkan tingkat kelas"""
# #         if not kelas.tingkat:
# #             self.status = 'naik'  # Default jika tidak ada tingkat
# #             return
        
# #         # Ambil data tingkat
# #         tingkat = kelas.tingkat
        
# #         # Cek apakah tingkat 12 (kelas SMA/MA/SMK)
# #         is_tingkat_12 = self._is_tingkat_12(tingkat)
# #         if is_tingkat_12:
# #             # Untuk tingkat 12, cek apakah ada kelas selanjutnya
# #             has_next_class = self._check_next_class_exists(kelas)
# #             if has_next_class:
# #                 self.status = 'naik'
# #             else:
# #                 self.status = 'lulus'
# #             return
        
# #         # Cara 1: Cek berdasarkan nama tingkat (jika ada field nama/name)
# #         if hasattr(tingkat, 'name'):
# #             tingkat_name = str(tingkat.name).lower()
# #             # Cek apakah tingkat 6 atau 9
# #             if '6' in tingkat_name or 'vi' in tingkat_name or 'enam' in tingkat_name:
# #                 self.status = 'lulus'
# #             elif '9' in tingkat_name or 'ix' in tingkat_name or 'sembilan' in tingkat_name:
# #                 self.status = 'lulus'
# #             else:
# #                 self.status = 'naik'
        
# #         # Cara 2: Cek berdasarkan field urutan (jika ada)
# #         elif hasattr(tingkat, 'urutan'):
# #             if tingkat.urutan in [6, 9]:
# #                 self.status = 'lulus'
# #             else:
# #                 self.status = 'naik'
        
# #         # Cara 3: Cek berdasarkan field level (jika ada)
# #         elif hasattr(tingkat, 'level'):
# #             if tingkat.level in [6, 9]:
# #                 self.status = 'lulus'
# #             else:
# #                 self.status = 'naik'
        
# #         # Cara 4: Cek berdasarkan jenjang dan tingkat
# #         elif hasattr(kelas, 'jenjang'):
# #             # Untuk SD/MI: tingkat 6 = lulus
# #             if kelas.jenjang in ['sd'] and hasattr(tingkat, 'name'):
# #                 if '6' in str(tingkat.name) or 'vi' in str(tingkat.name).lower():
# #                     self.status = 'lulus'
# #                 else:
# #                     self.status = 'naik'
# #             # Untuk SMP/MTS: tingkat 9 = lulus  
# #             elif kelas.jenjang in ['smp'] and hasattr(tingkat, 'name'):
# #                 if '9' in str(tingkat.name) or 'ix' in str(tingkat.name).lower():
# #                     self.status = 'lulus'
# #                 else:
# #                     self.status = 'naik'
# #             else:
# #                 self.status = 'naik'
        
# #         else:
# #             # Default jika tidak bisa menentukan
# #             self.status = 'naik'

# #     @api.onchange('tingkat_id')
# #     def _onchange_tingkat_id(self):
# #         """Update status ketika tingkat_id diubah manual"""
# #         if self.tingkat_id and self.kelas_id:
# #             # Buat object kelas sementara untuk menggunakan method yang sama
# #             class MockKelas:
# #                 def __init__(self, tingkat, jenjang):
# #                     self.tingkat = tingkat
# #                     self.jenjang = jenjang
            
# #             mock_kelas = MockKelas(self.tingkat_id, self.jenjang)
# #             self._set_status_by_tingkat(mock_kelas)

# #     def _is_tingkat_12(self, tingkat):
# #         """Cek apakah tingkat adalah kelas 12"""
# #         if hasattr(tingkat, 'name'):
# #             tingkat_name = str(tingkat.name).lower()
# #             if '12' in tingkat_name or 'xii' in tingkat_name or 'duabelas' in tingkat_name:
# #                 return True
        
# #         if hasattr(tingkat, 'urutan'):
# #             if tingkat.urutan == 12:
# #                 return True
        
# #         if hasattr(tingkat, 'level'):
# #             if tingkat.level == 12:
# #                 return True
                
# #         return False

# #     def _check_next_class_exists(self, kelas):
# #         """Cek apakah ada kelas selanjutnya setelah tingkat 12 di cdn.master_kelas"""
# #         try:
# #             # Ambil tingkat saat ini
# #             current_tingkat = kelas.tingkat
# #             if not current_tingkat:
# #                 return False
            
# #             # Ambil jenjang dan jurusan dari kelas saat ini
# #             current_jenjang = kelas.jenjang if hasattr(kelas, 'jenjang') else None
# #             current_jurusan = None
            
# #             # Coba ambil jurusan dari kelas saat ini
# #             if hasattr(kelas, 'jurusan_id'):
# #                 current_jurusan = kelas.jurusan_id
# #             elif hasattr(kelas, 'name') and hasattr(kelas.name, 'jurusan_id'):
# #                 current_jurusan = kelas.name.jurusan_id
            
# #             # Tentukan tingkat selanjutnya yang mungkin (13, 14, dst)
# #             next_tingkat_numbers = [13, 14, 15, 16]  # Bisa disesuaikan
            
# #             # Cari tingkat selanjutnya di cdn.tingkat
# #             next_tingkat_ids = []
# #             for num in next_tingkat_numbers:
# #                 tingkat_domain = []
                
# #                 # Cari berdasarkan nama
# #                 tingkat_records = self.env['cdn.tingkat'].search([
# #                     '|', '|', '|',
# #                     ('name', 'ilike', str(num)),
# #                     ('name', 'ilike', self._number_to_roman(num)),
# #                     ('urutan', '=', num),
# #                     ('level', '=', num)
# #                 ])
                
# #                 if tingkat_records:
# #                     next_tingkat_ids.extend(tingkat_records.ids)
            
# #             if not next_tingkat_ids:
# #                 return False
            
# #             # Cari di cdn.master_kelas apakah ada kelas dengan tingkat selanjutnya
# #             master_kelas_domain = [('tingkat', 'in', next_tingkat_ids)]
            
# #             # Filter berdasarkan jenjang jika ada
# #             if current_jenjang:
# #                 master_kelas_domain.append(('jenjang', '=', current_jenjang))
            
# #             # Filter berdasarkan jurusan jika ada
# #             if current_jurusan:
# #                 master_kelas_domain.append(('jurusan_id', '=', current_jurusan.id))
            
# #             next_classes = self.env['cdn.master_kelas'].search(master_kelas_domain, limit=1)
            
# #             return bool(next_classes)
            
# #         except Exception as e:
# #             # Jika terjadi error, default ke False (lulus)
# #             import logging
# #             _logger = logging.getLogger(__name__)
# #             _logger.warning(f"Error checking next class: {str(e)}")
# #             return False

# #     def _number_to_roman(self, num):
# #         """Convert number to roman numeral"""
# #         roman_numerals = {
# #             13: 'XIII', 14: 'XIV', 15: 'XV', 16: 'XVI',
# #             17: 'XVII', 18: 'XVIII', 19: 'XIX', 20: 'XX'
# #         }
# #         return roman_numerals.get(num, str(num))
   













# # from odoo import fields, models, api, _
# # from odoo.exceptions import UserError
# # from datetime import timedelta, datetime
# # from dateutil.relativedelta import relativedelta

# # class KenaikanKelasTransition(models.Model):
# #     _name = 'cdn.kenaikan_kelas.transition'
# #     _description = 'Class Transition Information'
    
# #     kenaikan_id = fields.Many2one('cdn.kenaikan_kelas', string='Kenaikan Kelas', ondelete='cascade')
# #     current_class_id = fields.Many2one('cdn.ruang_kelas', string='Current Class ID', readonly=True)
# #     current_class = fields.Char(string='Kelas Saat Ini', readonly=True)
# #     next_class = fields.Char(string='Kelas Tujuan', readonly=True)
    
# #     # Field ini akan diisi langsung dari method _generate_class_transitions
# #     student_count = fields.Integer(string='Jumlah Siswa', readonly=True)
# #     walikelas_id = fields.Many2one(
# #         comodel_name="hr.employee", 
# #         string="Wali Kelas", 
# #         domain="[('jns_pegawai','=','guru')]", 
# #         readonly=False
# #     )
    
# #     wali_kelas_id = fields.Many2one(
# #         comodel_name="hr.employee", 
# #         string="Wali Kelas", 
# #         domain="[('jns_pegawai','=','guru')]", 
# #         readonly=False
# #     )
    
# #     transition_type = fields.Selection([
# #         ('naik', 'Naik Kelas'),
# #         ('lulus', 'Lulus'),
# #         ('tidak_naik', 'Tidak Naik'),
# #         ('tidak_lulus', 'Tidak Lulus'),
# #         # ('error', 'Error'),
# #     ], string='Jenis Perpindahan', readonly=False)

# #     @api.onchange('transition_type')
# #     def _onchange_transition_type(self):
# #         """
# #         Update siswa secara real-time ketika transition type berubah
# #         """
# #         if self.kenaikan_id and self.current_class and self.transition_type:
# #             # Cari siswa dari kelas ini
# #             siswa_kelas = self.kenaikan_id.partner_ids.filtered(
# #                 lambda s: (s.ruang_kelas_id.name.name if s.ruang_kelas_id.name else s.ruang_kelas_id.display_name) == self.current_class
# #             )
            
# #             for siswa in siswa_kelas:
# #                 # Update status kenaikan
# #                 siswa.status_kenaikan = self.transition_type
                
# #                 # Update kelas selanjutnya berdasarkan transition type
# #                 if self.transition_type == 'naik':
# #                     # Untuk naik kelas, perlu cek tingkat akhir
# #                     if siswa.ruang_kelas_id and siswa.ruang_kelas_id.tingkat:
# #                         kelas = siswa.ruang_kelas_id
# #                         tingkat_sekarang = kelas.tingkat
# #                         jenjang_lower = (kelas.jenjang or '').lower()
                        
# #                         # Definisikan tingkat akhir untuk setiap jenjang
# #                         tingkat_akhir_map = {
# #                             'sd': 6, 'mi': 6, 'smp': 9, 'mts': 9,
# #                             'sma': 12, 'ma': 12, 'smk': 12, 'tk': 2, 'paud': 1
# #                         }
                        
# #                         tingkat_akhir = tingkat_akhir_map.get(jenjang_lower)
# #                         tingkat_saat_ini = int(tingkat_sekarang.name)
                        
# #                         # Cek apakah sudah mencapai tingkat akhir
# #                         if tingkat_akhir and tingkat_saat_ini >= tingkat_akhir:
# #                             # Sudah tingkat akhir, kosongkan kelas selanjutnya dan ubah status ke lulus
# #                             siswa.kelas_selanjutnya = ''
# #                             siswa.status_kenaikan = 'lulus'
# #                         else:
# #                             # Belum tingkat akhir, gunakan next_class dari transition
# #                             siswa.kelas_selanjutnya = self.next_class
                            
# #                 elif self.transition_type == 'lulus':
# #                     siswa.kelas_selanjutnya = ''
                    
# #                 elif self.transition_type == 'tidak_lulus':
# #                     siswa.kelas_selanjutnya = ''
                    
# #                 elif self.transition_type == 'tidak_naik':
# #                     siswa.kelas_selanjutnya = siswa.ruang_kelas_id.name.name if siswa.ruang_kelas_id.name else siswa.ruang_kelas_id.display_name


# # class KenaikanKelas(models.Model):
# #     _name           = 'cdn.kenaikan_kelas'
# #     _description    = 'Menu POP UP untuk mengatur kenaikan kelas dan kelas yang lulus'
# #     _rec_name       = 'tahunajaran_id'

# #     def _default_tahunajaran(self):
# #        return self.env['res.company'].search([('id','=',1)]).tahun_ajaran_aktif

# #     jenjang             = fields.Selection(
# #         selection=[('paud', 'PAUD'), ('tk', 'TK/RA'), ('sd', 'SD/MI'),
# #                    ('smp', 'SMP/MTS'), ('sma', 'SMA/MA/SMK'), ('nonformal', 'Nonformal')],
# #         string="Jenjang", 
# #         store=True, 
# #         related='kelas_id.jenjang', 
# #     )
    
# #     tahunajaran_id      = fields.Many2one(comodel_name="cdn.ref_tahunajaran", string="Tahun Ajaran", default=_default_tahunajaran, readonly=False, store=True)
# #     kelas_id            = fields.Many2many('cdn.ruang_kelas', string='Kelas', domain="[('tahunajaran_id','=',tahunajaran_id), ('aktif_tidak','=','aktif'), ('status','=','konfirm')]")
# #     partner_ids         = fields.Many2many('cdn.siswa', 'kenaikan_santri_rel', 'kenaikan_id', 'santri_id', 'Santri')
    
# #     tingkat_id          = fields.Many2many('cdn.tingkat', string="Tingkat", store=True, readonly=False)    
# #     # Field baru untuk menampilkan perpindahan kelas
# #     class_transition_ids = fields.One2many('cdn.kenaikan_kelas.transition', 'kenaikan_id', string='Perpindahan Kelas', readonly=False)

# #     # nama_kelas_id       = fields.Char(
# #     #     string="Nama Kelas Selanjutnya",
# #     #     related='partner_ids.nama_kelas_selanjutnya',
# #     #     store=True,
# #     #     readonly=False,
# #     #     tracking=True
# #     # )
    
# #     # kenaikan = fields.Many2one('cdn.kenaikan_kelas', string="Kenaikan")
    
# #     # jurusan_sma_id      = fields.Many2one(
# #     #     comodel_name="cdn.master_jurusan",
# #     #     string="Jurusan Selanjutnya",
# #     #     related='partner_ids.jurusan_selanjutnya',
# #     #     store=True,
# #     #     readonly=False,
# #     #     tracking=True
# #     # )

# #     @api.onchange('kelas_id')
# #     def _onchange_kelas_id(self):
# #         """
# #         Fungsi untuk menangani perubahan pada field kelas_id.
# #         """
# #         # Kosongkan dulu daftar santri dan transition
# #         self.partner_ids = [(5, 0, 0)]
# #         self.class_transition_ids = [(5, 0, 0)]
        
# #         # Jika tidak ada kelas yang dipilih, kembalikan list kosong dan kosongkan tingkat
# #         if not self.kelas_id:
# #             self.tingkat_id = [(5, 0, 0)]
# #             return
        
# #         # Cara 1: Menggunakan relasi dengan mencari siswa melalui ruang_kelas_id
# #         domain = [('ruang_kelas_id', 'in', self.kelas_id.ids)]
        
# #         # Cari santri berdasarkan domain
# #         santri_ids = self.env['cdn.siswa'].search(domain)
        
# #         # Jika ditemukan santri, tambahkan ke partner_ids
# #         if santri_ids:
# #             self.partner_ids = [(6, 0, santri_ids.ids)]
            
# #             # Generate kelas selanjutnya untuk semua siswa
# #             santri_ids.generate_kelas_selanjutnya(self.kelas_id.ids)
        
# #         # Jika tidak ditemukan dengan cara 1, coba cara 2 (mungkin relasi many2many langsung)
# #         elif hasattr(self.env['cdn.ruang_kelas'], 'siswa_ids'):
# #             all_santri_ids = []
# #             for kelas in self.kelas_id:
# #                 if kelas.siswa_ids:
# #                     all_santri_ids.extend(kelas.siswa_ids.ids)
            
# #             if all_santri_ids:
# #                 santri_ids = self.env['cdn.siswa'].browse(all_santri_ids)
# #                 self.partner_ids = [(6, 0, santri_ids.ids)]
                
# #                 # Generate kelas selanjutnya untuk semua siswa
# #                 santri_ids.generate_kelas_selanjutnya(self.kelas_id.ids)
        
# #         # Update tingkat_id berdasarkan kelas_id yang dipilih
# #         tingkat_ids = self.env['cdn.tingkat']
# #         for kelas in self.kelas_id:
# #             if kelas.tingkat and kelas.tingkat not in tingkat_ids:
# #                 tingkat_ids |= kelas.tingkat
                
# #         # Set nilai tingkat_id dengan tingkat dari kelas yang dipilih
# #         if tingkat_ids:
# #             self.tingkat_id = [(6, 0, tingkat_ids.ids)]
        
# #         # Generate class transition information - gunakan method yang sudah ada
# #         self._generate_class_transitions()

# #     def action_reset_all_to_auto(self):
# #         """
# #         Method untuk reset semua siswa ke nilai otomatis
# #         """
# #         for siswa in self.partner_ids:
# #             siswa.reset_to_auto()
        
# #         # Refresh class transitions setelah reset
# #         self._generate_class_transitions()
        
# #         return {
# #             'type': 'ir.actions.client',
# #             'tag': 'reload',
# #         }

# #     def _generate_class_transitions(self):
# #         """
# #         Generate informasi perpindahan kelas untuk setiap kelas yang dipilih
# #         """
# #         if not self.kelas_id:
# #             return
        
# #         # Definisikan tingkat akhir untuk setiap jenjang
# #         tingkat_akhir_map = {
# #             'sd': 6, 'mi': 6, 'smp': 9, 'mts': 9,
# #             'sma': 12, 'ma': 12, 'smk': 12, 'tk': 2, 'paud': 1
# #         }
        
# #         transition_data = []
        
# #         for kelas in self.kelas_id:
# #             if not kelas.tingkat:
# #                 continue
            
# #             tingkat_sekarang = kelas.tingkat
# #             jenjang_lower = (kelas.jenjang or '').lower()
# #             tingkat_akhir = tingkat_akhir_map.get(jenjang_lower)
            
# #             current_class_name = kelas.name.name if kelas.name else kelas.display_name
# #             tingkat_saat_ini = int(tingkat_sekarang.name)
            
# #             # Cek apakah ini sudah tingkat akhir
# #             if tingkat_akhir and tingkat_saat_ini >= tingkat_akhir:
# #                 # Sudah tingkat akhir - Lulus
# #                 transition_data.append((0, 0, {
# #                     'current_class_id': kelas.id,
# #                     'current_class': current_class_name,
# #                     'next_class': '',  # Kosong karena lulus
# #                     'student_count': kelas.jml_siswa,
# #                     'walikelas_id': kelas.walikelas_id.id if kelas.walikelas_id else False,
# #                     'transition_type': 'lulus'
# #                 }))
# #             else:
# #                 # Belum tingkat akhir - cari tingkat berikutnya
# #                 tingkat_berikutnya = self.env['cdn.tingkat'].search([
# #                     ('name', '=', tingkat_saat_ini + 1),
# #                     ('jenjang', '=', kelas.jenjang)
# #                 ], limit=1)
                
# #                 if tingkat_berikutnya:
# #                     # Cek apakah tingkat berikutnya melebihi tingkat akhir
# #                     if tingkat_akhir and int(tingkat_berikutnya.name) > tingkat_akhir:
# #                         # Tingkat berikutnya melebihi tingkat akhir - Lulus
# #                         transition_data.append((0, 0, {
# #                             'current_class_id': kelas.id,
# #                             'current_class': current_class_name,
# #                             'next_class': '',  # Kosong karena lulus
# #                             'student_count': kelas.jml_siswa,
# #                             'walikelas_id': kelas.walikelas_id.id if kelas.walikelas_id else False,
# #                             'transition_type': 'lulus'
# #                         }))
# #                     else:
# #                         # Cari master kelas untuk tingkat berikutnya
# #                         domain_master_kelas = [
# #                             ('tingkat', '=', tingkat_berikutnya.id),
# #                             ('jenjang', '=', kelas.jenjang)
# #                         ]
                        
# #                         # Tambahkan filter lain jika diperlukan
# #                         if hasattr(kelas.name, 'jurusan_id') and kelas.name.jurusan_id:
# #                             domain_master_kelas.append(('jurusan_id', '=', kelas.name.jurusan_id.id))
                        
# #                         if hasattr(kelas.name, 'nama_kelas') and kelas.name.nama_kelas:
# #                             domain_master_kelas.append(('nama_kelas', '=', kelas.name.nama_kelas))
                        
# #                         master_kelas_baru = self.env['cdn.master_kelas'].search(domain_master_kelas, limit=1)
                        
# #                         if master_kelas_baru:
# #                             next_class_name = master_kelas_baru.name
# #                             transition_data.append((0, 0, {
# #                                 'current_class_id': kelas.id,
# #                                 'current_class': current_class_name,
# #                                 'next_class': next_class_name,
# #                                 'student_count': kelas.jml_siswa,
# #                                 'walikelas_id': kelas.walikelas_id.id if kelas.walikelas_id else False,
# #                                 'transition_type': 'naik'
# #                             }))
# #                         else:
# #                             # Master kelas berikutnya tidak ditemukan
# #                             transition_data.append((0, 0, {
# #                                 'current_class_id': kelas.id,
# #                                 'current_class': current_class_name,
# #                                 'next_class': f'Tingkat {tingkat_berikutnya.name} (Master kelas tidak ditemukan)',
# #                                 'student_count': kelas.jml_siswa,
# #                                 'walikelas_id': kelas.walikelas_id.id if kelas.walikelas_id else False,
# #                                 'transition_type': 'naik'
# #                             }))
# #                 else:
# #                     # Tingkat berikutnya tidak ditemukan - anggap lulus
# #                     transition_data.append((0, 0, {
# #                         'current_class_id': kelas.id,
# #                         'current_class': current_class_name,
# #                         'next_class': '',  # Kosong karena lulus
# #                         'student_count': kelas.jml_siswa,
# #                         'walikelas_id': kelas.walikelas_id.id if kelas.walikelas_id else False,
# #                         'transition_type': 'lulus'
# #                     }))
        
# #         # Set transition data
# #         self.class_transition_ids = transition_data

# #     def action_apply_transitions(self):
# #         """
# #         Method untuk menerapkan semua transition ke siswa
# #         """
# #         for transition in self.class_transition_ids:
# #             if transition.transition_type:
# #                 # Update semua siswa dari kelas ini
# #                 siswa_kelas = self.partner_ids.filtered(
# #                     lambda s: (s.ruang_kelas_id.name.name if s.ruang_kelas_id.name else s.ruang_kelas_id.display_name) == transition.current_class
# #                 )
                
# #                 for siswa in siswa_kelas:
# #                     # Tandai sebagai manual override
# #                     siswa.is_manual_override = True
# #                     siswa.status_kenaikan = transition.transition_type
                    
# #                     if transition.transition_type == 'naik':
# #                         # Untuk naik kelas, cek apakah sudah tingkat akhir
# #                         if siswa.ruang_kelas_id and siswa.ruang_kelas_id.tingkat:
# #                             kelas = siswa.ruang_kelas_id
# #                             tingkat_sekarang = kelas.tingkat
# #                             jenjang_lower = (kelas.jenjang or '').lower()
                            
# #                             # Definisikan tingkat akhir untuk setiap jenjang
# #                             tingkat_akhir_map = {
# #                                 'sd': 6, 'mi': 6, 'smp': 9, 'mts': 9,
# #                                 'sma': 12, 'ma': 12, 'smk': 12, 'tk': 2, 'paud': 1
# #                             }
                            
# #                             tingkat_akhir = tingkat_akhir_map.get(jenjang_lower)
# #                             tingkat_saat_ini = int(tingkat_sekarang.name)
                            
# #                             if tingkat_akhir and tingkat_saat_ini >= tingkat_akhir:
# #                                 # Sudah tingkat akhir, kosongkan dan ubah status ke lulus
# #                                 siswa.kelas_selanjutnya = ''
# #                                 siswa.kelas_selanjutnya_id = False
# #                                 siswa.status_kenaikan = 'lulus'
# #                             else:
# #                                 # Belum tingkat akhir, gunakan next_class
# #                                 siswa.kelas_selanjutnya = transition.next_class
# #                                 # Cari master kelas yang sesuai
# #                                 master_kelas = self.env['cdn.master_kelas'].search([
# #                                     ('name', '=', transition.next_class)
# #                                 ], limit=1)
# #                                 siswa.kelas_selanjutnya_id = master_kelas.id if master_kelas else False
                                
# #                     elif transition.transition_type in ['lulus', 'tidak_lulus']:
# #                         siswa.kelas_selanjutnya = ''
# #                         siswa.kelas_selanjutnya_id = False
                        
# #                     elif transition.transition_type == 'tidak_naik':
# #                         current_class_name = siswa.ruang_kelas_id.name.name if siswa.ruang_kelas_id.name else siswa.ruang_kelas_id.display_name
# #                         siswa.kelas_selanjutnya = current_class_name
# #                         siswa.kelas_selanjutnya_id = False
        
# #         return {
# #             'type': 'ir.actions.client',
# #             'tag': 'reload',
# #         }

# #     @api.onchange('tingkat_id', 'tahunajaran_id', 'jenjang')
# #     def _onchange_tingkat_id(self):
# #         """
# #         Fungsi untuk menangani perubahan pada field tingkat_id.
# #         Jika tingkat_id diisi, akan menampilkan kelas_id yang sesuai dengan tingkat tersebut
# #         dan tahun ajaran yang dipilih. Jika dikosongkan, maka kelas_id juga dikosongkan.
# #         """
# #         # Jika tidak ada tingkat, kosongkan kelas dan partner
# #         if not self.tingkat_id:
# #             self.kelas_id = [(5, 0, 0)]
# #             self.partner_ids = [(5, 0, 0)]
# #             self.class_transition_ids = [(5, 0, 0)]
# #             return

# #         # Jika tidak ada tahun ajaran, batalkan
# #         if not self.tahunajaran_id:
# #             return

# #         # Buat domain kelas berdasarkan tingkat, tahun ajaran, dan jenjang
# #         domain = [
# #             ('tingkat', 'in', self.tingkat_id.ids),
# #             ('tahunajaran_id', '=', self.tahunajaran_id.id),
# #             ('aktif_tidak', '=', 'aktif'),
# #             ('status', '=', 'konfirm')
# #         ]

# #         if self.jenjang:
# #             domain.append(('jenjang', '=', self.jenjang))

# #         # Cari kelas yang sesuai
# #         kelas_ids = self.env['cdn.ruang_kelas'].search(domain)

# #         # Update kelas_id langsung
# #         self.kelas_id = [(6, 0, kelas_ids.ids)]

# #         # Panggil kembali onchange kelas untuk update partner_ids & tingkat_id
# #         self._onchange_kelas_id()
        
# #     def _create_next_tahun_ajaran(self, current_ta):
# #         """
# #         Fungsi untuk membuat tahun ajaran berikutnya jika belum ada
# #         Disesuaikan dengan sistem pendidikan di Indonesia (Juli-Juni)
        
# #         Args:
# #             current_ta: Tahun ajaran saat ini
            
# #         Returns:
# #             cdn.ref_tahunajaran: Tahun ajaran baru yang dibuat
# #         """
# #         try:
# #             print(f"DEBUG - Mencoba membuat tahun ajaran baru setelah {current_ta.name}")
            
# #             # Ekstrak tahun dari nama tahun ajaran saat ini
# #             current_year = int(current_ta.name.split('/')[0])
# #             next_year = current_year + 1
# #             next_ta_name = f"{next_year}/{next_year+1}"
            
# #             print(f"DEBUG - Tahun yang diekstrak: {current_year}, Tahun berikutnya: {next_year}")
# #             print(f"DEBUG - Nama tahun ajaran baru: {next_ta_name}")
            
# #             # Tentukan tanggal mulai dan akhir sesuai sistem pendidikan Indonesia
# #             # Tahun ajaran di Indonesia umumnya Juli-Juni
# #             today = fields.Date.from_string(fields.Date.today())
            
# #             # Untuk pembuatan tahun ajaran baru, selalu gunakan tahun +1 dari current year
# #             start_date = datetime(next_year, 7, 1).date()
# #             end_date = datetime(next_year + 1, 6, 30).date()
            
# #             print(f"DEBUG - Tanggal mulai: {start_date}, Tanggal akhir: {end_date}")
            
# #             # Cek apakah sudah ada tahun ajaran dengan nama tersebut
# #             existing_ta_by_name = self.env['cdn.ref_tahunajaran'].search([
# #                 ('name', '=', next_ta_name)
# #             ], limit=1)
            
# #             if existing_ta_by_name:
# #                 print(f"DEBUG - Tahun ajaran dengan nama {next_ta_name} sudah ada")
# #                 return existing_ta_by_name
                
# #             # Cek apakah sudah ada tahun ajaran dengan rentang waktu tersebut
# #             existing_ta = self.env['cdn.ref_tahunajaran'].search([
# #                 ('start_date', '=', start_date),
# #                 ('end_date', '=', end_date)
# #             ], limit=1)
            
# #             if existing_ta:
# #                 print(f"DEBUG - Tahun ajaran dengan rentang {start_date} - {end_date} sudah ada")
# #                 return existing_ta
            
# #             print(f"DEBUG - Membuat tahun ajaran baru: {next_ta_name}")
            
# #             # Buat tahun ajaran baru dengan sudo untuk memastikan hak akses
# #             new_ta = self.env['cdn.ref_tahunajaran'].sudo().create({
# #                 'name': next_ta_name,
# #                 'start_date': start_date,
# #                 'end_date': end_date,
# #                 'term_structure': current_ta.term_structure,
# #                 'company_id': current_ta.company_id.id,
# #                 'keterangan': f"Dibuat otomatis dari proses kenaikan kelas pada {fields.Date.today()}"
# #             })
            
# #             # Verifikasi record telah dibuat
# #             if not new_ta:
# #                 raise UserError(f"Gagal membuat tahun ajaran baru {next_ta_name}")
            
# #             # Commit transaksi untuk memastikan data tersimpan
# #             self.env.cr.commit()
            
# #             # Buat termin akademik dan periode tagihan
# #             new_ta.term_create()
            
# #             # Log untuk debug
# #             print(f"DEBUG - Tahun ajaran baru berhasil dibuat: {new_ta.name} ({new_ta.start_date} - {new_ta.end_date})")
            
# #             return new_ta
# #         except Exception as e:
# #             print(f"ERROR - Gagal membuat tahun ajaran baru: {str(e)}")
# #             # Re-raise supaya bisa dilihat di UI
# #             raise UserError(f"Gagal membuat tahun ajaran baru: {str(e)}")



# #     def action_proses_kenaikan_kelas(self):
# #         """
# #         Aksi untuk memproses kenaikan kelas dengan hanya memperbarui kelas yang sudah ada
# #         """
# #         # Logging awal
# #         print(f"DEBUG - Memulai proses kenaikan kelas untuk tahun ajaran: {self.tahunajaran_id.name}")
        
# #         if not self.partner_ids:
# #             raise UserError("Belum ada santri yang dipilih!")
        
# #         # Mencatat aktifitas untuk sistem log    
# #         self.ensure_one()
# #         message = ""
# #         count_siswa = 0
# #         count_siswa_filtered = 0  # Counter untuk siswa yang difilter
        
# #         # Mendapatkan tahun ajaran berikutnya dengan cara yang lebih tepat
# #         try:
# #             current_year = int(self.tahunajaran_id.name.split('/')[0])
# #             next_year = current_year + 1
# #             next_ta_name = f"{next_year}/{next_year+1}"
            
# #             print(f"DEBUG - Current year: {current_year}, Next year: {next_year}")
# #             print(f"DEBUG - Mencari tahun ajaran dengan nama: {next_ta_name}")
            
# #             # Cari tahun ajaran berikutnya dengan nama yang tepat
# #             tahun_ajaran_berikutnya = self.env['cdn.ref_tahunajaran'].search([
# #                 ('name', '=', next_ta_name)
# #             ], limit=1)
            
# #             print(f"DEBUG - Hasil pencarian tahun ajaran berikutnya: {tahun_ajaran_berikutnya.name if tahun_ajaran_berikutnya else 'Tidak ditemukan'}")
            
# #         except (ValueError, IndexError) as e:
# #             print(f"ERROR - Format tahun ajaran tidak valid: {str(e)}")
# #             raise UserError(f"Format tahun ajaran tidak valid: {self.tahunajaran_id.name}. Format yang diharapkan: YYYY/YYYY")
        
# #         # Jika tahun ajaran berikutnya tidak ditemukan, buat yang baru
# #         if not tahun_ajaran_berikutnya:
# #             message += f"Tahun ajaran {next_ta_name} tidak ditemukan. Mencoba membuat tahun ajaran baru...\n"
# #             try:
# #                 tahun_ajaran_berikutnya = self._create_next_tahun_ajaran(self.tahunajaran_id)
# #                 message += f"Berhasil membuat tahun ajaran baru: {tahun_ajaran_berikutnya.name}\n\n"
# #             except Exception as e:
# #                 message += f"Gagal membuat tahun ajaran baru: {str(e)}\n\n"
# #                 raise UserError(f"Gagal membuat tahun ajaran baru: {str(e)}")
        
# #         # Definisikan tingkat akhir untuk setiap jenjang
# #         tingkat_akhir_map = {
# #             'sd': 6,
# #             'mi': 6,
# #             'smp': 9,
# #             'mts': 9,
# #             'sma': 12,
# #             'ma': 12,
# #             'smk': 12,
# #             'tk': 2,  # TK B
# #             'paud': 1  # PAUD biasanya hanya 1 tingkat
# #         }
        
# #         # Kumpulkan semua kelas yang akan diperbarui
# #         kelas_untuk_update = {}
# #         kelas_untuk_nonaktif = []
        
# #         for kelas in self.kelas_id:
# #             if not kelas.tingkat:
# #                 message += f"- Kelas {kelas.name.name}: Tidak memiliki tingkat yang valid.\n"
# #                 continue
                        
# #             tingkat_sekarang = kelas.tingkat
# #             jenjang_lower = (kelas.jenjang or '').lower()
# #             tingkat_akhir = tingkat_akhir_map.get(jenjang_lower)
            
# #             print(f"DEBUG - Memeriksa kelas: {kelas.name.name}, Tingkat: {tingkat_sekarang.name}, Jenjang: {jenjang_lower}, Tingkat Akhir: {tingkat_akhir}")
            
# #             # *** PERBAIKAN UTAMA ***
# #             # Cek apakah ini sudah tingkat akhir sebelum mencari tingkat berikutnya
# #             if tingkat_akhir and int(tingkat_sekarang.name) >= tingkat_akhir:
# #                 # Ini sudah tingkat akhir, jadi nonaktifkan tanpa mencari tingkat berikutnya
# #                 kelas_untuk_nonaktif.append({
# #                     'kelas': kelas,
# #                     'tingkat_sekarang': tingkat_sekarang,
# #                     'reason': 'sudah_tingkat_akhir'
# #                 })
# #                 continue
            
# #             # Jika belum tingkat akhir, cari tingkat berikutnya
# #             tingkat_berikutnya = self.env['cdn.tingkat'].search([
# #                 ('name', '=', int(tingkat_sekarang.name) + 1),
# #                 ('jenjang', '=', self.jenjang) if self.jenjang else ('id', '!=', False)
# #             ], limit=1)

# #             if not tingkat_berikutnya:
# #                 # Tingkat berikutnya tidak ditemukan, tapi belum mencapai tingkat akhir teoritis
# #                 # Ini bisa terjadi jika data tingkat tidak lengkap
# #                 kelas_untuk_nonaktif.append({
# #                     'kelas': kelas,
# #                     'tingkat_sekarang': tingkat_sekarang,
# #                     'reason': 'tingkat_berikutnya_tidak_ditemukan'
# #                 })
# #                 continue
            
# #             # Cari master kelas untuk tingkat berikutnya yang sesuai
# #             domain_master_kelas = [
# #                 ('tingkat', '=', tingkat_berikutnya.id),
# #                 ('jenjang', '=', kelas.jenjang)
# #             ]
            
# #             # Tambahkan filter lain jika diperlukan
# #             if hasattr(kelas.name, 'jurusan_id') and kelas.name.jurusan_id:
# #                 domain_master_kelas.append(('jurusan_id', '=', kelas.name.jurusan_id.id))
            
# #             if hasattr(kelas.name, 'nama_kelas') and kelas.name.nama_kelas:
# #                 domain_master_kelas.append(('nama_kelas', '=', kelas.name.nama_kelas))
            
# #             master_kelas_baru = self.env['cdn.master_kelas'].search(domain_master_kelas, limit=1)
            
# #             if not master_kelas_baru:
# #                 message += f"- Kelas {kelas.name.name}: Master kelas untuk tingkat {tingkat_berikutnya.name} tidak ditemukan.\n"
# #                 continue
            
# #             # Simpan ke dictionary untuk diproses nanti
# #             kelas_untuk_update[kelas.id] = {
# #                 'kelas': kelas,
# #                 'tingkat_sekarang': tingkat_sekarang,
# #                 'tingkat_berikutnya': tingkat_berikutnya,
# #                 'master_kelas_baru': master_kelas_baru
# #             }
        
# #         # Proses kelas yang akan dinonaktifkan
# #         for item in kelas_untuk_nonaktif:
# #             kelas = item['kelas']
# #             tingkat_sekarang = item['tingkat_sekarang']
# #             reason = item['reason']
            
# #             try:
# #                 kelas.write({'aktif_tidak': 'tidak'})
                
# #                 if reason == 'sudah_tingkat_akhir':
# #                     message += f"- Kelas {kelas.name.name} dinonaktifkan karena sudah mencapai tingkat akhir ({tingkat_sekarang.name}).\n"
# #                 else:
# #                     message += f"- Kelas {kelas.name.name} dinonaktifkan karena tingkat berikutnya ({int(tingkat_sekarang.name) + 1}) tidak ditemukan.\n"
                    
# #             except Exception as e:
# #                 message += f"- ERROR: Gagal menonaktifkan kelas {kelas.name.name}: {str(e)}\n"
# #                 print(f"ERROR - Gagal menonaktifkan kelas {kelas.name.name}: {str(e)}")
        
# #         # Sekarang update kelas yang naik tingkat
# #         for kelas_id, info in kelas_untuk_update.items():
# #             kelas = info['kelas']
# #             tingkat_sekarang = info['tingkat_sekarang']
# #             tingkat_berikutnya = info['tingkat_berikutnya']
# #             master_kelas_baru = info['master_kelas_baru']
            
# #             # Perbarui kelas yang sudah ada
# #             try:
# #                 print(f"DEBUG - Memperbarui kelas: {kelas.name.name}, Dari tingkat {tingkat_sekarang.name} ke {tingkat_berikutnya.name}")
                
# #                 # Update kelas ke tingkat berikutnya
# #                 kelas.write({
# #                     'name': master_kelas_baru.id,
# #                     'tahunajaran_id': tahun_ajaran_berikutnya.id,
# #                     # Tingkat akan terupdate otomatis karena related field dari master_kelas
# #                 })
                
# #                 # Ambil siswa yang ada di kelas ini
# #                 siswa_dalam_kelas = self.partner_ids.filtered(lambda s: s.ruang_kelas_id.id == kelas.id)
                
# #                 # *** FITUR BARU: Filter siswa berdasarkan kesesuaian nama_kelas dan jurusan ***
# #                 siswa_valid = []
# #                 siswa_difilter = []
                
# #                 for siswa in siswa_dalam_kelas:
# #                     # Cek apakah siswa memiliki kelas_selanjutnya_id
# #                     if not siswa.kelas_selanjutnya_id:
# #                         # Jika tidak ada kelas selanjutnya, gunakan master_kelas_baru sebagai default
# #                         siswa_valid.append(siswa)
# #                         continue
                    
# #                     # Ambil data dari kelas selanjutnya siswa
# #                     nama_kelas_selanjutnya = siswa.nama_kelas_selanjutnya or ''
# #                     jurusan_selanjutnya = siswa.jurusan_selanjutnya
                    
# #                     # Ambil data dari ruang kelas tujuan
# #                     nama_kelas_ruang = kelas.nama_kelas or ''
# #                     jurusan_ruang = kelas.jurusan_id
                    
# #                     # Cek kesesuaian nama kelas dan jurusan
# #                     nama_kelas_cocok = nama_kelas_selanjutnya == nama_kelas_ruang
# #                     jurusan_cocok = (
# #                         (jurusan_selanjutnya and jurusan_ruang and jurusan_selanjutnya.id == jurusan_ruang.id) or
# #                         (not jurusan_selanjutnya and not jurusan_ruang)
# #                     )
                    
# #                     if nama_kelas_cocok and jurusan_cocok:
# #                         siswa_valid.append(siswa)
# #                     else:
# #                         siswa_difilter.append({
# #                             'siswa': siswa,
# #                             'nama_kelas_selanjutnya': nama_kelas_selanjutnya,
# #                             'jurusan_selanjutnya': jurusan_selanjutnya.name if jurusan_selanjutnya else 'Tidak ada',
# #                             'nama_kelas_ruang': nama_kelas_ruang,
# #                             'jurusan_ruang': jurusan_ruang.name if jurusan_ruang else 'Tidak ada'
# #                         })
                
# #                 # Log siswa yang difilter
# #                 if siswa_difilter:
# #                     count_siswa_filtered += len(siswa_difilter)
# #                     message += f"- Kelas {kelas.name.name}: {len(siswa_difilter)} siswa dikeluarkan dari proses kenaikan kelas karena ketidaksesuaian:\n"
# #                     for item in siswa_difilter:
# #                         siswa_info = item['siswa']
# #                         message += f"  * {siswa_info.name}: Kelas selanjutnya '{item['nama_kelas_selanjutnya']}' - Jurusan '{item['jurusan_selanjutnya']}' tidak sesuai dengan kelas tujuan '{item['nama_kelas_ruang']}' - Jurusan '{item['jurusan_ruang']}'\n"

# #                 # Update kelas siswa yang valid ke kelas baru
# #                 for siswa in siswa_valid:
# #                     kelas_baru = siswa.kelas_selanjutnya_id or master_kelas_baru
# #                     if kelas_baru:
# #                         # Cari ruang kelas berdasarkan master kelas dan tahun ajaran berikutnya
# #                         ruang_kelas_baru = self.env['cdn.ruang_kelas'].search([
# #                             ('name', '=', kelas_baru.id),
# #                             ('tahunajaran_id', '=', tahun_ajaran_berikutnya.id)
# #                         ], limit=1)

# #                         if ruang_kelas_baru:
# #                             siswa.write({'ruang_kelas_id': ruang_kelas_baru.id})
# #                         else:
# #                             message += f"- WARNING: Siswa {siswa.name} tidak dipindahkan karena ruang kelas untuk master kelas {kelas_baru.name} tahun ajaran {tahun_ajaran_berikutnya.name} tidak ditemukan.\n"
# #                     else:
# #                         message += f"- WARNING: Siswa {siswa.name} tidak memiliki kelas selanjutnya yang valid.\n"

# #                 count_siswa += len(siswa_valid)
                
# #                 siswa_count_info = f"{len(siswa_valid)} siswa"
# #                 if siswa_difilter:
# #                     siswa_count_info += f" (dari {len(siswa_dalam_kelas)} siswa total, {len(siswa_difilter)} difilter)"
                
# #                 message += f"- Kelas {kelas.name.name}: Berhasil diperbarui dari tingkat {tingkat_sekarang.name} ke tingkat {tingkat_berikutnya.name} untuk tahun ajaran {tahun_ajaran_berikutnya.name} dengan {siswa_count_info}.\n"
                
# #             except Exception as e:
# #                 message += f"- ERROR: Gagal memperbarui kelas {kelas.name.name}: {str(e)}\n"
# #                 print(f"ERROR - Gagal memperbarui kelas {kelas.name.name}: {str(e)}")
        
# #         # Commit perubahan setelah semua kelas diupdate
# #         try:
# #             self.env.cr.commit()
# #             print("DEBUG - Perubahan berhasil di-commit ke database")
# #         except Exception as e:
# #             print(f"ERROR - Gagal melakukan commit perubahan: {str(e)}")
        
# #         # Log hasil proses (hanya untuk debug, tidak ditampilkan ke user)
# #         result_message = f"Proses Kenaikan Kelas berhasil dilakukan!\n\n"
# #         result_message += f"Total siswa diproses: {count_siswa}\n"
# #         if count_siswa_filtered > 0:
# #             result_message += f"Total siswa difilter: {count_siswa_filtered}\n"
# #         result_message += f"\n{message}"
        
# #         print(f"DEBUG - Proses kenaikan kelas selesai dengan pesan: {result_message}")
        
# #         # Tambahkan pesan sukses ke wizard tanpa reset fields
# #         # Ini akan menampilkan pesan di form wizard tanpa menutupnya
# #         if hasattr(self, 'message_result'):
# #             self.message_result = result_message
        
# #         # Buat notification message yang lebih informatif
# #         notification_message = f'Proses kenaikan kelas berhasil! Total {count_siswa} siswa diproses.'
# #         if count_siswa_filtered > 0:
# #             notification_message += f' {count_siswa_filtered} siswa difilter karena ketidaksesuaian kelas/jurusan.'
        
# #         # Ganti return statement dengan ini untuk reload form sekaligus notifikasi
# #         return {
# #             'type': 'ir.actions.act_window',
# #             'name': 'Kenaikan Kelas',
# #             'res_model': 'cdn.kenaikan_kelas',
# #             'view_mode': 'form',
# #             'target': 'new',
# #             'context': dict(self.env.context, **{
# #                 'notification': {
# #                     'title': 'Kenaikan Kelas',
# #                     'message': notification_message,
# #                     'type': 'success'
# #                 }
# #             }),
# #         }


# #     # def action_proses_kenaikan_kelas(self):
# #     #     """
# #     #     Aksi untuk memproses kenaikan kelas dengan hanya memperbarui kelas yang sudah ada
# #     #     """
# #     #     # Logging awal
# #     #     print(f"DEBUG - Memulai proses kenaikan kelas untuk tahun ajaran: {self.tahunajaran_id.name}")
        
# #     #     if not self.partner_ids:
# #     #         raise UserError("Belum ada santri yang dipilih!")
        
# #     #     # Mencatat aktifitas untuk sistem log    
# #     #     self.ensure_one()
# #     #     message = ""
# #     #     count_siswa = 0
        
# #     #     # Mendapatkan tahun ajaran berikutnya dengan cara yang lebih tepat
# #     #     try:
# #     #         current_year = int(self.tahunajaran_id.name.split('/')[0])
# #     #         next_year = current_year + 1
# #     #         next_ta_name = f"{next_year}/{next_year+1}"
            
# #     #         print(f"DEBUG - Current year: {current_year}, Next year: {next_year}")
# #     #         print(f"DEBUG - Mencari tahun ajaran dengan nama: {next_ta_name}")
            
# #     #         # Cari tahun ajaran berikutnya dengan nama yang tepat
# #     #         tahun_ajaran_berikutnya = self.env['cdn.ref_tahunajaran'].search([
# #     #             ('name', '=', next_ta_name)
# #     #         ], limit=1)
            
# #     #         print(f"DEBUG - Hasil pencarian tahun ajaran berikutnya: {tahun_ajaran_berikutnya.name if tahun_ajaran_berikutnya else 'Tidak ditemukan'}")
            
# #     #     except (ValueError, IndexError) as e:
# #     #         print(f"ERROR - Format tahun ajaran tidak valid: {str(e)}")
# #     #         raise UserError(f"Format tahun ajaran tidak valid: {self.tahunajaran_id.name}. Format yang diharapkan: YYYY/YYYY")
        
# #     #     # Jika tahun ajaran berikutnya tidak ditemukan, buat yang baru
# #     #     if not tahun_ajaran_berikutnya:
# #     #         message += f"Tahun ajaran {next_ta_name} tidak ditemukan. Mencoba membuat tahun ajaran baru...\n"
# #     #         try:
# #     #             tahun_ajaran_berikutnya = self._create_next_tahun_ajaran(self.tahunajaran_id)
# #     #             message += f"Berhasil membuat tahun ajaran baru: {tahun_ajaran_berikutnya.name}\n\n"
# #     #         except Exception as e:
# #     #             message += f"Gagal membuat tahun ajaran baru: {str(e)}\n\n"
# #     #             raise UserError(f"Gagal membuat tahun ajaran baru: {str(e)}")
        
# #     #     # Definisikan tingkat akhir untuk setiap jenjang
# #     #     tingkat_akhir_map = {
# #     #         'sd': 6,
# #     #         'mi': 6,
# #     #         'smp': 9,
# #     #         'mts': 9,
# #     #         'sma': 12,
# #     #         'ma': 12,
# #     #         'smk': 12,
# #     #         'tk': 2,  # TK B
# #     #         'paud': 1  # PAUD biasanya hanya 1 tingkat
# #     #     }
        
# #     #     # Kumpulkan semua kelas yang akan diperbarui
# #     #     kelas_untuk_update = {}
# #     #     kelas_untuk_nonaktif = []
        
# #     #     for kelas in self.kelas_id:
# #     #         if not kelas.tingkat:
# #     #             message += f"- Kelas {kelas.name.name}: Tidak memiliki tingkat yang valid.\n"
# #     #             continue
                        
# #     #         tingkat_sekarang = kelas.tingkat
# #     #         jenjang_lower = (kelas.jenjang or '').lower()
# #     #         tingkat_akhir = tingkat_akhir_map.get(jenjang_lower)
            
# #     #         print(f"DEBUG - Memeriksa kelas: {kelas.name.name}, Tingkat: {tingkat_sekarang.name}, Jenjang: {jenjang_lower}, Tingkat Akhir: {tingkat_akhir}")
            
# #     #         # *** PERBAIKAN UTAMA ***
# #     #         # Cek apakah ini sudah tingkat akhir sebelum mencari tingkat berikutnya
# #     #         if tingkat_akhir and int(tingkat_sekarang.name) >= tingkat_akhir:
# #     #             # Ini sudah tingkat akhir, jadi nonaktifkan tanpa mencari tingkat berikutnya
# #     #             kelas_untuk_nonaktif.append({
# #     #                 'kelas': kelas,
# #     #                 'tingkat_sekarang': tingkat_sekarang,
# #     #                 'reason': 'sudah_tingkat_akhir'
# #     #             })
# #     #             continue
            
# #     #         # Jika belum tingkat akhir, cari tingkat berikutnya
# #     #         tingkat_berikutnya = self.env['cdn.tingkat'].search([
# #     #             ('name', '=', int(tingkat_sekarang.name) + 1),
# #     #             ('jenjang', '=', self.jenjang) if self.jenjang else ('id', '!=', False)
# #     #         ], limit=1)

# #     #         if not tingkat_berikutnya:
# #     #             # Tingkat berikutnya tidak ditemukan, tapi belum mencapai tingkat akhir teoritis
# #     #             # Ini bisa terjadi jika data tingkat tidak lengkap
# #     #             kelas_untuk_nonaktif.append({
# #     #                 'kelas': kelas,
# #     #                 'tingkat_sekarang': tingkat_sekarang,
# #     #                 'reason': 'tingkat_berikutnya_tidak_ditemukan'
# #     #             })
# #     #             continue
            
# #     #         # Cari master kelas untuk tingkat berikutnya yang sesuai
# #     #         domain_master_kelas = [
# #     #             ('tingkat', '=', tingkat_berikutnya.id),
# #     #             ('jenjang', '=', kelas.jenjang)
# #     #         ]
            
# #     #         # Tambahkan filter lain jika diperlukan
# #     #         if hasattr(kelas.name, 'jurusan_id') and kelas.name.jurusan_id:
# #     #             domain_master_kelas.append(('jurusan_id', '=', kelas.name.jurusan_id.id))
            
# #     #         if hasattr(kelas.name, 'nama_kelas') and kelas.name.nama_kelas:
# #     #             domain_master_kelas.append(('nama_kelas', '=', kelas.name.nama_kelas))
            
# #     #         master_kelas_baru = self.env['cdn.master_kelas'].search(domain_master_kelas, limit=1)
            
# #     #         if not master_kelas_baru:
# #     #             message += f"- Kelas {kelas.name.name}: Master kelas untuk tingkat {tingkat_berikutnya.name} tidak ditemukan.\n"
# #     #             continue
            
# #     #         # Simpan ke dictionary untuk diproses nanti
# #     #         kelas_untuk_update[kelas.id] = {
# #     #             'kelas': kelas,
# #     #             'tingkat_sekarang': tingkat_sekarang,
# #     #             'tingkat_berikutnya': tingkat_berikutnya,
# #     #             'master_kelas_baru': master_kelas_baru
# #     #         }
        
# #     #     # Proses kelas yang akan dinonaktifkan
# #     #     for item in kelas_untuk_nonaktif:
# #     #         kelas = item['kelas']
# #     #         tingkat_sekarang = item['tingkat_sekarang']
# #     #         reason = item['reason']
            
# #     #         try:
# #     #             kelas.write({'aktif_tidak': 'tidak'})
                
# #     #             if reason == 'sudah_tingkat_akhir':
# #     #                 message += f"- Kelas {kelas.name.name} dinonaktifkan karena sudah mencapai tingkat akhir ({tingkat_sekarang.name}).\n"
# #     #             else:
# #     #                 message += f"- Kelas {kelas.name.name} dinonaktifkan karena tingkat berikutnya ({int(tingkat_sekarang.name) + 1}) tidak ditemukan.\n"
                    
# #     #         except Exception as e:
# #     #             message += f"- ERROR: Gagal menonaktifkan kelas {kelas.name.name}: {str(e)}\n"
# #     #             print(f"ERROR - Gagal menonaktifkan kelas {kelas.name.name}: {str(e)}")
        
# #     #     # Sekarang update kelas yang naik tingkat
# #     #     for kelas_id, info in kelas_untuk_update.items():
# #     #         kelas = info['kelas']
# #     #         tingkat_sekarang = info['tingkat_sekarang']
# #     #         tingkat_berikutnya = info['tingkat_berikutnya']
# #     #         master_kelas_baru = info['master_kelas_baru']
            
# #     #         # Perbarui kelas yang sudah ada
# #     #         try:
# #     #             print(f"DEBUG - Memperbarui kelas: {kelas.name.name}, Dari tingkat {tingkat_sekarang.name} ke {tingkat_berikutnya.name}")
                
# #     #             # Update kelas ke tingkat berikutnya
# #     #             kelas.write({
# #     #                 'name': master_kelas_baru.id,
# #     #                 'tahunajaran_id': tahun_ajaran_berikutnya.id,
# #     #                 # Tingkat akan terupdate otomatis karena related field dari master_kelas
# #     #             })
                
# #     #             # # Hitung siswa yang ada di kelas ini
# #     #             # siswa_dalam_kelas = self.partner_ids.filtered(lambda s: s.ruang_kelas_id.id == kelas.id)
# #     #             # count_siswa += len(siswa_dalam_kelas)
                
                
# #     #             # Ambil siswa yang ada di kelas ini
# #     #             siswa_dalam_kelas = self.partner_ids.filtered(lambda s: s.ruang_kelas_id.id == kelas.id)

# #     #             # Update kelas siswa ke kelas baru berdasarkan field 'kelas_selanjutnya_id' jika tersedia
# #     #             for siswa in siswa_dalam_kelas:
# #     #                 kelas_baru = siswa.kelas_selanjutnya_id or master_kelas_baru
# #     #                 if kelas_baru:
# #     #                     # Cari ruang kelas berdasarkan master kelas dan tahun ajaran berikutnya
# #     #                     ruang_kelas_baru = self.env['cdn.ruang_kelas'].search([
# #     #                         ('name', '=', kelas_baru.id),
# #     #                         ('tahunajaran_id', '=', tahun_ajaran_berikutnya.id)
# #     #                     ], limit=1)

# #     #                     if ruang_kelas_baru:
# #     #                         siswa.write({'ruang_kelas_id': ruang_kelas_baru.id})
# #     #                     else:
# #     #                         message += f"- WARNING: Siswa {siswa.name} tidak dipindahkan karena ruang kelas untuk master kelas {kelas_baru.name} tahun ajaran {tahun_ajaran_berikutnya.name} tidak ditemukan.\n"
# #     #                 else:
# #     #                     message += f"- WARNING: Siswa {siswa.name} tidak memiliki kelas selanjutnya yang valid.\n"

# #     #             count_siswa += len(siswa_dalam_kelas)

                
# #     #             message += f"- Kelas {kelas.name.name}: Berhasil diperbarui dari tingkat {tingkat_sekarang.name} ke tingkat {tingkat_berikutnya.name} untuk tahun ajaran {tahun_ajaran_berikutnya.name} dengan {len(siswa_dalam_kelas)} siswa.\n"
                
# #     #         except Exception as e:
# #     #             message += f"- ERROR: Gagal memperbarui kelas {kelas.name.name}: {str(e)}\n"
# #     #             print(f"ERROR - Gagal memperbarui kelas {kelas.name.name}: {str(e)}")
        
# #     #     # Commit perubahan setelah semua kelas diupdate
# #     #     try:
# #     #         self.env.cr.commit()
# #     #         print("DEBUG - Perubahan berhasil di-commit ke database")
# #     #     except Exception as e:
# #     #         print(f"ERROR - Gagal melakukan commit perubahan: {str(e)}")
        
# #     #     # Log hasil proses (hanya untuk debug, tidak ditampilkan ke user)
# #     #     result_message = f"Proses Kenaikan Kelas berhasil dilakukan!\n\n"
# #     #     result_message += f"Total siswa diproses: {count_siswa}\n\n"
# #     #     result_message += message
        
# #     #     print(f"DEBUG - Proses kenaikan kelas selesai dengan pesan: {result_message}")
        
# #     #     # Tambahkan pesan sukses ke wizard tanpa reset fields
# #     #     # Ini akan menampilkan pesan di form wizard tanpa menutupnya
# #     #     if hasattr(self, 'message_result'):
# #     #         self.message_result = result_message
        
# #     #     # Ganti return statement dengan ini untuk reload form sekaligus notifikasi
# #     #     return {
# #     #         'type': 'ir.actions.act_window',
# #     #         'name': 'Kenaikan Kelas',
# #     #         'res_model': 'cdn.kenaikan_kelas',
# #     #         'view_mode': 'form',
# #     #         'target': 'new',
# #     #         'context': dict(self.env.context, **{
# #     #             'notification': {
# #     #                 'title': 'Kenaikan Kelas',
# #     #                 'message': f'Proses kenaikan kelas berhasil! Total {count_siswa} siswa diproses.',
# #     #                 'type': 'success'
# #     #             }
# #     #         }),
# #     #     }
        
        
