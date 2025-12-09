from odoo import api, fields, models
from odoo.exceptions import UserError


class hr_employee(models.Model):
    _inherit = 'hr.employee'
    _order   = 'name asc'

    nip = fields.Char('NIP')
    lembaga = fields.Selection([ ('paud','PAUD'),
                        ('tk','TK'),
                        ('sdmi','SD / MI'),
                        ('smpmts','SMP / MTS'),
                        ('smama','SMA / MA'),
                        ('smk','SMK'),
                        ('nonformal', 'Non Formal'),
                        ('pondokputra', 'Pondok Putra'),
                        ('pondokputri', 'Pondok Putri'),
                        ('rtq', 'RTQ')], string='Lembaga', default='smama')
    pendidikan_guru_ids = fields.One2many(comodel_name="edu.employee", inverse_name="employee_id", string="Riwayat Pendidikan", help="")
    marital = fields.Selection(string='Status Pernikahan', selection=[('single', 'Belum Kawin'), ('married', 'Menikah'), ('divorced', 'Cerai Hidup'), ('cerai', 'Cerai Mati')])
    jns_pegawai = fields.Selection([
        ('musyrif', 'Musyrif'),
        # ('ustadz', 'Ustadz'),
        ('guru', 'Guru Akademik'),   
        ("guruquran", "Guru Qur'an"),
        ("guru,guruquran", "Guru Akademik & Guru Qur'an"),
        ("musyrif,guru", "Musyrif & Guru Akademik"),
        ("musyrif,guruquran", "Musyrif & Guru Qur'an"),
        ("musyrif,guru,guruquran", "Musyrif & Guru Akademik & Guru Qur'an"),
        ('keamanan', 'Keamanan'),
        ('superadmin', 'Super Admin'),
        # ('kesehatan', 'Kesehatan'),
        # ('kasrama', 'Kepala Asrama')
    ], string='Jenis Pegawai')
    mata_pelajaran_ids = fields.Many2many(comodel_name="cdn.mata_pelajaran", string="Mata Pelajaran", help="")
    password = fields.Char(
        string='Password',
        help="Kosongkan jika ingin pakai otomatis dari NIP",
        store=True,
    )

    @api.onchange('nip')
    def _onchange_password(self):
        for record in self:
            if record.nip and len(record.nip) >= 6:
                record.password = record.nip[:6]
            else:
                record.password = ''
    
