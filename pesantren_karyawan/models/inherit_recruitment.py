from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from odoo.tools import format_date
import uuid
import pytz
import random
import string
import logging

class inheritRecruitment(models.Model):
    _inherit            = ['hr.candidate']
    _description        = 'Inherit Karyawan'

    tgl_pendaftaran     = fields.Date(string='Tanggal Pendaftaran', default=fields.Date.context_today, store=True)

    token               = fields.Char(string="Token", store=True)

    # kiri

    # kanan
    lembaga             = fields.Selection([
                            ('paud','PAUD'),
                            ('tk','TK'),
                            ('sdmi','SD / MI'),
                            ('smpmts','SMP / MTS'),
                            ('smama','SMA / MA'),
                            ('smk','SMK')], 
                        string='Lembaga')
    job_id              = fields.Many2one('hr.job', string="Jabatan Kerja", store=True)

    # Data Diri
    no_ktp              = fields.Char(string="No KTP", store=True)
    tgl_lahir           = fields.Date(string="Tanggal Lahir", store=True)
    tmp_lahir           = fields.Char(string="Tempat Lahir", store=True)
    gender              = fields.Selection(selection=[
                            ('L','Laki-laki'),('P','Perempuan')],
                            string="Jenis Kelamin",  help="", store=True)
    alamat              = fields.Text(string="Alamat", store=True)

    # Dokumen
    cv                  = fields.Binary(string="CV", help="CV mencakup:Identitas pribadi nama, alamat, nomor telepon, email. Pengalaman kerja sebelumnya. Pendidikan terakhir. Keterampilan yang relevan dengan pekerjaan yang dilamar. Sertifikat atau penghargaan jika ada", store=True)
    ktp                 = fields.Binary(string="Foto KTP", help="Untuk memverifikasi identitas Anda. Pastikan fotokopi identitas masih berlaku dan jelas.", store=True)
    pas_foto            = fields.Binary(string="Pas Foto Berwarna", help="Biasanya ukuran pas foto standar (3x4 cm atau 4x6 cm), sering kali diminta dalam format digital.", store=True)
    ijazah              = fields.Binary(string="Ijazah", help="Fotokopi atau dari ijazah pendidikan terakhir Anda.", store=True)
    sertifikat          = fields.Binary(string="Sertifikat/Dokumen Pendukung", help="Sertifikat pelatihan, kursus, atau keterampilan lainnya yang relevan dengan pekerjaan. Misalnya sertifikat bahasa asing, pelatihan teknis, atau sertifikat keterampilan lain. Opsional(Jika Ada)", store=True)
    surat_pengalaman    = fields.Binary(string="Surat Pengalaman Kerja", help="Jika Anda sudah memiliki pengalaman kerja sebelumnya, Anda mungkin perlu mengunggah surat pengalaman kerja dari perusahaan sebelumnya. Surat ini biasanya mencakup durasi kerja, jabatan, dan deskripsi pekerjaan. Opsional(Jika Ada)", store=True)
    surat_kesehatan     = fields.Binary(string="Surat Keterangan Sehat", help="Dokumen terkait kesehatan, seperti surat keterangan sehat dari dokter atau hasil pemeriksaan medis. Opsional(Jika Ada)", store=True)
    npwp                = fields.Binary(string="NPWP", help="Salinan NPWP Anda untuk keperluan administrasi perpajakan.", store=True)
    
    def get_formatted_tanggal_lahir(self):
        if self.tgl_lahir:
            # Langsung gunakan strftime untuk format DD-MM-YYYY
            return self.tgl_lahir.strftime('%d-%m-%Y')
        return 'Tanggal tidak tersedia'
    
    @api.model
    def create(self, vals):
        # Generate UUID token
        vals['token'] = str(uuid.uuid4())

        record =  super(inheritRecruitment, self).create(vals)
        return record
    
    def create_employee_from_candidate(self):
        self.ensure_one()
        self._check_interviewer_access()

        if not self.partner_id:
            if not self.partner_name:
                raise UserError(_('Please provide an candidate name.'))

            self.partner_id = self.env['res.partner'].create({
                'is_company': False,
                'name': self.partner_name,
                'email': self.email_from,
            })

        action = self.env['ir.actions.act_window']._for_xml_id('hr.open_view_employee_list')
        employee = self.env['hr.employee'].create(self._get_employee_create_vals())
        employee.user_id.write({
            'phone': self.partner_phone,
            'mobile': self.partner_phone,
        })
        action['res_id'] = employee.id
        return action

    def _get_employee_create_vals(self):
        self.ensure_one()
        address_id   = self.partner_id.address_get(['contact'])['contact']
        address_sudo = self.env['res.partner'].sudo().browse(address_id)
        return {
            'name'                  : self.partner_name or self.partner_id.display_name,
            'work_contact_id'       : self.partner_id.id,
            'private_street'        : address_sudo.street,
            'private_street2'       : address_sudo.street2,
            'private_city'          : address_sudo.city,
            'private_state_id'      : address_sudo.state_id.id,
            'private_zip'           : address_sudo.zip,
            'private_country_id'    : address_sudo.country_id.id,
            'private_phone'         : address_sudo.phone,
            'private_email'         : address_sudo.email,
            'lang'                  : address_sudo.lang,
            'address_id'            : self.company_id.partner_id.id,
            'phone'                 : self.partner_phone,
            'candidate_id'          : self.ids,
            'work_email'            : self.email_from,
            'lembaga'               : self.lembaga,
            'no_ktp'                : self.no_ktp,
            'job_id'                : int(self.job_id),
            'tgl_lahir'             : self.tgl_lahir,
            'tmp_lahir'             : self.tmp_lahir,
            'jk'                    : self.gender,
            'alamat'                : self.alamat,
            'cv'                    : self.cv,
            'ktp'                   : self.ktp,
            'pas_foto'              : self.pas_foto,
            'ijazah'                : self.ijazah,
            'sertifikat'            : self.sertifikat,
            'surat_pengalaman'      : self.surat_pengalaman,
            'surat_kesehatan'       : self.surat_kesehatan,
            'npwp'                  : self.npwp
        }




        # email_values = {
        #         'subject': "Informasi Login Sistem Pesantren Daarul Qur'an Istiqomah",
        #         'email_to': pendaftaran.email,
        #         'body_html': f'''
        #             <div style="background-color: #d9eaf7; padding: 20px; font-family: Arial, sans-serif;">
        #                 <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden;">
        #                     <!-- Header -->
        #                     <div style="background-color: #0066cc; color: #ffffff; text-align: center; padding: 20px;">
        #                         <h1 style="margin: 0; font-size: 24px;">Pesantren Daarul Qur'an Istiqomah</h1>
        #                     </div>
        #                     <!-- Body -->
        #                     <div style="padding: 20px; color: #555555;">
        #                         <p style="margin: 0 0 10px;">Assalamualaikum Wr. Wb,</p>
        #                         <p style="margin: 0 0 20px;">
        #                             Bapak/Ibu <strong>{pendaftaran.wali_nama or pendaftaran.nama_ayah or pendaftaran.nama_ibu}</strong>,<br>
        #                             Akun Login telah dibuat di sistem pesantren kami. Berikut adalah informasi login Anda:
        #                         </p>
        #                         <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
        #                             <h3>Akun Login</h3>
        #                             <table style="width: 100%; border-collapse: collapse;">
        #                                 <tr>
        #                                     <td style="padding: 8px; font-weight: bold; color: #333333;">Email :</td>
        #                                     <td style="padding: 8px; color: #555555;">{pendaftaran.email}</td>
        #                                 </tr>
        #                                 <tr>
        #                                     <td style="padding: 8px; font-weight: bold; color: #333333;">Kata Sandi :</td>
        #                                     <td style="padding: 8px; color: #555555;">{masked_password}</td>
        #                                 </tr>
        #                             </table>

        #                             <h3>Data Pendaftaran</h3>
        #                             <table style="width: 100%; border-collapse: collapse;">
        #                                 <tr>
        #                                     <td style="padding: 8px; font-weight: bold; color: #333333;">Nama :</td>
        #                                     <td style="padding: 8px; color: #555555;">{pendaftaran.partner_id.name}</td>
        #                                 </tr>
        #                                 <tr>
        #                                     <td style="padding: 8px; font-weight: bold; color: #333333;">TTL :</td>
        #                                     <td style="padding: 8px; color: #555555;">{pendaftaran.kota_lahir}, {pendaftaran.get_formatted_tanggal_lahir()}</td>
        #                                 </tr>
        #                                 <tr>
        #                                     <td style="padding: 8px; font-weight: bold; color: #333333;">Alamat :</td>
        #                                     <td style="padding: 8px; color: #555555;">{pendaftaran.alamat}</td>
        #                                 </tr>
        #                                 <tr>
        #                                     <td style="padding: 8px; font-weight: bold; color: #333333;">NIK :</td>
        #                                     <td style="padding: 8px; color: #555555;">{pendaftaran.nik}</td>
        #                                 </tr>
        #                             </table>

        #                             <h3>Jenjang Pendidikan Yang Dipilih</h3>
        #                             <table style="width: 100%; border-collapse: collapse;">
        #                                 <tr>
        #                                     <td style="padding: 8px; font-weight: bold; color: #333333;">Jenjang :</td>
        #                                     <td style="padding: 8px; color: #555555;">{pendaftaran.jenjang_id.name}</td>
        #                                 </tr>
        #                             </table>

        #                             <h3>Informasi Pembayaran</h3>
        #                             <table style="width: 100%; border-collapse: collapse;">
        #                                 <tr>
        #                                     <td style="padding: 8px; font-weight: bold; color: #333333;">Bank :</td>
        #                                     <td style="padding: 8px; color: #555555;">BSI</td>
        #                                 </tr>
        #                                 <tr>
        #                                     <td style="padding: 8px; font-weight: bold; color: #333333;">Nomor Rekening :</td>
        #                                     <td style="padding: 8px; color: #555555;">{no_rekening}</td>
        #                                 </tr>
        #                                 <tr>
        #                                     <td style="padding: 8px; font-weight: bold; color: #333333;">Sejumlah :</td>
        #                                     <td style="padding: 8px; color: #555555;">{biaya_formatted}</td>
        #                                 </tr>
        #                             </table>

        #                         </div>
        #                         <p style="text-align: center;">
        #                             <a href="https://aplikasi.dqi.ac.id/login" style="background-color: #0066cc; color: #ffffff; padding: 10px 20px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">
        #                                 Masuk Ke Akun Anda
        #                             </a>
        #                         </p>
        #                         <p style="margin: 20px 0;">
        #                             Apabila terdapat kesulitan atau membutuhkan bantuan, silakan hubungi tim teknis kami melalui nomor:
        #                         </p>
        #                         <ul style="margin: 0; padding-left: 20px; color: #555555;">
        #                             <li>0822 5207 9785</li>
        #                             <li>0853 9051 1124</li>
        #                         </ul>
        #                         <p style="margin: 20px 0;">
        #                             Kami berharap portal ini dapat membantu Bapak/Ibu memantau perkembangan putra/putri selama berada di pesantren.
        #                         </p>
        #                     </div>
        #                     <!-- Footer -->
        #                     <div style="background-color: #f1f1f1; text-align: center; padding: 10px;">
        #                         <p style="font-size: 12px; color: #888888; margin: 0;">
        #                             &copy; {thn_sekarang} Pesantren Tahfizh Daarul Qur'an Istiqomah. All rights reserved.
        #                         </p>
        #                     </div>
        #                 </div>
        #             </div>
        #         ''',
        #     }

        #     mail = request.env['mail.mail'].sudo().create(email_values)
        #     mail.send()
    
    # def get_formatted_tanggal_lahir(self):
    #     if self.tgl_lahir:
    #         # Langsung gunakan strftime untuk format DD-MM-YYYY
    #         return self.tgl_lahir.strftime('%d-%m-%Y')
    #     return 'Tanggal tidak tersedia'