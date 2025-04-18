# from odoo import api, fields, models

# class Tagihan(models.Model):
#     _inherit = "account.move"
           
#     activate_automation = fields.Boolean(
#         string="Tagihan Otomatis", 
#         help="Jika diaktifkan, maka jika ada tagihan yang melebihi tenggat waktu, sistem akan otomatis menggunakan uang saku sebagai pembayaran tagihan."
#     )
    
    
# from odoo import api, fields, models
# from odoo.exceptions import UserError

# class Tagihan(models.Model):
#     _inherit = "account.move"

#     activate_automation = fields.Boolean(
#         string="Tagihan Otomatis", 
#         help="Jika diaktifkan, maka jika ada tagihan yang melebihi tenggat waktu, sistem akan otomatis menggunakan uang saku sebagai pembayaran tagihan."
#     )


#     def kirimemail_saldodipotong(self):
#         ortu_email = self.orangtua_id.partner_id.email

#         subject = f"Saldo Saku {self.partner_id.name} telah dipotong untuk membayar tagihan"

#         tagihan_table = ""

#         for line in self.invoice_line_ids:
#             product = line.product_id.name or ''
#             qty = line.quantity or 0
#             price_unit = line.price_unit or 0
#             tax = ", ".join(line.tax_ids.mapped('name')) or '0%'
#             subtotal = line.price_subtotal or 0

#             harga_format = f"Rp {price_unit:,.0f}".replace(",", ".")
#             subtotal_format = f"Rp {subtotal:,.0f}".replace(",", ".")

#             tagihan_table += f"""
#                 <tr>    
#                     <td style="padding: 8px; border-bottom: 1px solid #eee; word-break: break-word;">{product}</td>
#                     <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">{qty}</td>
#                     <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">{harga_format}</td>
#                     <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">{tax}</td>
#                     <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">{subtotal_format}</td>
#                 </tr>
#             """

#         santri = self.partner_id.name
#         batas_waktu = self.invoice_date_due
#         nomor_tagihan = self.name
#         subtotal_semua = f"Rp {self.amount_untaxed:,.0f}".replace(",", ".")
#         pajak_semua = f"Rp {self.amount_tax:,.0f}".replace(",", ".")
#         total_semua = f"Rp {self.amount_total:,.0f}".replace(",", ".")

#         body_html = f"""
#         <!DOCTYPE html>
#                 <html>
#                 <head>
#                     <meta charset="UTF-8">
#                     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#                     <style>
#                         @media only screen and (max-width: 600px) {{
#                             table {{
#                                 width: 100% !important;
#                             }}
#                             .main-container {{
#                                 width: 100% !important;
#                                 padding: 10px !important;
#                             }}
#                             .content {{
#                                 padding: 15px !important;
#                             }}
#                             .invoice-table {{
#                                 font-size: 12px !important;
#                             }}
#                             .invoice-table th, .invoice-table td {{
#                                 padding: 6px 4px !important;
#                             }}
#                         }}
#                     </style>
#                 </head>
#                 <body style="margin: 0; padding: 0; font-family: Arial, sans-serif;">
#                     <div class="main-container" style="background-color: #f5f8fa; padding: 20px; width: 100%; box-sizing: border-box;">
#                         <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow: hidden;">
#                             <!-- Header -->
#                             <div style="background-color: #005299; color: #ffffff; text-align: center; padding: 20px;">
#                                 <img src="https://i.ibb.co.com/SmWmBTW/SAVE-20220114-075750-removebg-preview-4.png" alt="Logo" style="margin:0 0 15px 0;box-sizing:border-box;vertical-align:middle;width: 60px; height: 60px; margin-bottom: 15px;" width="60">
#                                 <h1 style="margin: 0; font-size: 20px; font-weight: 600;">Pesantren Daarul Qur'an Istiqomah</h1>
#                             </div>
                            
#                             <!-- Content -->
#                             <div class="content" style="padding: 20px;">
#                                 <p style="font-size: 16px; line-height: 1.6; color: #333333; margin-top: 0;">Assalamualaikum,</p>
                                
#                                 <p style="font-size: 16px; line-height: 1.6; color: #333333;">Dengan ini kami informasikan bahwa saldo uang saku telah dipotong untuk membayar tagihan berikut :</p>
                                
