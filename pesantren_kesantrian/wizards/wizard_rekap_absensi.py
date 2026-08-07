from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64
import csv
import io

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


class WizardRekapAbsensi(models.TransientModel):
    _name = 'cdn.wizard_rekap_absensi'
    _description = 'Wizard Rekap Absensi Santri'

    siswa_id = fields.Many2one('cdn.siswa', string='Nama Siswa', required=True)
    barcode = fields.Char(string='Kartu Santri')
    tgl_awal = fields.Date(string='Tanggal Awal',
                           required=True, default=fields.Date.context_today)
    tgl_akhir = fields.Date(string='Tanggal Akhir',
                            required=True, default=fields.Date.context_today)

    # Inline results
    rekap_line_ids = fields.One2many(
        'cdn.wizard_rekap_absensi_line', 'wizard_id', string='Detail Kehadiran', readonly=True)

    # Summary fields
    jml_hadir = fields.Integer(string='Hadir', compute='_compute_summary')
    jml_izin = fields.Integer(string='Izin', compute='_compute_summary')
    jml_sakit = fields.Integer(string='Sakit', compute='_compute_summary')
    jml_alpa = fields.Integer(string='Alpa', compute='_compute_summary')
    jml_pulang_sakit = fields.Integer(string='Pulang Sakit', compute='_compute_summary')
    jml_pulang_izin = fields.Integer(string='Pulang Izin', compute='_compute_summary')
    jml_pulang_alpa = fields.Integer(string='Pulang Alpa', compute='_compute_summary')
    jml_guru_pengganti = fields.Integer(string='Guru Pengganti', compute='_compute_summary')
    jml_keluar = fields.Integer(
        string='Izin Keluar', compute='_compute_summary')

    # Export fields
    data_file = fields.Binary(string='File')
    file_name = fields.Char(string='Nama File')

    @api.depends('rekap_line_ids')
    def _compute_summary(self):
        for rec in self:
            rec.jml_hadir = len(rec.rekap_line_ids.filtered(
                lambda x: x.kehadiran == 'Hadir'))
            rec.jml_izin = len(rec.rekap_line_ids.filtered(
                lambda x: x.kehadiran == 'Izin'))
            rec.jml_sakit = len(rec.rekap_line_ids.filtered(
                lambda x: x.kehadiran == 'Sakit'))
            rec.jml_alpa = len(rec.rekap_line_ids.filtered(
                lambda x: x.kehadiran == 'Alpa'))
            rec.jml_pulang_sakit = len(rec.rekap_line_ids.filtered(
                lambda x: x.kehadiran == 'Pulang-Sakit'))
            rec.jml_pulang_izin = len(rec.rekap_line_ids.filtered(
                lambda x: x.kehadiran == 'Pulang-Izin'))
            rec.jml_pulang_alpa = len(rec.rekap_line_ids.filtered(
                lambda x: x.kehadiran == 'Pulang-Alpa'))
            rec.jml_guru_pengganti = len(rec.rekap_line_ids.filtered(
                lambda x: 'Guru Pengganti' in (x.pengabsen or '')))
            rec.jml_keluar = len(rec.rekap_line_ids.filtered(
                lambda x: x.kehadiran == 'keluar'))

    @api.onchange('barcode')
    def _onchange_barcode(self):
        if self.barcode:
            siswa = self.env['cdn.siswa'].search(
                [('barcode_santri', '=', self.barcode)], limit=1)
            if siswa:
                self.siswa_id = siswa.id
            else:
                self.siswa_id = False
                barcode_sementara = self.barcode
                self.barcode = False
                return {
                    'warning': {
                        'title': "Perhatian !",
                        'message': f"Data Santri dengan Kartu Santri {barcode_sementara} tidak ditemukan."
                    }
                }
        else:
            self.siswa_id = False

    @api.onchange('siswa_id', 'tgl_awal', 'tgl_akhir')
    def _onchange_rekap_params(self):
        if self.siswa_id:
            self.barcode = self.siswa_id.barcode_santri
        else:
            self.barcode = False

        if not (self.siswa_id and self.tgl_awal and self.tgl_akhir):
            self.rekap_line_ids = [(5, 0, 0)]
            return

        if self.tgl_awal > self.tgl_akhir:
            return

        lines = []

        # 1. Halaqoh
        halaqoh_lines = self.env['cdn.absen_halaqoh_line'].search([
            ('siswa_id', '=', self.siswa_id.id),
            ('tanggal', '>=', self.tgl_awal),
            ('tanggal', '<=', self.tgl_akhir)
        ], order='tanggal asc')
        for line in halaqoh_lines:
            absen_hdr = line.absen_id if line.absen_id else False
            is_pengganti = getattr(absen_hdr, 'is_guru_pengganti', False) if absen_hdr else False
            ustadz = getattr(absen_hdr, 'ustadz_id', False)
            pj = getattr(absen_hdr, 'penanggung_jawab_id', False)
            
            pengabsen_str = ustadz.name if ustadz else '-'
            if ustadz and (is_pengganti or (pj and ustadz.id != pj.id)):
                pengabsen_str += ' (Guru Pengganti)'
            lines.append((0, 0, {
                'tanggal': line.tanggal,
                'jenis': 'Halaqoh',
                'kehadiran': line.kehadiran,
                'pengabsen': pengabsen_str,
                'keterangan': line.keterangan or '-'
            }))

        # 2. Malam
        malam_lines = self.env['cdn.absensi_malam_line'].search([
            ('siswa_id', '=', self.siswa_id.id),
            ('tanggal', '>=', self.tgl_awal),
            ('tanggal', '<=', self.tgl_akhir)
        ], order='tanggal asc')
        for line in malam_lines:
            lines.append((0, 0, {
                'tanggal': line.tanggal,
                'jenis': 'Malam',
                'kehadiran': line.kehadiran_absen,
                'pengabsen': '-',
                'keterangan': line.keterangan or '-'
            }))

        # 3. Tahfidz
        tahfidz_lines = self.env['cdn.absen_tahfidz_quran_line'].search([
            ('siswa_id', '=', self.siswa_id.id),
            ('tanggal', '>=', self.tgl_awal),
            ('tanggal', '<=', self.tgl_akhir)
        ], order='tanggal asc')
        for line in tahfidz_lines:
            lines.append((0, 0, {
                'tanggal': line.tanggal,
                'jenis': 'Tahfidz',
                'kehadiran': line.kehadiran,
                'pengabsen': '-',
                'keterangan': line.keterangan or '-'
            }))

        # 4. Tahsin
        tahsin_lines = self.env['cdn.absen_tahsin_quran_line'].search([
            ('siswa_id', '=', self.siswa_id.id),
            ('tanggal', '>=', self.tgl_awal),
            ('tanggal', '<=', self.tgl_akhir)
        ], order='tanggal asc')
        for line in tahsin_lines:
            lines.append((0, 0, {
                'tanggal': line.tanggal,
                'jenis': 'Tahsin',
                'kehadiran': line.kehadiran,
                'pengabsen': '-',
                'keterangan': line.keterangan or '-'
            }))

        # Sort lines by date
        lines.sort(key=lambda x: x[2]['tanggal'])

        self.rekap_line_ids = [(5, 0, 0)] + lines

    def action_export_csv(self):
        self._onchange_rekap_params()  # Ensure lines are populated even if called directly
        if not self.rekap_line_ids:
            raise UserError(_("Tidak ada data untuk diekspor."))

        output = io.StringIO()
        writer = csv.writer(output, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)

        # Header
        writer.writerow(['No', 'Tanggal', 'Kegiatan',
                        'Kehadiran', 'Guru / Pengabsen', 'Keterangan'])

        # Data
        for i, line in enumerate(self.rekap_line_ids, 1):
            writer.writerow([
                i,
                line.tanggal,
                line.jenis,
                dict(line._fields['kehadiran'].selection).get(
                    line.kehadiran, line.kehadiran),
                line.pengabsen or '-',
                line.keterangan or '-'
            ])

        csv_data = output.getvalue().encode('utf-8')
        file_name = f"Rekap_Absensi_{self.siswa_id.name}_{self.tgl_awal}_sd_{self.tgl_akhir}.csv"

        self.write({
            'data_file': base64.b64encode(csv_data),
            'file_name': file_name
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model={self._name}&id={self.id}&field=data_file&download=true&filename={self.file_name}',
            'target': 'self',
        }

    def action_export_xlsx(self):
        if not xlsxwriter:
            raise UserError(
                _("Modul 'xlsxwriter' tidak ditemukan. Silakan hubungi administrator."))

        self._onchange_rekap_params()
        if not self.rekap_line_ids:
            raise UserError(_("Tidak ada data untuk diekspor."))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Rekap Absensi')

        # Formats
        header_format = workbook.add_format(
            {'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
        title_format = workbook.add_format({'bold': True, 'font_size': 14})
        date_format = workbook.add_format(
            {'num_format': 'dd/mm/yyyy', 'border': 1})
        border_format = workbook.add_format({'border': 1})

        # Title
        sheet.write(0, 0, 'Rekap Absensi Santri', title_format)
        sheet.write(1, 0, f'Nama Siswa: {self.siswa_id.name}')
        sheet.write(2, 0, f'NIS: {self.siswa_id.nis}')
        sheet.write(3, 0, f'Periode: {self.tgl_awal} s/d {self.tgl_akhir}')

        # Table Header
        headers = ['No', 'Tanggal', 'Kegiatan', 'Kehadiran', 'Guru / Pengabsen', 'Keterangan']
        for col, header in enumerate(headers):
            sheet.write(5, col, header, header_format)

        # Table Data
        row = 6
        for i, line in enumerate(self.rekap_line_ids, 1):
            sheet.write(row, 0, i, border_format)
            sheet.write(row, 1, line.tanggal, date_format)
            sheet.write(row, 2, line.jenis, border_format)
            sheet.write(row, 3, dict(line._fields['kehadiran'].selection).get(
                line.kehadiran, line.kehadiran), border_format)
            sheet.write(row, 4, line.pengabsen or '-', border_format)
            sheet.write(row, 5, line.keterangan or '-', border_format)
            row += 1

        # Summary
        row += 1
        sheet.write(row, 0, 'Ringkasan:', header_format)
        sheet.write(row + 1, 0, 'Hadir', border_format)
        sheet.write(row + 1, 1, self.jml_hadir, border_format)
        sheet.write(row + 2, 0, 'Izin', border_format)
        sheet.write(row + 2, 1, self.jml_izin, border_format)
        sheet.write(row + 3, 0, 'Sakit', border_format)
        sheet.write(row + 3, 1, self.jml_sakit, border_format)
        sheet.write(row + 4, 0, 'Alpa', border_format)
        sheet.write(row + 4, 1, self.jml_alpa, border_format)
        sheet.write(row + 5, 0, 'Pulang Sakit', border_format)
        sheet.write(row + 5, 1, self.jml_pulang_sakit, border_format)
        sheet.write(row + 6, 0, 'Pulang Izin', border_format)
        sheet.write(row + 6, 1, self.jml_pulang_izin, border_format)
        sheet.write(row + 7, 0, 'Pulang Alpa', border_format)
        sheet.write(row + 7, 1, self.jml_pulang_alpa, border_format)
        sheet.write(row + 8, 0, 'Sesi Guru Pengganti', border_format)
        sheet.write(row + 8, 1, self.jml_guru_pengganti, border_format)
        sheet.write(row + 9, 0, 'Izin Keluar', border_format)
        sheet.write(row + 9, 1, self.jml_keluar, border_format)

        workbook.close()
        output.seek(0)
        xlsx_data = output.read()

        file_name = f"Rekap_Absensi_{self.siswa_id.name}_{self.tgl_awal}_sd_{self.tgl_akhir}.xlsx"

        self.write({
            'data_file': base64.b64encode(xlsx_data),
            'file_name': file_name
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model={self._name}&id={self.id}&field=data_file&download=true&filename={self.file_name}',
            'target': 'self',
        }


class WizardRekapAbsensiLine(models.TransientModel):
    _name = 'cdn.wizard_rekap_absensi_line'
    _description = 'Line Rekap Absensi Santri'

    wizard_id = fields.Many2one(
        'cdn.wizard_rekap_absensi', string='Wizard', ondelete='cascade')
    tanggal = fields.Date(string='Tanggal')
    jenis = fields.Char(string='Kegiatan')
    kehadiran = fields.Selection([
        ('Hadir', 'Hadir'),
        ('Sakit', 'Sakit'),
        ('Izin', 'Izin'),
        ('Alpa', 'Alpa'),
        ('Pulang-Sakit', 'Pulang-Sakit'),
        ('Pulang-Izin', 'Pulang-Izin'),
        ('Pulang-Alpa', 'Pulang-Alpa'),
    ], string='Kehadiran')
    pengabsen = fields.Char(string='Guru / Pengabsen')
    keterangan = fields.Char(string='Keterangan')
