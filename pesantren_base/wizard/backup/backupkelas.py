from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta

class KenaikanKelas(models.Model):
    _name           = 'cdn.kenaikan_kelas'
    _description    = 'Menu POP UP untuk mengatur kenaikan kelas dan kelas yang lulus'
    _rec_name       = 'tahunajaran_id'

    def _default_tahunajaran(self):
       return self.env['res.company'].search([('id','=',1)]).tahun_ajaran_aktif

    jenjang             = fields.Selection(
        selection=[('paud', 'PAUD'), ('tk', 'TK/RA'), ('sd', 'SD/MI'),
                   ('smp', 'SMP/MTS'), ('sma', 'SMA/MA/SMK'), ('nonformal', 'Nonformal')],
        string="Jenjang", 
        store=True, 
        related='kelas_id.jenjang', 
    )
    
    # kenaikan            = fields.Selection(
    #     selection = [
    #         ('naik', 'Naik'),
    #         ('lulus', 'Lulus'),
    #     ], string="Naik/Lulus", required=True, default='naik',
    # )
    
    tahunajaran_id      = fields.Many2one(comodel_name="cdn.ref_tahunajaran", string="Tahun Ajaran", default=_default_tahunajaran, readonly=False, store=True)
    kelas_id            = fields.Many2many('cdn.ruang_kelas', string='Kelas', domain="[('tahunajaran_id','=',tahunajaran_id), ('aktif_tidak','=','aktif'), ('status','=','konfirm')]")
    partner_ids         = fields.Many2many('cdn.siswa', 'kenaikan_santri_rel', 'kenaikan_id', 'santri_id', 'Santri')
    
    tingkat_id          = fields.Many2many('cdn.tingkat', string="Tingkat", store=True, readonly=False)

    @api.onchange('kelas_id')
    def _onchange_kelas_id(self):
        """
        Fungsi untuk menangani perubahan pada field kelas_id.
        1. Menampilkan semua santri yang terkait dengan kelas yang dipilih
        2. Menampilkan tingkat_id sesuai kelas yang dipilih
        """
        # Kosongkan dulu daftar santri
        self.partner_ids = [(5, 0, 0)]
        
        # Jika tidak ada kelas yang dipilih, kembalikan list kosong dan kosongkan tingkat
        if not self.kelas_id:
            self.tingkat_id = [(5, 0, 0)]
            return
        
        # Cara 1: Menggunakan relasi dengan mencari siswa melalui ruang_kelas_id
        domain = [('ruang_kelas_id', 'in', self.kelas_id.ids)]
        
        # Log untuk debugging (hapus saat produksi)
        print(f"DEBUG - Mencari santri dengan domain: {domain}")
        print(f"DEBUG - Kelas yang dipilih: {self.kelas_id.mapped('name')}")
        
        # Cari santri berdasarkan domain
        santri_ids = self.env['cdn.siswa'].search(domain)
        
        # Log hasil pencarian
        print(f"DEBUG - Jumlah santri ditemukan: {len(santri_ids)}")
        print(f"DEBUG - ID Santri: {santri_ids.ids}")
        
        # Jika ditemukan santri, tambahkan ke partner_ids
        if santri_ids:
            self.partner_ids = [(6, 0, santri_ids.ids)]
            
            # Log hasil akhir (hapus saat produksi)
            print(f"DEBUG - Partner IDs setelah update: {self.partner_ids.ids}")
        
        # Jika tidak ditemukan dengan cara 1, coba cara 2 (mungkin relasi many2many langsung)
        elif hasattr(self.env['cdn.ruang_kelas'], 'siswa_ids'):
            all_santri_ids = []
            for kelas in self.kelas_id:
                if kelas.siswa_ids:
                    all_santri_ids.extend(kelas.siswa_ids.ids)
            
            if all_santri_ids:
                santri_ids = self.env['cdn.siswa'].browse(all_santri_ids)
                self.partner_ids = [(6, 0, santri_ids.ids)]
                
                # Log hasil akhir (hapus saat produksi)
                print(f"DEBUG - Partner IDs setelah update cara 2: {self.partner_ids.ids}")
        
        # Update tingkat_id berdasarkan kelas_id yang dipilih
        tingkat_ids = self.env['cdn.tingkat']
        for kelas in self.kelas_id:
            if kelas.tingkat and kelas.tingkat not in tingkat_ids:
                tingkat_ids |= kelas.tingkat
                
        # Set nilai tingkat_id dengan tingkat dari kelas yang dipilih
        if tingkat_ids:
            self.tingkat_id = [(6, 0, tingkat_ids.ids)]
            # Log untuk debugging
            print(f"DEBUG - Tingkat yang diset: {self.tingkat_id.mapped('name')}")


    @api.onchange('tingkat_id', 'tahunajaran_id', 'jenjang')
    def _onchange_tingkat_id(self):
        """
        Fungsi untuk menangani perubahan pada field tingkat_id.
        Jika tingkat_id diisi, akan menampilkan kelas_id yang sesuai dengan tingkat tersebut
        dan tahun ajaran yang dipilih. Jika dikosongkan, maka kelas_id juga dikosongkan.
        """
        # Jika tidak ada tingkat, kosongkan kelas dan partner
        if not self.tingkat_id:
            self.kelas_id = [(5, 0, 0)]
            self.partner_ids = [(5, 0, 0)]
            return

        # Jika tidak ada tahun ajaran, batalkan
        if not self.tahunajaran_id:
            return

        # Buat domain kelas berdasarkan tingkat, tahun ajaran, dan jenjang
        domain = [
            ('tingkat', 'in', self.tingkat_id.ids),
            ('tahunajaran_id', '=', self.tahunajaran_id.id),
            ('aktif_tidak', '=', 'aktif'),
            ('status', '=', 'konfirm')
        ]

        if self.jenjang:
            domain.append(('jenjang', '=', self.jenjang))

        # Cari kelas yang sesuai
        kelas_ids = self.env['cdn.ruang_kelas'].search(domain)

        # Update kelas_id langsung
        self.kelas_id = [(6, 0, kelas_ids.ids)]

        # Panggil kembali onchange kelas untuk update partner_ids & tingkat_id
        self._onchange_kelas_id()
        
        

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
            print(f"DEBUG - Mencoba membuat tahun ajaran baru setelah {current_ta.name}")
            
            # Ekstrak tahun dari nama tahun ajaran saat ini
            current_year = int(current_ta.name.split('/')[0])
            next_year = current_year + 1
            next_ta_name = f"{next_year}/{next_year+1}"
            
            print(f"DEBUG - Tahun yang diekstrak: {current_year}, Tahun berikutnya: {next_year}")
            print(f"DEBUG - Nama tahun ajaran baru: {next_ta_name}")
            
            # Tentukan tanggal mulai dan akhir sesuai sistem pendidikan Indonesia
            # Tahun ajaran di Indonesia umumnya Juli-Juni
            today = fields.Date.from_string(fields.Date.today())
            
            # Untuk pembuatan tahun ajaran baru, selalu gunakan tahun +1 dari current year
            start_date = datetime(next_year, 7, 1).date()
            end_date = datetime(next_year + 1, 6, 30).date()
            
            print(f"DEBUG - Tanggal mulai: {start_date}, Tanggal akhir: {end_date}")
            
            # Cek apakah sudah ada tahun ajaran dengan nama tersebut
            existing_ta_by_name = self.env['cdn.ref_tahunajaran'].search([
                ('name', '=', next_ta_name)
            ], limit=1)
            
            if existing_ta_by_name:
                print(f"DEBUG - Tahun ajaran dengan nama {next_ta_name} sudah ada")
                return existing_ta_by_name
                
            # Cek apakah sudah ada tahun ajaran dengan rentang waktu tersebut
            existing_ta = self.env['cdn.ref_tahunajaran'].search([
                ('start_date', '=', start_date),
                ('end_date', '=', end_date)
            ], limit=1)
            
            if existing_ta:
                print(f"DEBUG - Tahun ajaran dengan rentang {start_date} - {end_date} sudah ada")
                return existing_ta
            
            print(f"DEBUG - Membuat tahun ajaran baru: {next_ta_name}")
            
            # Buat tahun ajaran baru dengan sudo untuk memastikan hak akses
            new_ta = self.env['cdn.ref_tahunajaran'].sudo().create({
                'name': next_ta_name,
                'start_date': start_date,
                'end_date': end_date,
                'term_structure': current_ta.term_structure,
                'company_id': current_ta.company_id.id,
                'keterangan': f"Dibuat otomatis dari proses kenaikan kelas pada {fields.Date.today()}"
            })
            
            # Verifikasi record telah dibuat
            if not new_ta:
                raise UserError(f"Gagal membuat tahun ajaran baru {next_ta_name}")
            
            # Commit transaksi untuk memastikan data tersimpan
            self.env.cr.commit()
            
            # Buat termin akademik dan periode tagihan
            new_ta.term_create()
            
            # Log untuk debug
            print(f"DEBUG - Tahun ajaran baru berhasil dibuat: {new_ta.name} ({new_ta.start_date} - {new_ta.end_date})")
            
            return new_ta
        except Exception as e:
            print(f"ERROR - Gagal membuat tahun ajaran baru: {str(e)}")
            # Re-raise supaya bisa dilihat di UI
            raise UserError(f"Gagal membuat tahun ajaran baru: {str(e)}")


    def action_proses_kenaikan_kelas(self):
        """
        Aksi untuk memproses kenaikan kelas dengan hanya memperbarui kelas yang sudah ada
        """
        # Logging awal
        print(f"DEBUG - Memulai proses kenaikan kelas untuk tahun ajaran: {self.tahunajaran_id.name}")
        
        if not self.partner_ids:
            raise UserError("Belum ada santri yang dipilih!")
        
        # Mencatat aktifitas untuk sistem log    
        self.ensure_one()
        message = ""
        count_siswa = 0
        
        # Mendapatkan tahun ajaran berikutnya dengan cara yang lebih tepat
        try:
            current_year = int(self.tahunajaran_id.name.split('/')[0])
            next_year = current_year + 1
            next_ta_name = f"{next_year}/{next_year+1}"
            
            print(f"DEBUG - Current year: {current_year}, Next year: {next_year}")
            print(f"DEBUG - Mencari tahun ajaran dengan nama: {next_ta_name}")
            
            # Cari tahun ajaran berikutnya dengan nama yang tepat
            tahun_ajaran_berikutnya = self.env['cdn.ref_tahunajaran'].search([
                ('name', '=', next_ta_name)
            ], limit=1)
            
            print(f"DEBUG - Hasil pencarian tahun ajaran berikutnya: {tahun_ajaran_berikutnya.name if tahun_ajaran_berikutnya else 'Tidak ditemukan'}")
            
        except (ValueError, IndexError) as e:
            print(f"ERROR - Format tahun ajaran tidak valid: {str(e)}")
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
        
        # Definisikan tingkat akhir untuk setiap jenjang
        tingkat_akhir_map = {
            'sd': 6,
            'mi': 6,
            'smp': 9,
            'mts': 9,
            'sma': 12,
            'ma': 12,
            'smk': 12,
            'tk': 2,  # TK B
            'paud': 1  # PAUD biasanya hanya 1 tingkat
        }
        
        # Kumpulkan semua kelas yang akan diperbarui
        kelas_untuk_update = {}
        kelas_untuk_nonaktif = []
        
        for kelas in self.kelas_id:
            if not kelas.tingkat:
                message += f"- Kelas {kelas.name.name}: Tidak memiliki tingkat yang valid.\n"
                continue
                        
            tingkat_sekarang = kelas.tingkat
            jenjang_lower = (kelas.jenjang or '').lower()
            tingkat_akhir = tingkat_akhir_map.get(jenjang_lower)
            
            print(f"DEBUG - Memeriksa kelas: {kelas.name.name}, Tingkat: {tingkat_sekarang.name}, Jenjang: {jenjang_lower}, Tingkat Akhir: {tingkat_akhir}")
            
            # *** PERBAIKAN UTAMA ***
            # Cek apakah ini sudah tingkat akhir sebelum mencari tingkat berikutnya
            if tingkat_akhir and int(tingkat_sekarang.name) >= tingkat_akhir:
                # Ini sudah tingkat akhir, jadi nonaktifkan tanpa mencari tingkat berikutnya
                kelas_untuk_nonaktif.append({
                    'kelas': kelas,
                    'tingkat_sekarang': tingkat_sekarang,
                    'reason': 'sudah_tingkat_akhir'
                })
                continue
            
            # Jika belum tingkat akhir, cari tingkat berikutnya
            tingkat_berikutnya = self.env['cdn.tingkat'].search([
                ('name', '=', int(tingkat_sekarang.name) + 1),
                ('jenjang', '=', self.jenjang) if self.jenjang else ('id', '!=', False)
            ], limit=1)

            if not tingkat_berikutnya:
                # Tingkat berikutnya tidak ditemukan, tapi belum mencapai tingkat akhir teoritis
                # Ini bisa terjadi jika data tingkat tidak lengkap
                kelas_untuk_nonaktif.append({
                    'kelas': kelas,
                    'tingkat_sekarang': tingkat_sekarang,
                    'reason': 'tingkat_berikutnya_tidak_ditemukan'
                })
                continue
            
            # Cari master kelas untuk tingkat berikutnya yang sesuai
            domain_master_kelas = [
                ('tingkat', '=', tingkat_berikutnya.id),
                ('jenjang', '=', kelas.jenjang)
            ]
            
            # Tambahkan filter lain jika diperlukan
            if hasattr(kelas.name, 'jurusan_id') and kelas.name.jurusan_id:
                domain_master_kelas.append(('jurusan_id', '=', kelas.name.jurusan_id.id))
            
            if hasattr(kelas.name, 'nama_kelas') and kelas.name.nama_kelas:
                domain_master_kelas.append(('nama_kelas', '=', kelas.name.nama_kelas))
            
            master_kelas_baru = self.env['cdn.master_kelas'].search(domain_master_kelas, limit=1)
            
            if not master_kelas_baru:
                message += f"- Kelas {kelas.name.name}: Master kelas untuk tingkat {tingkat_berikutnya.name} tidak ditemukan.\n"
                continue
            
            # Simpan ke dictionary untuk diproses nanti
            kelas_untuk_update[kelas.id] = {
                'kelas': kelas,
                'tingkat_sekarang': tingkat_sekarang,
                'tingkat_berikutnya': tingkat_berikutnya,
                'master_kelas_baru': master_kelas_baru
            }
        
        # Proses kelas yang akan dinonaktifkan
        for item in kelas_untuk_nonaktif:
            kelas = item['kelas']
            tingkat_sekarang = item['tingkat_sekarang']
            reason = item['reason']
            
            try:
                kelas.write({'aktif_tidak': 'tidak'})
                
                if reason == 'sudah_tingkat_akhir':
                    message += f"- Kelas {kelas.name.name} dinonaktifkan karena sudah mencapai tingkat akhir ({tingkat_sekarang.name}).\n"
                else:
                    message += f"- Kelas {kelas.name.name} dinonaktifkan karena tingkat berikutnya ({int(tingkat_sekarang.name) + 1}) tidak ditemukan.\n"
                    
            except Exception as e:
                message += f"- ERROR: Gagal menonaktifkan kelas {kelas.name.name}: {str(e)}\n"
                print(f"ERROR - Gagal menonaktifkan kelas {kelas.name.name}: {str(e)}")
        
        # Sekarang update kelas yang naik tingkat
        for kelas_id, info in kelas_untuk_update.items():
            kelas = info['kelas']
            tingkat_sekarang = info['tingkat_sekarang']
            tingkat_berikutnya = info['tingkat_berikutnya']
            master_kelas_baru = info['master_kelas_baru']
            
            # Perbarui kelas yang sudah ada
            try:
                print(f"DEBUG - Memperbarui kelas: {kelas.name.name}, Dari tingkat {tingkat_sekarang.name} ke {tingkat_berikutnya.name}")
                
                # Update kelas ke tingkat berikutnya
                kelas.write({
                    'name': master_kelas_baru.id,
                    'tahunajaran_id': tahun_ajaran_berikutnya.id,
                    # Tingkat akan terupdate otomatis karena related field dari master_kelas
                })
                
                # Hitung siswa yang ada di kelas ini
                siswa_dalam_kelas = self.partner_ids.filtered(lambda s: s.ruang_kelas_id.id == kelas.id)
                count_siswa += len(siswa_dalam_kelas)
                
                message += f"- Kelas {kelas.name.name}: Berhasil diperbarui dari tingkat {tingkat_sekarang.name} ke tingkat {tingkat_berikutnya.name} untuk tahun ajaran {tahun_ajaran_berikutnya.name} dengan {len(siswa_dalam_kelas)} siswa.\n"
                
            except Exception as e:
                message += f"- ERROR: Gagal memperbarui kelas {kelas.name.name}: {str(e)}\n"
                print(f"ERROR - Gagal memperbarui kelas {kelas.name.name}: {str(e)}")
        
        # Commit perubahan setelah semua kelas diupdate
        try:
            self.env.cr.commit()
            print("DEBUG - Perubahan berhasil di-commit ke database")
        except Exception as e:
            print(f"ERROR - Gagal melakukan commit perubahan: {str(e)}")
        
        # Tampilkan pesan hasil proses
        result_message = f"Proses Kenaikan Kelas berhasil dilakukan!\n\n"
        result_message += f"Total siswa diproses: {count_siswa}\n\n"
        result_message += message
        
        # Tampilkan pesan dalam dialog
        message_id = self.env['message.wizard'].create({
            'message': result_message
        })
        
        print(f"DEBUG - Proses kenaikan kelas selesai dengan pesan: {result_message}")
        
        return {
            'name': ('Hasil Proses Kenaikan Kelas'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'message.wizard',
            'res_id': message_id.id,
            'target': 'new'
        }