#                                 <div style="background-color: #f8f9fa; border-left: 4px solid #005299; padding: 15px; margin: 20px 0; border-radius: 4px;">
#                                     <h3 style="margin-top: 0; color: #005299; font-size: 18px;">Detail Tagihan</h3>
#                                     <p style="margin: 5px 0;"><strong>Nomor Tagihan:</strong> {nomor_tagihan}</p>
#                                     <p style="margin: 5px 0;"><strong>Tanggal:</strong> {batas_waktu}</p>
#                                     <p style="margin: 5px 0;"><strong>Santri:</strong> {santri}</p>
                                    
#                                     <div style="overflow-x: auto; margin-top: 15px;">
#                                         <table class="invoice-table" style="width: 100%; border-collapse: collapse; min-width: 100%;">
#                                             <thead>
#                                                 <tr style="background-color: #eef2f7;">
#                                                     <th style="padding: 8px 6px; text-align: left; font-size: 14px;">Produk</th>
#                                                     <th style="padding: 8px 6px; text-align: left; font-size: 14px;">Kuantitas</th>
#                                                     <th style="padding: 8px 6px; text-align: center; font-size: 14px;">Harga</th>
#                                                     <th style="padding: 8px 6px; text-align: right; font-size: 14px;">Pajak</th>
#                                                     <th style="padding: 8px 6px; text-align: right; font-size: 14px;">Jumlah</th>
#                                                 </tr>
#                                             </thead>
#                                             <tbody>
#                                                 {tagihan_table}
#                                             </tbody>
#                                         </table>
#                                     </div>
                                    
#                                     <div style="margin-top: 20px; border-top: 1px solid #eee; padding-top: 10px; text-align: right;">
#                                         <p style="font-size: 16px; margin: 5px 0;">Jumlah Sebelum Pajak: <strong>{subtotal_semua}</strong></p>
#                                         <p style="font-size: 16px; margin: 5px 0;">Pajak: <strong>{pajak_semua}</p>
#                                         <p style="font-size: 18px; font-weight: bold; margin: 10px 0;">Total: <strong>{total_semua}</strong></p>
#                                     </div>
#                                 </div>
                                
#                                 <p style="font-size: 16px; line-height: 1.6; color: #333333;">Kami sangat menghargai kerja sama Bapak/Ibu, dan berharap proses pembayaran tagihan dapat berjalan lebih lancar dan tepat waktu di masa mendatang</p>
#                             </div>
                            
#                             <div style="background-color: #f0f4f8; text-align: center; padding: 15px; color: #666666; font-size: 14px; border-top: 1px solid #e7eaec;">
#                                 <p style="margin: 5px 0;">Pesantren Daarul Qur'an Istiqomah</p>
#                             </div>
#                         </div>
#                     </div>
#                 </body>
#                 </html>
#                 """ 

#         email_values = {
#             'subject': subject,
#             'email_to': ortu_email,
#             'body_html': body_html
#         }
#         self.env['mail.mail'].create(email_values).send()

#     def email_saldosaku_tidakcukup(self):
        
#         ortu_email = self.orangtua_id.partner_id.email

#         subject = f"Saldo saku Tidak Cukup"
#         body_html = f"""
#             <div style="background-color: #f5f8fa; padding: 30px; font-family: 'Arial', sans-serif;">
#                 <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow: hidden;">
#                     <div style="background-color: #005299; color: #ffffff; text-align: center; padding: 30px;">
#                         <img src="https://i.ibb.co.com/SmWmBTW/SAVE-20220114-075750-removebg-preview-4.png" alt="Logo" style="margin:0 0 15px 0;box-sizing:border-box;vertical-align:middle;width: 80px; height: 80px; margin-bottom: 15px;" width="80">
#                         <h1 style="margin: 0; font-size: 24px; font-weight: 600;">Pesantren Daarul Qur'an Istiqomah</h1>
#                     </div>
#                     <div style="padding: 30px;">
#                         <p style="font-size: 16px; line-height: 1.6; color: #333333; margin-top: 0;">Assalamualaikum,</p>
                        
#                         <p style="font-size: 16px; line-height: 1.6; color: #333333;">Dengan ini kami informasikan bahwa saldo uang saku telah dipotong untuk membayar tagihan berikut</p>
                        
#                         <div style="background-color: #f8f9fa; border-left: 4px solid #005299; padding: 15px; margin: 20px 0; border-radius: 4px;">
#                         </div>
                        
