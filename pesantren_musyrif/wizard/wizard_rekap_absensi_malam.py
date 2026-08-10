from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64
import csv
import io
from datetime import date

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


class WizardRekapAbsensiMalam(models.TransientModel):
    _name = 'cdn.wizard_rekap_absensi_malam'
    _description = 'Wizard Rekap Absensi Malam (Musyrif)'

    def _default_musyrif_id(self):
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)
        if employee and (employee.has_role('musyrif') or employee.has_role('superadmin')):
            return employee.id
        return False

    def _domain_musyrif_id(self):
        admin_user_ids = self.env.ref('base.group_system').users.ids
        return [
            '|',
            ('user_id', 'in', admin_user_ids),
            ('jns_pegawai_ids.code', 'in', ['musyrif', 'superadmin'])
        ]

    def _domain_kamar_id(self):
        tahun_ajaran = self.env.user.company_id.tahun_ajaran_aktif.id
        base_domain = [('fiscalyear_id', '=', tahun_ajaran)]

        if self.env.user.has_group('base.group_system') or self.env.user.has_group('pesantren_kesantrian.group_kesantrian_manager'):
            return base_domain

        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)
        if employee and (employee.has_role('musyrif') or employee.has_role('superadmin')):
            kamar_ids = self.env['cdn.kamar_santri'].search([
                ('musyrif_id', '=', employee.id),
                ('fiscalyear_id', '=', tahun_ajaran)
            ]).ids
            return [('id', 'in', kamar_ids)]
        return base_domain

    musyrif_id = fields.Many2one(
        'hr.employee', string='Musyrif/Pembina',
        domain=_domain_musyrif_id, default=_default_musyrif_id)
    kamar_id = fields.Many2one(
        'cdn.kamar_santri', string='Kamar',
        domain=_domain_kamar_id)
    tgl_awal = fields.Date(
        string='Tanggal Awal', required=True,
        default=fields.Date.context_today)
    tgl_akhir = fields.Date(
        string='Tanggal Akhir', required=True,
        default=fields.Date.context_today)

    # Result lines
    rekap_line_ids = fields.One2many(
        'cdn.wizard_rekap_absensi_malam_line', 'wizard_id',
        string='Detail Kehadiran', readonly=True)

    # Summary
    jml_hadir = fields.Integer(string='Hadir', compute='_compute_summary')
    jml_izin = fields.Integer(string='Izin', compute='_compute_summary')
    jml_sakit = fields.Integer(string='Sakit', compute='_compute_summary')
    jml_alpa = fields.Integer(string='Alpa', compute='_compute_summary')
    jml_keluar = fields.Integer(string='Izin Keluar', compute='_compute_summary')

    # Export
    data_file = fields.Binary(string='File')
    file_name = fields.Char(string='Nama File')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        today = date.today()
        tgl_awal = res.get('tgl_awal', today)
        tgl_akhir = res.get('tgl_akhir', today)

        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)
        
        musyrif_id = res.get('musyrif_id')
        if not musyrif_id and employee and (employee.has_role('musyrif') or employee.has_role('superadmin')):
            musyrif_id = employee.id
            res['musyrif_id'] = musyrif_id

        kamar_id = res.get('kamar_id')
        if not kamar_id and musyrif_id:
            tahun_ajaran = self.env.user.company_id.tahun_ajaran_aktif.id
            kamar = self.env['cdn.kamar_santri'].search([
                ('musyrif_id', '=', musyrif_id),
                ('fiscalyear_id', '=', tahun_ajaran)
            ], limit=1)
            if kamar:
                kamar_id = kamar.id
                res['kamar_id'] = kamar_id

        if tgl_awal and tgl_akhir:
            lines = self._build_rekap_lines(musyrif_id, kamar_id, tgl_awal, tgl_akhir)
            res['rekap_line_ids'] = lines

        return res

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
            rec.jml_keluar = len(rec.rekap_line_ids.filtered(
                lambda x: x.kehadiran == 'keluar'))

    @api.onchange('musyrif_id')
    def _onchange_musyrif_id(self):
        """Auto set kamar pertama dari musyrif yang dipilih dan filter domain dropdown kamar."""
        tahun_ajaran = self.env.user.company_id.tahun_ajaran_aktif.id
        if self.musyrif_id:
            kamars = self.env['cdn.kamar_santri'].search([
                ('fiscalyear_id', '=', tahun_ajaran),
                '|',
                ('musyrif_id', '=', self.musyrif_id.id),
                ('pengganti_ids', 'in', [self.musyrif_id.id])
            ])
            first_kamar = kamars[0].id if kamars else False
            self.kamar_id = first_kamar

            if self.tgl_awal and self.tgl_akhir:
                lines = self._build_rekap_lines(self.musyrif_id.id, first_kamar, self.tgl_awal, self.tgl_akhir)
                self.rekap_line_ids = [(5, 0, 0)] + lines

            return {
                'domain': {'kamar_id': [('id', 'in', kamars.ids)]}
            }
        else:
            self.kamar_id = False
            if self.tgl_awal and self.tgl_akhir:
                lines = self._build_rekap_lines(False, False, self.tgl_awal, self.tgl_akhir)
                self.rekap_line_ids = [(5, 0, 0)] + lines

            return {
                'domain': {'kamar_id': [('fiscalyear_id', '=', tahun_ajaran)]}
            }

    @api.onchange('musyrif_id', 'kamar_id', 'tgl_awal', 'tgl_akhir')
    def _onchange_rekap_params(self):
        if not (self.tgl_awal and self.tgl_akhir):
            self.rekap_line_ids = [(5, 0, 0)]
            return

        if self.tgl_awal > self.tgl_akhir:
            return

        musyrif_id = self.musyrif_id.id if self.musyrif_id else False
        kamar_id = self.kamar_id.id if self.kamar_id else False

        lines = self._build_rekap_lines(musyrif_id, kamar_id, self.tgl_awal, self.tgl_akhir)
        self.rekap_line_ids = [(5, 0, 0)] + lines

    def _build_rekap_lines(self, musyrif_id, kamar_id, tgl_awal, tgl_akhir):
        if not (kamar_id or musyrif_id):
            return []

        domain = [
            ('tanggal', '>=', tgl_awal),
            ('tanggal', '<=', tgl_akhir)
        ]

        if kamar_id:
            domain.extend(['|', ('kamar_id', '=', kamar_id), ('absen_id.kamar_id', '=', kamar_id)])
        elif musyrif_id:
            kamar_ids = self.env['cdn.kamar_santri'].search([
                ('fiscalyear_id', '=', self.env.user.company_id.tahun_ajaran_aktif.id),
                '|',
                ('musyrif_id', '=', musyrif_id),
                ('pengganti_ids', 'in', [musyrif_id])
            ]).ids
            if kamar_ids:
                domain.extend(['|', ('kamar_id', 'in', kamar_ids), ('absen_id.kamar_id', 'in', kamar_ids)])
            else:
                return []

        malam_lines = self.env['cdn.absensi_malam_line'].search(
            domain, order='tanggal desc, kamar_id asc, name asc')

        lines = []
        no = 1
        if malam_lines:
            for line in malam_lines:
                lines.append((0, 0, {
                    'no': no,
                    'tanggal': line.tanggal,
                    'kamar_id': line.kamar_id.id if line.kamar_id else (line.absen_id.kamar_id.id if line.absen_id else False),
                    'siswa_id': line.siswa_id.id if line.siswa_id else False,
                    'nis': line.nis or '',
                    'nama': line.name or '',
                    'kehadiran': line.kehadiran_absen or 'Hadir',
                    'keterangan': line.keterangan or ''
                }))
                no += 1
        else:
            # Fallback jika belum ada data absensi: daftar santri di kamar/musyrif tersebut
            santri_list = self.env['cdn.siswa']
            if kamar_id:
                kamar_rec = self.env['cdn.kamar_santri'].browse(kamar_id)
                santri_list = kamar_rec.siswa_ids
            elif musyrif_id:
                kamar_recs = self.env['cdn.kamar_santri'].search([('musyrif_id', '=', musyrif_id)])
                santri_list = kamar_recs.mapped('siswa_ids')

            for santri in santri_list.sorted(key=lambda s: s.name or ''):
                lines.append((0, 0, {
                    'no': no,
                    'tanggal': tgl_akhir,
                    'kamar_id': santri.kamar_id.id if santri.kamar_id else kamar_id,
                    'siswa_id': santri.id,
                    'nis': santri.nis or '',
                    'nama': santri.name or '',
                    'kehadiran': False,
                    'keterangan': 'Belum Diabsen'
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

        writer.writerow(['REKAP ABSENSI MALAM SANTRI'])
        writer.writerow([self.env.user.company_id.name or ''])
        writer.writerow([f'Musyrif: {self.musyrif_id.name or "Semua"}'])
        writer.writerow([f'Kamar: {self.kamar_id.display_name or "Semua"}'])
        writer.writerow([f'Periode: {self.tgl_awal} s/d {self.tgl_akhir}'])
        writer.writerow([])

        headers = ['No', 'Tanggal', 'Kamar', 'NIS', 'Nama Santri', 'Kehadiran', 'Keterangan']
        writer.writerow(headers)

        for line in self.rekap_line_ids:
            writer.writerow([
                line.no, line.tanggal,
                line.kamar_id.display_name if line.kamar_id else '-',
                line.nis or '-', line.nama or '-',
                dict(line._fields['kehadiran'].selection).get(line.kehadiran, line.kehadiran) if line.kehadiran else '-',
                line.keterangan or '-'
            ])

        writer.writerow([])
        writer.writerow(['Ringkasan Kehadiran'])
        writer.writerow(['Hadir', self.jml_hadir])
        writer.writerow(['Izin', self.jml_izin])
        writer.writerow(['Sakit', self.jml_sakit])
        writer.writerow(['Alpa', self.jml_alpa])
        writer.writerow(['Izin Keluar', self.jml_keluar])

        csv_data = output.getvalue().encode('utf-8')
        kamar_str = self.kamar_id.display_name if self.kamar_id else 'Semua'
        file_name = f"Rekap_Absensi_Malam_{kamar_str}_{self.tgl_awal}_sd_{self.tgl_akhir}.csv"

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
        sheet = workbook.add_worksheet('Rekap Absensi Malam')

        # Formats
        title_format = workbook.add_format({
            'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter'
        })
        subtitle_format = workbook.add_format({
            'bold': True, 'font_size': 12, 'align': 'center', 'valign': 'vcenter'
        })
        info_bold_format = workbook.add_format({'font_size': 11, 'bold': True})
        info_format = workbook.add_format({'font_size': 11})

        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#203764', 'font_color': 'white',
            'border': 1, 'align': 'center', 'valign': 'vcenter'
        })
        cell_border = workbook.add_format({'border': 1, 'valign': 'vcenter'})
        cell_center = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy', 'border': 1, 'align': 'center', 'valign': 'vcenter'})

        # Column widths
        sheet.set_column(0, 0, 5)    # No
        sheet.set_column(1, 1, 14)   # Tanggal
        sheet.set_column(2, 2, 22)   # Kamar
        sheet.set_column(3, 3, 14)   # NIS
        sheet.set_column(4, 4, 25)   # Nama
        sheet.set_column(5, 5, 14)   # Kehadiran
        sheet.set_column(6, 6, 25)   # Keterangan

        company_name = self.env.user.company_id.name or ''

        # Header Info
        row = 0
        sheet.merge_range(row, 0, row, 6, 'LAPORAN REKAP ABSENSI MALAM SANTRI', title_format)
        row += 1
        sheet.merge_range(row, 0, row, 6, company_name, subtitle_format)
        row += 2

        sheet.write(row, 0, 'MUSYRIF / PEMBINA', info_bold_format)
        sheet.merge_range(row, 1, row, 3, f': {self.musyrif_id.name if self.musyrif_id else "Semua Musyrif"}', info_format)
        row += 1
        sheet.write(row, 0, 'KAMAR', info_bold_format)
        sheet.merge_range(row, 1, row, 3, f': {self.kamar_id.display_name if self.kamar_id else "Semua Kamar"}', info_format)
        row += 1
        sheet.write(row, 0, 'PERIODE', info_bold_format)
        sheet.merge_range(row, 1, row, 3, f': {self.tgl_awal} s/d {self.tgl_akhir}', info_format)
        row += 2

        # Table Header
        headers = ['No', 'Tanggal', 'Kamar', 'NIS', 'Nama Santri', 'Kehadiran', 'Keterangan']
        for col, h in enumerate(headers):
            sheet.write(row, col, h, header_format)
        sheet.set_row(row, 25)
        row += 1

        # Table Data
        for line in self.rekap_line_ids:
            sheet.write(row, 0, line.no, cell_center)
            sheet.write(row, 1, line.tanggal, date_format)
            sheet.write(row, 2, line.kamar_id.display_name if line.kamar_id else '-', cell_border)
            sheet.write(row, 3, line.nis or '-', cell_center)
            sheet.write(row, 4, line.nama or '-', cell_border)
            keh_label = dict(line._fields['kehadiran'].selection).get(line.kehadiran, line.kehadiran) if line.kehadiran else '-'
            sheet.write(row, 5, keh_label, cell_center)
            sheet.write(row, 6, line.keterangan or '-', cell_border)
            row += 1

        # Summary Table
        row += 2
        sheet.merge_range(row, 0, row, 2, 'Ringkasan Kehadiran:', info_bold_format)
        row += 1

        summary_headers = ['Status Kehadiran', 'Jumlah']
        sheet.write(row, 0, summary_headers[0], header_format)
        sheet.write(row, 1, summary_headers[1], header_format)
        row += 1

        summary_data = [
            ('Hadir', self.jml_hadir),
            ('Izin', self.jml_izin),
            ('Sakit', self.jml_sakit),
            ('Alpa', self.jml_alpa),
            ('Izin Keluar', self.jml_keluar),
        ]
        for label, val in summary_data:
            sheet.write(row, 0, label, cell_border)
            sheet.write(row, 1, val, cell_center)
            row += 1

        # Signatures
        row += 3
        today = date.today()
        sheet.merge_range(row, 0, row, 2, 'Mengetahui,', cell_center)
        sheet.merge_range(row, 4, row, 6, f'Tanggal: {today.strftime("%d/%m/%Y")}', cell_center)
        row += 1
        sheet.merge_range(row, 0, row, 2, 'Kepala Pengasuhan / Kesantrian', cell_center)
        sheet.merge_range(row, 4, row, 6, 'Musyrif Pembina', cell_center)
        row += 4
        sheet.merge_range(row, 0, row, 2, '(______________________________)', cell_center)
        sheet.merge_range(row, 4, row, 6, f'({self.musyrif_id.name if self.musyrif_id else "______________________________"})', cell_center)

        workbook.close()
        output.seek(0)
        xlsx_data = output.read()

        kamar_str = self.kamar_id.display_name if self.kamar_id else 'Semua'
        file_name = f"Rekap_Absensi_Malam_{kamar_str}_{self.tgl_awal}_sd_{self.tgl_akhir}.xlsx"

        self.write({
            'data_file': base64.b64encode(xlsx_data),
            'file_name': file_name
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model={self._name}&id={self.id}&field=data_file&download=true&filename={self.file_name}',
            'target': 'self',
        }


class WizardRekapAbsensiMalamLine(models.TransientModel):
    _name = 'cdn.wizard_rekap_absensi_malam_line'
    _description = 'Line Rekap Absensi Malam'

    wizard_id = fields.Many2one(
        'cdn.wizard_rekap_absensi_malam', string='Wizard', ondelete='cascade')
    no = fields.Integer(string='No')
    tanggal = fields.Date(string='Tanggal')
    kamar_id = fields.Many2one('cdn.kamar_santri', string='Kamar')
    siswa_id = fields.Many2one('cdn.siswa', string='Santri')
    nis = fields.Char(string='NIS')
    nama = fields.Char(string='Nama Santri')
    kehadiran = fields.Selection([
        ('Hadir', 'Hadir'),
        ('Izin', 'Izin'),
        ('keluar', 'Izin Keluar'),
        ('Sakit', 'Sakit'),
        ('Alpa', 'Alpa'),
    ], string='Kehadiran')
    keterangan = fields.Char(string='Keterangan')
