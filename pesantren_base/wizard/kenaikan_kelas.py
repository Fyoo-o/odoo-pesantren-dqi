# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import logging
import re

_logger = logging.getLogger(__name__)


class KenaikanKelasLine(models.Model):
    _name = 'cdn.kenaikan_kelas.line'
    _description = 'Detail santri dalam proses kenaikan kelas'
    _order = 'id desc'

    kenaikan_id = fields.Many2one('cdn.kenaikan_kelas', string='Header')
    siswa_id = fields.Many2one('cdn.siswa', string='Santri')
    nis = fields.Char(related='siswa_id.nis', string='NIS', store=False)
    kelas_sekarang_id = fields.Many2one(
        related='siswa_id.ruang_kelas_id', string='Kelas Sekarang', store=False)
    next_class_id = fields.Many2one(
        'cdn.master_kelas', string='Kelas Selanjutnya')


class MockKelas:
    def __init__(self, tingkat, jenjang):
        self.tingkat = tingkat
        self.jenjang = jenjang


class KenaikanKelas(models.Model):
    _name = 'cdn.kenaikan_kelas'
    _description = 'Menu POP UP untuk mengatur kenaikan kelas dan kelas yang lulus'
    _order = 'id desc'
    _rec_name = 'tahunajaran_id'

    jenjang = fields.Selection(
        string="Jenjang",
        store=True,
        related='kelas_id.jenjang',
    )

    tahunajaran_id = fields.Many2one(
        comodel_name="cdn.ref_tahunajaran", string="Tahun Ajaran", readonly=False, store=True)
    kelas_id = fields.Many2one('cdn.ruang_kelas', string='Kelas',
                               domain="[('tahunajaran_id','=',tahunajaran_id), ('aktif_tidak','=','aktif'), ('status','=','konfirm')]")
    partner_ids = fields.Many2many(
        'cdn.siswa', 'kenaikan_santri_rel', 'kenaikan_id', 'santri_id', 'Daftar Santri')

    tingkat_id = fields.Many2one(
        'cdn.tingkat', string="Tingkat", store=True, readonly=False)

    next_tingkat_id = fields.Many2one(
        'cdn.tingkat',
        string="Tingkat Selanjutnya",
        compute='_compute_next_tingkat_id',
        store=True,
    )

    walikelas_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Wali Kelas",
        domain="[('jns_pegawai_ids.code', 'in', ['guru'])]"
    )

    status = fields.Selection(
        selection=[('naik', 'Naik Kelas'), ('tidak_naik', 'Tidak Naik'),
                   ('lulus', 'Lulus'), ('tidak_lulus', 'Tidak Lulus'), ],
        string="Status",
    )

    # Field baru untuk menampilkan kelas selanjutnya
    next_class = fields.Many2one(
        comodel_name='cdn.master_kelas',
        string='Kelas Selanjutnya',
        compute='_compute_next_class',
        store=True,
        readonly=False,
        domain="[('tingkat', '=', next_tingkat_id)]",
        help="Kelas selanjutnya berdasarkan tingkat, nama kelas, dan jurusan"
    )

    # Field untuk menampilkan hasil proses
    message_result = fields.Text(string="Hasil Proses", readonly=True)

    angkatan_id = fields.Many2one(
        related="kelas_id.angkatan_id", string="Angkatan", readonly=True)

    partner_lines = fields.One2many(
        'cdn.kenaikan_kelas.line', 'kenaikan_id', string='Santri')

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
        string="Nama Tahun Ajaran Baru",
        compute='_compute_next_tahunajaran',
        store=True,
        readonly=True,
        help="Nama tahun ajaran berikutnya"
    )

    @api.onchange('next_class', 'next_tahunajaran_id')
    def _onchange_next_class_validation(self):
        """Memunculkan peringatan jika kelas target sudah terisi pada tahun ajaran berikutnya"""
        if self.next_class and self.next_tahunajaran_id:
            existing_kelas = self.env['cdn.ruang_kelas'].search([
                ('name', '=', self.next_class.id),
                ('tahunajaran_id', '=', self.next_tahunajaran_id.id),
                ('jml_siswa', '>', 0)
            ], limit=1)
            
            if existing_kelas:
                return {
                    'warning': {
                        'title': 'Peringatan',
                        'message': f'Kelas tersebut telah terisi ({existing_kelas.jml_siswa} siswa) pada tahun ajaran {self.next_tahunajaran_name}!'
                    }
                }

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
            santri = self.env['cdn.siswa'].search(
                [('ruang_kelas_id', '=', self.kelas_id.id)])

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
                _logger.warning(
                    f"Format tahun ajaran tidak valid untuk record {record.id}: {e}")
                record.next_tahunajaran_id = False
                record.next_tahunajaran_name = "Format tahun ajaran tidak valid"
            except Exception as e:
                _logger.error(
                    f"Error computing next tahun ajaran for record {record.id}: {e}")
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
            _logger.info(
                f"Mencoba membuat tahun ajaran baru setelah {current_ta.name}")

            # Ekstrak tahun dari nama tahun ajaran saat ini
            current_year = int(current_ta.name.split('/')[0])
            next_year = current_year + 1
            next_ta_name = f"{next_year}/{next_year+1}"

            _logger.info(
                f"Tahun yang diekstrak: {current_year}, Tahun berikutnya: {next_year}")
            _logger.info(f"Nama tahun ajaran baru: {next_ta_name}")

            # Tentukan tanggal mulai dan akhir sesuai sistem pendidikan Indonesia
            start_date = datetime(next_year, 7, 1).date()
            end_date = datetime(next_year + 1, 6, 30).date()

            _logger.info(
                f"Tanggal mulai: {start_date}, Tanggal akhir: {end_date}")

            # Cek apakah sudah ada tahun ajaran dengan nama tersebut
            existing_ta_by_name = self.env['cdn.ref_tahunajaran'].search([
                ('name', '=', next_ta_name)
            ], limit=1)

            if existing_ta_by_name:
                _logger.info(
                    f"Tahun ajaran dengan nama {next_ta_name} sudah ada")
                return existing_ta_by_name

            # Cek apakah sudah ada tahun ajaran dengan rentang waktu tersebut
            existing_ta = self.env['cdn.ref_tahunajaran'].search([
                ('start_date', '=', start_date),
                ('end_date', '=', end_date)
            ], limit=1)

            if existing_ta:
                _logger.info(
                    f"Tahun ajaran dengan rentang {start_date} - {end_date} sudah ada")
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
                raise UserError(
                    f"Gagal membuat tahun ajaran baru {next_ta_name}")

            # Commit transaksi untuk memastikan data tersimpan
            self.env.cr.commit()

            # Buat termin akademik dan periode tagihan jika method tersedia
            if hasattr(new_ta, 'term_create'):
                try:
                    new_ta.term_create()
                except Exception as e:
                    _logger.warning(
                        f"Gagal membuat termin untuk tahun ajaran {next_ta_name}: {str(e)}")

            _logger.info(
                f"Tahun ajaran baru berhasil dibuat: {new_ta.name} ({new_ta.start_date} - {new_ta.end_date})")

            return new_ta
        except Exception as e:
            _logger.error(f"Gagal membuat tahun ajaran baru: {str(e)}")
            raise UserError(f"Gagal membuat tahun ajaran baru: {str(e)}")

    def _get_next_tingkat_for_progression(self, current_class, current_tingkat):
        """Return the next tingkat using the configured promotion sequence."""
        if not current_class or not current_tingkat:
            return False

        return self._get_next_tingkat(current_tingkat)

    def _get_tingkat_level_number(self, tingkat):
        """Return a numeric level for comparison, regardless of raw field type."""
        if not tingkat:
            return None

        level_name = getattr(tingkat, 'name', tingkat)
        try:
            return int(level_name)
        except (TypeError, ValueError):
            return self._extract_tingkat_number(level_name)

    def _extract_section_from_name(self, class_name):
        """Extract the section letter from names like 'Kelas III A' or 'VII B'."""
        if not class_name:
            return False

        text = str(class_name).strip()
        if not text:
            return False

        last_token = re.split(r'[\s\-_/]+', text)[-1].strip()
        if not last_token:
            return False

        compact_match = re.match(r'^([IVXLCDM]+)([A-Z]\d*)$', last_token, re.I)
        if compact_match:
            return compact_match.group(2)[0].upper()

        alpha_num_match = re.match(r'^([A-Z])(\d+)$', last_token, re.I)
        if alpha_num_match:
            return alpha_num_match.group(1).upper()

        alpha_alpha_match = re.match(r'^([A-Z])([A-Z]\d*)$', last_token, re.I)
        if alpha_alpha_match:
            return alpha_alpha_match.group(1).upper()

        if re.fullmatch(r'[IVXLCDM]+', last_token, re.I):
            return False

        match = re.search(r'([A-Z])\d*$', last_token, re.I)
        if match:
            return match.group(1).upper()

        return False

    def _normalize_class_text(self, text):
        """Normalize a class name for tolerant comparisons."""
        if not text:
            return ''

        return re.sub(r'[\s\-_/]+', '', str(text)).upper()

    def _extract_label_tail(self, text):
        """Return the last visible label token for ranking fallbacks."""
        if not text:
            return False

        normalized = str(text).strip()
        if not normalized:
            return False

        last_token = re.split(r'[\s\-_/]+', normalized)[-1].strip()
        if not last_token:
            return False

        return last_token.upper()

    def _section_distance(self, source_section, target_section):
        """Score section distance; lower is better."""
        if not source_section or not target_section:
            return None

        source = source_section[0].upper()
        target = target_section[0].upper()
        if not source.isalpha() or not target.isalpha():
            return None

        return abs(ord(source) - ord(target))

    def _section_rank(self, section):
        """Convert a section token like A/B/C into a numeric rank."""
        if not section:
            return None

        token = str(section).strip().upper()
        if not token:
            return None

        char = token[0]
        if not char.isalpha():
            return None

        return ord(char) - ord('A') + 1

    def _class_label_rank(self, label_text):
        """Return a sortable rank for a class label."""
        if not label_text:
            return (999, 999)

        text = str(label_text).upper()
        section = self._extract_section_from_name(text)
        section_rank = self._section_rank(section)
        if section_rank is None:
            section_rank = 999

        number_match = re.search(r'(\d+)\s*$', text)
        number_rank = int(number_match.group(1)) if number_match else 999
        return (section_rank, number_rank)

    def _pick_best_fallback_master_class(self, target_classes, current_class, preferred_suffix=False):
        """Pick the closest target class when no exact label match exists."""
        if not target_classes:
            return False

        current_label = getattr(current_class, 'nama_kelas', False) or getattr(
            getattr(current_class, 'name', False), 'nama_kelas', False) or ''
        current_section = self._extract_section_from_name(current_label)
        current_tail = self._extract_label_tail(current_label)

        best_match = False
        best_score = None

        for target_class in target_classes:
            target_label = getattr(target_class, 'nama_kelas', False) or getattr(
                target_class, 'name', False) or ''
            target_section = self._extract_section_from_name(target_label)
            target_tail = self._extract_label_tail(target_label)
            target_rank = self._section_rank(target_section)

            score = (1000, 0)

            if preferred_suffix and target_tail and preferred_suffix.upper() == target_tail.upper():
                score = (0, 0)
            elif current_section and target_section:
                current_rank = self._section_rank(current_section)
                if current_rank is not None and target_rank is not None:
                    score = (abs(current_rank - target_rank), -target_rank)
                    # If there is no exact match, prefer the closest section,
                    # and when tied, prefer the later section so C/D do not
                    # collapse back to A when B is available.
                else:
                    distance = self._section_distance(current_section, target_section)
                    if distance is not None:
                        score = (distance, 0)
            elif current_tail and target_tail and current_tail.upper() == target_tail.upper():
                score = (1, 0)

            # Prefer classes with the same section first, then smaller urutan.
            if best_score is None or score < best_score:
                best_score = score
                best_match = target_class

        return best_match

    def _score_target_class(self, current_section, target_class, preferred_section=False):
        """Score a target class using section proximity and section order."""
        target_label = getattr(target_class, 'nama_kelas', False) or getattr(
            target_class, 'name', False) or ''
        target_section = self._extract_section_from_name(target_label)
        target_rank = self._section_rank(target_section)
        target_label_rank = self._class_label_rank(target_label)

        if preferred_section and target_section and preferred_section.upper() == target_section.upper():
            return (0, 0, target_label_rank[0], target_label_rank[1])

        if current_section and target_section:
            current_rank = self._section_rank(current_section)
            if current_rank is not None and target_rank is not None:
                if target_rank <= current_rank:
                    return (1, current_rank - target_rank, -target_rank, target_label_rank[1])
                return (2, target_rank - current_rank, target_rank, target_label_rank[1])

        return (9, target_label_rank[0], target_label_rank[1], 0)

    def _split_label_components(self, label_name):
        """Return prefix, level, and suffix from a compact class label."""
        if not label_name:
            return False, False, False

        text = str(label_name).strip()
        if not text:
            return False, False, False

        prefix = ''
        if text.lower().startswith('kelas '):
            prefix = 'Kelas '
            text = text[6:].strip()

        # Common forms:
        # - I A
        # - IA
        # - A1
        # - B2
        # - VIII D
        # - VIII-D
        match = re.match(r'^([IVXLCDM]+)[\s\-_/]+(.+)$', text, re.I)
        if match:
            return prefix, match.group(1).upper(), match.group(2).strip()

        match = re.match(r'^([IVXLCDM]+)([A-Z]\d*)$', text, re.I)
        if match:
            return prefix, match.group(1).upper(), match.group(2).strip()

        match = re.match(r'^([A-Z])(\d+)$', text, re.I)
        if match:
            return prefix, match.group(1).upper(), match.group(2).strip()

        match = re.match(r'^([A-Z])([A-Z]\d*)$', text, re.I)
        if match:
            return prefix, match.group(1).upper(), match.group(2).strip()

        parts = text.split(None, 1)
        if len(parts) == 2:
            return prefix, parts[0].upper(), parts[1].strip()

        return prefix, text.upper(), ''

    def _split_master_class_name(self, class_name):
        """Split master class name into base and label parts."""
        if not class_name:
            return False, False

        text = str(class_name).strip()
        if not text:
            return False, False

        if ' - ' in text:
            base_name, label_name = text.split(' - ', 1)
            return base_name.strip(), label_name.strip()

        return False, text

    def _shift_class_label_level(self, label_name, next_level_text):
        """Replace the leading level token in a class label while keeping the suffix."""
        if not label_name or not next_level_text:
            return False

        prefix, _current_level, suffix = self._split_label_components(label_name)
        if not prefix and not _current_level and not suffix:
            return False

        if suffix:
            return f"{prefix}{next_level_text} {suffix}".strip()

        return f"{prefix}{next_level_text}".strip()

    def _build_progression_name_candidates(self, class_name, current_jenjang, current_tingkat, next_tingkat):
        """Build class name candidates for the next progression step.

        This keeps the existing class suffix when possible and adds the most
        likely next-level representations used by the master class naming
        scheme.
        """
        if not class_name or not current_tingkat or not next_tingkat:
            return []

        candidates = []
        text = str(class_name).strip()
        if text:
            candidates.append(text)

        current_base_name, current_label_name = self._split_master_class_name(text)
        section = self._extract_section_from_name(text)
        if not section:
            return candidates

        next_level = getattr(next_tingkat, 'name', False)
        if current_jenjang in ['sd', 'smp', 'sma'] and next_level:
            try:
                next_roman = self._number_to_roman(int(next_level))
            except (TypeError, ValueError):
                next_roman = str(next_level).strip().upper()

            if next_roman:
                shifted_label = self._shift_class_label_level(
                    current_label_name or text, next_roman)
                if shifted_label:
                    candidates.append(shifted_label)
                    candidates.append(f"{next_roman} - {shifted_label}")

                candidates.append(f"{next_roman} {section}")
                candidates.append(f"Kelas {next_roman} {section}")
                candidates.append(f"{next_roman} - {next_roman} {section}")

        if current_jenjang == 'tk':
            candidates.append(f"TK {section}")
            candidates.append(f"TK/{section}")

        if current_jenjang == 'paud':
            candidates.append(f"Kelas I {section}")
            candidates.append("Kelas IA")

        return candidates

    def _build_candidate_class_names(self, class_name, current_jenjang, current_tingkat, next_jenjang, next_tingkat):
        """Build a simple next-class name using jenjang/tingkat first, then the section from the current name."""
        if not class_name or not current_tingkat or not next_tingkat:
            return []

        candidates = []
        text = str(class_name).strip()
        if text:
            candidates.append(text)

        current_base_name, current_label_name = self._split_master_class_name(text)
        section = self._extract_section_from_name(text)
        if not section:
            return candidates

        target_jenjang = next_jenjang or current_jenjang
        next_level = getattr(next_tingkat, 'name', False)

        if target_jenjang in ['sd', 'smp', 'sma']:
            if next_level:
                try:
                    next_roman = self._number_to_roman(int(next_level))
                except (TypeError, ValueError):
                    next_roman = str(next_level).strip().upper()

                shifted_label = self._shift_class_label_level(
                    current_label_name or text, next_roman)
                if shifted_label:
                    candidates.append(shifted_label)
                    candidates.append(f"{next_roman} - {shifted_label}")

                candidates.append(f"{next_roman} {section}")
                candidates.append(f"Kelas {next_roman} {section}")
                candidates.append(f"{next_roman} - {next_roman} {section}")
                candidates.append(f"{next_roman} - Kelas {next_roman} {section}")

        if target_jenjang == 'tk':
            candidates.append(f"TK {section}")
            candidates.append(f"TK/{section}")

        if target_jenjang == 'paud':
            candidates.append(f"Kelas I {section}")
            candidates.append(f"Kelas IA")

        return candidates

    def _build_transition_specific_candidates(self, current_class, current_jenjang, current_tingkat, next_tingkat, target_jenjang):
        """Build exact candidate names from the known data transitions."""
        if not current_class or not current_tingkat or not next_tingkat:
            return []

        current_level = self._get_tingkat_level_number(current_tingkat)
        next_level = self._get_tingkat_level_number(next_tingkat)
        current_label = ' '.join([
            str(getattr(current_class, 'nama_kelas', '') or ''),
            str(getattr(getattr(current_class, 'name', False), 'nama_kelas', '') or ''),
            str(getattr(getattr(current_class, 'name', False), 'name', '') or ''),
        ]).strip()
        current_label_upper = current_label.upper()
        current_tail = self._extract_label_tail(current_label)
        current_section = self._extract_section_from_name(current_label)

        candidates = []

        # PAUD/TK move from the A-bucket to the B-bucket on the next level.
        if current_jenjang in ['paud', 'tk'] and current_level in [1, 2] and next_level in [2, 1]:
            suffix_number = None
            tail_match = re.search(r'(\d+)$', current_tail or '')
            if tail_match:
                suffix_number = tail_match.group(1)
            else:
                label_match = re.search(r'(\d+)$', current_label_upper)
                if label_match:
                    suffix_number = label_match.group(1)

            if suffix_number:
                prefix = 'PAUD' if current_jenjang == 'paud' else 'TK'
                room_prefix = 'KB' if current_jenjang == 'paud' else 'TK'
                candidates.extend([
                    f"{prefix} B - {room_prefix} B{suffix_number}",
                    f"{room_prefix} B{suffix_number}",
                    f"{prefix} B - {room_prefix} B",
                ])

        # TK level 2 to SD level 1 should enter grade I A.
        if current_jenjang == 'tk' and current_level == 2 and next_level == 1 and target_jenjang == 'sd':
            candidates.extend([
                'I - Kelas I A',
                'Kelas I A',
            ])

        # SMP level 8 to 9: A/B stay in A, C/D move to B.
        if current_jenjang == 'smp' and current_level == 8 and next_level == 9:
            if current_section in ['A', 'B']:
                target_section = 'A'
            elif current_section in ['C', 'D']:
                target_section = 'B'
            else:
                target_section = 'A'

            candidates.extend([
                f"IX - IX {target_section}",
                f"IX {target_section}",
            ])

        # SD levels preserve the section letter and only advance the roman numeral.
        if current_jenjang == 'sd' and target_jenjang == 'sd' and next_level:
            try:
                next_roman = self._number_to_roman(int(next_level))
            except (TypeError, ValueError):
                next_roman = str(next_level).strip().upper()

            if current_section and next_roman:
                candidates.extend([
                    f"{next_roman} - Kelas {next_roman} {current_section}",
                    f"{next_roman} - {next_roman} {current_section}",
                    f"Kelas {next_roman} {current_section}",
                ])

        return candidates

    def _find_next_master_class(self, current_class, next_tingkat, current_jurusan=False):
        """Cari master kelas selanjutnya dengan prioritas nama yang mempertahankan suffix kelas."""
        if not current_class or not next_tingkat:
            return False

        current_tingkat = current_class.tingkat
        current_master_class = getattr(current_class, 'name', False)
        current_jenjang = getattr(current_class, 'jenjang', False) or getattr(
            current_master_class, 'jenjang', False)
        target_tingkat = next_tingkat
        target_jenjang = getattr(next_tingkat, 'jenjang', False) or current_jenjang
        current_level = self._get_tingkat_level_number(current_tingkat)
        next_level = self._get_tingkat_level_number(next_tingkat)
        current_label_text = ' '.join([
            str(getattr(current_class, 'nama_kelas', '') or ''),
            str(getattr(current_master_class, 'nama_kelas', '') or ''),
            str(getattr(current_master_class, 'name', '') or ''),
        ]).strip()
        current_section = self._extract_section_from_name(current_label_text)

        transition_target_section = False
        if current_jenjang == 'smp' and current_level == 8 and next_level == 9:
            if current_section in ['A', 'B']:
                transition_target_section = 'A'
            else:
                transition_target_section = 'B'

        if current_jenjang in ['paud', 'tk'] and current_level in [1, 2] and next_level in [2, 1]:
            if re.search(r'\b(A1|B1)\b', current_label_text, re.I):
                transition_target_section = 'A'
            elif re.search(r'\b(B2|B3)\b', current_label_text, re.I):
                transition_target_section = 'B'

        if transition_target_section:
            direct_domain = [('tingkat', '=', target_tingkat.id)]
            if target_jenjang:
                direct_domain.append(('jenjang', '=', target_jenjang))
            if current_jurusan:
                direct_domain.append(('jurusan_id', '=', current_jurusan.id))

            direct_name_candidates = []
            if current_jenjang == 'smp' and current_level == 8 and next_level == 9:
                direct_name_candidates = [
                    f"IX - IX {transition_target_section}",
                    f"IX {transition_target_section}",
                ]
            elif current_jenjang in ['paud', 'tk'] and current_level in [1, 2] and next_level in [2, 1]:
                if target_jenjang == 'sd' and current_jenjang == 'tk' and transition_target_section == 'A':
                    direct_name_candidates = [
                        'I - Kelas I A',
                        'Kelas I A',
                    ]
                elif transition_target_section == 'A':
                    direct_name_candidates = [
                        'PAUD B - KB B1' if current_jenjang == 'paud' else 'TK B - TK B1',
                        'KB B1',
                    ]
                else:
                    direct_name_candidates = [
                        'PAUD B - KB B2' if current_jenjang == 'paud' else 'TK B - TK B2',
                        'PAUD B - KB B3' if current_jenjang == 'paud' else 'TK B - TK B3',
                        'KB B2',
                        'KB B3',
                    ]

            for direct_name in direct_name_candidates:
                direct_match = self.env['cdn.master_kelas'].search(direct_domain + [('name', '=', direct_name)], limit=1)
                if direct_match:
                    return direct_match
                direct_match = self.env['cdn.master_kelas'].search(direct_domain + [('nama_kelas', '=', direct_name)], limit=1)
                if direct_match:
                    return direct_match

        preferred_names = []
        if current_master_class:
            if getattr(current_master_class, 'name', False):
                preferred_names.append(current_master_class.name)
            if getattr(current_master_class, 'nama_kelas', False):
                preferred_names.append(current_master_class.nama_kelas)

        if getattr(current_class, 'nama_kelas', False):
            preferred_names.append(current_class.nama_kelas)

        if getattr(current_class, 'name', False):
            master_name = getattr(current_class.name, 'name', False)
            if master_name:
                preferred_names.append(master_name)

        candidate_names = []
        candidate_names.extend(
            self._build_transition_specific_candidates(
                current_class, current_jenjang, current_tingkat, target_tingkat, target_jenjang
            )
        )

        for preferred_name in preferred_names:
            candidate_names.extend(self._build_progression_name_candidates(
                preferred_name, current_jenjang, current_tingkat, target_tingkat))
            candidate_names.extend(self._build_candidate_class_names(
                preferred_name, current_jenjang, current_tingkat, target_jenjang, target_tingkat))

        candidate_names = list(dict.fromkeys(candidate_names))
        candidate_norms = {self._normalize_class_text(name) for name in candidate_names if name}

        for name_value in candidate_names:
            domain = [('tingkat', '=', target_tingkat.id)]
            if target_jenjang:
                domain.append(('jenjang', '=', target_jenjang))
            if current_jurusan:
                domain.append(('jurusan_id', '=', current_jurusan.id))
            domain.append(('name', '=', name_value))

            match = self.env['cdn.master_kelas'].search(domain, limit=1)
            if match:
                return match

        target_domain = [
            ('tingkat', '=', target_tingkat.id),
        ]
        if target_jenjang:
            target_domain.append(('jenjang', '=', target_jenjang))
        if current_jurusan:
            target_domain.append(('jurusan_id', '=', current_jurusan.id))

        target_classes = self.env['cdn.master_kelas'].search(target_domain, order='tingkat_urutan, nama_kelas, id')

        for target_class in target_classes:
            record_norms = {
                self._normalize_class_text(getattr(target_class, 'name', False)),
                self._normalize_class_text(getattr(target_class, 'nama_kelas', False)),
            }
            if candidate_norms.intersection(record_norms):
                return target_class

        if target_classes:
            scored_targets = sorted(
                target_classes,
                key=lambda target_class: self._score_target_class(
                    self._extract_section_from_name(
                        getattr(current_class, 'nama_kelas', False) or getattr(current_master_class, 'nama_kelas', False) or ''),
                    target_class,
                    preferred_section=False,
                ),
            )
            return scored_targets[0]

        return False

    @api.depends('kelas_id', 'status')
    def _compute_next_tingkat_id(self):
        for record in self:
            if not record.kelas_id:
                record.next_tingkat_id = False
                continue

            current_tingkat = record.kelas_id.tingkat
            if not current_tingkat:
                record.next_tingkat_id = False
                continue

            if record.status in ['tidak_naik', 'tidak_lulus']:
                record.next_tingkat_id = current_tingkat.id
            else:
                next_tingkat = record._get_next_tingkat_for_progression(
                    record.kelas_id, current_tingkat)
                record.next_tingkat_id = next_tingkat.id if next_tingkat else current_tingkat.id

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
                current_class = record.kelas_id
                current_tingkat = current_class.tingkat
                current_jurusan = current_class.jurusan_id

                if not current_tingkat:
                    record.next_class = False
                    continue

                current_master_class = self.env['cdn.master_kelas'].search([
                    ('tingkat', '=', current_tingkat.id),
                    ('nama_kelas', '=', current_class.nama_kelas),
                    ('jurusan_id', '=', current_jurusan.id if current_jurusan else False),
                ], limit=1)
                if not current_master_class and current_jurusan:
                    current_master_class = self.env['cdn.master_kelas'].search([
                        ('tingkat', '=', current_tingkat.id),
                        ('jurusan_id', '=', current_jurusan.id),
                    ], limit=1)
                if not current_master_class:
                    current_master_class = self.env['cdn.master_kelas'].search([
                        ('tingkat', '=', current_tingkat.id),
                    ], limit=1)

                record.next_class = current_master_class.id if current_master_class else False
                continue

            # Untuk status naik, cari kelas selanjutnya
            current_class = record.kelas_id
            current_tingkat = current_class.tingkat
            current_jurusan = current_class.jurusan_id

            if not current_tingkat:
                record.next_class = False
                continue

            next_tingkat = record._get_next_tingkat_for_progression(
                current_class, current_tingkat)
            if not next_tingkat:
                record.next_class = False
                continue

            next_master_class = record._find_next_master_class(
                current_class, next_tingkat, current_jurusan)
            record.next_class = next_master_class.id if next_master_class else False

    def _get_next_tingkat(self, current_tingkat):
        """Mendapatkan tingkat selanjutnya berdasarkan tingkat saat ini"""
        if not current_tingkat:
            return False

        try:
            current_order = int(current_tingkat.name)
        except (TypeError, ValueError):
            current_order = self._extract_tingkat_number(current_tingkat.name)

        if not current_order or not getattr(current_tingkat, 'jenjang', False):
            return False

        jenjang_val = current_tingkat.jenjang

        progression = {
            'paud': {
                1: ('paud', 2),
                2: ('tk', 1),
            },
            'tk': {
                1: ('tk', 2),
                2: ('sd', 1),
            },
            'sd': {
                1: ('sd', 2),
                2: ('sd', 3),
                3: ('sd', 4),
                4: ('sd', 5),
                5: ('sd', 6),
                6: ('smp', 7),
            },
            'smp': {
                7: ('smp', 8),
                8: ('smp', 9),
                9: ('sma', 10),
            },
            'sma': {
                10: ('sma', 11),
                11: ('sma', 12),
            },
        }

        next_spec = progression.get(jenjang_val, {}).get(current_order)
        if not next_spec:
            return False

        next_jenjang, next_order = next_spec
        return self.env['cdn.tingkat'].search([
            ('jenjang', '=', next_jenjang),
            ('name', '=', next_order),
        ], limit=1)

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
        self.next_tingkat_id = False
        self.walikelas_id = False
        self.status = False
        self.partner_ids = [(5, 0, 0)]  # kosongkan M2M
        self.partner_lines = [(5, 0, 0)]  # kosongkan One2many
        self.filtered_santri_ids = [(5, 0, 0)]  # kosongkan filtered santri
        self.next_class = False
        self.message_result = False

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
            # Gunakan object kelas sementara untuk menggunakan method yang sama
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
            current_jenjang = kelas.jenjang if hasattr(
                kelas, 'jenjang') else None
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

                # Cari tingkat berdasarkan field name
                tingkat_records = self.env['cdn.tingkat'].search([
                    ('name', '=', num)
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
                master_kelas_domain.append(
                    ('jurusan_id', '=', current_jurusan.id))

            next_classes = self.env['cdn.master_kelas'].search(
                master_kelas_domain, limit=1)

            return bool(next_classes)

        except Exception as e:
            # Jika terjadi error, default ke False (lulus)
            _logger.warning(f"Error checking next class: {str(e)}")
            return False

    def action_proses_kenaikan_kelas(self):
        """
        Aksi untuk memproses kenaikan kelas dengan memperbarui data siswa
        berdasarkan status centang masing-masing siswa
        """
        _logger.info(
            f"Memulai proses kenaikan kelas untuk tahun ajaran: {self.tahunajaran_id.name}")

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

            _logger.info(
                f"Current year: {current_year}, Next year: {next_year}")
            _logger.info(f"Mencari tahun ajaran dengan nama: {next_ta_name}")

            # Cari tahun ajaran berikutnya
            tahun_ajaran_berikutnya = self.env['cdn.ref_tahunajaran'].search([
                ('name', '=', next_ta_name)
            ], limit=1)

            _logger.info(
                f"Hasil pencarian tahun ajaran berikutnya: {tahun_ajaran_berikutnya.name if tahun_ajaran_berikutnya else 'Tidak ditemukan'}")

        except (ValueError, IndexError) as e:
            _logger.error(f"Format tahun ajaran tidak valid: {str(e)}")
            raise UserError(
                f"Format tahun ajaran tidak valid: {self.tahunajaran_id.name}. Format yang diharapkan: YYYY/YYYY")

        # Jika tahun ajaran berikutnya tidak ditemukan, buat yang baru
        if not tahun_ajaran_berikutnya:
            message += f"Tahun ajaran {next_ta_name} tidak ditemukan. Mencoba membuat tahun ajaran baru...\n"
            try:
                tahun_ajaran_berikutnya = self._create_next_tahun_ajaran(
                    self.tahunajaran_id)
                message += f"Berhasil membuat tahun ajaran baru: {tahun_ajaran_berikutnya.name}\n\n"
            except Exception as e:
                message += f"Gagal membuat tahun ajaran baru: {str(e)}\n\n"
                raise UserError(f"Gagal membuat tahun ajaran baru: {str(e)}")

        # Pisahkan santri berdasarkan status centang
        santri_naik = self.partner_ids.filtered(lambda s: s.centang == True)
        santri_tidak_naik = self.partner_ids.filtered(
            lambda s: s.centang == False)

        _logger.info(f"Santri naik kelas: {len(santri_naik)}")
        _logger.info(f"Santri tidak naik kelas: {len(santri_tidak_naik)}")

        try:
            # ===== PROSES BERDASARKAN STATUS (NAIK ATAU LULUS) =====
            if self.status == 'naik':
                message += f"\n=== PROSES KENAIKAN KELAS ===\n"

                if not self.next_class:
                    raise UserError(
                        "Kelas selanjutnya tidak ditentukan untuk proses kenaikan kelas!")

                # Proses santri yang naik kelas (dicentang)
                if santri_naik:
                    for siswa in santri_naik:
                        siswa.write({
                            'tahunajaran_id': tahun_ajaran_berikutnya.id,
                        })
                        count_siswa_naik += 1

                    message += f"✓ {len(santri_naik)} siswa naik kelas ke {self.next_class.name}\n"

                # Proses santri yang tidak naik kelas (tidak dicentang)
                if santri_tidak_naik:
                    # PENTING: Hapus siswa yang tidak naik dari kelas saat ini DULU
                    self.kelas_id.write({
                        'siswa_ids': [(3, siswa.id) for siswa in santri_tidak_naik]
                    })
                    message += f"✓ Menghapus {len(santri_tidak_naik)} siswa dari kelas {self.kelas_id.nama_kelas}\n"

                    # Cari atau buat kelas untuk siswa yang tinggal kelas
                    kelas_tinggal_kelas = self._find_or_create_tinggal_kelas(
                        tahun_ajaran_berikutnya)

                    if kelas_tinggal_kelas:
                        # Masukkan siswa ke kelas tinggal kelas
                        kelas_tinggal_kelas.write({
                            'siswa_ids': [(4, siswa.id) for siswa in santri_tidak_naik]
                        })

                        # Update data siswa yang tidak naik
                        for siswa in santri_tidak_naik:
                            siswa.write({
                                'ruang_kelas_id': kelas_tinggal_kelas.id,
                                'tahunajaran_id': tahun_ajaran_berikutnya.id,
                            })
                            count_siswa_tidak_naik += 1

                        message += f"✓ {len(santri_tidak_naik)} siswa dipindahkan ke kelas tinggal kelas: {kelas_tinggal_kelas.nama_kelas}\n"
                    else:
                        # Jika gagal membuat kelas tinggal kelas, siswa tetap dihapus dari kelas
                        for siswa in santri_tidak_naik:
                            siswa.write({
                                'ruang_kelas_id': False,  # Hapus dari kelas
                                'tahunajaran_id': tahun_ajaran_berikutnya.id,
                            })
                            count_siswa_tidak_naik += 1

                        message += f"⚠ {len(santri_tidak_naik)} siswa dihapus dari kelas (tidak dapat membuat kelas tinggal kelas)\n"

                # Update kelas utama ke tingkat selanjutnya (hanya untuk siswa yang naik)
                if santri_naik:
                    self.kelas_id.write({
                        'name': self.next_class.id,
                        'tahunajaran_id': tahun_ajaran_berikutnya.id,
                        # 'walikelas_id': self.wali_kelas_selanjutnya.id,
                    })
                    message += f"✓ Kelas {self.kelas_id.nama_kelas} diupdate ke {self.next_class.name}\n"

            elif self.status == 'lulus':
                message += f"\n=== PROSES KELULUSAN ===\n"

                # Proses santri yang lulus (dicentang)
                if santri_naik:

                    self.kelas_id.write({
                        'aktif_tidak': 'tidak',
                        # 'tahunajaran_id': tahun_ajaran_berikutnya.id,
                    })

                    for siswa in santri_naik:
                        siswa.write({
                            # 'tahun_lulus': tahun_ajaran_berikutnya.name,
                        })
                        count_siswa_lulus += 1

                    message += f"✓ {len(santri_naik)} siswa lulus\n"

                # Proses santri yang tidak lulus (tidak dicentang)
                if santri_tidak_naik:
                    # Hapus siswa yang tidak lulus dari kelas
                    self.kelas_id.write({
                        'siswa_ids': [(3, siswa.id) for siswa in santri_tidak_naik]
                    })

                    kelas_tinggal_kelas = self._find_or_create_tinggal_kelas(
                        tahun_ajaran_berikutnya)

                    if kelas_tinggal_kelas:
                        # Masukkan siswa ke kelas tinggal kelas
                        kelas_tinggal_kelas.write({
                            'siswa_ids': [(4, siswa.id) for siswa in santri_tidak_naik]
                        })

                        # Update data siswa yang tidak naik
                        for siswa in santri_tidak_naik:
                            siswa.write({
                                'ruang_kelas_id': kelas_tinggal_kelas.id,
                                'tahunajaran_id': tahun_ajaran_berikutnya.id,
                            })
                            count_siswa_tidak_naik += 1

                        message += f"✓ {len(santri_tidak_naik)} siswa dipindahkan ke kelas tinggal kelas: {kelas_tinggal_kelas.nama_kelas}\n"
                    else:
                        # Jika gagal membuat kelas tinggal kelas, siswa tetap dihapus dari kelas
                        for siswa in santri_tidak_naik:
                            siswa.write({
                                'ruang_kelas_id': False,  # Hapus dari kelas
                                'tahunajaran_id': tahun_ajaran_berikutnya.id,
                            })
                            count_siswa_tidak_naik += 1

                        message += f"⚠ {len(santri_tidak_naik)} siswa dihapus dari kelas (tidak dapat membuat kelas tinggal kelas)\n"

                # Jika semua siswa lulus, nonaktifkan kelas
                if len(santri_naik) == len(self.partner_ids):
                    self.kelas_id.write({
                        'aktif_tidak': 'tidak',
                    })
                    message += f"✓ Kelas {self.kelas_id.nama_kelas} dinonaktifkan (semua siswal lulus)\n"

        except Exception as e:
            error_msg = f"ERROR memproses kenaikan kelas: {str(e)}"
            message += f"❌ {error_msg}\n"
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
        result_message = f"✅ Proses Kenaikan Kelas berhasil dilakukan!\n\n"
        result_message += f"📊 Ringkasan Hasil:\n"
        result_message += f"- Siswa naik kelas: {count_siswa_naik}\n"
        result_message += f"- Siswa tidak naik: {count_siswa_tidak_naik}\n"
        result_message += f"- Siswa lulus: {count_siswa_lulus}\n"
        result_message += f"- Siswa tidak lulus: {count_siswa_tidak_lulus}\n"
        result_message += f"Total siswa diproses: {len(self.partner_ids)}\n\n"
        result_message += f"📝 Detail Proses:\n{message}"

        _logger.info(
            f"Proses kenaikan kelas selesai dengan hasil: {result_message}")

        # Update field message_result
        self.message_result = result_message

        # Reset field centang semua siswa
        self.partner_ids.write({'centang': False})

        # Kirim notification via bus
        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'simple_notification',
            {
                'title': 'Sukses!',
                # 'message': f'Proses kenaikan kelas berhasil! Total {len(self.partner_ids)} siswa diproses.',
                'message': 'Proses kenaikan kelas berhasil!',
                'type': 'success',
                'sticky': False,
                'timeout': 150000,
            }
        )

        # Buat wizard baru dan return
        new_wizard = self.create({})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Kenaikan Kelas',
            'res_model': 'cdn.kenaikan_kelas',
            'view_mode': 'form',
            'res_id': new_wizard.id,
            'target': 'new',
        }

    def _find_or_create_tinggal_kelas(self, tahun_ajaran_berikutnya):
        """
        Helper method untuk mencari atau membuat kelas tinggal kelas
        """
        try:
            # Cari kelas dengan tingkat, nama kelas, dan jurusan yang sama untuk tahun ajaran berikutnya
            domain = [
                ('name.tingkat', '=', self.kelas_id.name.tingkat.id),
                ('name.nama_kelas', '=', self.kelas_id.name.nama_kelas),
                ('tahunajaran_id', '=', tahun_ajaran_berikutnya.id),
                ('aktif_tidak', '=', 'aktif'),
            ]

            # Tambahkan filter jurusan jika ada
            if self.kelas_id.name.jurusan_id:
                domain.append(
                    ('name.jurusan_id', '=', self.kelas_id.name.jurusan_id.id))

            kelas_tinggal_kelas = self.env['cdn.ruang_kelas'].search(
                domain, limit=1)

            if not kelas_tinggal_kelas:
                # Buat kelas baru untuk tinggal kelas
                kelas_tinggal_kelas = self.env['cdn.ruang_kelas'].create({
                    'name': self.kelas_id.name.id,  # Nama kelas sama dengan kelas asal
                    'tahunajaran_id': tahun_ajaran_berikutnya.id,
                    'walikelas_id': self.walikelas_id.id,
                    'status': 'konfirm',
                    'aktif_tidak': 'aktif',
                    'keterangan': 'Kelas baru untuk santri yang tiddak naik/lulus.',
                })
                _logger.info(
                    f"Berhasil membuat kelas tinggal kelas baru: {kelas_tinggal_kelas.nama_kelas}")

            return kelas_tinggal_kelas

        except Exception as e:
            _logger.error(
                f"Gagal mencari/membuat kelas tinggal kelas: {str(e)}")
            return False