#                         <p style="font-size: 16px; line-height: 1.6; color: #333333;">Terima kasih.</p>
#                     </div>
#                     <div style="background-color: #f0f4f8; text-align: center; padding: 15px; color: #666666; font-size: 14px; border-top: 1px solid #e7eaec;">
#                         <p style="margin: 5px 0;">Pesantren Daarul Qur'an Istiqomah</p>
#                     </div>
#                 </div>
#             </div>
#         """ 

#         email_values = {
#             'subject': subject,
#             'email_to': ortu_email,
#             'body_html': body_html,
#         }
#         self.env['mail.mail'].create(email_values).send()

#     def action_post(self):
#         """ Override action_post untuk mengecek tagihan otomatis dan memotong saldo uang saku """
#         super(Tagihan, self).action_post()

#         for invoice in self:
#             if invoice.activate_automation and invoice.invoice_date_due and invoice.invoice_date_due <= fields.Date.today():
#                 partner = invoice.partner_id
#                 if not partner:
#                     raise UserError("Tidak ada pelanggan yang terkait dengan tagihan ini.")
#                 saldo_saku = partner.saldo_uang_saku

#                 if saldo_saku >= invoice.amount_total:
#                     self._bayar_dengan_saku(invoice, partner)
#                     self.kirimemail_saldodipotong()
#                 else:
#                     self.email_saldosaku_tidakcukup()
#                     # raise UserError(f"Saldo uang saku ({saldo_saku}) tidak mencukupi untuk membayar tagihan sebesar {invoice.amount_total}.")
    
#     def _bayar_dengan_saku(self, invoice, partner):
#         """ Membayar tagihan menggunakan saldo uang saku tanpa metode pembayaran """
#         # Kurangi saldo uang saku
#         partner.saldo_uang_saku -= invoice.amount_total

#         # Cek apakah jurnal "Faktur Pelanggan" tersedia
#         journal = self.env['account.journal'].search([('name', '=', 'Faktur Pelanggan')], limit=1)
#         if not journal:
#             raise UserError("Jurnal 'Faktur Pelanggan' tidak ditemukan. Pastikan jurnal tersedia di konfigurasi.")

#         # Buat entri jurnal langsung tanpa metode pembayaran
#         move_vals = {
#             'move_type': 'entry',
#             'journal_id': journal.id,
#             'date': fields.Date.today(),
#             'line_ids': [
#                 (0, 0, {
#                     'account_id': invoice.line_ids[0].account_id.id,
#                     'partner_id': partner.id,
#                     'name': f"Pembayaran otomatis tagihan {invoice.name}",
#                     'debit': invoice.amount_total,
#                     'credit': 0.0,
#                 }),
#                 (0, 0, {
#                     'account_id': journal.default_account_id.id,
#                     'partner_id': partner.id,
#                     'name': f"Pengurangan saldo uang saku {invoice.name}",
#                     'debit': 0.0,
#                     'credit': invoice.amount_total,
#                 }),
#             ]
#         }
        
#         payment_move = self.env['account.move'].create(move_vals)
#         payment_move.action_post()

#         # Tandai invoice sebagai lunas
#         invoice.payment_state = 'paid'





from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import timedelta, datetime