# args=None
    # def activate_account(self):
    #     # Mengambil email dan jenis pegawai langsung dari instance hr.employee
    #     if not self.work_email:
    #         raise UserError("Email tidak ditemukan di data karyawan.")
    #     if not self.password or not self.name:
    #         raise UserError("Password atau Nama karyawan belum diisi.")
        
    #     # Cari user berdasarkan email dari work_email
    #     user = self.env['res.users'].search([('login', '=', self.work_email)], limit=1)
        
    #     if not user:
    #         raise UserError(f"User dengan email {self.work_email} tidak ditemukan.")

    #     user.groups_id = [(5, 0, 0)]  # Menghapus semua grup yang sudah ada

    #     # Menentukan group yang sesuai berdasarkan jenis pegawai
    #     groups_to_add = []
    #     groups_to_add.append(self.env.ref('base.group_user'))
    #     if self.jns_pegawai == 'superadmin':
    #         groups_to_add.append(self.env.ref('base.group_system'))
    #         groups_to_add.append(self.env.ref('hr.group_hr_manager'))
    #         groups_to_add.append(self.env.ref('hr_attendance.group_hr_attendance_officer'))
    #         groups_to_add.append(self.env.ref('pesantren_pendaftaran.group_pendaftaran_manager'))
    #         groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_manager'))
    #         groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_manager'))
    #         groups_to_add.append(self.env.ref('pesantren_guru.group_guru_manager'))
    #         groups_to_add.append(self.env.ref('pesantren_guruquran.group_guru_quran_manager'))
    #         groups_to_add.append(self.env.ref('pesantren_musyrif.group_musyrif_manager'))
    #         groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_kesehatan'))
    #         groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_keamanan'))
    #         # Hak akses Akuntansi Administrator
    #         groups_to_add.append(self.env.ref('account.group_account_manager'))
    #         # Hak Akses Pembuatan Kontak
    #         groups_to_add.append(self.env.ref('base.group_partner_manager'))
    #         # Hak Akses Export Data
    #         groups_to_add.append(self.env.ref('base.group_allow_export'))
    #     elif self.jns_pegawai == 'guruquran':
    #         # groups_to_add.append(self.env.ref('pesantren_guruquran.group_guru_quran_manager')) 
    #         # groups_to_add.append(self.env.ref('pesantren_guruquran.group_guru_quran_manager')) 
    #         groups_to_add.append(self.env.ref('pesantren_guruquran.group_guru_quran_staff')) 
    #         # groups_to_add.append(self.env.ref('pesantren_guruquran.group_guru_quran_user')) 
    #         # groups_to_add.append(self.env.ref('pesantren_guru.group_guru_manager')) 
    #         groups_to_add.append(self.env.ref('pesantren_guru.group_guru_user')) 
    #         # groups_to_add.append(self.env.ref('pesantren_guru.group_guru_staff')) 
            
    #         groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_user')) 
    #         groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_user')) 
    #         # groups_to_add.append(self.env.ref('hr.group_hr_manager')) # Menambahkan grup HR User # groups_to_add.append(self.env.ref('hr_attendance.group_hr_attendance_officer')) # Menambahkan grup Absensi
    #         groups_to_add.append(self.env.ref('pesantren_base.group_hr_employee_readonly'))
    #         groups_to_add.append(self.env.ref('base.group_allow_export'))
    #     elif self.jns_pegawai == 'guru':
    #         # groups_to_add.append(self.env.ref('pesantren_guru.group_guru_manager'))
    #         groups_to_add.append(self.env.ref('pesantren_guru.group_guru_staff'))
    #         groups_to_add.append(self.env.ref('pesantren_guruquran.group_guru_quran_user'))
    #         # groups_to_add.append(self.env.ref('pesantren_guru.group_guru_user'))
    #         # groups_to_add.append(self.env.ref('pesantren_guruquran.group_guru_quran_manager'))

    #         groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_user'))
    #         groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_user'))
    #         # groups_to_add.append(self.env.ref('hr.group_hr_manager'))
    #         groups_to_add.append(self.env.ref('pesantren_base.group_hr_employee_readonly'))
    #         # groups_to_add.append(self.env.ref('hr_attendance.group_hr_attendance_officer'))
    #         groups_to_add.append(self.env.ref('base.group_allow_export'))
    #     # elif self.jns_pegawai in ['musyrif', 'ustadz']:
    #     elif self.jns_pegawai == 'guru,guruquran':
    #         groups_to_add.append(self.env.ref('pesantren_guru.group_guru_staff'))
    #         groups_to_add.append(self.env.ref('pesantren_guruquran.group_guru_quran_staff'))

    #         groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_user')) 
    #         groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_user')) 
    #         # groups_to_add.append(self.env.ref('hr.group_hr_manager')) # Menambahkan grup HR Use
    #         groups_to_add.append(self.env.ref('pesantren_base.group_hr_employee_readonly'))
    #         groups_to_add.append(self.env.ref('base.group_allow_export'))
    #     elif self.jns_pegawai == 'musyrif,guru':
    #         groups_to_add.append(self.env.ref('pesantren_musyrif.group_musyrif_staff'))
    #         groups_to_add.append(self.env.ref('pesantren_guru.group_guru_staff'))
    #         groups_to_add.append(self.env.ref('pesantren_guruquran.group_guru_quran_user'))

    #         groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_user')) 
    #         groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_user')) 
    #         # groups_to_add.append(self.env.ref('hr.group_hr_manager')) # Menambahkan grup HR User # groups_to_add.append(self.env.ref('hr_attendance.group_hr_attendance_officer')) # Menambahkan grup Absensi
    #         groups_to_add.append(self.env.ref('pesantren_base.group_hr_employee_readonly'))
    #         groups_to_add.append(self.env.ref('base.group_allow_export'))
    #     elif self.jns_pegawai == 'musyrif,guruquran':
    #         groups_to_add.append(self.env.ref('pesantren_musyrif.group_musyrif_staff'))
    #         groups_to_add.append(self.env.ref('pesantren_guruquran.group_guru_quran_staff'))
    #         groups_to_add.append(self.env.ref('pesantren_guru.group_guru_user')) 

    #         groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_user')) 
    #         groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_user')) 
    #         # groups_to_add.append(self.env.ref('hr.group_hr_manager')) # Menambahkan grup HR User # groups_to_add.append(self.env.ref('hr_attendance.group_hr_attendance_officer')) # Menambahkan grup Absensi
    #         groups_to_add.append(self.env.ref('pesantren_base.group_hr_employee_readonly'))
    #         groups_to_add.append(self.env.ref('base.group_allow_export'))
    #     elif self.jns_pegawai == 'musyrif,guru,guruquran':
    #         groups_to_add.append(self.env.ref('pesantren_musyrif.group_musyrif_staff'))
    #         groups_to_add.append(self.env.ref('pesantren_guru.group_guru_staff'))
    #         groups_to_add.append(self.env.ref('pesantren_guruquran.group_guru_quran_staff'))

    #         groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_user')) 
    #         groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_user')) 
    #         # groups_to_add.append(self.env.ref('hr.group_hr_manager')) # Menambahkan grup HR User # groups_to_add.append(self.env.ref('hr_attendance.group_hr_attendance_officer')) # Menambahkan grup Absensi
    #         groups_to_add.append(self.env.ref('pesantren_base.group_hr_employee_readonly'))
    #         groups_to_add.append(self.env.ref('base.group_allow_export'))
    #     elif self.jns_pegawai == 'musyrif':
    #         groups_to_add.append(self.env.ref('pesantren_musyrif.group_musyrif_staff'))

    #         groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_user'))
    #         groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_user'))
    #         # groups_to_add.append(self.env.ref('hr.group_hr_manager'))
    #         groups_to_add.append(self.env.ref('pesantren_base.group_hr_employee_readonly'))
    #         # groups_to_add.append(self.env.ref('hr_attendance.group_hr_attendance_officer'))
    #         groups_to_add.append(self.env.ref('base.group_allow_export'))
    #     elif self.jns_pegawai == 'keamanan':
    #         groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_keamanan'))
    #         groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_user'))
    #         groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_user'))
    #         groups_to_add.append(self.env.ref('pesantren_base.group_hr_employee_readonly'))
    #         groups_to_add.append(self.env.ref('base.group_allow_export'))
    #     else:
    #         groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_user'))
    #         groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_user'))
    #         groups_to_add.append(self.env.ref('pesantren_base.group_hr_employee_readonly'))
    #         groups_to_add.append(self.env.ref('base.group_allow_export'))

    #     if not groups_to_add:
    #         raise UserError("Jenis pegawai tidak terdaftar untuk penambahan group.")
        
    #     # Menambahkan semua grup yang diperlukan ke user
    #     for group in groups_to_add:
    #         if group not in user.groups_id:
    #             user.groups_id = [(4, group.id)]

    #     # Atur ulang password user dengan format name-nip
    #     new_password = f"{self.password}"  # Gunakan 4 digit pertama NIP
    #     masked_password = new_password[:2] + '*' * (len(new_password) - 4) + new_password[-2:]

    #     user.write({'password': new_password})

    #     email_values = { 
    #                 'subject': "Akun Diaktifkan", 
    #                 'email_to': self.work_email, 
    #                 'body_html': f''' 
    #                     <div style="background-color: #f0f8ff; padding: 20px; font-family: Arial, sans-serif;"> 
    #                         <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);"> 
    #                             <!-- Header --> 
    #                             <div style="background-color: #0078d7; color: #ffffff; text-align: center; padding: 25px;"> 
    #                                 <h1 style="margin: 0; font-size: 26px;">Aktivasi Akun Anda</h1> 
    #                             </div> 
    #                             <!-- Body --> 
    #                             <div style="padding: 20px; color: #333333;"> 
    #                                 <p style="margin: 0 0 10px; font-size: 16px;">Assalamualaikum Wr. Wb,</p> 
    #                                 <p style="margin: 0 0 20px; font-size: 16px;"> 
    #                                     Selamat, akun Anda telah berhasil diaktifkan! Berikut adalah informasi akun Anda: 
    #                                 </p> 
    #                                 <div style="background-color: #f9f9f9; padding: 20px; border-radius: 8px; margin: 20px 0;"> 
    #                                     <table style="width: 100%; border-collapse: collapse;"> 
    #                                         <tr> 
    #                                             <td style="padding: 10px; font-weight: bold; color: #555555;">Email :</td> 
    #                                             <td style="padding: 10px; color: #555555;">{self.work_email}</td> 
    #                                         </tr> 
    #                                         <tr> 
    #                                             <td style="padding: 10px; font-weight: bold; color: #555555;">Kata Sandi :</td> 
    #                                             <td style="padding: 10px; color: #555555;">{masked_password}</td> 
    #                                         </tr> 
    #                                         <tr> 
    #                                             <td style="padding: 10px; font-weight: bold; color: #555555;">Jenis Akun :</td> 
    #                                             <td style="padding: 10px; color: #555555;">{self.jns_pegawai}</td> 
    #                                         </tr> 
    #                                         <tr> 
    #                                             <td style="padding: 10px; font-weight: bold; color: #555555;">Tanggal Aktivasi :</td> 
    #                                             <td style="padding: 10px; color: #555555;">{fields.Datetime.now()}</td> 
    #                                         </tr> 
    #                                     </table> 
    #                                 </div> 
    #                                 <p style="text-align: center;"> 
    #                                     <a href="https://aplikasi.dqi.ac.id/login" style="background-color: #0078d7; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block; font-size: 16px;"> 
    #                                         Masuk Ke Akun Anda 
    #                                     </a> 
    #                                 </p> 
    #                                 <p style="margin: 20px 0; font-size: 14px;"> 
    #                                     Apabila Anda mengalami kendala, silakan hubungi tim teknis kami melalui nomor berikut: 
    #                                 </p> 
    #                                 <ul style="margin: 0; padding-left: 20px; color: #555555; font-size: 14px;"> 
    #                                     <li>0822 5207 9785</li> 
    #                                 </ul> 
    #                                 <p style="margin: 20px 0; font-size: 14px;"> 
    #                                     Terima kasih telah menggunakan layanan kami. Kami berharap akun ini dapat membantu Anda dalam menjalankan aktivitas di pesantren. 
    #                                 </p> 
    #                             </div> 
    #                             <!-- Footer --> 
    #                             <div style="background-color: #f1f1f1; text-align: center; padding: 15px; border-top: 1px solid #dddddd;"> 
    #                                 <p style="font-size: 12px; color: #888888; margin: 0;"> 
    #                                     &copy; 2024 Pesantren Tahfizh Daarul Qur'an Istiqomah. All rights reserved. 
    #                                 </p> 
    #                             </div> 
    #                         </div> 
    #                     </div> 
    #                 ''' 
    #             }

    #     mail = self.env['mail.mail'].sudo().create(email_values)
    #     mail.send()
        
    #     # tampilkan notifikasi dulu
    #     self.env['bus.bus']._sendone(
    #         self.env.user.partner_id, 
    #         'simple_notification', 
    #         {
    #             'title': 'Aktivasi Akun Berhasil', 
    #             'message': f'Akun {self.name} berhasil diaktifkan.',
    #             'type': 'success',}
    #     )

    #     # Lanjutkan buka form user
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'User',
    #         'res_model': 'res.users',
    #         'res_id': user.id,
    #         'view_mode': 'form',
    #         'target': 'current',
    #     }
        
    # def activate_account_action(self):
    #     for rec in self:
    #         # Mengambil email dan jenis pegawai langsung dari instance hr.employee
    #         if not rec.work_email:
    #             raise UserError("Email tidak ditemukan di data karyawan.")
    #         if not rec.password or not rec.name:
    #             raise UserError("Password atau Nama karyawan belum diisi.")
            
    #         # Cari user berdasarkan email dari work_email
    #         user = rec.env['res.users'].search([('login', '=', rec.work_email)], limit=1)
            
    #         if not user:
    #             raise UserError(f"User dengan email {rec.work_email} tidak ditemukan.")

    #         user.groups_id = [(5, 0, 0)]  # Menghapus semua grup yang sudah ada

    #         # Menentukan group yang sesuai berdasarkan jenis pegawai
    #         groups_to_add = []
    #         groups_to_add.append(rec.env.ref('base.group_user'))
    #         if self.jns_pegawai == 'superadmin':
    #             groups_to_add.append(self.env.ref('base.group_system'))
    #             groups_to_add.append(self.env.ref('hr.group_hr_manager'))
    #             groups_to_add.append(self.env.ref('hr_attendance.group_hr_attendance_officer'))
    #             groups_to_add.append(self.env.ref('pesantren_pendaftaran.group_pendaftaran_manager'))
    #             groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_manager'))
    #             groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_manager'))
    #             groups_to_add.append(self.env.ref('pesantren_guru.group_guru_manager'))
    #             groups_to_add.append(self.env.ref('pesantren_guruquran.group_guru_quran_manager'))
    #             groups_to_add.append(self.env.ref('pesantren_musyrif.group_musyrif_manager'))
    #             groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_kesehatan'))
    #             groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_keamanan'))
    #             # Hak akses Akuntansi Administrator
    #             groups_to_add.append(self.env.ref('account.group_account_manager'))
    #             # Hak Akses Pembuatan Kontak
    #             groups_to_add.append(self.env.ref('base.group_partner_manager'))
    #             # Hak Akses Export Data
    #             groups_to_add.append(self.env.ref('base.group_allow_export'))
    #         elif self.jns_pegawai == 'guruquran':
    #             # groups_to_add.append(self.env.ref('pesantren_guruquran.group_guru_quran_manager')) 
    #             # groups_to_add.append(self.env.ref('pesantren_guruquran.group_guru_quran_manager')) 
    #             groups_to_add.append(self.env.ref('pesantren_guruquran.group_guru_quran_staff')) 
    #             # groups_to_add.append(self.env.ref('pesantren_guruquran.group_guru_quran_user')) 
    #             # groups_to_add.append(self.env.ref('pesantren_guru.group_guru_manager')) 
    #             groups_to_add.append(self.env.ref('pesantren_guru.group_guru_user')) 
    #             # groups_to_add.append(self.env.ref('pesantren_guru.group_guru_staff')) 
                
    #             groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_user')) 
    #             groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_user')) 
    #             # groups_to_add.append(self.env.ref('hr.group_hr_manager')) # Menambahkan grup HR User # groups_to_add.append(self.env.ref('hr_attendance.group_hr_attendance_officer')) # Menambahkan grup Absensi
    #             groups_to_add.append(self.env.ref('pesantren_base.group_hr_employee_readonly'))
    #             groups_to_add.append(self.env.ref('base.group_allow_export'))
    #         elif self.jns_pegawai == 'guru':
    #             # groups_to_add.append(self.env.ref('pesantren_guru.group_guru_manager'))
    #             groups_to_add.append(self.env.ref('pesantren_guru.group_guru_staff'))
    #             # groups_to_add.append(self.env.ref('pesantren_guru.group_guru_user'))
    #             # groups_to_add.append(self.env.ref('pesantren_guruquran.group_guru_quran_manager'))
    #             groups_to_add.append(self.env.ref('pesantren_guruquran.group_guru_quran_user'))

    #             groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_user'))
    #             groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_user'))
    #             # groups_to_add.append(self.env.ref('hr.group_hr_manager'))
    #             groups_to_add.append(self.env.ref('pesantren_base.group_hr_employee_readonly'))
    #             # groups_to_add.append(self.env.ref('hr_attendance.group_hr_attendance_officer'))
    #             groups_to_add.append(self.env.ref('base.group_allow_export'))
    #         # elif self.jns_pegawai in ['musyrif', 'ustadz']:
    #         elif self.jns_pegawai == 'guru,guruquran':
    #             groups_to_add.append(self.env.ref('pesantren_guru.group_guru_staff'))
    #             groups_to_add.append(self.env.ref('pesantren_guruquran.group_guru_quran_staff'))

    #             groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_user')) 
    #             groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_user')) 
    #             # groups_to_add.append(self.env.ref('hr.group_hr_manager')) # Menambahkan grup HR Use
    #             groups_to_add.append(self.env.ref('pesantren_base.group_hr_employee_readonly'))
    #             groups_to_add.append(self.env.ref('base.group_allow_export'))
    #         elif self.jns_pegawai == 'musyrif,guru':
    #             groups_to_add.append(self.env.ref('pesantren_musyrif.group_musyrif_staff'))
    #             groups_to_add.append(self.env.ref('pesantren_guru.group_guru_staff'))

    #             groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_user')) 
    #             groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_user')) 
    #             # groups_to_add.append(self.env.ref('hr.group_hr_manager')) # Menambahkan grup HR User # groups_to_add.append(self.env.ref('hr_attendance.group_hr_attendance_officer')) # Menambahkan grup Absensi
    #             groups_to_add.append(self.env.ref('pesantren_base.group_hr_employee_readonly'))
    #             groups_to_add.append(self.env.ref('base.group_allow_export'))
    #         elif self.jns_pegawai == 'musyrif,guruquran':
    #             groups_to_add.append(self.env.ref('pesantren_musyrif.group_musyrif_staff'))
    #             groups_to_add.append(self.env.ref('pesantren_guruquran.group_guru_quran_staff'))

    #             groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_user')) 
    #             groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_user')) 
    #             # groups_to_add.append(self.env.ref('hr.group_hr_manager')) # Menambahkan grup HR User # groups_to_add.append(self.env.ref('hr_attendance.group_hr_attendance_officer')) # Menambahkan grup Absensi
    #             groups_to_add.append(self.env.ref('pesantren_base.group_hr_employee_readonly'))
    #             groups_to_add.append(self.env.ref('base.group_allow_export'))
    #         elif self.jns_pegawai == 'musyrif,guru,guruquran':
    #             groups_to_add.append(self.env.ref('pesantren_musyrif.group_musyrif_staff'))
    #             groups_to_add.append(self.env.ref('pesantren_guru.group_guru_staff'))
    #             groups_to_add.append(self.env.ref('pesantren_guruquran.group_guru_quran_staff'))

    #             groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_user')) 
    #             groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_user')) 
    #             # groups_to_add.append(self.env.ref('hr.group_hr_manager')) # Menambahkan grup HR User # groups_to_add.append(self.env.ref('hr_attendance.group_hr_attendance_officer')) # Menambahkan grup Absensi
    #             groups_to_add.append(self.env.ref('pesantren_base.group_hr_employee_readonly'))
    #             groups_to_add.append(self.env.ref('base.group_allow_export'))
    #         elif self.jns_pegawai == 'musyrif':
    #             groups_to_add.append(self.env.ref('pesantren_musyrif.group_musyrif_staff'))

    #             groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_user'))
    #             groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_user'))
    #             # groups_to_add.append(self.env.ref('hr.group_hr_manager'))
    #             groups_to_add.append(self.env.ref('pesantren_base.group_hr_employee_readonly'))
    #             # groups_to_add.append(self.env.ref('hr_attendance.group_hr_attendance_officer'))
    #             groups_to_add.append(self.env.ref('base.group_allow_export'))
    #         elif self.jns_pegawai == 'keamanan':
    #             groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_keamanan'))
    #             groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_user'))
    #             groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_user'))
    #             groups_to_add.append(self.env.ref('pesantren_base.group_hr_employee_readonly'))
    #             groups_to_add.append(self.env.ref('base.group_allow_export'))
    #         else:
    #             groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_user'))
    #             groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_user'))
    #             groups_to_add.append(self.env.ref('pesantren_base.group_hr_employee_readonly'))
    #             groups_to_add.append(self.env.ref('base.group_allow_export'))


    #         if not groups_to_add:
    #             raise UserError("Jenis pegawai tidak terdaftar untuk penambahan group.")
            
    #         # Menambahkan semua grup yang diperlukan ke user
    #         for group in groups_to_add:
    #             if group not in user.groups_id:
    #                 user.groups_id = [(4, group.id)]

    #         # Atur ulang password user dengan format name-nip
    #         new_password = f"{rec.password}"  # Gunakan 4 digit pertama NIP
    #         masked_password = new_password[:2] + '*' * (len(new_password) - 4) + new_password[-2:]

    #         user.write({'password': new_password})

    #         email_values = { 
    #                     'subject': "Akun Diaktifkan", 
    #                     'email_to': rec.work_email, 
    #                     'body_html': f''' 
    #                         <div style="background-color: #f0f8ff; padding: 20px; font-family: Arial, sans-serif;"> 
    #                             <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);"> 
    #                                 <!-- Header --> 
    #                                 <div style="background-color: #0078d7; color: #ffffff; text-align: center; padding: 25px;"> 
    #                                     <h1 style="margin: 0; font-size: 26px;">Aktivasi Akun Anda</h1> 
    #                                 </div> 
    #                                 <!-- Body --> 
    #                                 <div style="padding: 20px; color: #333333;"> 
    #                                     <p style="margin: 0 0 10px; font-size: 16px;">Assalamualaikum Wr. Wb,</p> 
    #                                     <p style="margin: 0 0 20px; font-size: 16px;"> 
    #                                         Selamat, akun Anda telah berhasil diaktifkan! Berikut adalah informasi akun Anda: 
    #                                     </p> 
    #                                     <div style="background-color: #f9f9f9; padding: 20px; border-radius: 8px; margin: 20px 0;"> 
    #                                         <table style="width: 100%; border-collapse: collapse;"> 
    #                                             <tr> 
    #                                                 <td style="padding: 10px; font-weight: bold; color: #555555;">Email :</td> 
    #                                                 <td style="padding: 10px; color: #555555;">{rec.work_email}</td> 
    #                                             </tr> 
    #                                             <tr> 
    #                                                 <td style="padding: 10px; font-weight: bold; color: #555555;">Kata Sandi :</td> 
    #                                                 <td style="padding: 10px; color: #555555;">{masked_password}</td> 
    #                                             </tr> 
    #                                             <tr> 
    #                                                 <td style="padding: 10px; font-weight: bold; color: #555555;">Jenis Akun :</td> 
    #                                                 <td style="padding: 10px; color: #555555;">{rec.jns_pegawai}</td> 
    #                                             </tr> 
    #                                             <tr> 
    #                                                 <td style="padding: 10px; font-weight: bold; color: #555555;">Tanggal Aktivasi :</td> 
    #                                                 <td style="padding: 10px; color: #555555;">{fields.Datetime.now()}</td> 
    #                                             </tr> 
    #                                         </table> 
    #                                     </div> 
    #                                     <p style="text-align: center;"> 
    #                                         <a href="https://aplikasi.dqi.ac.id/login" style="background-color: #0078d7; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block; font-size: 16px;"> 
    #                                             Masuk Ke Akun Anda 
    #                                         </a> 
    #                                     </p> 
    #                                     <p style="margin: 20px 0; font-size: 14px;"> 
    #                                         Apabila Anda mengalami kendala, silakan hubungi tim teknis kami melalui nomor berikut: 
    #                                     </p> 
    #                                     <ul style="margin: 0; padding-left: 20px; color: #555555; font-size: 14px;"> 
    #                                         <li>0822 5207 9785</li> 
    #                                     </ul> 
    #                                     <p style="margin: 20px 0; font-size: 14px;"> 
    #                                         Terima kasih telah menggunakan layanan kami. Kami berharap akun ini dapat membantu Anda dalam menjalankan aktivitas di pesantren. 
    #                                     </p> 
    #                                 </div> 
    #                                 <!-- Footer --> 
    #                                 <div style="background-color: #f1f1f1; text-align: center; padding: 15px; border-top: 1px solid #dddddd;"> 
    #                                     <p style="font-size: 12px; color: #888888; margin: 0;"> 
    #                                         &copy; 2024 Pesantren Tahfizh Daarul Qur'an Istiqomah. All rights reserved. 
    #                                     </p> 
    #                                 </div> 
    #                             </div> 
    #                         </div> 
    #                     ''' 
    #                 }

    #         mail = rec.env['mail.mail'].sudo().create(email_values)
    #         mail.send()
            
    #     # Setelah semua selesai, munculkan notifikasi ringkasan
    #     names = ', '.join(self.mapped('name'))
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'title': 'Aktivasi Akun Berhasil',
    #             'message': f'{len(self)} akun berhasil diaktifkan: {names}',
    #             'type': 'success',
    #             'sticky': False,
    #         }
    #     }
    
    def activate_account(self):
        """
        Fungsi untuk aktivasi akun single record (dipanggil dari button di form view)
        """
        # Validasi: Jika email tidak ada
        if not self.work_email:
            raise UserError("Email tidak ditemukan di data karyawan.")
        
        # Validasi: Jika password atau nama belum diisi
        if not self.password or not self.name:
            raise UserError("Password atau Nama karyawan belum diisi.")
        
        # Cari user berdasarkan email dari work_email
        user = self.env['res.users'].search([('login', '=', self.work_email)], limit=1)
        
        # Validasi: Jika user tidak ditemukan
        if not user:
            raise UserError(f"User dengan email {self.work_email} tidak ditemukan.")

        user.groups_id = [(5, 0, 0)]  # Menghapus semua grup yang sudah ada

        # Menentukan group yang sesuai berdasarkan jenis pegawai
        groups_to_add = []
        groups_to_add.append(self.env.ref('base.group_user'))
        
        if self.jns_pegawai == 'superadmin':
            groups_to_add.append(self.env.ref('base.group_system'))
            groups_to_add.append(self.env.ref('hr.group_hr_manager'))
            groups_to_add.append(self.env.ref('hr_attendance.group_hr_attendance_officer'))
            groups_to_add.append(self.env.ref('pesantren_pendaftaran.group_pendaftaran_manager'))
            groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_manager'))
            groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_manager'))
            groups_to_add.append(self.env.ref('pesantren_guru.group_guru_manager'))
            groups_to_add.append(self.env.ref('pesantren_guruquran.group_guru_quran_manager'))
            groups_to_add.append(self.env.ref('pesantren_musyrif.group_musyrif_manager'))
            groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_kesehatan'))
            groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_keamanan'))
            groups_to_add.append(self.env.ref('account.group_account_manager'))
            groups_to_add.append(self.env.ref('base.group_partner_manager'))
            groups_to_add.append(self.env.ref('base.group_allow_export'))
        elif self.jns_pegawai == 'guruquran':
            groups_to_add.append(self.env.ref('pesantren_guruquran.group_guru_quran_staff')) 
            groups_to_add.append(self.env.ref('pesantren_guru.group_guru_user')) 
            groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_user')) 
            groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_user')) 
            groups_to_add.append(self.env.ref('pesantren_base.group_hr_employee_readonly'))
            groups_to_add.append(self.env.ref('base.group_allow_export'))
        elif self.jns_pegawai == 'guru':
            groups_to_add.append(self.env.ref('pesantren_guru.group_guru_staff'))
            groups_to_add.append(self.env.ref('pesantren_guruquran.group_guru_quran_user'))
            groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_user'))
            groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_user'))
            groups_to_add.append(self.env.ref('pesantren_base.group_hr_employee_readonly'))
            groups_to_add.append(self.env.ref('base.group_allow_export'))
        elif self.jns_pegawai == 'guru,guruquran':
            groups_to_add.append(self.env.ref('pesantren_guru.group_guru_staff'))
            groups_to_add.append(self.env.ref('pesantren_guruquran.group_guru_quran_staff'))
            groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_user')) 
            groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_user')) 
            groups_to_add.append(self.env.ref('pesantren_base.group_hr_employee_readonly'))
            groups_to_add.append(self.env.ref('base.group_allow_export'))
        elif self.jns_pegawai == 'musyrif,guru':
            groups_to_add.append(self.env.ref('pesantren_musyrif.group_musyrif_staff'))
            groups_to_add.append(self.env.ref('pesantren_guru.group_guru_staff'))
            groups_to_add.append(self.env.ref('pesantren_guruquran.group_guru_quran_user'))
            groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_user')) 
            groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_user')) 
            groups_to_add.append(self.env.ref('pesantren_base.group_hr_employee_readonly'))
            groups_to_add.append(self.env.ref('base.group_allow_export'))
        elif self.jns_pegawai == 'musyrif,guruquran':
            groups_to_add.append(self.env.ref('pesantren_musyrif.group_musyrif_staff'))
            groups_to_add.append(self.env.ref('pesantren_guruquran.group_guru_quran_staff'))
            groups_to_add.append(self.env.ref('pesantren_guru.group_guru_user')) 
            groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_user')) 
            groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_user')) 
            groups_to_add.append(self.env.ref('pesantren_base.group_hr_employee_readonly'))
            groups_to_add.append(self.env.ref('base.group_allow_export'))
        elif self.jns_pegawai == 'musyrif,guru,guruquran':
            groups_to_add.append(self.env.ref('pesantren_musyrif.group_musyrif_staff'))
            groups_to_add.append(self.env.ref('pesantren_guru.group_guru_staff'))
            groups_to_add.append(self.env.ref('pesantren_guruquran.group_guru_quran_staff'))
            groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_user')) 
            groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_user')) 
            groups_to_add.append(self.env.ref('pesantren_base.group_hr_employee_readonly'))
            groups_to_add.append(self.env.ref('base.group_allow_export'))
        elif self.jns_pegawai == 'musyrif':
            groups_to_add.append(self.env.ref('pesantren_musyrif.group_musyrif_staff'))
            groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_user'))
            groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_user'))
            groups_to_add.append(self.env.ref('pesantren_base.group_hr_employee_readonly'))
            groups_to_add.append(self.env.ref('base.group_allow_export'))
        elif self.jns_pegawai == 'keamanan':
            groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_keamanan'))
            groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_user'))
            groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_user'))
            groups_to_add.append(self.env.ref('pesantren_base.group_hr_employee_readonly'))
            groups_to_add.append(self.env.ref('base.group_allow_export'))
        else:
            groups_to_add.append(self.env.ref('pesantren_base.group_sekolah_user'))
            groups_to_add.append(self.env.ref('pesantren_kesantrian.group_kesantrian_user'))
            groups_to_add.append(self.env.ref('pesantren_base.group_hr_employee_readonly'))
            groups_to_add.append(self.env.ref('base.group_allow_export'))

        if not groups_to_add:
            raise UserError("Jenis pegawai tidak terdaftar untuk penambahan group.")
        
        # Menambahkan semua grup yang diperlukan ke user
        for group in groups_to_add:
            if group not in user.groups_id:
                user.groups_id = [(4, group.id)]

        # Atur ulang password user
        new_password = f"{self.password}"
        masked_password = new_password[:2] + '*' * (len(new_password) - 4) + new_password[-2:]

        user.write({'password': new_password})

        email_values = { 
            'subject': "Akun Diaktifkan", 
            'email_to': self.work_email, 
            'body_html': f''' 
                <div style="background-color: #f0f8ff; padding: 20px; font-family: Arial, sans-serif;"> 
                    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);"> 
                        <!-- Header --> 
                        <div style="background-color: #0078d7; color: #ffffff; text-align: center; padding: 25px;"> 
                            <h1 style="margin: 0; font-size: 26px;">Aktivasi Akun Anda</h1> 
                        </div> 
                        <!-- Body --> 
                        <div style="padding: 20px; color: #333333;"> 
                            <p style="margin: 0 0 10px; font-size: 16px;">Assalamualaikum Wr. Wb,</p> 
                            <p style="margin: 0 0 20px; font-size: 16px;"> 
                                Selamat, akun Anda telah berhasil diaktifkan! Berikut adalah informasi akun Anda: 
                            </p> 
                            <div style="background-color: #f9f9f9; padding: 20px; border-radius: 8px; margin: 20px 0;"> 
                                <table style="width: 100%; border-collapse: collapse;"> 
                                    <tr> 
                                        <td style="padding: 10px; font-weight: bold; color: #555555;">Email :</td> 
                                        <td style="padding: 10px; color: #555555;">{self.work_email}</td> 
                                    </tr> 
                                    <tr> 
                                        <td style="padding: 10px; font-weight: bold; color: #555555;">Kata Sandi :</td> 
                                        <td style="padding: 10px; color: #555555;">{masked_password}</td> 
                                    </tr> 
                                    <tr> 
                                        <td style="padding: 10px; font-weight: bold; color: #555555;">Jenis Akun :</td> 
                                        <td style="padding: 10px; color: #555555;">{self.jns_pegawai}</td> 
                                    </tr> 
                                    <tr> 
                                        <td style="padding: 10px; font-weight: bold; color: #555555;">Tanggal Aktivasi :</td> 
                                        <td style="padding: 10px; color: #555555;">{fields.Datetime.now()}</td> 
                                    </tr> 
                                </table> 
                            </div> 
                            <p style="text-align: center;"> 
                                <a href="https://aplikasi.dqi.ac.id/login" style="background-color: #0078d7; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block; font-size: 16px;"> 
                                    Masuk Ke Akun Anda 
                                </a> 
                            </p> 
                            <p style="margin: 20px 0; font-size: 14px;"> 
                                Apabila Anda mengalami kendala, silakan hubungi tim teknis kami melalui nomor berikut: 
                            </p> 
                            <ul style="margin: 0; padding-left: 20px; color: #555555; font-size: 14px;"> 
                                <li>0822 5207 9785</li> 
                            </ul> 
                            <p style="margin: 20px 0; font-size: 14px;"> 
                                Terima kasih telah menggunakan layanan kami. Kami berharap akun ini dapat membantu Anda dalam menjalankan aktivitas di pesantren. 
                            </p> 
                        </div> 
                        <!-- Footer --> 
                        <div style="background-color: #f1f1f1; text-align: center; padding: 15px; border-top: 1px solid #dddddd;"> 
                            <p style="font-size: 12px; color: #888888; margin: 0;"> 
                                &copy; 2024 Pesantren Tahfizh Daarul Qur'an Istiqomah. All rights reserved. 
                            </p> 
                        </div> 
                    </div> 
                </div> 
            ''' 
        }

        mail = self.env['mail.mail'].sudo().create(email_values)
        mail.send()
        
        # tampilkan notifikasi dulu
        self.env['bus.bus']._sendone(
            self.env.user.partner_id, 
            'simple_notification', 
            {
                'title': 'Aktivasi Akun Berhasil', 
                'message': f'Akun {self.name} berhasil diaktifkan.',
                'type': 'success',
            }
        )

        # Lanjutkan buka form user
        return {
            'type': 'ir.actions.act_window',
            'name': 'User',
            'res_model': 'res.users',
            'res_id': user.id,
            'view_mode': 'form',
            'target': 'current',
        }


    # def activate_account_action(self):
    #     success_count = 0
    #     skipped_records = []
        
    #     for rec in self:
    #         # Validasi: Skip jika email tidak ada
    #         if not rec.work_email:
    #             skipped_records.append({
    #                 'name': rec.name,
    #                 'reason': 'Email tidak ditemukan'
    #             })
    #             continue
            
    #         # Validasi: Skip jika password atau nama belum diisi
    #         if not rec.password or not rec.name:
    #             skipped_records.append({
    #                 'name': rec.name or 'Nama Kosong',
    #                 'reason': 'Password atau Nama karyawan belum diisi'
    #             })
    #             continue
            
    #         # Cari user berdasarkan email dari work_email
    #         user = rec.env['res.users'].search([('login', '=', rec.work_email)], limit=1)
            
    #         # Validasi: Skip jika user tidak ditemukan
    #         if not user:
    #             skipped_records.append({
    #                 'name': rec.name,
    #                 'reason': f'User dengan email {rec.work_email} tidak ditemukan'
    #             })
    #             continue

    #         # Proses aktivasi akun
    #         try:
    #             user.groups_id = [(5, 0, 0)]  # Menghapus semua grup yang sudah ada

    #             # Menentukan group yang sesuai berdasarkan jenis pegawai
    #             groups_to_add = []
    #             groups_to_add.append(rec.env.ref('base.group_user'))
                
    #             if rec.jns_pegawai == 'superadmin':
    #                 groups_to_add.append(rec.env.ref('base.group_system'))
    #                 groups_to_add.append(rec.env.ref('hr.group_hr_manager'))
    #                 groups_to_add.append(rec.env.ref('hr_attendance.group_hr_attendance_officer'))
    #                 groups_to_add.append(rec.env.ref('pesantren_pendaftaran.group_pendaftaran_manager'))
    #                 groups_to_add.append(rec.env.ref('pesantren_base.group_sekolah_manager'))
    #                 groups_to_add.append(rec.env.ref('pesantren_kesantrian.group_kesantrian_manager'))
    #                 groups_to_add.append(rec.env.ref('pesantren_guru.group_guru_manager'))
    #                 groups_to_add.append(rec.env.ref('pesantren_guruquran.group_guru_quran_manager'))
    #                 groups_to_add.append(rec.env.ref('pesantren_musyrif.group_musyrif_manager'))
    #                 groups_to_add.append(rec.env.ref('pesantren_kesantrian.group_kesantrian_kesehatan'))
    #                 groups_to_add.append(rec.env.ref('pesantren_kesantrian.group_kesantrian_keamanan'))
    #                 groups_to_add.append(rec.env.ref('account.group_account_manager'))
    #                 groups_to_add.append(rec.env.ref('base.group_partner_manager'))
    #                 groups_to_add.append(rec.env.ref('base.group_allow_export'))
    #             elif rec.jns_pegawai == 'guruquran':
    #                 groups_to_add.append(rec.env.ref('pesantren_guruquran.group_guru_quran_staff')) 
    #                 groups_to_add.append(rec.env.ref('pesantren_guru.group_guru_user')) 
    #                 groups_to_add.append(rec.env.ref('pesantren_kesantrian.group_kesantrian_user')) 
    #                 groups_to_add.append(rec.env.ref('pesantren_base.group_sekolah_user')) 
    #                 groups_to_add.append(rec.env.ref('pesantren_base.group_hr_employee_readonly'))
    #                 groups_to_add.append(rec.env.ref('base.group_allow_export'))
    #             elif rec.jns_pegawai == 'guru':
    #                 groups_to_add.append(rec.env.ref('pesantren_guru.group_guru_staff'))
    #                 groups_to_add.append(rec.env.ref('pesantren_guruquran.group_guru_quran_user'))
    #                 groups_to_add.append(rec.env.ref('pesantren_base.group_sekolah_user'))
    #                 groups_to_add.append(rec.env.ref('pesantren_kesantrian.group_kesantrian_user'))
    #                 groups_to_add.append(rec.env.ref('pesantren_base.group_hr_employee_readonly'))
    #                 groups_to_add.append(rec.env.ref('base.group_allow_export'))
    #             elif rec.jns_pegawai == 'guru,guruquran':
    #                 groups_to_add.append(rec.env.ref('pesantren_guru.group_guru_staff'))
    #                 groups_to_add.append(rec.env.ref('pesantren_guruquran.group_guru_quran_staff'))
    #                 groups_to_add.append(rec.env.ref('pesantren_kesantrian.group_kesantrian_user')) 
    #                 groups_to_add.append(rec.env.ref('pesantren_base.group_sekolah_user')) 
    #                 groups_to_add.append(rec.env.ref('pesantren_base.group_hr_employee_readonly'))
    #                 groups_to_add.append(rec.env.ref('base.group_allow_export'))
    #             elif rec.jns_pegawai == 'musyrif,guru':
    #                 groups_to_add.append(rec.env.ref('pesantren_musyrif.group_musyrif_staff'))
    #                 groups_to_add.append(rec.env.ref('pesantren_guru.group_guru_staff'))
    #                 groups_to_add.append(rec.env.ref('pesantren_guruquran.group_guru_quran_user'))
    #                 groups_to_add.append(rec.env.ref('pesantren_kesantrian.group_kesantrian_user')) 
    #                 groups_to_add.append(rec.env.ref('pesantren_base.group_sekolah_user')) 
    #                 groups_to_add.append(rec.env.ref('pesantren_base.group_hr_employee_readonly'))
    #                 groups_to_add.append(rec.env.ref('base.group_allow_export'))
    #             elif rec.jns_pegawai == 'musyrif,guruquran':
    #                 groups_to_add.append(rec.env.ref('pesantren_musyrif.group_musyrif_staff'))
    #                 groups_to_add.append(rec.env.ref('pesantren_guruquran.group_guru_quran_staff'))
    #                 groups_to_add.append(rec.env.ref('pesantren_guru.group_guru_user')) 
    #                 groups_to_add.append(rec.env.ref('pesantren_kesantrian.group_kesantrian_user')) 
    #                 groups_to_add.append(rec.env.ref('pesantren_base.group_sekolah_user')) 
    #                 groups_to_add.append(rec.env.ref('pesantren_base.group_hr_employee_readonly'))
    #                 groups_to_add.append(rec.env.ref('base.group_allow_export'))
    #             elif rec.jns_pegawai == 'musyrif,guru,guruquran':
    #                 groups_to_add.append(rec.env.ref('pesantren_musyrif.group_musyrif_staff'))
    #                 groups_to_add.append(rec.env.ref('pesantren_guru.group_guru_staff'))
    #                 groups_to_add.append(rec.env.ref('pesantren_guruquran.group_guru_quran_staff'))
    #                 groups_to_add.append(rec.env.ref('pesantren_kesantrian.group_kesantrian_user')) 
    #                 groups_to_add.append(rec.env.ref('pesantren_base.group_sekolah_user')) 
    #                 groups_to_add.append(rec.env.ref('pesantren_base.group_hr_employee_readonly'))
    #                 groups_to_add.append(rec.env.ref('base.group_allow_export'))
    #             elif rec.jns_pegawai == 'musyrif':
    #                 groups_to_add.append(rec.env.ref('pesantren_musyrif.group_musyrif_staff'))
    #                 groups_to_add.append(rec.env.ref('pesantren_kesantrian.group_kesantrian_user'))
    #                 groups_to_add.append(rec.env.ref('pesantren_base.group_sekolah_user'))
    #                 groups_to_add.append(rec.env.ref('pesantren_base.group_hr_employee_readonly'))
    #                 groups_to_add.append(rec.env.ref('base.group_allow_export'))
    #             elif rec.jns_pegawai == 'keamanan':
    #                 groups_to_add.append(rec.env.ref('pesantren_kesantrian.group_kesantrian_keamanan'))
    #                 groups_to_add.append(rec.env.ref('pesantren_kesantrian.group_kesantrian_user'))
    #                 groups_to_add.append(rec.env.ref('pesantren_base.group_sekolah_user'))
    #                 groups_to_add.append(rec.env.ref('pesantren_base.group_hr_employee_readonly'))
    #                 groups_to_add.append(rec.env.ref('base.group_allow_export'))
    #             else:
    #                 groups_to_add.append(rec.env.ref('pesantren_base.group_sekolah_user'))
    #                 groups_to_add.append(rec.env.ref('pesantren_kesantrian.group_kesantrian_user'))
    #                 groups_to_add.append(rec.env.ref('pesantren_base.group_hr_employee_readonly'))
    #                 groups_to_add.append(rec.env.ref('base.group_allow_export'))

    #             if not groups_to_add:
    #                 skipped_records.append({
    #                     'name': rec.name,
    #                     'reason': 'Jenis pegawai tidak terdaftar'
    #                 })
    #                 continue
                
    #             # Menambahkan semua grup yang diperlukan ke user
    #             for group in groups_to_add:
    #                 if group not in user.groups_id:
    #                     user.groups_id = [(4, group.id)]

    #             # Atur ulang password user
    #             new_password = f"{rec.password}"
    #             masked_password = new_password[:2] + '*' * (len(new_password) - 4) + new_password[-2:]

    #             user.write({'password': new_password})

    #             email_values = { 
    #                 'subject': "Akun Diaktifkan", 
    #                 'email_to': rec.work_email, 
    #                 'body_html': f''' 
    #                     <div style="background-color: #f0f8ff; padding: 20px; font-family: Arial, sans-serif;"> 
    #                         <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);"> 
    #                             <!-- Header --> 
    #                             <div style="background-color: #0078d7; color: #ffffff; text-align: center; padding: 25px;"> 
    #                                 <h1 style="margin: 0; font-size: 26px;">Aktivasi Akun Anda</h1> 
    #                             </div> 
    #                             <!-- Body --> 
    #                             <div style="padding: 20px; color: #333333;"> 
    #                                 <p style="margin: 0 0 10px; font-size: 16px;">Assalamualaikum Wr. Wb,</p> 
    #                                 <p style="margin: 0 0 20px; font-size: 16px;"> 
    #                                     Selamat, akun Anda telah berhasil diaktifkan! Berikut adalah informasi akun Anda: 
    #                                 </p> 
    #                                 <div style="background-color: #f9f9f9; padding: 20px; border-radius: 8px; margin: 20px 0;"> 
    #                                     <table style="width: 100%; border-collapse: collapse;"> 
    #                                         <tr> 
    #                                             <td style="padding: 10px; font-weight: bold; color: #555555;">Email :</td> 
    #                                             <td style="padding: 10px; color: #555555;">{rec.work_email}</td> 
    #                                         </tr> 
    #                                         <tr> 
    #                                             <td style="padding: 10px; font-weight: bold; color: #555555;">Kata Sandi :</td> 
    #                                             <td style="padding: 10px; color: #555555;">{masked_password}</td> 
    #                                         </tr> 
    #                                         <tr> 
    #                                             <td style="padding: 10px; font-weight: bold; color: #555555;">Jenis Akun :</td> 
    #                                             <td style="padding: 10px; color: #555555;">{rec.jns_pegawai}</td> 
    #                                         </tr> 
    #                                         <tr> 
    #                                             <td style="padding: 10px; font-weight: bold; color: #555555;">Tanggal Aktivasi :</td> 
    #                                             <td style="padding: 10px; color: #555555;">{fields.Datetime.now()}</td> 
    #                                         </tr> 
    #                                     </table> 
    #                                 </div> 
    #                                 <p style="text-align: center;"> 
    #                                     <a href="https://aplikasi.dqi.ac.id/login" style="background-color: #0078d7; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block; font-size: 16px;"> 
    #                                         Masuk Ke Akun Anda 
    #                                     </a> 
    #                                 </p> 
    #                                 <p style="margin: 20px 0; font-size: 14px;"> 
    #                                     Apabila Anda mengalami kendala, silakan hubungi tim teknis kami melalui nomor berikut: 
    #                                 </p> 
    #                                 <ul style="margin: 0; padding-left: 20px; color: #555555; font-size: 14px;"> 
    #                                     <li>0822 5207 9785</li> 
    #                                 </ul> 
    #                                 <p style="margin: 20px 0; font-size: 14px;"> 
    #                                     Terima kasih telah menggunakan layanan kami. Kami berharap akun ini dapat membantu Anda dalam menjalankan aktivitas di pesantren. 
    #                                 </p> 
    #                             </div> 
    #                             <!-- Footer --> 
    #                             <div style="background-color: #f1f1f1; text-align: center; padding: 15px; border-top: 1px solid #dddddd;"> 
    #                                 <p style="font-size: 12px; color: #888888; margin: 0;"> 
    #                                     &copy; 2024 Pesantren Tahfizh Daarul Qur'an Istiqomah. All rights reserved. 
    #                                 </p> 
    #                             </div> 
    #                         </div> 
    #                     </div> 
    #                 ''' 
    #             }

    #             mail = rec.env['mail.mail'].sudo().create(email_values)
    #             mail.send()
                
    #             success_count += 1
                
    #         except Exception as e:
    #             skipped_records.append({
    #                 'name': rec.name,
    #                 'reason': f'Error: {str(e)}'
    #             })
    #             continue
        
    #     # Buat pesan notifikasi
    #     message_parts = []
        
    #     if success_count > 0:
    #         success_names = [rec.name for rec in self if rec.name not in [s['name'] for s in skipped_records]]
    #         message_parts.append(f'✓ {success_count} akun berhasil diaktifkan')
        
    #     if skipped_records:
    #         message_parts.append(f'⚠ {len(skipped_records)} akun dilewati:')
    #         for skip in skipped_records[:5]:  # Tampilkan maksimal 5 record pertama
    #             message_parts.append(f"  • {skip['name']}: {skip['reason']}")
    #         if len(skipped_records) > 5:
    #             message_parts.append(f"  ... dan {len(skipped_records) - 5} lainnya")
        
    #     message = '\n'.join(message_parts) if message_parts else 'Tidak ada akun yang diproses'
        
    #     # Tentukan tipe notifikasi berdasarkan hasil
    #     if success_count > 0 and not skipped_records:
    #         notification_type = 'success'
    #         title = 'Aktivasi Akun Berhasil'
    #     elif success_count > 0 and skipped_records:
    #         notification_type = 'warning'
    #         title = 'Aktivasi Akun Selesai dengan Peringatan'
    #     else:
    #         notification_type = 'warning'
    #         title = 'Tidak Ada Akun yang Diaktifkan'
        
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'title': title,
    #             'message': message,
    #             'type': notification_type,
    #         }
    #     }
    # def activate_account_action(self):
    #     """
    #     Aktivasi massal akun karyawan — VERSI SUPER CEPAT + PROGRESS BAR + QUEUE_JOB
    #     """
    #     total = len(self)
    #     if not total:
    #         raise UserError("Tidak ada karyawan yang dipilih untuk diaktifkan.")

    #     # ===================================================================
    #     # 1. CACHE SEMUA GROUP SEKALI DI AWAL (PENTING BANGET!)
    #     # ===================================================================
    #     group_refs = {
    #         'base.group_user': self.env.ref('base.group_user'),
    #         'base.group_system': self.env.ref('base.group_system'),
    #         'hr.group_hr_manager': self.env.ref('hr.group_hr_manager'),
    #         'hr_attendance.group_hr_attendance_officer': self.env.ref('hr_attendance.group_hr_attendance_officer'),
    #         'pesantren_pendaftaran.group_pendaftaran_manager': self.env.ref('pesantren_pendaftaran.group_pendaftaran_manager'),
    #         'pesantren_base.group_sekolah_manager': self.env.ref('pesantren_base.group_sekolah_manager'),
    #         'pesantren_kesantrian.group_kesantrian_manager': self.env.ref('pesantren_kesantrian.group_kesantrian_manager'),
    #         'pesantren_guru.group_guru_manager': self.env.ref('pesantren_guru.group_guru_manager'),
    #         'pesantren_guruquran.group_guru_quran_manager': self.env.ref('pesantren_guruquran.group_guru_quran_manager'),
    #         'pesantren_musyrif.group_musyrif_manager': self.env.ref('pesantren_musyrif.group_musyrif_manager'),
    #         'pesantren_kesantrian.group_kesantrian_kesehatan': self.env.ref('pesantren_kesantrian.group_kesantrian_kesehatan'),
    #         'pesantren_kesantrian.group_kesantrian_keamanan': self.env.ref('pesantren_kesantrian.group_kesantrian_keamanan'),
    #         'account.group_account_manager': self.env.ref('account.group_account_manager'),
    #         'base.group_partner_manager': self.env.ref('base.group_partner_manager'),
    #         'base.group_allow_export': self.env.ref('base.group_allow_export'),

    #         # Staff & User groups
    #         'pesantren_guruquran.group_guru_quran_staff': self.env.ref('pesantren_guruquran.group_guru_quran_staff'),
    #         'pesantren_guru.group_guru_staff': self.env.ref('pesantren_guru.group_guru_staff'),
    #         'pesantren_musyrif.group_musyrif_staff': self.env.ref('pesantren_musyrif.group_musyrif_staff'),
    #         'pesantren_guru.group_guru_user': self.env.ref('pesantren_guru.group_guru_user'),
    #         'pesantren_guruquran.group_guru_quran_user': self.env.ref('pesantren_guruquran.group_guru_quran_user'),
    #         'pesantren_kesantrian.group_kesantrian_user': self.env.ref('pesantren_kesantrian.group_kesantrian_user'),
    #         'pesantren_base.group_sekolah_user': self.env.ref('pesantren_base.group_sekolah_user'),
    #         'pesantren_base.group_hr_employee_readonly': self.env.ref('pesantren_base.group_hr_employee_readonly'),
    #     }

    #     # Mapping jenis pegawai → list XMLID group
    #     GROUP_MAPPING = {
    #         'superadmin': [
    #             'base.group_system', 'hr.group_hr_manager', 'hr_attendance.group_hr_attendance_officer',
    #             'pesantren_pendaftaran.group_pendaftaran_manager', 'pesantren_base.group_sekolah_manager',
    #             'pesantren_kesantrian.group_kesantrian_manager', 'pesantren_guru.group_guru_manager',
    #             'pesantren_guruquran.group_guru_quran_manager', 'pesantren_musyrif.group_musyrif_manager',
    #             'pesantren_kesantrian.group_kesantrian_kesehatan', 'pesantren_kesantrian.group_kesantrian_keamanan',
    #             'account.group_account_manager', 'base.group_partner_manager', 'base.group_allow_export',
    #         ],
    #         'guruquran': ['pesantren_guruquran.group_guru_quran_staff', 'pesantren_guru.group_guru_user',
    #                       'pesantren_kesantrian.group_kesantrian_user', 'pesantren_base.group_sekolah_user',
    #                       'pesantren_base.group_hr_employee_readonly', 'base.group_allow_export'],
    #         'guru': ['pesantren_guru.group_guru_staff', 'pesantren_guruquran.group_guru_quran_user',
    #                  'pesantren_base.group_sekolah_user', 'pesantren_kesantrian.group_kesantrian_user',
    #                  'pesantren_base.group_hr_employee_readonly', 'base.group_allow_export'],
    #         'guru,guruquran': ['pesantren_guru.group_guru_staff', 'pesantren_guruquran.group_guru_quran_staff',
    #                            'pesantren_kesantrian.group_kesantrian_user', 'pesantren_base.group_sekolah_user',
    #                            'pesantren_base.group_hr_employee_readonly', 'base.group_allow_export'],
    #         'musyrif,guru': ['pesantren_musyrif.group_musyrif_staff', 'pesantren_guru.group_guru_staff',
    #                          'pesantren_guruquran.group_guru_quran_user', 'pesantren_kesantrian.group_kesantrian_user',
    #                          'pesantren_base.group_sekolah_user', 'pesantren_base.group_hr_employee_readonly',
    #                          'base.group_allow_export'],
    #         'musyrif,guruquran': ['pesantren_musyrif.group_musyrif_staff', 'pesantren_guruquran.group_guru_quran_staff',
    #                               'pesantren_guru.group_guru_user', 'pesantren_kesantrian.group_kesantrian_user',
    #                               'pesantren_base.group_sekolah_user', 'pesantren_base.group_hr_employee_readonly',
    #                               'base.group_allow_export'],
    #         'musyrif,guru,guruquran': ['pesantren_musyrif.group_musyrif_staff', 'pesantren_guru.group_guru_staff',
    #                                    'pesantren_guruquran.group_guru_quran_staff', 'pesantren_kesantrian.group_kesantrian_user',
    #                                    'pesantren_base.group_sekolah_user', 'pesantren_base.group_hr_employee_readonly',
    #                                    'base.group_allow_export'],
    #         'musyrif': ['pesantren_musyrif.group_musyrif_staff', 'pesantren_kesantrian.group_kesantrian_user',
    #                     'pesantren_base.group_sekolah_user', 'pesantren_base.group_hr_employee_readonly',
    #                     'base.group_allow_export'],
    #         'keamanan': ['pesantren_kesantrian.group_kesantrian_keamanan', 'pesantren_kesantrian.group_kesantrian_user',
    #                      'pesantren_base.group_sekolah_user', 'pesantren_base.group_hr_employee_readonly',
    #                      'base.group_allow_export'],
    #     }

    #     # Default groups (jika jenis pegawai tidak cocok)
    #     DEFAULT_GROUPS = [
    #         'pesantren_base.group_sekolah_user', 'pesantren_kesantrian.group_kesantrian_user',
    #         'pesantren_base.group_hr_employee_readonly', 'base.group_allow_export'
    #     ]

    #     success_count = 0
    #     skipped_records = []
    #     emails_to_send = []

    #     for rec in self.with_progress(
    #         msg=f"Sedang mengaktifkan akun karyawan ({total} akun)...",
    #         total=total,
    #         cancellable=True
    #     ):
    #         # Validasi wajib
    #         if not rec.work_email or not rec.password or not rec.name:
    #             skipped_records.append({
    #                 'name': rec.name or 'Tanpa Nama',
    #                 'reason': 'Email / Password / Nama belum diisi'
    #             })
    #             continue

    #         user = self.env['res.users'].sudo().search([('login', '=', rec.work_email)], limit=1)
    #         if not user:
    #             skipped_records.append({
    #                 'name': rec.name,
    #                 'reason': f'User tidak ditemukan: {rec.work_email}'
    #             })
    #             continue

    #         try:
    #             # Tentukan group yang harus diberikan
    #             jenis = rec.jns_pegawai or ''
    #             group_xmlids = ['base.group_user']  # selalu ada

    #             # Cari mapping yang cocok (bisa multi, misal "guru,guruquran")
    #             for key in GROUP_MAPPING:
    #                 if key in jenis:
    #                     group_xmlids.extend(GROUP_MAPPING[key])

    #             # Jika tidak ada yang cocok → pakai default
    #             if len(group_xmlids) == 1:
    #                 group_xmlids.extend(DEFAULT_GROUPS)

    #             # Konversi ke ID nyata
    #             final_group_ids = [group_refs[x].id for x in group_xmlids if x in group_refs]

    #             # UPDATE USER — SEKALI JALAN (super cepat!)
    #             user.write({
    #                 'groups_id': [(6, 0, final_group_ids)],
    #                 'password': rec.password,
    #             })

    #             # Mask password untuk email
    #             pwd = rec.password
    #             masked = pwd[:2] + '*' * max(0, len(pwd) - 4) + pwd[-2:] if len(pwd) > 4 else '*' * len(pwd)

    #             emails_to_send.append({
    #                 'email_to': rec.work_email,
    #                 'name': rec.name,
    #                 'jenis': rec.jns_pegawai or '-',
    #                 'masked_password': masked,
    #             })

    #             success_count += 1

    #         except Exception as e:
    #             _logger.exception("Error aktivasi akun untuk %s", rec.name)
    #             skipped_records.append({
    #                 'name': rec.name or 'Tanpa Nama',
    #                 'reason': str(e)[:100]
    #             })

    #     if emails_to_send:
    #         self.with_delay(priority=10).send_activation_emails_batch(emails_to_send)
        
    #     message_parts = []
    #     if success_count:
    #         message_parts.append(f'✓ Success: {success_count} akun berhasil diaktifkan')
    #     if skipped_records:
    #         message_parts.append(f'\n\n⚠ Warning: {len(skipped_records)} akun dilewati:')
    #         for i, s in enumerate(skipped_records[:7], 1):
    #             message_parts.append(f'\n  • {s["name"]}: {s["reason"]}')
    #         if len(skipped_records) > 7:
    #             message_parts.append(f'\n  • ... dan {len(skipped_records) - 7} lainnya')
    #     if emails_to_send:
    #         message_parts.append('\n\nℹ Info: Email sedang dikirim di latar belakang...')
    #         message_parts.append('\n(Anda dapat melanjutkan pekerjaan tanpa perlu menunggu)')
    #     if success_count and not skipped_records:
    #         message_parts.append('\n\n✓ Semua akun berhasil diaktifkan!')

    #     message = ''.join(message_parts) if message_parts else 'Tidak ada perubahan.'
    #     title = 'Aktivasi Akun Selesai!' if success_count else 'Tidak Ada yang Diaktifkan'

    #     # Buat wizard record
    #     wizard = self.env['activation.result.wizard'].create({
    #         'message': message,
    #     })

    #     # Return wizard pop-up
    #     return {
    #         'name': title,
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'activation.result.wizard',
    #         'res_id': wizard.id,
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': self.env.context,
    #     }
    def activate_account_action(self):
        """
        Aktivasi massal akun karyawan — VERSI SUPER CEPAT + PROGRESS BAR + QUEUE_JOB
        """
        # ✅ FILTER EMPLOYEE ADMIN DI AWAL - SKIP EMPLOYEE ID=1
        records_to_process = self.filtered(lambda r: r.id != 1)
        admin_records = self - records_to_process
        
        total = len(records_to_process)
        if not total:
            if admin_records:
                raise UserError("Tidak dapat mengaktifkan akun Employee ID=1 (Administrator). Silakan pilih karyawan lain.")
            else:
                raise UserError("Tidak ada karyawan yang dipilih untuk diaktifkan.")

        # ===================================================================
        # 1. CACHE SEMUA GROUP SEKALI DI AWAL (PENTING BANGET!)
        # ===================================================================
        group_refs = {
            'base.group_user': self.env.ref('base.group_user'),
            'base.group_system': self.env.ref('base.group_system'),
            'hr.group_hr_manager': self.env.ref('hr.group_hr_manager'),
            'hr_attendance.group_hr_attendance_officer': self.env.ref('hr_attendance.group_hr_attendance_officer'),
            'pesantren_pendaftaran.group_pendaftaran_manager': self.env.ref('pesantren_pendaftaran.group_pendaftaran_manager'),
            'pesantren_base.group_sekolah_manager': self.env.ref('pesantren_base.group_sekolah_manager'),
            'pesantren_kesantrian.group_kesantrian_manager': self.env.ref('pesantren_kesantrian.group_kesantrian_manager'),
            'pesantren_guru.group_guru_manager': self.env.ref('pesantren_guru.group_guru_manager'),
            'pesantren_guruquran.group_guru_quran_manager': self.env.ref('pesantren_guruquran.group_guru_quran_manager'),
            'pesantren_musyrif.group_musyrif_manager': self.env.ref('pesantren_musyrif.group_musyrif_manager'),
            'pesantren_kesantrian.group_kesantrian_kesehatan': self.env.ref('pesantren_kesantrian.group_kesantrian_kesehatan'),
            'pesantren_kesantrian.group_kesantrian_keamanan': self.env.ref('pesantren_kesantrian.group_kesantrian_keamanan'),
            'account.group_account_manager': self.env.ref('account.group_account_manager'),
            'base.group_partner_manager': self.env.ref('base.group_partner_manager'),
            'base.group_allow_export': self.env.ref('base.group_allow_export'),

            # Staff & User groups
            'pesantren_guruquran.group_guru_quran_staff': self.env.ref('pesantren_guruquran.group_guru_quran_staff'),
            'pesantren_guru.group_guru_staff': self.env.ref('pesantren_guru.group_guru_staff'),
            'pesantren_musyrif.group_musyrif_staff': self.env.ref('pesantren_musyrif.group_musyrif_staff'),
            'pesantren_guru.group_guru_user': self.env.ref('pesantren_guru.group_guru_user'),
            'pesantren_guruquran.group_guru_quran_user': self.env.ref('pesantren_guruquran.group_guru_quran_user'),
            'pesantren_kesantrian.group_kesantrian_user': self.env.ref('pesantren_kesantrian.group_kesantrian_user'),
            'pesantren_base.group_sekolah_user': self.env.ref('pesantren_base.group_sekolah_user'),
            'pesantren_base.group_hr_employee_readonly': self.env.ref('pesantren_base.group_hr_employee_readonly'),
        }

        # Mapping jenis pegawai → list XMLID group
        GROUP_MAPPING = {
            'superadmin': [
                'base.group_system', 'hr.group_hr_manager', 'hr_attendance.group_hr_attendance_officer',
                'pesantren_pendaftaran.group_pendaftaran_manager', 'pesantren_base.group_sekolah_manager',
                'pesantren_kesantrian.group_kesantrian_manager', 'pesantren_guru.group_guru_manager',
                'pesantren_guruquran.group_guru_quran_manager', 'pesantren_musyrif.group_musyrif_manager',
                'pesantren_kesantrian.group_kesantrian_kesehatan', 'pesantren_kesantrian.group_kesantrian_keamanan',
                'account.group_account_manager', 'base.group_partner_manager', 'base.group_allow_export',
            ],
            'guruquran': ['pesantren_guruquran.group_guru_quran_staff', 'pesantren_guru.group_guru_user',
                        'pesantren_kesantrian.group_kesantrian_user', 'pesantren_base.group_sekolah_user',
                        'pesantren_base.group_hr_employee_readonly', 'base.group_allow_export'],
            'guru': ['pesantren_guru.group_guru_staff', 'pesantren_guruquran.group_guru_quran_user',
                    'pesantren_base.group_sekolah_user', 'pesantren_kesantrian.group_kesantrian_user',
                    'pesantren_base.group_hr_employee_readonly', 'base.group_allow_export'],
            'guru,guruquran': ['pesantren_guru.group_guru_staff', 'pesantren_guruquran.group_guru_quran_staff',
                            'pesantren_kesantrian.group_kesantrian_user', 'pesantren_base.group_sekolah_user',
                            'pesantren_base.group_hr_employee_readonly', 'base.group_allow_export'],
            'musyrif,guru': ['pesantren_musyrif.group_musyrif_staff', 'pesantren_guru.group_guru_staff',
                            'pesantren_guruquran.group_guru_quran_user', 'pesantren_kesantrian.group_kesantrian_user',
                            'pesantren_base.group_sekolah_user', 'pesantren_base.group_hr_employee_readonly',
                            'base.group_allow_export'],
            'musyrif,guruquran': ['pesantren_musyrif.group_musyrif_staff', 'pesantren_guruquran.group_guru_quran_staff',
                                'pesantren_guru.group_guru_user', 'pesantren_kesantrian.group_kesantrian_user',
                                'pesantren_base.group_sekolah_user', 'pesantren_base.group_hr_employee_readonly',
                                'base.group_allow_export'],
            'musyrif,guru,guruquran': ['pesantren_musyrif.group_musyrif_staff', 'pesantren_guru.group_guru_staff',
                                    'pesantren_guruquran.group_guru_quran_staff', 'pesantren_kesantrian.group_kesantrian_user',
                                    'pesantren_base.group_sekolah_user', 'pesantren_base.group_hr_employee_readonly',
                                    'base.group_allow_export'],
            'musyrif': ['pesantren_musyrif.group_musyrif_staff', 'pesantren_kesantrian.group_kesantrian_user',
                        'pesantren_base.group_sekolah_user', 'pesantren_base.group_hr_employee_readonly',
                        'base.group_allow_export'],
            'keamanan': ['pesantren_kesantrian.group_kesantrian_keamanan', 'pesantren_kesantrian.group_kesantrian_user',
                        'pesantren_base.group_sekolah_user', 'pesantren_base.group_hr_employee_readonly',
                        'base.group_allow_export'],
        }

        # Default groups (jika jenis pegawai tidak cocok)
        DEFAULT_GROUPS = [
            'pesantren_base.group_sekolah_user', 'pesantren_kesantrian.group_kesantrian_user',
            'pesantren_base.group_hr_employee_readonly', 'base.group_allow_export'
        ]

        success_count = 0
        skipped_records = []
        emails_to_send = []

        for rec in records_to_process.with_progress(
            msg=f"Sedang mengaktifkan akun karyawan ({total} akun)...",
            total=total,
            cancellable=True
        ):
            # Validasi wajib
            if not rec.work_email or not rec.password or not rec.name:
                skipped_records.append({
                    'name': rec.name or 'Tanpa Nama',
                    'reason': 'Email / Password / Nama belum diisi'
                })
                continue

            user = self.env['res.users'].sudo().search([('login', '=', rec.work_email)], limit=1)
            if not user:
                skipped_records.append({
                    'name': rec.name,
                    'reason': f'User tidak ditemukan: {rec.work_email}'
                })
                continue

            try:
                # Tentukan group yang harus diberikan
                jenis = rec.jns_pegawai or ''
                group_xmlids = ['base.group_user']  # selalu ada

                # 🔧 PERBAIKAN: Gunakan exact match agar konsisten dengan activate_account()
                if jenis in GROUP_MAPPING:
                    group_xmlids.extend(GROUP_MAPPING[jenis])
                else:
                    # Jika tidak ada exact match → pakai default
                    group_xmlids.extend(DEFAULT_GROUPS)

                # Konversi ke ID nyata
                final_group_ids = [group_refs[x].id for x in group_xmlids if x in group_refs]

                # UPDATE USER — SEKALI JALAN (super cepat!)
                user.write({
                    'groups_id': [(6, 0, final_group_ids)],
                    'password': rec.password,
                })

                # Mask password untuk email
                pwd = rec.password
                masked = pwd[:2] + '*' * max(0, len(pwd) - 4) + pwd[-2:] if len(pwd) > 4 else '*' * len(pwd)

                emails_to_send.append({
                    'email_to': rec.work_email,
                    'name': rec.name,
                    'jenis': rec.jns_pegawai or '-',
                    'masked_password': masked,
                })

                success_count += 1

            except Exception as e:
                _logger.exception("Error aktivasi akun untuk %s", rec.name)
                skipped_records.append({
                    'name': rec.name or 'Tanpa Nama',
                    'reason': str(e)[:100]
                })

        # Tambahkan admin records ke skipped jika ada
        for admin_rec in admin_records:
            skipped_records.append({
                'name': admin_rec.name or 'Administrator',
                'reason': 'Employee ID=1 (Administrator) tidak dapat dimodifikasi'
            })

        if emails_to_send:
            self.with_delay(priority=10).send_activation_emails_batch(emails_to_send)
        
        message_parts = []
        if success_count:
            message_parts.append(f'✓ Success: {success_count} akun berhasil diaktifkan')
        if skipped_records:
            message_parts.append(f'\n\n⚠ Warning: {len(skipped_records)} akun dilewati:')
            for i, s in enumerate(skipped_records[:7], 1):
                message_parts.append(f'\n  • {s["name"]}: {s["reason"]}')
            if len(skipped_records) > 7:
                message_parts.append(f'\n  • ... dan {len(skipped_records) - 7} lainnya')
        if emails_to_send:
            message_parts.append('\n\nℹ Info: Email sedang dikirim di latar belakang...')
            message_parts.append('\n(Anda dapat melanjutkan pekerjaan tanpa perlu menunggu)')
        if success_count and not skipped_records:
            message_parts.append('\n\n✓ Semua akun berhasil diaktifkan!')

        message = ''.join(message_parts) if message_parts else 'Tidak ada perubahan.'
        title = 'Aktivasi Akun Selesai!' if success_count else 'Tidak Ada yang Diaktifkan'

        # Buat wizard record
        wizard = self.env['activation.result.wizard'].create({
            'message': message,
        })

        # Return wizard pop-up
        return {
            'name': title,
            'type': 'ir.actions.act_window',
            'res_model': 'activation.result.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }

    @api.model
    def send_activation_emails_batch(self, emails_data):
        """
        Method yang di-queue untuk kirim email batch di background.
        Dipanggil via with_delay() → tidak blocking UI!
        """
        mail_values = []
        for data in emails_data:
            mail_values.append({
                'subject': 'Akun Anda Telah Diaktifkan',
                'email_to': data['email_to'],
                'body_html': f'''
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; background:#f9f9f9; padding:20px; border-radius:10px;">
                        <h2 style="color:#0078d7;">Assalamualaikum Wr. Wb,</h2>
                        <p>Selamat! Akun Anda telah berhasil diaktifkan.</p>
                        <table style="width:100%; background:white; padding:15px; border-radius:8px;">
                            <tr><td><strong>Email</strong></td><td>{data['email_to']}</td></tr>
                            <tr><td><strong>Password</strong></td><td>{data['masked_password']}</td></tr>
                            <tr><td><strong>Jenis Akun</strong></td><td>{data['jenis']}</td></tr>
                            <tr><td><strong>Tanggal</strong></td><td>{fields.Datetime.now().strftime("%d/%m/%Y %H:%M")}</td></tr>
                        </table>
                        <p style="text-align:center; margin:20px 0;">
                            <a href="https://aplikasi.dqi.ac.id/login" style="background:#0078d7; color:white; padding:12px 30px; text-decoration:none; border-radius:6px;">
                                Masuk Sekarang
                            </a>
                        </p>
                        <p>Hubungi tim IT (0822 5207 9785) jika ada kendala.</p>
                        <hr>
                        <small>&copy; 2025 Pesantren Tahfizh Daarul Qur'an Istiqomah</small>
                    </div>
                '''
            })

        if mail_values:
            mails = self.env['mail.mail'].sudo().create(mail_values)
            mails.send()
            _logger.info("Batch email aktivasi berhasil dikirim untuk %d penerima", len(emails_data))

class pendidikan_guru(models.Model):
    _name               = 'edu.employee'
    _description        = 'Riwayat Pendidikan Guru'

    name                = fields.Char(string='Nama Institusi')
    jenjang             = fields.Selection(string='Jenjang', selection=[('sd', 'SD/MI'), ('smp', 'SMP/MTS'),('sma', 'SMA/MA'),('diploma', 'D1/D2/D3'),('sarjana', 'D4/S1'),('pasca', 'S2/S3'),('lainnya', 'Lainnya/Non Formal')])
    fakultas            = fields.Char(string='Fakultas/Jurusan')
    gelar               = fields.Char(string='Gelar')
    karya_ilmiah        = fields.Char(string='Skripsi/Tesis/Disertasi')
    lulus               = fields.Date(string='Lulus')
    employee_id         = fields.Many2one(comodel_name="hr.employee",  string="Guru/Karyawan",  help="")
    