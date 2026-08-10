from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64
import csv
import io
from datetime import date
import calendar

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


BULAN_SELECTION = [
    ('1', 'Januari'), ('2', 'Februari'), ('3', 'Maret'),
    ('4', 'April'), ('5', 'Mei'), ('6', 'Juni'),
    ('7', 'Juli'), ('8', 'Agustus'), ('9', 'September'),
    ('10', 'Oktober'), ('11', 'November'), ('12', 'Desember'),
]

BULAN_DICT = dict(BULAN_SELECTION)


class WizardRekapTahsinTahfidz(models.TransientModel):
    _name = 'cdn.wizard_rekap_tahsin_tahfidz'
    _description = 'Wizard Rekap Tahsin Tahfidz (Laporan Pencapaian Per Halaqoh)'

    def _domain_halaqoh_id(self):
        tahun_ajaran = self.env.user.company_id.tahun_ajaran_aktif.id
        user = self.env.user

        if user.has_group('pesantren_kesantrian.group_kesantrian_manager'):
            return [('fiscalyear_id', '=', tahun_ajaran)]

        employee = self.env['hr.employee'].search(
            [('user_id', '=', user.id)], limit=1)
        if employee:
            return [
                ('fiscalyear_id', '=', tahun_ajaran),
                '|',
                ('penanggung_jawab_id', '=', employee.id),
                ('pengganti_ids', 'in', [employee.id])
            ]
        return [('id', '=', 0)]

    halaqoh_id = fields.Many2one(
        'cdn.halaqoh', string='Halaqoh', required=True,
        domain=_domain_halaqoh_id)
    bulan = fields.Selection(
        BULAN_SELECTION, string='Bulan', required=True,
        default=lambda self: str(date.today().month))
    tahun = fields.Integer(
        string='Tahun', required=True,
        default=lambda self: date.today().year)

    # Auto-filled from halaqoh
    pembimbing_id = fields.Many2one(
        'hr.employee', string='Pembimbing Halaqah',
        related='halaqoh_id.penanggung_jawab_id', readonly=True)

    # Inline results
    rekap_line_ids = fields.One2many(
        'cdn.wizard_rekap_tahsin_tahfidz_line', 'wizard_id',
        string='Detail Pencapaian', readonly=True)

    # Export
    data_file = fields.Binary(string='File')
    file_name = fields.Char(string='Nama File')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        bulan = res.get('bulan', str(date.today().month))
        tahun = res.get('tahun', date.today().year)

        halaqoh_id = res.get('halaqoh_id')
        if not halaqoh_id:
            tahun_ajaran = self.env.user.company_id.tahun_ajaran_aktif.id
            employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            domain = [('fiscalyear_id', '=', tahun_ajaran)]
            if employee and not self.env.user.has_group('pesantren_kesantrian.group_kesantrian_manager'):
                domain.extend(['|', ('penanggung_jawab_id', '=', employee.id), ('pengganti_ids', 'in', [employee.id])])
            halaqoh = self.env['cdn.halaqoh'].search(domain, limit=1)
            if halaqoh:
                halaqoh_id = halaqoh.id
                res['halaqoh_id'] = halaqoh_id

        if halaqoh_id and bulan and tahun:
            lines = self._build_rekap_lines(halaqoh_id, int(bulan), int(tahun))
            res['rekap_line_ids'] = lines

        return res

    @api.onchange('halaqoh_id', 'bulan', 'tahun')
    def _onchange_rekap_params(self):
        if not (self.halaqoh_id and self.bulan and self.tahun):
            self.rekap_line_ids = [(5, 0, 0)]
            return

        lines = self._build_rekap_lines(self.halaqoh_id.id, int(self.bulan), int(self.tahun))
        self.rekap_line_ids = [(5, 0, 0)] + lines

    def _build_rekap_lines(self, halaqoh_id, bulan_int, tahun_int):
        _, last_day = calendar.monthrange(tahun_int, bulan_int)
        tgl_awal = date(tahun_int, bulan_int, 1)
        tgl_akhir = date(tahun_int, bulan_int, last_day)

        halaqoh = self.env['cdn.halaqoh'].browse(halaqoh_id)
        lines = []
        no = 1

        for siswa in halaqoh.siswa_ids.sorted(key=lambda s: s.name or ''):
            penilaian_records = self.env['cdn.penilaian_quran'].search([
                ('siswa_id', '=', siswa.id),
                ('tanggal', '>=', tgl_awal),
                ('tanggal', '<=', tgl_akhir),
                ('state', '=', 'done')
            ], order='tanggal asc')

            tahsin_parts = []
            for rec in penilaian_records:
                if rec.buku_harian_id:
                    parts = []
                    if rec.buku_harian_id:
                        parts.append(rec.buku_harian_id.name)
                    if rec.jilid_harian_id:
                        parts.append(rec.jilid_harian_id.name)
                    if rec.halaman_harian:
                        parts.append(f"Hal {rec.halaman_harian}")
                    tahsin_parts.append(' '.join(parts))
            tahsin_str = tahsin_parts[-1] if tahsin_parts else '-'

            murojaah_parts = []
            for rec in penilaian_records:
                if rec.juz_murajaah:
                    parts = []
                    parts.append(f"Juz {rec.juz_murajaah}")
                    if rec.surah_murajaah_id:
                        parts.append(rec.surah_murajaah_id.name)
                    if rec.halaman_murajaah:
                        parts.append(f"Hal {rec.halaman_murajaah}")
                    murojaah_parts.append(' '.join(parts))
            murojaah_str = murojaah_parts[-1] if murojaah_parts else '-'

            total_maqra_bulan = 0
            for rec in penilaian_records:
                for line in rec.tahfidz_line_ids:
                    total_maqra_bulan += line.jml_baris or 0
            hafalan_baru_str = f"{total_maqra_bulan} Maqra" if total_maqra_bulan > 0 else '-'

            all_penilaian = self.env['cdn.penilaian_quran'].search([
                ('siswa_id', '=', siswa.id),
                ('state', '=', 'done')
            ])
            total_maqra_all = 0
            for rec in all_penilaian:
                for line in rec.tahfidz_line_ids:
                    total_maqra_all += line.jml_baris or 0
            jml_semua_str = f"{total_maqra_all} Maqra" if total_maqra_all > 0 else '-'

            nilai_list = []
            for rec in penilaian_records:
                for line in rec.tahfidz_line_ids:
                    if line.nilai_hafalan:
                        nilai_list.append(line.nilai_hafalan)
            nilai_avg = round(sum(nilai_list) / len(nilai_list)) if nilai_list else 0

            keterangan_parts = []
            for rec in penilaian_records:
                if rec.keterangan_tahfidz:
                    keterangan_parts.append(rec.keterangan_tahfidz)
            keterangan_str = '; '.join(keterangan_parts) if keterangan_parts else ''

            lines.append((0, 0, {
                'no': no,
                'siswa_id': siswa.id,
                'nama': siswa.name,
                'tahsin': tahsin_str,
                'murojaah': murojaah_str,
                'hafalan_baru': hafalan_baru_str,
                'jml_semua_hafalan': jml_semua_str,
                'nilai': nilai_avg,
                'keterangan': keterangan_str,
            }))
            no += 1

        return lines

    def action_export_csv(self):
        self._onchange_rekap_params()
        if not self.rekap_line_ids:
            raise UserError(_("Tidak ada data untuk diekspor."))

        output = io.StringIO()
        writer = csv.writer(output, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)

        writer.writerow(['LAPORAN PENCAPAIAN TAHFIZH SANTRI/WATI'])
        writer.writerow([self.env.user.company_id.name or ''])
        writer.writerow([f'Pembimbing Halaqah: {self.pembimbing_id.name or "-"}'])
        writer.writerow([f'Halaqoh: {self.halaqoh_id.name}'])
        writer.writerow([f'Bulan: {BULAN_DICT.get(self.bulan, "")}'])
        writer.writerow([f'Tahun: {self.tahun}'])
        writer.writerow([])

        writer.writerow(['NO', 'NAMA', 'TAHSIN', 'MUROJAAH',
                         'HAFALAN BARU', 'JUMLAH SEMUA HAFALAN',
                         'NILAI', 'KETERANGAN'])

        for line in self.rekap_line_ids:
            writer.writerow([
                line.no, line.nama, line.tahsin, line.murojaah,
                line.hafalan_baru, line.jml_semua_hafalan,
                line.nilai, line.keterangan or ''
            ])

        csv_data = output.getvalue().encode('utf-8')
        nama_bulan = BULAN_DICT.get(self.bulan, '')
        file_name = f"Rekap_TahsinTahfidz_{self.halaqoh_id.name}_{nama_bulan}_{self.tahun}.csv"

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
        sheet = workbook.add_worksheet('Rekap Tahsin Tahfidz')

        title_format = workbook.add_format({
            'bold': True, 'font_size': 14, 'align': 'center',
            'valign': 'vcenter'
        })
        subtitle_format = workbook.add_format({
            'bold': True, 'font_size': 12, 'align': 'center',
            'valign': 'vcenter'
        })
        info_format = workbook.add_format({
            'font_size': 11, 'align': 'left'
        })
        info_bold_format = workbook.add_format({
            'font_size': 11, 'bold': True, 'align': 'left'
        })
        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#4472C4', 'font_color': 'white',
            'border': 1, 'align': 'center', 'valign': 'vcenter',
            'text_wrap': True
        })
        cell_format = workbook.add_format({
            'border': 1, 'valign': 'vcenter', 'text_wrap': True
        })
        cell_center_format = workbook.add_format({
            'border': 1, 'align': 'center', 'valign': 'vcenter'
        })
        cell_number_format = workbook.add_format({
            'border': 1, 'align': 'center', 'valign': 'vcenter',
            'num_format': '0'
        })
        sign_format = workbook.add_format({
            'font_size': 11, 'align': 'center', 'valign': 'vcenter'
        })
        sign_bold_format = workbook.add_format({
            'font_size': 11, 'align': 'center', 'valign': 'vcenter',
            'bold': True, 'bottom': 1
        })

        sheet.set_column(0, 0, 5)    # NO
        sheet.set_column(1, 1, 25)   # NAMA
        sheet.set_column(2, 2, 15)   # TAHSIN
        sheet.set_column(3, 3, 15)   # MUROJAAH
        sheet.set_column(4, 4, 18)   # HAFALAN BARU
        sheet.set_column(5, 5, 22)   # JML SEMUA HAFALAN
        sheet.set_column(6, 6, 10)   # NILAI
        sheet.set_column(7, 7, 18)   # KETERANGAN

        nama_bulan = BULAN_DICT.get(self.bulan, '')
        company_name = self.env.user.company_id.name or ''

        row = 0
        sheet.merge_range(row, 0, row, 7,
                          'LAPORAN PENCAPAIAN TAHFIZH SANTRI/WATI', title_format)
        row += 1
        sheet.merge_range(row, 0, row, 7, company_name, subtitle_format)
        row += 2

        sheet.write(row, 0, 'PEMBIMBING HALAQAH', info_bold_format)
        sheet.merge_range(row, 1, row, 3,
                          f': {self.pembimbing_id.name or "-"}', info_format)
        row += 1
        sheet.write(row, 0, 'HALAQOH', info_bold_format)
        sheet.merge_range(row, 1, row, 3,
                          f': {self.halaqoh_id.name}', info_format)
        row += 1
        sheet.write(row, 0, 'KELAS', info_bold_format)
        sheet.merge_range(row, 1, row, 3,
                          ': TAHSIN-TAHFIDZ', info_format)
        row += 1
        sheet.write(row, 0, 'BULAN', info_bold_format)
        sheet.merge_range(row, 1, row, 3,
                          f': {nama_bulan.upper()}', info_format)
        row += 1
        sheet.write(row, 0, 'TAHUN', info_bold_format)
        sheet.merge_range(row, 1, row, 3,
                          f': {self.tahun}', info_format)
        row += 2

        sheet.merge_range(row, 0, row, 7,
                          'PROGRAM TAHSIN TAHFIZH', subtitle_format)
        row += 1

        headers = ['NO', 'NAMA', 'TAHSIN', 'MUROJAAH',
                   'HAFALAN BARU', 'JUMLAH SEMUA\nHAFALAN',
                   'NILAI', 'KETERANGAN']
        for col, header in enumerate(headers):
            sheet.write(row, col, header, header_format)
        sheet.set_row(row, 30)
        row += 1

        for line in self.rekap_line_ids:
            sheet.write(row, 0, line.no, cell_center_format)
            sheet.write(row, 1, line.nama, cell_format)
            sheet.write(row, 2, line.tahsin, cell_format)
            sheet.write(row, 3, line.murojaah, cell_format)
            sheet.write(row, 4, line.hafalan_baru, cell_format)
            sheet.write(row, 5, line.jml_semua_hafalan, cell_format)
            sheet.write(row, 6, line.nilai, cell_number_format)
            sheet.write(row, 7, line.keterangan or '', cell_format)
            row += 1

        row += 2
        today = date.today()
        tgl_str = f"{today.day} {BULAN_DICT.get(str(today.month), '')} {today.year}"

        sheet.merge_range(row, 0, row, 3,
                          'Mengetahui,', sign_format)
        sheet.merge_range(row, 4, row, 7,
                          f'Pelaihari, {tgl_str}', sign_format)
        row += 1
        sheet.merge_range(row, 0, row, 3,
                          f'Kepala {company_name}', sign_format)
        sheet.merge_range(row, 4, row, 7,
                          'Pembimbing', sign_format)
        row += 4
        sheet.merge_range(row, 0, row, 3,
                          '(______________________________)', sign_bold_format)
        sheet.merge_range(row, 4, row, 7,
                          f'({self.pembimbing_id.name or "______________________________"})',
                          sign_bold_format)

        workbook.close()
        output.seek(0)
        xlsx_data = output.read()

        file_name = f"Rekap_TahsinTahfidz_{self.halaqoh_id.name}_{nama_bulan}_{self.tahun}.xlsx"

        self.write({
            'data_file': base64.b64encode(xlsx_data),
            'file_name': file_name
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model={self._name}&id={self.id}&field=data_file&download=true&filename={self.file_name}',
            'target': 'self',
        }


class WizardRekapTahsinTahfidzLine(models.TransientModel):
    _name = 'cdn.wizard_rekap_tahsin_tahfidz_line'
    _description = 'Line Rekap Tahsin Tahfidz'

    wizard_id = fields.Many2one(
        'cdn.wizard_rekap_tahsin_tahfidz', string='Wizard', ondelete='cascade')
    no = fields.Integer(string='No')
    siswa_id = fields.Many2one('cdn.siswa', string='Santri')
    nama = fields.Char(string='Nama')
    tahsin = fields.Char(string='Tahsin')
    murojaah = fields.Char(string='Murojaah')
    hafalan_baru = fields.Char(string='Hafalan Baru')
    jml_semua_hafalan = fields.Char(string='Jumlah Semua Hafalan')
    nilai = fields.Integer(string='Nilai')
    keterangan = fields.Char(string='Keterangan')