class Tagihan(models.Model):
    _inherit = "account.move"

    activate_automation = fields.Boolean(
        string="Tagihan Otomatis", 
        help="Jika diaktifkan, maka jika ada tagihan yang melebihi tenggat waktu, sistem akan otomatis menggunakan uang saku sebagai pembayaran tagihan."
    )



    siswa_id         = fields.Many2one(comodel_name='cdn.siswa', string='Santri', required=True)

    barcode          = fields.Char(string="Kartu Santri",readonly=False)

    kelas_id         = fields.Many2one('cdn.ruang_kelas', string='Kelas', related='siswa_id.ruang_kelas_id', readonly=True, store=True)
    kamar_id         = fields.Many2one('cdn.kamar_santri', string='Kamar', related='siswa_id.kamar_id', readonly=True)
    halaqoh_id       = fields.Many2one('cdn.halaqoh', string='Halaqoh', related='siswa_id.halaqoh_id', readonly=True)
    musyrif_id       = fields.Many2one('hr.employee', string='Musyrif', related='siswa_id.musyrif_id', readonly=True)


    @api.onchange('siswa_id')
    def _onchange_siswa_id(self):
        if self.siswa_id:
            self.barcode = self.siswa_id.barcode_santri
            self.partner_id = self.siswa_id.partner_id
        else:
            self.barcode = False

    @api.onchange('barcode')
    def _onchange_barcode(self):
        if self.barcode:
            siswa = self.env['cdn.siswa'].search([('barcode_santri', '=', self.barcode)], limit=1)
            if siswa:
                self.siswa_id = siswa.id
                self.partner_id = self.siswa_id.partner_id
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
            self.barcode = False
            self.siswa_id = False

    barcode = fields.Char(string="Barcode")

    def kirimemail_saldodipotong(self):
        ortu_email = self.orangtua_id.partner_id.email

        subject = f"Saldo Saku {self.partner_id.name} telah dipotong untuk membayar tagihan"

        # Ambil email dari model cdn.siswa
        ayah_email = self.siswa_id.ayah_email or ''
        ibu_email = self.siswa_id.ibu_email or ''
        wali_email = self.siswa_id.wali_email or ''

        # Tentukan email penerima: Ayah dan Ibu dulu, jika kosong baru ke Wali
        email_penerima = []
        
        if ayah_email:
            email_penerima.append(ayah_email)
        if ibu_email:
            email_penerima.append(ibu_email)
        
        # Jika kedua orang tua tidak memiliki email, gunakan email wali
        if not email_penerima and wali_email:
            email_penerima.append(wali_email)

        if not email_penerima:
            return  # Jika tidak ada email penerima, tidak perlu mengirim email


        tagihan_table = ""

        for line in self.invoice_line_ids:
            product = line.product_id.name or ''
            qty = line.quantity or 0
            price_unit = line.price_unit or 0
            tax = ", ".join(line.tax_ids.mapped('name')) or '0%'
            subtotal = line.price_subtotal or 0

            harga_format = f"Rp {price_unit:,.0f}".replace(",", ".")
            subtotal_format = f"Rp {subtotal:,.0f}".replace(",", ".")

            tagihan_table += f"""
                <tr>    
                    <td style="padding: 8px; border-bottom: 1px solid #eee; word-break: break-word;">{product}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">{qty}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">{harga_format}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">{tax}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">{subtotal_format}</td>
                </tr>
            """

        santri = self.partner_id.name
        batas_waktu = self.invoice_date_due
        nomor_tagihan = self.name
        subtotal_semua = f"Rp {self.amount_untaxed:,.0f}".replace(",", ".")
        pajak_semua = f"Rp {self.amount_tax:,.0f}".replace(",", ".")
        total_semua = f"Rp {self.amount_total:,.0f}".replace(",", ".")

        body_html = f"""
        <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        @media only screen and (max-width: 600px) {{
                            table {{
                                width: 100% !important;
                            }}
                            .main-container {{
                                width: 100% !important;
                                padding: 10px !important;
                            }}
                            .content {{
                                padding: 15px !important;
                            }}
                            .invoice-table {{
                                font-size: 12px !important;
                            }}
                            .invoice-table th, .invoice-table td {{
                                padding: 6px 4px !important;
                            }}
                        }}
                    </style>
                </head>
                <body style="margin: 0; padding: 0; font-family: Arial, sans-serif;">
                    <div class="main-container" style="background-color: #f5f8fa; padding: 20px; width: 100%; box-sizing: border-box;">
                        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow: hidden;">
                            <!-- Header -->
                            <div style="background-color: #005299; color: #ffffff; text-align: center; padding: 20px;">
                                <img src="https://i.ibb.co.com/SmWmBTW/SAVE-20220114-075750-removebg-preview-4.png" alt="Logo" style="margin:0 0 15px 0;box-sizing:border-box;vertical-align:middle;width: 60px; height: 60px; margin-bottom: 15px;" width="60">
                                <h1 style="margin: 0; font-size: 20px; font-weight: 600;">Pesantren Daarul Qur'an Istiqomah</h1>
                            </div>
                            
                            <!-- Content -->
                            <div class="content" style="padding: 20px;">
                                <p style="font-size: 16px; line-height: 1.6; color: #333333; margin-top: 0;">Assalamualaikum,</p>
                                
                                <p style="font-size: 16px; line-height: 1.6; color: #333333;">Dengan ini kami informasikan bahwa saldo uang saku telah dipotong untuk membayar tagihan berikut :</p>
                                
                                <div style="background-color: #f8f9fa; border-left: 4px solid #005299; padding: 15px; margin: 20px 0; border-radius: 4px;">
                                    <h3 style="margin-top: 0; color: #005299; font-size: 18px;">Detail Tagihan</h3>
                                    <p style="margin: 5px 0;"><strong>Nomor Tagihan:</strong> {nomor_tagihan}</p>
                                    <p style="margin: 5px 0;"><strong>Tanggal:</strong> {batas_waktu}</p>
                                    <p style="margin: 5px 0;"><strong>Santri:</strong> {santri}</p>
                                    
                                    <div style="overflow-x: auto; margin-top: 15px;">
                                        <table class="invoice-table" style="width: 100%; border-collapse: collapse; min-width: 100%;">
                                            <thead>
                                                <tr style="background-color: #eef2f7;">
                                                    <th style="padding: 8px 6px; text-align: left; font-size: 14px;">Produk</th>
                                                    <th style="padding: 8px 6px; text-align: left; font-size: 14px;">Kuantitas</th>
                                                    <th style="padding: 8px 6px; text-align: center; font-size: 14px;">Harga</th>
                                                    <th style="padding: 8px 6px; text-align: right; font-size: 14px;">Pajak</th>
                                                    <th style="padding: 8px 6px; text-align: right; font-size: 14px;">Jumlah</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {tagihan_table}
                                            </tbody>
                                        </table>
                                    </div>
                                    
                                    <div style="margin-top: 20px; border-top: 1px solid #eee; padding-top: 10px; text-align: right;">
                                        <p style="font-size: 16px; margin: 5px 0;">Jumlah Sebelum Pajak: <strong>{subtotal_semua}</strong></p>
                                        <p style="font-size: 16px; margin: 5px 0;">Pajak: <strong>{pajak_semua}</p>
                                        <p style="font-size: 18px; font-weight: bold; margin: 10px 0;">Total: <strong>{total_semua}</strong></p>
                                    </div>
                                </div>
                                
                                <p style="font-size: 16px; line-height: 1.6; color: #333333;">Kami sangat menghargai kerja sama Bapak/Ibu, dan berharap proses pembayaran tagihan dapat berjalan lebih lancar dan tepat waktu di masa mendatang</p>
                            </div>
                            
                            <div style="background-color: #f0f4f8; text-align: center; padding: 15px; color: #666666; font-size: 14px; border-top: 1px solid #e7eaec;">
                                <p style="margin: 5px 0;">Pesantren Daarul Qur'an Istiqomah</p>
                            </div>
                        </div>
                    </div>
                </body>
                </html>
                """ 

        # Kirim email
        self.env['mail.mail'].create({
            'subject': subject,
            'email_to': ','.join(email_penerima),
            'body_html': body_html,
        }).send()
        


    def email_saldosaku_tidakcukup(self):
        """Mengirim email jika saldo uang saku tidak cukup, sekali per hari."""
        today = fields.Date.today()
        last_email = self.env['mail.activity'].search([
            ('res_id', '=', self.id),
            ('res_model', '=', 'account.move'),
            ('activity_type_id', '=', self.env.ref('mail.mail_activity_data_email').id),
            ('date_deadline', '=', today)
        ], limit=1)

        if last_email:
            return  # Jangan kirim email lagi hari ini

        # Ambil email dari model cdn.siswa
        ayah_email = self.siswa_id.ayah_email or ''
        ibu_email = self.siswa_id.ibu_email or ''
        wali_email = self.siswa_id.wali_email or ''

        # Tentukan email penerima: Ayah dan Ibu dulu, jika kosong baru ke Wali
        email_penerima = []
        
        if ayah_email:
            email_penerima.append(ayah_email)
        if ibu_email:
            email_penerima.append(ibu_email)
        
        # Jika kedua orang tua tidak memiliki email, gunakan email wali
        if not email_penerima and wali_email:
            email_penerima.append(wali_email)

        if not email_penerima:
            return  # Jika tidak ada email penerima, tidak perlu mengirim email

        # Buat tabel tagihan
        tagihan_table = ""
        for line in self.invoice_line_ids:
            product = line.product_id.name or ''
            qty = line.quantity or 0
            price_unit = line.price_unit or 0
            tax = ", ".join(line.tax_ids.mapped('name')) or '0%'
            subtotal = line.price_subtotal or 0

            harga_format = f"Rp {price_unit:,.0f}".replace(",", ".")
            subtotal_format = f"Rp {subtotal:,.0f}".replace(",", ".")

            tagihan_table += f"""
                <tr>    
                    <td style="padding: 8px; border-bottom: 1px solid #eee; word-break: break-word;">{product}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">{qty}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">{harga_format}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">{tax}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">{subtotal_format}</td>
                </tr>
            """

        santri = self.partner_id.name
        batas_waktu = self.invoice_date_due
        nomor_tagihan = self.name
        subtotal_semua = f"Rp {self.amount_untaxed:,.0f}".replace(",", ".")
        pajak_semua = f"Rp {self.amount_tax:,.0f}".replace(",", ".")
        total_semua = f"Rp {self.amount_total:,.0f}".replace(",", ".")

        subject = "Saldo Saku Tidak Cukup"
        body_html = f"""
        <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        @media only screen and (max-width: 600px) {{
                            table {{
                                width: 100% !important;
                            }}
                            .main-container {{
                                width: 100% !important;
                                padding: 10px !important;
                            }}
                            .content {{
                                padding: 15px !important;
                            }}
                            .invoice-table {{
                                font-size: 12px !important;
                            }}
                            .invoice-table th, .invoice-table td {{
                                padding: 6px 4px !important;
                            }}
                        }}
                    </style>
                </head>
                <body style="margin: 0; padding: 0; font-family: Arial, sans-serif;">
                    <div class="main-container" style="background-color: #f5f8fa; padding: 20px; width: 100%; box-sizing: border-box;">
                        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow: hidden;">
                            <!-- Header -->
                            <div style="background-color: #005299; color: #ffffff; text-align: center; padding: 20px;">
                                <img src="https://i.ibb.co.com/SmWmBTW/SAVE-20220114-075750-removebg-preview-4.png" alt="Logo" style="margin:0 0 15px 0;box-sizing:border-box;vertical-align:middle;width: 60px; height: 60px; margin-bottom: 15px;" width="60">
                                <h1 style="margin: 0; font-size: 20px; font-weight: 600;">Pesantren Daarul Qur'an Istiqomah</h1>
                            </div>
                            
                            <!-- Content -->
                            <div class="content" style="padding: 20px;">
                                <p style="font-size: 16px; line-height: 1.6; color: #333333; margin-top: 0;">Assalamualaikum,</p>
                                
                                <p style="font-size: 16px; line-height: 1.6; color: #333333;">Dengan ini kami informasikan bahwa saldo uang saku tidak mencukupi untuk membayar tagihan berikut :</p>
                                
                                <div style="background-color: #f8f9fa; border-left: 4px solid #005299; padding: 15px; margin: 20px 0; border-radius: 4px;">
                                    <h3 style="margin-top: 0; color: #005299; font-size: 18px;">Detail Tagihan</h3>
                                    <p style="margin: 5px 0;"><strong>Nomor Tagihan:</strong> {nomor_tagihan}</p>
                                    <p style="margin: 5px 0;"><strong>Tanggal:</strong> {batas_waktu}</p>
                                    <p style="margin: 5px 0;"><strong>Santri:</strong> {santri}</p>
                                    
                                    <div style="overflow-x: auto; margin-top: 15px;">
                                        <table class="invoice-table" style="width: 100%; border-collapse: collapse; min-width: 100%;">
                                            <thead>
                                                <tr style="background-color: #eef2f7;">
                                                    <th style="padding: 8px 6px; text-align: left; font-size: 14px;">Produk</th>
                                                    <th style="padding: 8px 6px; text-align: left; font-size: 14px;">Kuantitas</th>
                                                    <th style="padding: 8px 6px; text-align: center; font-size: 14px;">Harga</th>
                                                    <th style="padding: 8px 6px; text-align: right; font-size: 14px;">Pajak</th>
                                                    <th style="padding: 8px 6px; text-align: right; font-size: 14px;">Jumlah</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {tagihan_table}
                                            </tbody>
                                        </table>
                                    </div>         
                                    <div style="margin-top: 20px; border-top: 1px solid #eee; padding-top: 10px; text-align: right;">
                                        <p style="font-size: 16px; margin: 5px 0;">Jumlah Sebelum Pajak: <strong>{subtotal_semua}</strong></p>
                                        <p style="font-size: 16px; margin: 5px 0;">Pajak: <strong>{pajak_semua}</p>
                                        <p style="font-size: 18px; font-weight: bold; margin: 10px 0;">Total: <strong>{total_semua}</strong></p>
                                    </div>
                                </div>
                                
                                <p style="font-size: 16px; line-height: 1.6; color: #333333;">Dengan ini kami mohon kerja sama nya dalam pembayaran tagihan yang telah melewati batas waktu. Dimohon untuk segera membayarnya dengan cara topup ke uang saku santri ataupun membayar dengan cara Log In ke akun masing - masing.</p>

                                <p style="font-size: 16px; line-height: 1.6; color: #333333;">Terima Kasih atas kerjasamanya.</p>
                                
                                <p style="font-size: 16px; line-height: 1.6; color: #333333;">Wassalamualaikum Wr Wb.</p>
                            </div>
                            
                            <div style="background-color: #f0f4f8; text-align: center; padding: 15px; color: #666666; font-size: 14px; border-top: 1px solid #e7eaec;">
                                <p style="margin: 5px 0;">Pesantren Daarul Qur'an Istiqomah</p>
                            </div>
                        </div>
                    </div>
                </body>
                </html>
                """  

        # Kirim email
        self.env['mail.mail'].create({
            'subject': subject,
            'email_to': ','.join(email_penerima),
            'body_html': body_html,
        }).send()

        # Catat aktivitas
        self.env['mail.activity'].create({
            'res_id': self.id,
            'res_model_id': self.env['ir.model']._get_id('account.move'),
            'activity_type_id': self.env.ref('mail.mail_activity_data_email').id,
            'summary': 'Pemberitahuan Saldo Tidak Cukup.',
            'date_deadline': today,
            'user_id': self.env.user.id,
        })




    def email_pemberitahuan_tenggat(self):
        """Mengirim email pemberitahuan tenggat waktu 7, 3, dan 1 hari sebelum jatuh tempo."""
        today = fields.Date.today()
        batas_waktu = self.invoice_date_due

        if not batas_waktu:
            return  # Tidak ada tenggat waktu, tidak perlu mengirim email

        delta_days = (batas_waktu - today).days
        if delta_days not in [7, 3, 1]:
            return  # Hanya kirim pada 7, 3, atau 1 hari sebelum tenggat

        # Cek apakah email sudah dikirim hari ini
        last_email = self.env['mail.activity'].search([
            ('res_id', '=', self.id),
            ('res_model', '=', 'account.move'),
            ('activity_type_id', '=', self.env.ref('mail.mail_activity_data_email').id),
            ('date_deadline', '=', today)
        ], limit=1)

        if last_email:
            return  # Jangan kirim email lagi hari ini

        self._kirim_email_tagihan(delta_days)

    def _kirim_email_tagihan(self, delta_days):
        """Fungsi untuk mengirim email tagihan."""
        # Ambil email dari model siswa
        ayah_email = self.siswa_id.ayah_email or ''
        ibu_email = self.siswa_id.ibu_email or ''
        wali_email = self.siswa_id.wali_email or ''

        email_penerima = []
        if ayah_email:
            email_penerima.append(ayah_email)
        if ibu_email:
            email_penerima.append(ibu_email)
        if not email_penerima and wali_email:
            email_penerima.append(wali_email)

        if not email_penerima:
            return  # Tidak ada email penerima, tidak perlu mengirim email

        # Buat tabel tagihan
        tagihan_table = ""
        for line in self.invoice_line_ids:
            product = line.product_id.name or ''
            qty = line.quantity or 0
            price_unit = line.price_unit or 0
            tax = ", ".join(line.tax_ids.mapped('name')) or '0%'
            subtotal = line.price_subtotal or 0

            harga_format = f"Rp {price_unit:,.0f}".replace(",", ".")
            subtotal_format = f"Rp {subtotal:,.0f}".replace(",", ".")

            tagihan_table += f"""
                <tr>    
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{product}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">{qty}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">{harga_format}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">{tax}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">{subtotal_format}</td>
                </tr>
            """

        santri = self.partner_id.name
        nomor_tagihan = self.name
        batas_waktu = self.invoice_date_due
        subtotal_semua = f"Rp {self.amount_untaxed:,.0f}".replace(",", ".")
        pajak_semua = f"Rp {self.amount_tax:,.0f}".replace(",", ".")
        total_semua = f"Rp {self.amount_total:,.0f}".replace(",", ".")

        subject = f"Pengingat Pembayaran Tagihan ({delta_days} Hari Lagi)"
        body_html = f"""
        <html>
        <head>
            <style>
                @media only screen and (max-width: 600px) {{
                    table {{ width: 100% !important; }}
                    .main-container {{ width: 100% !important; padding: 10px !important; }}
                    .content {{ padding: 15px !important; }}
                    .invoice-table {{ font-size: 12px !important; }}
                    .invoice-table th, .invoice-table td {{ padding: 6px 4px !important; }}
                }}
            </style>
        </head>
        <body style="font-family: Arial, sans-serif;">
            <div class="main-container" style="background-color: #f5f8fa; padding: 20px;">
                <div style="max-width: 600px; margin: auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="background-color: #005299; color: #ffffff; text-align: center; padding: 20px;">
                        <h1>Pesantren Daarul Qur'an Istiqomah</h1>
                    </div>
                    <div class="content" style="padding: 20px;">
                        <p>Assalamualaikum,</p>
                        <p>Kami ingin mengingatkan bahwa pembayaran tagihan berikut akan jatuh tempo dalam <strong>{delta_days} hari</strong>:</p>
                        <div style="background-color: #f8f9fa; border-left: 4px solid #005299; padding: 15px; margin: 20px 0; border-radius: 4px;">
                            <h3>Detail Tagihan</h3>
                            <p><strong>Nomor Tagihan:</strong> {nomor_tagihan}</p>
                            <p><strong>Tanggal Jatuh Tempo:</strong> {batas_waktu}</p>
                            <p><strong>Santri:</strong> {santri}</p>
                            <table class="invoice-table" style="width: 100%; border-collapse: collapse;">
                                <thead>
                                    <tr style="background-color: #eef2f7;">
                                        <th>Produk</th>
                                        <th>Kuantitas</th>
                                        <th>Harga</th>
                                        <th>Pajak</th>
                                        <th>Jumlah</th>
                                    </tr>
                                </thead>
                                <tbody>{tagihan_table}</tbody>
                            </table>
                            <div style="margin-top: 20px; text-align: right;">
                                <p>Jumlah Sebelum Pajak: <strong>{subtotal_semua}</strong></p>
                                <p>Pajak: <strong>{pajak_semua}</strong></p>
                                <p>Total: <strong>{total_semua}</strong></p>
                            </div>
                        </div>
                        <p>Dimohon untuk segera melakukan pembayaran sebelum jatuh tempo.</p>
                        <p>Terima Kasih.</p>
                        <p>Wassalamualaikum Wr Wb.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        self.env['mail.mail'].create({
            'subject': subject,
            'email_to': ','.join(email_penerima),
            'body_html': body_html,
        }).send()

    @api.model
    def create(self, vals):
        """Kirim email saat tagihan dibuat jika tenggatnya 7 hari dari sekarang."""
        record = super(Tagihan, self).create(vals)
        if 'invoice_date_due' in vals:
            today = fields.Date.today()
            batas_waktu = fields.Date.from_string(vals['invoice_date_due'])
            if (batas_waktu - today).days == 7:
                record._kirim_email_tagihan(7)
            if (batas_waktu - today).days == 3:
                record._kirim_email_tagihan(3)
            if (batas_waktu - today).days == 1:
                record._kirim_email_tagihan(1)
        return record





    def action_post(self):
        super(Tagihan, self).action_post()
        
        for invoice in self:
            if invoice.invoice_date_due and invoice.invoice_date_due <= fields.Date.today():
                partner = invoice.partner_id
                saldo_saku = partner.saldo_uang_saku
                
                if saldo_saku >= invoice.amount_total:
                    self._bayar_dengan_saku(invoice, partner)
                    self.kirimemail_saldodipotong()
                else:
                    self.email_saldosaku_tidakcukup()
    
    def _bayar_dengan_saku(self, invoice, partner):
        partner.saldo_uang_saku -= invoice.amount_total
        journal = self.env['account.journal'].search([('name', '=', 'Faktur Pelanggan')], limit=1)
        if not journal:
            raise UserError("Jurnal 'Faktur Pelanggan' tidak ditemukan.")
        
        move_vals = {
            'move_type': 'entry',
            'journal_id': journal.id,
            'date': fields.Date.today(),
            'line_ids': [
                (0, 0, {
                    'account_id': invoice.line_ids[0].account_id.id,
                    'partner_id': partner.id,
                    'name': f"Pembayaran otomatis {invoice.name}",
                    'debit': invoice.amount_total,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'account_id': journal.default_account_id.id,
                    'partner_id': partner.id,
                    'name': f"Pengurangan saldo uang saku {invoice.name}",
                    'debit': 0.0,
                    'credit': invoice.amount_total,
                }),
            ]
        }
        
        payment_move = self.env['account.move'].create(move_vals)
        payment_move.action_post()
        invoice.payment_state = 'paid'
