from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64
import io

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


class WizardRekapAbsensiSiswa(models.TransientModel):
    _name = 'cdn.wizard_rekap_absensi_siswa'
    _description = 'Wizard Rekap Absensi Siswa'
    _order = 'id desc'

    tgl_awal = fields.Date(string='Tanggal Awal', required=True, default=fields.Date.context_today)
    tgl_akhir = fields.Date(string='Tanggal Akhir', required=True, default=fields.Date.context_today)
    
    tipe_absensi = fields.Selection(
        selection=[
            ('kelas', 'Absensi Kelas (KBM)'),
            ('halaqoh', 'Absensi Halaqoh'),
            ('semua', 'Semua (Kelas & Halaqoh)')
        ],
        string="Tipe Absensi",
        default='kelas',
        required=True
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
        string="Jenjang"
    )
    kelas_id = fields.Many2one('cdn.ruang_kelas', string='Kelas')
    halaqoh_id = fields.Many2one('cdn.halaqoh', string='Halaqoh')

    rekap_line_ids = fields.One2many(
        'cdn.wizard_rekap_absensi_siswa_line', 'wizard_id', string='Detail Kehadiran', readonly=True)

    data_file = fields.Binary(string='File')
    file_name = fields.Char(string='Nama File')

    @api.onchange('tipe_absensi')
    def _onchange_tipe_absensi(self):
        if self.tipe_absensi == 'kelas':
            self.halaqoh_id = False
        elif self.tipe_absensi == 'halaqoh':
            self.jenjang = False
            self.kelas_id = False

    @api.onchange('jenjang')
    def _onchange_jenjang(self):
        if self.jenjang and self.kelas_id and self.kelas_id.jenjang != self.jenjang:
            self.kelas_id = False

    def action_proses(self):
        if self.tgl_awal > self.tgl_akhir:
            raise UserError(_('Tanggal Awal tidak boleh lebih besar dari Tanggal Akhir.'))

        # Hapus line sebelumnya
        self.rekap_line_ids = [(5, 0, 0)]

        rekap_data = {}

        def _init_siswa(siswa):
            s_id = siswa.id
            if s_id not in rekap_data:
                rk = getattr(siswa, 'ruang_kelas_id', False) or getattr(siswa, 'kelas_id', False)
                rekap_data[s_id] = {
                    'siswa_id': s_id,
                    'kelas_id': rk.id if rk else False,
                    'jenjang': rk.jenjang if rk and hasattr(rk, 'jenjang') else False,
                    'walikelas_id': rk.walikelas_id.id if rk and hasattr(rk, 'walikelas_id') and rk.walikelas_id else False,
                    'hadir': 0,
                    'sakit': 0,
                    'izin': 0,
                    'alpa': 0,
                    'pulang_sakit': 0,
                    'pulang_izin': 0,
                    'pulang_alpa': 0,
                    'keluar': 0,
                }
            return rekap_data[s_id]

        def _add_kehadiran(s_dict, kehadiran):
            if kehadiran == 'Hadir':
                s_dict['hadir'] += 1
            elif kehadiran == 'Sakit':
                s_dict['sakit'] += 1
            elif kehadiran == 'Izin':
                s_dict['izin'] += 1
            elif kehadiran == 'Alpa':
                s_dict['alpa'] += 1
            elif kehadiran == 'Pulang-Sakit':
                s_dict['pulang_sakit'] += 1
            elif kehadiran == 'Pulang-Izin':
                s_dict['pulang_izin'] += 1
            elif kehadiran == 'Pulang-Alpa':
                s_dict['pulang_alpa'] += 1
            elif kehadiran == 'keluar':
                s_dict['keluar'] += 1

        # 1. Ambil data Absensi Kelas / KBM
        if self.tipe_absensi in ['kelas', 'semua']:
            domain_kbm = [
                ('tanggal', '>=', self.tgl_awal),
                ('tanggal', '<=', self.tgl_akhir)
            ]
            if self.kelas_id:
                domain_kbm.append(('kelas_id', '=', self.kelas_id.id))
            if self.jenjang:
                domain_kbm.append(('kelas_id.jenjang', '=', self.jenjang))
                
            kbm_lines = self.env['cdn.absensi_siswa_lines'].search(domain_kbm)
            for line in kbm_lines:
                if not line.siswa_id:
                    continue
                s_dict = _init_siswa(line.siswa_id)
                if line.kelas_id and not s_dict['kelas_id']:
                    s_dict['kelas_id'] = line.kelas_id.id
                _add_kehadiran(s_dict, line.kehadiran)

        # 2. Ambil data Absensi Halaqoh
        if self.tipe_absensi in ['halaqoh', 'semua']:
            domain_halaqoh = [
                ('tanggal', '>=', self.tgl_awal),
                ('tanggal', '<=', self.tgl_akhir)
            ]
            if self.halaqoh_id:
                domain_halaqoh.append(('halaqoh_id', '=', self.halaqoh_id.id))
            if self.kelas_id:
                domain_halaqoh.append(('siswa_id.ruang_kelas_id', '=', self.kelas_id.id))
                
            halaqoh_lines = self.env['cdn.absen_halaqoh_line'].search(domain_halaqoh)
            for line in halaqoh_lines:
                if not line.siswa_id:
                    continue
                s_dict = _init_siswa(line.siswa_id)
                _add_kehadiran(s_dict, line.kehadiran)

        # Buat lines diurutkan A-Z berdasarkan nama siswa
        lines = []
        sorted_rekap = sorted(
            rekap_data.items(),
            key=lambda x: self.env['cdn.siswa'].browse(x[0]).name or ''
        )
        for siswa_id, data in sorted_rekap:
            lines.append((0, 0, data))

        self.rekap_line_ids = lines
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'cdn.wizard_rekap_absensi_siswa',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_export_xlsx(self):
        self.action_proses()
        
        if not xlsxwriter:
            raise UserError(_("Modul 'xlsxwriter' tidak ditemukan. Silakan hubungi administrator."))

        if not self.rekap_line_ids:
            raise UserError(_("Tidak ada data untuk diekspor pada rentang tanggal tersebut."))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Rekap Absensi')

        # Formats
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        title_format = workbook.add_format({'bold': True, 'font_size': 14})
        border_format = workbook.add_format({'border': 1})
        center_format = workbook.add_format({'border': 1, 'align': 'center'})

        # Judul & Info Header
        sheet.write(0, 0, 'REKAP ABSENSI SISWA', title_format)
        
        info_row = 2
        
        MONTHS = {
            1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
            5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
            9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
        }
        
        if self.tgl_awal.month == self.tgl_akhir.month and self.tgl_awal.year == self.tgl_akhir.year:
            periode_str = f"Periode : {self.tgl_awal.day} - {self.tgl_akhir.day} {MONTHS[self.tgl_akhir.month]} {self.tgl_akhir.year}"
        elif self.tgl_awal.year == self.tgl_akhir.year:
            periode_str = f"Periode : {self.tgl_awal.day} {MONTHS[self.tgl_awal.month]} - {self.tgl_akhir.day} {MONTHS[self.tgl_akhir.month]} {self.tgl_akhir.year}"
        else:
            periode_str = f"Periode : {self.tgl_awal.day} {MONTHS[self.tgl_awal.month]} {self.tgl_awal.year} - {self.tgl_akhir.day} {MONTHS[self.tgl_akhir.month]} {self.tgl_akhir.year}"

        sheet.write(info_row, 0, periode_str)
        info_row += 1

        tipe_dict = dict(self._fields['tipe_absensi'].selection)
        sheet.write(info_row, 0, f'Tipe Absensi: {tipe_dict.get(self.tipe_absensi, self.tipe_absensi)}')
        info_row += 1

        if self.jenjang:
            j_dict = dict(self._fields['jenjang'].selection)
            sheet.write(info_row, 0, f'Jenjang: {j_dict.get(self.jenjang, self.jenjang)}')
            info_row += 1

        if self.kelas_id:
            k_name = self.kelas_id.name.name if hasattr(self.kelas_id.name, 'name') and self.kelas_id.name.name else self.kelas_id.display_name
            sheet.write(info_row, 0, f'Kelas: {k_name}')
            info_row += 1

        if self.halaqoh_id:
            sheet.write(info_row, 0, f'Halaqoh: {self.halaqoh_id.name}')
            info_row += 1

        # Table Header (7 Pilihan Kehadiran Utama + Izin Keluar)
        headers = ['No', 'Nama Siswa', 'Hadir', 'Sakit', 'Izin', 'Alpa', 'Pulang Sakit', 'Pulang Izin', 'Pulang Alpa', 'Izin Keluar']
        
        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 35)
        sheet.set_column('C:J', 14)
        
        table_header_row = info_row + 1
        for col, header in enumerate(headers):
            sheet.write(table_header_row, col, header, header_format)

        # Mengurutkan data berdasarkan Nama Siswa A-Z
        sorted_lines = self.rekap_line_ids.sorted(key=lambda r: (r.siswa_name or r.siswa_id.name or ''))

        # Table Data
        row = table_header_row + 1
        for i, line in enumerate(sorted_lines, 1):
            sheet.write(row, 0, i, center_format)
            sheet.write(row, 1, line.siswa_id.name if line.siswa_id else '-', border_format)
            sheet.write(row, 2, line.hadir, center_format)
            sheet.write(row, 3, line.sakit, center_format)
            sheet.write(row, 4, line.izin, center_format)
            sheet.write(row, 5, line.alpa, center_format)
            sheet.write(row, 6, line.pulang_sakit, center_format)
            sheet.write(row, 7, line.pulang_izin, center_format)
            sheet.write(row, 8, line.pulang_alpa, center_format)
            sheet.write(row, 9, line.keluar, center_format)
            row += 1

        workbook.close()
        output.seek(0)
        xlsx_data = output.read()

        file_name = f"Rekap_Absensi_Siswa_{self.tgl_awal}_sd_{self.tgl_akhir}.xlsx"

        self.write({
            'data_file': base64.b64encode(xlsx_data),
            'file_name': file_name
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model={self._name}&id={self.id}&field=data_file&download=true&filename={self.file_name}',
            'target': 'self',
        }


class WizardRekapAbsensiSiswaLine(models.TransientModel):
    _name = 'cdn.wizard_rekap_absensi_siswa_line'
    _description = 'Detail Rekap Absensi Siswa'
    _order = 'jenjang, kelas_id, siswa_name asc, id asc'

    wizard_id = fields.Many2one('cdn.wizard_rekap_absensi_siswa', string='Wizard', ondelete='cascade')
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
        string="Jenjang"
    )
    kelas_id = fields.Many2one('cdn.ruang_kelas', string='Kelas')
    walikelas_id = fields.Many2one('hr.employee', string='Wali Kelas')
    siswa_id = fields.Many2one('cdn.siswa', string='Nama Siswa')
    siswa_name = fields.Char(string='Nama Siswa String', related='siswa_id.name', store=True)
    
    hadir = fields.Integer(string='Hadir')
    sakit = fields.Integer(string='Sakit')
    izin = fields.Integer(string='Izin')
    alpa = fields.Integer(string='Alpa')
    pulang_sakit = fields.Integer(string='Pulang Sakit')
    pulang_izin = fields.Integer(string='Pulang Izin')
    pulang_alpa = fields.Integer(string='Pulang Alpa')
    keluar = fields.Integer(string='Izin Keluar')
