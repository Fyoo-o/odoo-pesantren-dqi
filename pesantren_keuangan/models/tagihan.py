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


# from odoo import api, fields, models
# from odoo.exceptions import UserError
# from datetime import timedelta, datetime
# import logging

# _logger = logging.getLogger(__name__)

# class Tagihan(models.Model):
#     _inherit = "account.move"

#     activate_automation = fields.Boolean(
#         string="Tagihan Otomatis", 
#         help="Jika diaktifkan, maka jika ada tagihan yang melebihi tenggat waktu, sistem akan otomatis menggunakan uang saku sebagai pembayaran tagihan."
#     )

#     siswa_id         = fields.Many2one(comodel_name='cdn.siswa', string='Santri', required=True)
#     barcode          = fields.Char(string="Kartu Santri", readonly=False)
#     ruang_kelas_id   = fields.Many2one('cdn.ruang_kelas', string='Kelas', related='siswa_id.ruang_kelas_id', store=True)
#     kamar_id         = fields.Many2one('cdn.kamar_santri', string='Kamar', related='siswa_id.kamar_id', readonly=True)
#     halaqoh_id       = fields.Many2one('cdn.halaqoh', string='Halaqoh', related='siswa_id.halaqoh_id', readonly=True)
#     musyrif_id       = fields.Many2one('hr.employee', string='Musyrif', related='siswa_id.musyrif_id', readonly=True)
#     # Tambahkan field untuk sekolah santri - tanpa related field untuk menghindari error
#     sekolah_id       = fields.Many2one('ubig.pendidikan', string='Sekolah', readonly=True)
    
#     @api.onchange('siswa_id')
#     def _onchange_siswa_id(self):
#         if self.siswa_id:
#             self.barcode = self.siswa_id.barcode_santri
#             self.partner_id = self.siswa_id.partner_id
            
#             # Set sekolah dengan metode yang lebih aman
#             siswa = self.env['cdn.siswa'].browse(self.siswa_id.id)
#             jenjang = False
#             if siswa:
#                 # Pastikan field jenjang_id ada dan bukan False
#                 pendaftaran = self.env['ubig.pendaftaran'].search([('siswa_id', '=', self.siswa_id.id)], limit=1)
#                 if pendaftaran and pendaftaran.jenjang_id:
#                     self.sekolah_id = pendaftaran.jenjang_id.id if pendaftaran and pendaftaran.jenjang_id else False
#                 else:
#                     self.sekolah_id = False
#         else:
#             self.barcode = False
#             self.sekolah_id = False

#     @api.depends('siswa_id', 'siswa_id.ruang_kelas_id')
#     def _compute_kelas_id(self):
#         for record in self:
#             if record.siswa_id:
#                 record.ruang_kelas_id = record.siswa_id.ruang_kelas_id
#             else:
#                 record.ruang_kelas_id = False

#     @api.onchange('barcode')
#     def _onchange_barcode(self):
#         if self.barcode:
#             siswa = self.env['cdn.siswa'].search([('barcode_santri', '=', self.barcode)], limit=1)
#             if siswa:
#                 self.siswa_id = siswa.id
#                 self.partner_id = siswa.partner_id
                
#                 # Set sekolah dengan metode yang lebih aman
#                 jenjang = False
#                 pendaftaran = self.env['ubig.pendaftaran'].search([('siswa_id', '=', siswa.id)], limit=1)
#                 if pendaftaran and pendaftaran.jenjang_id:
#                     self.sekolah_id = pendaftaran.jenjang_id.id if pendaftaran and pendaftaran.jenjang_id else False
#                 else:
#                     self.sekolah_id = False

#             else:
#                 self.siswa_id = False
#                 self.sekolah_id = False
#                 barcode_sementara = self.barcode
#                 self.barcode = False
#                 return {
#                     'warning': {
#                         'title': "Perhatian !",
#                         'message': f"Data Santri dengan Kartu Santri {barcode_sementara} tidak ditemukan."
#                     }
#                 }
#         else:
#             self.barcode = False
#             self.siswa_id = False
#             self.sekolah_id = False

#     @api.model
#     def create(self, vals):
#         if 'siswa_id' in vals:
#             siswa = self.env['cdn.siswa'].browse(vals['siswa_id'])
#             if siswa:
#                 if not vals.get('barcode'):
#                     vals['barcode'] = siswa.barcode_santri
#                 # Memastikan partner_id terisi saat impor
#                 if not vals.get('partner_id'):
#                     vals['partner_id'] = siswa.partner_id.id
                
#                 # Set sekolah dengan metode yang lebih aman
#                 pendaftaran = self.env['ubig.pendaftaran'].search([('siswa_id', '=', siswa.id)], limit=1)
#                 if pendaftaran and pendaftaran.jenjang_id:
#                     vals['sekolah_id'] = pendaftaran.jenjang_id.id


                    
#         return super(Tagihan, self).create(vals)
    
#     # Menambahkan metode untuk memastikan partner_id terisi pada rekaman yang sudah ada
#     def write(self, vals):
#         res = super(Tagihan, self).write(vals)
        
#         # Jika siswa_id diperbarui, pastikan partner_id juga diperbarui
#         if 'siswa_id' in vals:
#             for record in self:
#                 if record.siswa_id:
#                     if not record.partner_id:
#                         record.partner_id = record.siswa_id.partner_id
                    
#                     # Setel sekolah_id dengan metode yang lebih aman
#                     jenjang_id = False
#                     pendaftaran = self.env['ubig.pendaftaran'].search([('siswa_id', '=', record.siswa_id.id)], limit=1)
#                     if pendaftaran and pendaftaran.jenjang_id:
#                         record.sekolah_id = pendaftaran.jenjang_id.id if pendaftaran and pendaftaran.jenjang_id else False
#                     else:
#                         record.sekolah_id = False

                    
#         return res
    
#     # Fungsi untuk memperbaiki data yang sudah ada tanpa partner_id
#     @api.model
#     def fix_missing_partner_ids(self):
#         """Fungsi ini dapat dipanggil dari menu Developer Tools atau melalui cron job"""
#         moves = self.search([('siswa_id', '!=', False), ('partner_id', '=', False)])
#         for move in moves:
#             if move.siswa_id.partner_id:
#                 move.partner_id = move.siswa_id.partner_id
        
#         return True


from odoo import api, fields, models,_
from odoo.exceptions import UserError
from datetime import timedelta, datetime
import logging

_logger = logging.getLogger(__name__)

class Tagihan(models.Model):
    _inherit = "account.move"

    activate_automation = fields.Boolean(
        string="Tagihan Otomatis", 
        help="Jika diaktifkan, maka jika ada tagihan yang melebihi tenggat waktu, sistem akan otomatis menggunakan uang saku sebagai pembayaran tagihan."
    )

    def action_recover_kerugian_piutang(self):
        pass

    siswa_id         = fields.Many2one(comodel_name='cdn.siswa', string='Santri',ondelete='cascade' , required=True)
    barcode          = fields.Char(string="Kartu Santri",readonly=False)
    ruang_kelas_id   = fields.Many2one('cdn.ruang_kelas', string='Kelas', related='siswa_id.ruang_kelas_id', store=True)
    kamar_id         = fields.Many2one('cdn.kamar_santri', string='Kamar', related='siswa_id.kamar_id', readonly=True)
    halaqoh_id       = fields.Many2one('cdn.halaqoh', string='Halaqoh', related='siswa_id.halaqoh_id', readonly=True)
    musyrif_id       = fields.Many2one('hr.employee', string='Musyrif', related='siswa_id.musyrif_id', readonly=True)
    nama_sekolah     = fields.Selection(selection='_get_nama_sekolah_selection',string='Nama Sekolah',related='siswa_id.nama_sekolah',readonly=True,store=True)

    is_auto_payment = fields.Boolean(string="Pembayaran Otomatis", default=False, help="Menandakan bahwa tagihan ini dibayar secara otomatis")
    auto_payment_date = fields.Date(string="Tanggal Pembayaran Otomatis", readonly=True)

    # @api.model
    # def _run_check_overdue_invoices(self):
    #     # today = fields.Date.today()
    #     today = fields.Date.from_string('2025-05-19')  
        
    #     invoices = self.search([
    #         ('state', '=', 'posted'),
    #         ('payment_state', '!=', 'paid'),
    #         # ('activate_automation', '=', True),
    #         ('amount_residual', '>', 0),
    #         ('invoice_date_due', '<=', today)
    #     ])
        
    #     for invoice in invoices:
    #         partner = invoice.partner_id
    #         saldo_saku = partner.saldo_uang_saku
            
    #         if saldo_saku >= invoice.amount_total:
    #             invoice._bayar_dengan_saku(invoice, partner)
    #             # invoice.kirimemail_saldodipotong()
    #         else:
    #             # invoice.email_saldosaku_tidakcukup()
    #             _logger.info(f"Ini Akan Mengirim Email Saldo Tidak cukup")

        
    #     future_invoices = self.search([
    #         ('state', '=', 'posted'),
    #         ('payment_state', '!=', 'paid')
    #     ])
        
    #     for invoice in future_invoices:
    #         _logger.info(f"Ini akan mengirim email tenggat")
    #         # invoice.email_pemberitahuan_tenggat()


    # @api.model
    # def _run_check_overdue_invoices(self):
    #     today = fields.Date.from_string('2025-05-19')  
        
    #     invoices = self.search([
    #         ('state', '=', 'posted'),
    #         ('payment_state', '!=', 'paid'),
    #         ('amount_residual', '>', 0),
    #         ('invoice_date_due', '<=', today)
    #     ])
        
    #     for invoice in invoices:
    #         partner = invoice.partner_id
    #         saldo_saku = partner.saldo_uang_saku
    #         amount_residual = invoice.amount_residual
            
    #         if saldo_saku >= amount_residual:
    #             # Saldo cukup untuk bayar penuh
    #             invoice._bayar_dengan_saku(invoice, partner, amount_residual)
    #         elif saldo_saku > 0:
    #             # Saldo tidak cukup, tapi bisa bayar sebagian
    #             # Bisa kamu ganti juga ke: `amount_to_pay = amount_residual * 0.5`
    #             amount_to_pay = saldo_saku
    #             invoice._bayar_dengan_saku(invoice, partner, amount_to_pay)
    #             _logger.info(f"Saldo tidak cukup. Membayar sebagian invoice {invoice.name} sebesar {amount_to_pay}")
    #         else:
    #             _logger.info(f"Saldo 0. Tidak bisa bayar invoice {invoice.name}")

    #     future_invoices = self.search([
    #         ('state', '=', 'posted'),
    #         ('payment_state', '!=', 'paid')
    #     ])
        
    #     for invoice in future_invoices:
    #         _logger.info(f"Reminder untuk invoice {invoice.name} akan dikirim (tenggat belum lewat)")



    @api.model
    def _run_check_overdue_invoices(self):
        today = fields.Date.today()
        # today = fields.Date.from_string('2025-05-19')

        invoices = self.search([
            ('state', '=', 'posted'),
            ('payment_state', '!=', 'paid'),
            ('amount_residual', '>', 0),
            ('invoice_date_due', '<=', today)
        ])

        for invoice in invoices:
            partner = invoice.partner_id

            siswa = self.env['cdn.siswa'].search([('partner_id', '=', partner.id)], limit=1)
            if siswa and siswa.status_akun in ['nonaktif', 'blokir']:
                invoice.message_post(
                    body=_(
                        f"⛔ Pembayaran otomatis gagal karena akun santri *{partner.name}* saat ini berstatus *{siswa.status_akun}*."),
                    subject="Gagal Pembayaran Otomatis",
                    message_type='notification',
                    subtype_xmlid="mail.mt_note"
                )
                continue  

            saldo_saku = partner.saldo_uang_saku
            amount_residual = invoice.amount_residual

            if saldo_saku >= amount_residual:
                invoice._bayar_dengan_saku(invoice, partner, amount_residual)

                # ✅ Notifikasi penuh
                invoice.message_post(
                    body=_(f"✅ Tagihan {invoice.name} berhasil dibayar penuh menggunakan saldo santri sebesar {amount_residual}."),
                    subject="Pembayaran Penuh via Saldo Saku",
                    message_type='notification',
                    subtype_xmlid="mail.mt_note"
                )

            elif saldo_saku > 0:
                amount_to_pay = saldo_saku
                invoice._bayar_dengan_saku(invoice, partner, amount_to_pay)

                _logger.info(f"Saldo santri tidak cukup. Membayar sebagian tagihan {invoice.name} sebesar {amount_to_pay}")

                # ✅ Notifikasi sebagian
                invoice.message_post(
                    body=_(f"⚠️ Tagihan {invoice.name} hanya terbayar sebagian sebesar {amount_to_pay} dari total {amount_residual}."),
                    subject="Pembayaran Sebagian via Saldo Saku",
                    message_type='notification',
                    subtype_xmlid="mail.mt_note"
                )

            else:
                _logger.info(f"Saldo 0. Tidak bisa bayar Tagihan {invoice.name}")

                # ✅ Notifikasi gagal bayar
                invoice.message_post(
                    body=_(f"❌ Tagihan {invoice.name} belum dibayar karena saldo santri 0."),
                    subject="Gagal Pembayaran via Saldo Saku",
                    message_type='notification',
                    subtype_xmlid="mail.mt_note"
                )

        # Reminder untuk invoice yang belum jatuh tempo
        future_invoices = self.search([
            ('state', '=', 'posted'),
            ('payment_state', '!=', 'paid')
        ])

        for invoice in future_invoices:
            invoice.message_post(
                body=_(f"🔔 Tagihan {invoice.name} akan segera jatuh tempo pada {invoice.invoice_date_due}."),
                subject="Reminder Invoice",
                message_type='notification',
                subtype_xmlid="mail.mt_note"
            )

    # @api.model
    # def _run_check_overdue_invoices(self):
    #     # today = fields.Date.from_string('2025-05-19')  # kamu bisa ubah ke Date.today()

    #     today = fields.Date.today()

    #     invoices = self.search([
    #         ('state', '=', 'posted'),
    #         ('payment_state', '!=', 'paid'),
    #         ('amount_residual', '>', 0),
    #         ('invoice_date_due', '<=', today)
    #     ])

    #     for invoice in invoices:
    #         partner = invoice.partner_id
    #         saldo_saku = partner.saldo_uang_saku
    #         amount_residual = invoice.amount_residual

    #         # Hitung 50% dari sisa tagihan
    #         amount_to_pay = amount_residual * 0.5

    #         siswa = self.env['cdn.siswa'].search([('partner_id', '=', partner.id)], limit=1)
    #         orangtua_partner = siswa.orangtua_id.partner_id

    #         if orangtua_partner and orangtua_partner.user_ids:
    #             invoice.message_subscribe(partner_ids=[orangtua_partner.id])

    #         if saldo_saku >= amount_to_pay:
    #             invoice._bayar_dengan_saku(invoice, partner, amount_to_pay)
    #             invoice.message_post(
    #                 body=_(
    #                     f"Tagihan {invoice.name} telah dibayar otomatis sebesar 50% "
    #                     f"sebesar <strong>{amount_to_pay:.2f}</strong> menggunakan saldo uang saku."
    #                 ),
    #                 subject="Pembayaran Otomatis via Uang Saku",
    #                 message_type="comment"
    #             )
    #         else:
    #             invoice.message_post(
    #                 body=_(
    #                     f"Saldo uang saku saat ini tidak mencukupi untuk membayar 50% dari tagihan {invoice.name}. "
    #                     f"Segera lakukan pelunasan untuk menghindari denda keterlambatan."
    #                 ),
    #                 subject="Saldo Uang Saku Tidak Cukup",
    #                 message_type="comment"
    #             )
        
    #     # Optional: tagihan masa depan
    #     future_invoices = self.search([
    #         ('state', '=', 'posted'),
    #         ('payment_state', '!=', 'paid'),
    #         ('invoice_date_due', '>', today)
    #     ])
        
    #     for invoice in future_invoices:
    #         _logger.info(f"Reminder: invoice {invoice.name} belum jatuh tempo.")
    #         # invoice.email_pemberitahuan_tenggat()
    #         siswa = self.env['cdn.siswa'].search([('partner_id', '=', partner.id)], limit=1)
    #         orangtua_partner = siswa.orangtua_id.partner_id
    #         invoice.message_post(
    #             body=_(
    #                 f"Tagihan {invoice.name} akan jatuh tempo pada tanggal <strong>{invoice.invoice_date_due}</strong>. "
    #                 f"Silakan lakukan pembayaran sebelum tenggat waktu untuk menghindari denda."
    #             ),
    #             subject="Pengingat Tagihan Mendekati Jatuh Tempo",
    #             message_type="comment"
    #         )


    # @api.model
    # def _run_check_overdue_invoices(self):
    #     today = fields.Date.today()

    #     invoices = self.search([
    #         ('state', '=', 'posted'),
    #         ('payment_state', '!=', 'paid'),
    #         ('amount_residual', '>', 0),
    #         ('invoice_date_due', '<=', today)
    #     ])

    #     for invoice in invoices:
    #         partner = invoice.partner_id
    #         saldo_saku = partner.saldo_uang_saku
    #         amount_residual = invoice.amount_residual

    #         siswa = self.env['cdn.siswa'].search([('partner_id', '=', partner.id)], limit=1)
    #         orangtua_partner = siswa.orangtua_id.partner_id if siswa else False

    #         # Subscribe orangtua untuk menerima update jika ada
    #         if orangtua_partner and orangtua_partner.user_ids:
    #             invoice.message_subscribe(partner_ids=[orangtua_partner.id])

    #         if saldo_saku >= amount_residual:
    #             # Saldo cukup untuk lunas
    #             invoice._bayar_dengan_saku(invoice, partner, amount_residual)
    #             invoice.message_post(
    #                 body=_(
    #                     f"Tagihan {invoice.name} telah dibayar lunas sebesar <strong>{amount_residual:.2f}</strong> "
    #                     f"menggunakan saldo uang saku."
    #                 ),
    #                 subject="Pembayaran Otomatis via Uang Saku",
    #                 message_type="comment"
    #             )
    #         elif saldo_saku > 0:
    #             # Saldo tidak cukup lunas, bayar 50%
    #             amount_to_pay = amount_residual * 0.5
    #             # Tapi kalau saldo saku kurang dari 50%, bayar sebanyak saldo_saku saja
    #             amount_to_pay = min(amount_to_pay, saldo_saku)

    #             invoice._bayar_dengan_saku(invoice, partner, amount_to_pay)
    #             invoice.message_post(
    #                 body=_(
    #                     f"Tagihan {invoice.name} telah dibayar otomatis sebesar <strong>{amount_to_pay:.2f}</strong> "
    #                     f"menggunakan saldo uang saku."
    #                 ),
    #                 subject="Pembayaran Otomatis via Uang Saku",
    #                 message_type="comment"
    #             )
    #         else:
    #             # Saldo tidak cukup sama sekali
    #             invoice.message_post(
    #                 body=_(
    #                     f"Saldo uang saku saat ini tidak mencukupi untuk membayar tagihan {invoice.name}. "
    #                     f"Segera lakukan pelunasan untuk menghindari denda keterlambatan."
    #                 ),
    #                 subject="Saldo Uang Saku Tidak Cukup",
    #                 message_type="comment"
    #             )
        
    #     # Optional: tagihan masa depan
    #     future_invoices = self.search([
    #         ('state', '=', 'posted'),
    #         ('payment_state', '!=', 'paid'),
    #         ('invoice_date_due', '>', today)
    #     ])
        
    #     for invoice in future_invoices:
    #         _logger.info(f"Reminder: invoice {invoice.name} belum jatuh tempo.")
    #         siswa = self.env['cdn.siswa'].search([('partner_id', '=', invoice.partner_id.id)], limit=1)
    #         orangtua_partner = siswa.orangtua_id.partner_id if siswa else False
    #         invoice.message_post(
    #             body=_(
    #                 f"Tagihan {invoice.name} akan jatuh tempo pada tanggal <strong>{invoice.invoice_date_due}</strong>. "
    #                 f"Silakan lakukan pembayaran sebelum tenggat waktu untuk menghindari denda."
    #             ),
    #             subject="Pengingat Tagihan Mendekati Jatuh Tempo",
    #             message_type="comment" 
    #         )


    @api.onchange('siswa_id')
    def _onchange_siswa_id(self):
        if self.siswa_id:
            self.barcode = self.siswa_id.barcode_santri
            self.partner_id = self.siswa_id.partner_id
        else:
            self.barcode = False

    @api.depends('siswa_id', 'siswa_id.ruang_kelas_id')
    def _compute_kelas_id(self):
        for record in self:
            if record.siswa_id:
                record.ruang_kelas_id = record.siswa_id.ruang_kelas_id
            else:
                record.ruang_kelas_id = False

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

    @api.model
    def _get_nama_sekolah_selection(self):
        return self.env['cdn.siswa']._get_pilihan_nama_sekolah()

    @api.model
    def create(self, vals):
        if 'siswa_id' in vals:
            siswa = self.env['cdn.siswa'].browse(vals['siswa_id'])
            if siswa:
                if not vals.get('barcode'):
                    vals['barcode'] = siswa.barcode_santri
                # Memastikan partner_id terisi saat impor
                if not vals.get('partner_id'):
                    vals['partner_id'] = siswa.partner_id.id
        return super(Tagihan, self).create(vals)
    
    # Menambahkan metode untuk memastikan partner_id terisi pada rekaman yang sudah ada
    def write(self, vals):
        res = super(Tagihan, self).write(vals)
        
        # Jika siswa_id diperbarui, pastikan partner_id juga diperbarui
        if 'siswa_id' in vals and not vals.get('partner_id'):
            for record in self:
                if record.siswa_id and not record.partner_id:
                    record.partner_id = record.siswa_id.partner_id
                    
        return res
    
    # Fungsi untuk memperbaiki data yang sudah ada tanpa partner_id
    @api.model
    def fix_missing_partner_ids(self):
        """Fungsi ini dapat dipanggil dari menu Developer Tools atau melalui cron job"""
        moves = self.search([('siswa_id', '!=', False), ('partner_id', '=', False)])
        for move in moves:
            if move.siswa_id.partner_id:
                move.partner_id = move.siswa_id.partner_id
                
        return True




    # def kirimemail_saldodipotong(self):
    #     ortu_email = self.orangtua_id.partner_id.email

    #     subject = f"Saldo Saku {self.partner_id.name} telah dipotong untuk membayar tagihan"

    #     # Ambil email dari model cdn.siswa
    #     ayah_email = self.siswa_id.ayah_email or ''
    #     ibu_email = self.siswa_id.ibu_email or ''
    #     wali_email = self.siswa_id.wali_email or ''

    #     # Tentukan email penerima: Ayah dan Ibu dulu, jika kosong baru ke Wali
    #     email_penerima = []
        
    #     if ayah_email:
    #         email_penerima.append(ayah_email)
    #     if ibu_email:
    #         email_penerima.append(ibu_email)
        
    #     # Jika kedua orang tua tidak memiliki email, gunakan email wali
    #     if not email_penerima and wali_email:
    #         email_penerima.append(wali_email)

    #     if not email_penerima:
    #         return  # Jika tidak ada email penerima, tidak perlu mengirim email


    #     tagihan_table = ""

    #     for line in self.invoice_line_ids:
    #         product = line.product_id.name or ''
    #         qty = line.quantity or 0
    #         price_unit = line.price_unit or 0
    #         tax = ", ".join(line.tax_ids.mapped('name')) or '0%'
    #         subtotal = line.price_subtotal or 0

    #         harga_format = f"Rp {price_unit:,.0f}".replace(",", ".")
    #         subtotal_format = f"Rp {subtotal:,.0f}".replace(",", ".")

    #         tagihan_table += f"""
    #             <tr>    
    #                 <td style="padding: 8px; border-bottom: 1px solid #eee; word-break: break-word;">{product}</td>
    #                 <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">{qty}</td>
    #                 <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">{harga_format}</td>
    #                 <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">{tax}</td>
    #                 <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">{subtotal_format}</td>
    #             </tr>
    #         """

    #     santri = self.partner_id.name
    #     batas_waktu = self.invoice_date_due
    #     nomor_tagihan = self.name
    #     subtotal_semua = f"Rp {self.amount_untaxed:,.0f}".replace(",", ".")
    #     pajak_semua = f"Rp {self.amount_tax:,.0f}".replace(",", ".")
    #     total_semua = f"Rp {self.amount_total:,.0f}".replace(",", ".")

    #     body_html = f"""
    #     <!DOCTYPE html>
    #             <html>
    #             <head>
    #                 <meta charset="UTF-8">
    #                 <meta name="viewport" content="width=device-width, initial-scale=1.0">
    #                 <style>
    #                     @media only screen and (max-width: 600px) {{
    #                         table {{
    #                             width: 100% !important;
    #                         }}
    #                         .main-container {{
    #                             width: 100% !important;
    #                             padding: 10px !important;
    #                         }}
    #                         .content {{
    #                             padding: 15px !important;
    #                         }}
    #                         .invoice-table {{
    #                             font-size: 12px !important;
    #                         }}
    #                         .invoice-table th, .invoice-table td {{
    #                             padding: 6px 4px !important;
    #                         }}
    #                     }}
    #                 </style>
    #             </head>
    #             <body style="margin: 0; padding: 0; font-family: Arial, sans-serif;">
    #                 <div class="main-container" style="background-color: #f5f8fa; padding: 20px; width: 100%; box-sizing: border-box;">
    #                     <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow: hidden;">
    #                         <!-- Header -->
    #                         <div style="background-color: #005299; color: #ffffff; text-align: center; padding: 20px;">
    #                             <img src="https://i.ibb.co.com/SmWmBTW/SAVE-20220114-075750-removebg-preview-4.png" alt="Logo" style="margin:0 0 15px 0;box-sizing:border-box;vertical-align:middle;width: 60px; height: 60px; margin-bottom: 15px;" width="60">
    #                             <h1 style="margin: 0; font-size: 20px; font-weight: 600;">Pesantren Daarul Qur'an Istiqomah</h1>
    #                         </div>
                            
    #                         <!-- Content -->
    #                         <div class="content" style="padding: 20px;">
    #                             <p style="font-size: 16px; line-height: 1.6; color: #333333; margin-top: 0;">Assalamualaikum,</p>
                                
    #                             <p style="font-size: 16px; line-height: 1.6; color: #333333;">Dengan ini kami informasikan bahwa saldo uang saku telah dipotong untuk membayar tagihan berikut :</p>
                                
    #                             <div style="background-color: #f8f9fa; border-left: 4px solid #005299; padding: 15px; margin: 20px 0; border-radius: 4px;">
    #                                 <h3 style="margin-top: 0; color: #005299; font-size: 18px;">Detail Tagihan</h3>
    #                                 <p style="margin: 5px 0;"><strong>Nomor Tagihan:</strong> {nomor_tagihan}</p>
    #                                 <p style="margin: 5px 0;"><strong>Tanggal:</strong> {batas_waktu}</p>
    #                                 <p style="margin: 5px 0;"><strong>Santri:</strong> {santri}</p>
                                    
    #                                 <div style="overflow-x: auto; margin-top: 15px;">
    #                                     <table class="invoice-table" style="width: 100%; border-collapse: collapse; min-width: 100%;">
    #                                         <thead>
    #                                             <tr style="background-color: #eef2f7;">
    #                                                 <th style="padding: 8px 6px; text-align: left; font-size: 14px;">Produk</th>
    #                                                 <th style="padding: 8px 6px; text-align: left; font-size: 14px;">Kuantitas</th>
    #                                                 <th style="padding: 8px 6px; text-align: center; font-size: 14px;">Harga</th>
    #                                                 <th style="padding: 8px 6px; text-align: right; font-size: 14px;">Pajak</th>
    #                                                 <th style="padding: 8px 6px; text-align: right; font-size: 14px;">Jumlah</th>
    #                                             </tr>
    #                                         </thead>
    #                                         <tbody>
    #                                             {tagihan_table}
    #                                         </tbody>
    #                                     </table>
    #                                 </div>
                                    
    #                                 <div style="margin-top: 20px; border-top: 1px solid #eee; padding-top: 10px; text-align: right;">
    #                                     <p style="font-size: 16px; margin: 5px 0;">Jumlah Sebelum Pajak: <strong>{subtotal_semua}</strong></p>
    #                                     <p style="font-size: 16px; margin: 5px 0;">Pajak: <strong>{pajak_semua}</p>
    #                                     <p style="font-size: 18px; font-weight: bold; margin: 10px 0;">Total: <strong>{total_semua}</strong></p>
    #                                 </div>
    #                             </div>
                                
    #                             <p style="font-size: 16px; line-height: 1.6; color: #333333;">Kami sangat menghargai kerja sama Bapak/Ibu, dan berharap proses pembayaran tagihan dapat berjalan lebih lancar dan tepat waktu di masa mendatang</p>
    #                         </div>
                            
    #                         <div style="background-color: #f0f4f8; text-align: center; padding: 15px; color: #666666; font-size: 14px; border-top: 1px solid #e7eaec;">
    #                             <p style="margin: 5px 0;">Pesantren Daarul Qur'an Istiqomah</p>
    #                         </div>
    #                     </div>
    #                 </div>
    #             </body>
    #             </html>
    #             """ 

    #     # Kirim email
    #     self.env['mail.mail'].create({
    #         'subject': subject,
    #         'email_to': ','.join(email_penerima),
    #         'body_html': body_html,
    #     }).send()
        


    # def email_saldosaku_tidakcukup(self):
    #     """Mengirim email jika saldo uang saku tidak cukup, sekali per hari."""
    #     today = fields.Date.today()
    #     last_email = self.env['mail.activity'].search([
    #         ('res_id', '=', self.id),
    #         ('res_model', '=', 'account.move'),
    #         ('activity_type_id', '=', self.env.ref('mail.mail_activity_data_email').id),
    #         ('date_deadline', '=', today)
    #     ], limit=1)

    #     if last_email:
    #         return  # Jangan kirim email lagi hari ini

    #     # Ambil email dari model cdn.siswa
    #     ayah_email = self.siswa_id.ayah_email or ''
    #     ibu_email = self.siswa_id.ibu_email or ''
    #     wali_email = self.siswa_id.wali_email or ''

    #     # Tentukan email penerima: Ayah dan Ibu dulu, jika kosong baru ke Wali
    #     email_penerima = []
        
    #     if ayah_email:
    #         email_penerima.append(ayah_email)
    #     if ibu_email:
    #         email_penerima.append(ibu_email)
        
    #     # Jika kedua orang tua tidak memiliki email, gunakan email wali
    #     if not email_penerima and wali_email:
    #         email_penerima.append(wali_email)

    #     if not email_penerima:
    #         return  # Jika tidak ada email penerima, tidak perlu mengirim email

    #     # Buat tabel tagihan
    #     tagihan_table = ""
    #     for line in self.invoice_line_ids:
    #         product = line.product_id.name or ''
    #         qty = line.quantity or 0
    #         price_unit = line.price_unit or 0
    #         tax = ", ".join(line.tax_ids.mapped('name')) or '0%'
    #         subtotal = line.price_subtotal or 0

    #         harga_format = f"Rp {price_unit:,.0f}".replace(",", ".")
    #         subtotal_format = f"Rp {subtotal:,.0f}".replace(",", ".")

    #         tagihan_table += f"""
    #             <tr>    
    #                 <td style="padding: 8px; border-bottom: 1px solid #eee; word-break: break-word;">{product}</td>
    #                 <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">{qty}</td>
    #                 <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">{harga_format}</td>
    #                 <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">{tax}</td>
    #                 <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">{subtotal_format}</td>
    #             </tr>
    #         """

    #     santri = self.partner_id.name
    #     batas_waktu = self.invoice_date_due
    #     nomor_tagihan = self.name
    #     subtotal_semua = f"Rp {self.amount_untaxed:,.0f}".replace(",", ".")
    #     pajak_semua = f"Rp {self.amount_tax:,.0f}".replace(",", ".")
    #     total_semua = f"Rp {self.amount_total:,.0f}".replace(",", ".")

    #     subject = "Saldo Saku Tidak Cukup"
    #     body_html = f"""
    #     <!DOCTYPE html>
    #             <html>
    #             <head>
    #                 <meta charset="UTF-8">
    #                 <meta name="viewport" content="width=device-width, initial-scale=1.0">
    #                 <style>
    #                     @media only screen and (max-width: 600px) {{
    #                         table {{
    #                             width: 100% !important;
    #                         }}
    #                         .main-container {{
    #                             width: 100% !important;
    #                             padding: 10px !important;
    #                         }}
    #                         .content {{
    #                             padding: 15px !important;
    #                         }}
    #                         .invoice-table {{
    #                             font-size: 12px !important;
    #                         }}
    #                         .invoice-table th, .invoice-table td {{
    #                             padding: 6px 4px !important;
    #                         }}
    #                     }}
    #                 </style>
    #             </head>
    #             <body style="margin: 0; padding: 0; font-family: Arial, sans-serif;">
    #                 <div class="main-container" style="background-color: #f5f8fa; padding: 20px; width: 100%; box-sizing: border-box;">
    #                     <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow: hidden;">
    #                         <!-- Header -->
    #                         <div style="background-color: #005299; color: #ffffff; text-align: center; padding: 20px;">
    #                             <img src="https://i.ibb.co.com/SmWmBTW/SAVE-20220114-075750-removebg-preview-4.png" alt="Logo" style="margin:0 0 15px 0;box-sizing:border-box;vertical-align:middle;width: 60px; height: 60px; margin-bottom: 15px;" width="60">
    #                             <h1 style="margin: 0; font-size: 20px; font-weight: 600;">Pesantren Daarul Qur'an Istiqomah</h1>
    #                         </div>
                            
    #                         <!-- Content -->
    #                         <div class="content" style="padding: 20px;">
    #                             <p style="font-size: 16px; line-height: 1.6; color: #333333; margin-top: 0;">Assalamualaikum,</p>
                                
    #                             <p style="font-size: 16px; line-height: 1.6; color: #333333;">Dengan ini kami informasikan bahwa saldo uang saku tidak mencukupi untuk membayar tagihan berikut :</p>
                                
    #                             <div style="background-color: #f8f9fa; border-left: 4px solid #005299; padding: 15px; margin: 20px 0; border-radius: 4px;">
    #                                 <h3 style="margin-top: 0; color: #005299; font-size: 18px;">Detail Tagihan</h3>
    #                                 <p style="margin: 5px 0;"><strong>Nomor Tagihan:</strong> {nomor_tagihan}</p>
    #                                 <p style="margin: 5px 0;"><strong>Tanggal:</strong> {batas_waktu}</p>
    #                                 <p style="margin: 5px 0;"><strong>Santri:</strong> {santri}</p>
                                    
    #                                 <div style="overflow-x: auto; margin-top: 15px;">
    #                                     <table class="invoice-table" style="width: 100%; border-collapse: collapse; min-width: 100%;">
    #                                         <thead>
    #                                             <tr style="background-color: #eef2f7;">
    #                                                 <th style="padding: 8px 6px; text-align: left; font-size: 14px;">Produk</th>
    #                                                 <th style="padding: 8px 6px; text-align: left; font-size: 14px;">Kuantitas</th>
    #                                                 <th style="padding: 8px 6px; text-align: center; font-size: 14px;">Harga</th>
    #                                                 <th style="padding: 8px 6px; text-align: right; font-size: 14px;">Pajak</th>
    #                                                 <th style="padding: 8px 6px; text-align: right; font-size: 14px;">Jumlah</th>
    #                                             </tr>
    #                                         </thead>
    #                                         <tbody>
    #                                             {tagihan_table}
    #                                         </tbody>
    #                                     </table>
    #                                 </div>         
    #                                 <div style="margin-top: 20px; border-top: 1px solid #eee; padding-top: 10px; text-align: right;">
    #                                     <p style="font-size: 16px; margin: 5px 0;">Jumlah Sebelum Pajak: <strong>{subtotal_semua}</strong></p>
    #                                     <p style="font-size: 16px; margin: 5px 0;">Pajak: <strong>{pajak_semua}</p>
    #                                     <p style="font-size: 18px; font-weight: bold; margin: 10px 0;">Total: <strong>{total_semua}</strong></p>
    #                                 </div>
    #                             </div>
                                
    #                             <p style="font-size: 16px; line-height: 1.6; color: #333333;">Dengan ini kami mohon kerja sama nya dalam pembayaran tagihan yang telah melewati batas waktu. Dimohon untuk segera membayarnya dengan cara topup ke uang saku santri ataupun membayar dengan cara Log In ke akun masing - masing.</p>

    #                             <p style="font-size: 16px; line-height: 1.6; color: #333333;">Terima Kasih atas kerjasamanya.</p>
                                
    #                             <p style="font-size: 16px; line-height: 1.6; color: #333333;">Wassalamualaikum Wr Wb.</p>
    #                         </div>
                            
    #                         <div style="background-color: #f0f4f8; text-align: center; padding: 15px; color: #666666; font-size: 14px; border-top: 1px solid #e7eaec;">
    #                             <p style="margin: 5px 0;">Pesantren Daarul Qur'an Istiqomah</p>
    #                         </div>
    #                     </div>
    #                 </div>
    #             </body>
    #             </html>
    #             """  

    #     # Kirim email
    #     self.env['mail.mail'].create({
    #         'subject': subject,
    #         'email_to': ','.join(email_penerima),
    #         'body_html': body_html,
    #     }).send()

    #     # Catat aktivitas
    #     self.env['mail.activity'].create({
    #         'res_id': self.id,
    #         'res_model_id': self.env['ir.model']._get_id('account.move'),
    #         'activity_type_id': self.env.ref('mail.mail_activity_data_email').id,
    #         'summary': 'Pemberitahuan Saldo Tidak Cukup.',
    #         'date_deadline': today,
    #         'user_id': self.env.user.id,
    #     })




    # def email_pemberitahuan_tenggat(self):
    #     """Mengirim email pemberitahuan tenggat waktu 7, 3, dan 1 hari sebelum jatuh tempo."""
    #     today = fields.Date.today()
    #     batas_waktu = self.invoice_date_due

    #     if not batas_waktu:
    #         return  # Tidak ada tenggat waktu, tidak perlu mengirim email

    #     delta_days = (batas_waktu - today).days
    #     if delta_days not in [7, 3, 1]:
    #         return  # Hanya kirim pada 7, 3, atau 1 hari sebelum tenggat

    #     # Cek apakah email sudah dikirim hari ini
    #     last_email = self.env['mail.activity'].search([
    #         ('res_id', '=', self.id),
    #         ('res_model', '=', 'account.move'),
    #         ('activity_type_id', '=', self.env.ref('mail.mail_activity_data_email').id),
    #         ('date_deadline', '=', today)
    #     ], limit=1)

    #     if last_email:
    #         return  # Jangan kirim email lagi hari ini

    #     self._kirim_email_tagihan(delta_days)

    # def _kirim_email_tagihan(self, delta_days):
    #     """Fungsi untuk mengirim email tagihan."""
    #     # Ambil email dari model siswa
    #     ayah_email = self.siswa_id.ayah_email or ''
    #     ibu_email = self.siswa_id.ibu_email or ''
    #     wali_email = self.siswa_id.wali_email or ''

    #     email_penerima = []
    #     if ayah_email:
    #         email_penerima.append(ayah_email)
    #     if ibu_email:
    #         email_penerima.append(ibu_email)
    #     if not email_penerima and wali_email:
    #         email_penerima.append(wali_email)

    #     if not email_penerima:
    #         return  # Tidak ada email penerima, tidak perlu mengirim email

    #     # Buat tabel tagihan
    #     tagihan_table = ""
    #     for line in self.invoice_line_ids:
    #         product = line.product_id.name or ''
    #         qty = line.quantity or 0
    #         price_unit = line.price_unit or 0
    #         tax = ", ".join(line.tax_ids.mapped('name')) or '0%'
    #         subtotal = line.price_subtotal or 0

    #         harga_format = f"Rp {price_unit:,.0f}".replace(",", ".")
    #         subtotal_format = f"Rp {subtotal:,.0f}".replace(",", ".")

    #         tagihan_table += f"""
    #             <tr>    
    #                 <td style="padding: 8px; border-bottom: 1px solid #eee;">{product}</td>
    #                 <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">{qty}</td>
    #                 <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">{harga_format}</td>
    #                 <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">{tax}</td>
    #                 <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">{subtotal_format}</td>
    #             </tr>
    #         """

    #     santri = self.partner_id.name
    #     nomor_tagihan = self.name
    #     batas_waktu = self.invoice_date_due
    #     subtotal_semua = f"Rp {self.amount_untaxed:,.0f}".replace(",", ".")
    #     pajak_semua = f"Rp {self.amount_tax:,.0f}".replace(",", ".")
    #     total_semua = f"Rp {self.amount_total:,.0f}".replace(",", ".")

    #     subject = f"Pengingat Pembayaran Tagihan ({delta_days} Hari Lagi)"
    #     body_html = f"""
    #     <html>
    #     <head>
    #         <style>
    #             @media only screen and (max-width: 600px) {{
    #                 table {{ width: 100% !important; }}
    #                 .main-container {{ width: 100% !important; padding: 10px !important; }}
    #                 .content {{ padding: 15px !important; }}
    #                 .invoice-table {{ font-size: 12px !important; }}
    #                 .invoice-table th, .invoice-table td {{ padding: 6px 4px !important; }}
    #             }}
    #         </style>
    #     </head>
    #     <body style="font-family: Arial, sans-serif;">
    #         <div class="main-container" style="background-color: #f5f8fa; padding: 20px;">
    #             <div style="max-width: 600px; margin: auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
    #                 <div style="background-color: #005299; color: #ffffff; text-align: center; padding: 20px;">
    #                     <h1>Pesantren Daarul Qur'an Istiqomah</h1>
    #                 </div>
    #                 <div class="content" style="padding: 20px;">
    #                     <p>Assalamualaikum,</p>
    #                     <p>Kami ingin mengingatkan bahwa pembayaran tagihan berikut akan jatuh tempo dalam <strong>{delta_days} hari</strong>:</p>
    #                     <div style="background-color: #f8f9fa; border-left: 4px solid #005299; padding: 15px; margin: 20px 0; border-radius: 4px;">
    #                         <h3>Detail Tagihan</h3>
    #                         <p><strong>Nomor Tagihan:</strong> {nomor_tagihan}</p>
    #                         <p><strong>Tanggal Jatuh Tempo:</strong> {batas_waktu}</p>
    #                         <p><strong>Santri:</strong> {santri}</p>
    #                         <table class="invoice-table" style="width: 100%; border-collapse: collapse;">
    #                             <thead>
    #                                 <tr style="background-color: #eef2f7;">
    #                                     <th>Produk</th>
    #                                     <th>Kuantitas</th>
    #                                     <th>Harga</th>
    #                                     <th>Pajak</th>
    #                                     <th>Jumlah</th>
    #                                 </tr>
    #                             </thead>
    #                             <tbody>{tagihan_table}</tbody>
    #                         </table>
    #                         <div style="margin-top: 20px; text-align: right;">
    #                             <p>Jumlah Sebelum Pajak: <strong>{subtotal_semua}</strong></p>
    #                             <p>Pajak: <strong>{pajak_semua}</strong></p>
    #                             <p>Total: <strong>{total_semua}</strong></p>
    #                         </div>
    #                     </div>
    #                     <p>Dimohon untuk segera melakukan pembayaran sebelum jatuh tempo.</p>
    #                     <p>Terima Kasih.</p>
    #                     <p>Wassalamualaikum Wr Wb.</p>
    #                 </div>
    #             </div>
    #         </div>
    #     </body>
    #     </html>
    #     """

    #     self.env['mail.mail'].create({
    #         'subject': subject,
    #         'email_to': ','.join(email_penerima),
    #         'body_html': body_html,
    #     }).send()

    # @api.model
    # def create(self, vals):
    #     """Kirim email saat tagihan dibuat jika tenggatnya 7 hari dari sekarang."""
    #     record = super(Tagihan, self).create(vals)
    #     if 'invoice_date_due' in vals:
    #         today = fields.Date.today()
    #         batas_waktu = fields.Date.from_string(vals['invoice_date_due'])
    #         if (batas_waktu - today).days == 7:
    #             record._kirim_email_tagihan(7)
    #         if (batas_waktu - today).days == 3:
    #             record._kirim_email_tagihan(3)
    #         if (batas_waktu - today).days == 1:
    #             record._kirim_email_tagihan(1)
    #     return record


    # def action_post(self):
    #     super(Tagihan, self).action_post()
        
    #     for invoice in self:
    #         if invoice.invoice_date_due and invoice.invoice_date_due <= fields.Date.today():
    #             partner = invoice.partner_id
    #             saldo_saku = partner.saldo_uang_saku
                
    #             if saldo_saku >= invoice.amount_total:
    #                 self._bayar_dengan_saku(invoice, partner)
    #                 self.kirimemail_saldodipotong()
    #             else:
    #                 self.email_saldosaku_tidakcukup()
    
    # def _bayar_dengan_saku(self, invoice, partner):
    #     partner.saldo_uang_saku -= invoice.amount_total
    #     journal = self.env['account.journal'].with_context(lang='id_ID').search([
    #         ('name', 'ilike', 'Faktur Pelanggan')
    #     ], limit=1)

    #     _logger.info(f"Jurnal Ditemukan {journal.name}")
    #     if not journal:
    #         raise UserError(f"Jurnal {journal.id}' tidak ditemukan.")
        
    #     move_vals = {
    #         'move_type': 'entry',
    #         'journal_id': journal.id,
    #         'date': fields.Date.today(),
    #         'line_ids': [
    #             (0, 0, {
    #                 'account_id': invoice.line_ids[0].account_id.id,
    #                 'partner_id': partner.id,
    #                 'name': f"Pembayaran otomatis {invoice.name}",
    #                 'debit': invoice.amount_total,
    #                 'credit': 0.0,
    #             }),
    #             (0, 0, {
    #                 'account_id': journal.default_account_id.id,
    #                 'partner_id': partner.id,
    #                 'name': f"Pengurangan saldo uang saku {invoice.name}",
    #                 'debit': 0.0,
    #                 'credit': invoice.amount_total,
    #             }),
    #         ]
    #     }
        
    #     payment_move = self.env['account.move'].create(move_vals)
    #     payment_move.action_post()
    #     invoice.payment_state = 'paid'


    # def _bayar_dengan_saku(self, invoice, partner):
    #     partner.saldo_uang_saku -= invoice.amount_total
    #     _logger.info(f"Saldo Santri {partner.saldo_uang_saku}")
    #     _logger.info(f"Total Tagihan {invoice.amount_total}")


    #     # Cari jurnal sesuai perusahaan
    #     journal = self.env['account.journal'].search([
    #         ('type', '=', 'sale'),
    #         ('company_id', '=', invoice.company_id.id)
    #     ], limit=1)

    #     if not journal:
    #         raise UserError(f"Jurnal untuk perusahaan {invoice.company_id.name} tidak ditemukan.")

    #     # Gunakan akun partner receivable dan pastikan cocok
    #     account_debit = partner.property_account_receivable_id
    #     if invoice.company_id not in account_debit.company_ids:
    #         raise UserError("Akun debit bukan milik perusahaan invoice.")


    #     account_credit = journal.default_account_id
        
    #     if invoice.company_id not in account_credit.company_ids:
    #         raise UserError("Akun default jurnal tidak cocok dengan perusahaan invoice.")

    #     move_vals = {
    #         'move_type': 'entry',
    #         'journal_id': journal.id,
    #         'date': fields.Date.today(),
    #         'company_id': invoice.company_id.id,
    #         'line_ids': [
    #             (0, 0, {
    #                 'account_id': account_debit.id,
    #                 'partner_id': partner.id,
    #                 'name': f"Pembayaran otomatis {invoice.name}",
    #                 'debit': invoice.amount_total,
    #                 'credit': 0.0,
    #             }),
    #             (0, 0, {
    #                 'account_id': account_credit.id,
    #                 'partner_id': partner.id,
    #                 'name': f"Pengurangan saldo uang saku {invoice.name}",
    #                 'debit': 0.0,
    #                 'credit': invoice.amount_total,
    #             }),
    #         ]
    #     }

    #     payment_move = self.env['account.move'].create(move_vals)
    #     payment_move.action_post()
    #     invoice.payment_state = 'paid'


    # def _bayar_dengan_saku(self, invoice, partner):
    #     self.env['cdn.uang_saku'].sudo().create({
    #         'tgl_transaksi': fields.Datetime.now(),
    #         'siswa_id': partner.id,
    #         'jns_transaksi': 'keluar',
    #         'amount_out': invoice.amount_total,
    #         'validasi_id': self.env.user.id,
    #         'validasi_time': fields.Datetime.now(),
    #         'keterangan': f'Pembayaran otomatis invoice {invoice.name}',
    #         'state': 'confirm',
    #     })

    #     partner.saldo_uang_saku = partner.calculate_saku()

    #     journal = self.env['account.journal'].search([('name', '=', 'Faktur Pelanggan')], limit=1)
    #     if not journal:
    #         raise UserError("Jurnal 'Faktur Pelanggan' tidak ditemukan.")
        
    #     move_vals = {
    #         'move_type': 'entry',
    #         'journal_id': journal.id,
    #         'date': fields.Date.today(),
    #         'line_ids': [
    #             (0, 0, {
    #                 'account_id': invoice.line_ids[0].account_id.id,  
    #                 'partner_id': partner.id,
    #                 'name': f"Pembayaran otomatis {invoice.name}",
    #                 'debit': invoice.amount_total,
    #                 'credit': 0.0,
    #             }),
    #             (0, 0, {
    #                 'account_id': journal.default_account_id.id,
    #                 'partner_id': partner.id,
    #                 'name': f"Pengurangan saldo uang saku {invoice.name}",
    #                 'debit': 0.0,
    #                 'credit': invoice.amount_total,
    #             }),
    #         ]
    #     }

    #     payment_move = self.env['account.move'].create(move_vals)
    #     payment_move.action_post()

    #     invoice.payment_state = 'paid'

    #     return True

    # def _bayar_dengan_saku(self, invoice, partner):
    #     # Tambahkan catatan transaksi uang saku
    #     self.env['cdn.uang_saku'].sudo().create({
    #         'tgl_transaksi': fields.Datetime.now(),
    #         'siswa_id': partner.id,
    #         'jns_transaksi': 'keluar',
    #         'amount_out': invoice.amount_total,
    #         'validasi_id': self.env.user.id,
    #         'validasi_time': fields.Datetime.now(),
    #         'keterangan': f'Pembayaran otomatis invoice {invoice.name}',
    #         'state': 'confirm',
    #     })

    #     # Update saldo uang saku dari fungsi kalkulasi (bukan dikurang manual)
    #     partner.saldo_uang_saku = partner.calculate_saku()

    #     # Cari jurnal sesuai perusahaan dan tipe 'sale'
    #     journal = self.env['account.journal'].search([
    #         ('type', '=', 'sale'),
    #         ('company_id', '=', invoice.company_id.id)
    #     ], limit=1)

    #     if not journal:
    #         raise UserError(f"Jurnal untuk perusahaan {invoice.company_id.name} tidak ditemukan.")

    #     # Ambil akun piutang partner dan validasi perusahaan
    #     account_debit = partner.property_account_receivable_id
    #     if account_debit.company_ids != invoice.company_id:
    #         raise UserError("Akun piutang partner tidak cocok dengan perusahaan invoice.")

    #     # Ambil akun default dari jurnal dan validasi perusahaan
    #     account_credit = journal.default_account_id
    #     if account_credit.company_ids != invoice.company_id:
    #         raise UserError("Akun default jurnal tidak cocok dengan perusahaan invoice.")

    #     # Buat jurnal entri
    #     move_vals = {
    #         'move_type': 'entry',
    #         'journal_id': journal.id,
    #         'date': fields.Date.today(),
    #         'company_id': invoice.company_id.id,
    #         'line_ids': [
    #             (0, 0, {
    #                 'account_id': account_debit.id,
    #                 'partner_id': partner.id,
    #                 'name': f"Pembayaran otomatis {invoice.name}",
    #                 'debit': invoice.amount_total,
    #                 'credit': 0.0,
    #             }),
    #             (0, 0, {
    #                 'account_id': account_credit.id,
    #                 'partner_id': partner.id,
    #                 'name': f"Pengurangan saldo uang saku {invoice.name}",
    #                 'debit': 0.0,
    #                 'credit': invoice.amount_total,
    #             }),
    #         ]
    #     }

    #     payment_move = self.env['account.move'].create(move_vals)
    #     payment_move.action_post()

    #     invoice._compute_telah_dibayar()
    #     invoice.payment_state = 'paid'

    # def _bayar_dengan_saku(self, invoice, partner):
    #     # 1. Catat transaksi uang saku
    #     self.env['cdn.uang_saku'].sudo().create({
    #         'tgl_transaksi': fields.Datetime.now(),
    #         'siswa_id': partner.id,
    #         'jns_transaksi': 'keluar',
    #         'amount_out': invoice.amount_total,
    #         'validasi_id': self.env.user.id,
    #         'validasi_time': fields.Datetime.now(),
    #         'keterangan': f'Pembayaran otomatis invoice {invoice.name}',
    #         'state': 'confirm',
    #     })

    #     # 2. Update saldo uang saku dari fungsi kalkulasi (bukan manual)
    #     partner.saldo_uang_saku = partner.calculate_saku()

    #     # 3. Cari jurnal pembayaran yang sesuai (pastikan ini jurnal dengan tipe 'bank' atau 'cash')
    #     journal = self.env['account.journal'].search([
    #         ('type', 'in', ['bank', 'cash']),
    #         ('company_id', '=', invoice.company_id.id)
    #     ], limit=1)

    #     if not journal:
    #         raise UserError(f"Jurnal bertipe 'bank' atau 'cash' untuk perusahaan {invoice.company_id.name} tidak ditemukan.")

    #     # 4. Buat payment resmi di Odoo
    #     payment_vals = {
    #         'amount': invoice.amount_total,
    #         'payment_type': 'inbound',
    #         'partner_type': 'customer',
    #         'partner_id': partner.id,
    #         'journal_id': journal.id,
    #         'date': fields.Date.today(),
    #         'invoice_ids': [(6, 0, [invoice.id])],
    #         'company_id': invoice.company_id.id,
    #     }

    #     payment = self.env['account.payment'].create(payment_vals)  # ✅ ini record
    #     payment.action_post()  # ✅ ini akan berhasil


    #     # 6. Rekonsiliasi pembayaran ke invoice
    #     outstanding_line = payment.move_id.line_ids.filtered(
    #         lambda line: line.account_id.internal_group == 'receivable' and line.partner_id == partner
    #     )
    #     if outstanding_line:
    #         invoice.js_assign_outstanding_line(outstanding_line)

    #     return True

    # def _bayar_dengan_saku(self, invoice, partner):
    #     # 1. Catat transaksi uang saku
    #     self.env['cdn.uang_saku'].sudo().create({
    #         'tgl_transaksi': fields.Datetime.now(),
    #         'siswa_id': partner.id,
    #         'jns_transaksi': 'keluar',
    #         'amount_out': invoice.amount_total,
    #         'validasi_id': self.env.user.id,
    #         'validasi_time': fields.Datetime.now(),
    #         'keterangan': f'Pembayaran otomatis invoice {invoice.name}',
    #         'state': 'confirm',
    #     })

    #     # 2. Update saldo uang saku
    #     partner.saldo_uang_saku = partner.calculate_saku()

    #     # 3. Cari jurnal bertipe bank/cash
    #     journal = self.env['account.journal'].search([
    #         ('type', 'in', ['bank', 'cash']),
    #         ('company_id', '=', invoice.company_id.id)
    #     ], limit=1)

    #     if not journal:
    #         raise UserError(f"Jurnal bertipe 'bank' atau 'cash' untuk perusahaan {invoice.company_id.name} tidak ditemukan.")

    #     # 4. Buat payment
    #     payment_vals = {
    #         'amount': invoice.amount_total,
    #         'payment_type': 'inbound',
    #         'partner_type': 'customer',
    #         'partner_id': partner.id,
    #         'journal_id': journal.id,
    #         'date': fields.Date.today(),
    #         'invoice_ids': [(6, 0, [invoice.id])],
    #         'company_id': invoice.company_id.id,
    #     }

    #     payment = self.env['account.payment'].create(payment_vals)
    #     payment.action_post()

    #     # 5. Rekonsiliasi: Hubungkan langsung receivable lines
    #     invoice_lines = invoice.line_ids.filtered(lambda l: l.account_id.internal_group == 'receivable' and not l.reconciled)
    #     payment_lines = payment.move_id.line_ids.filtered(lambda l: l.account_id.internal_group == 'receivable' and not l.reconciled)

    #     (invoice_lines + payment_lines).reconcile()

    #     return True

    # def _bayar_dengan_saku(self, invoice, partner):
    #     # 1. Catat transaksi uang saku
    #     self.env['cdn.uang_saku'].sudo().create({
    #         'tgl_transaksi': fields.Datetime.now(),
    #         'siswa_id': partner.id,
    #         'jns_transaksi': 'keluar',
    #         'amount_out': invoice.amount_total,
    #         'validasi_id': self.env.user.id,
    #         'validasi_time': fields.Datetime.now(),
    #         'keterangan': f'Pembayaran otomatis invoice {invoice.name}',
    #         'state': 'confirm',
    #     })
        
    #     # 2. Update saldo uang saku
    #     partner.saldo_uang_saku = partner.calculate_saku()
        
    #     # 3. Cari jurnal bertipe bank/cash
    #     journal = self.env['account.journal'].search([
    #         ('type', 'in', ['bank', 'cash']),
    #         ('company_id', '=', invoice.company_id.id)
    #     ], limit=1)
        
    #     if not journal:
    #         raise UserError(f"Jurnal bertipe 'bank' atau 'cash' untuk perusahaan {invoice.company_id.name} tidak ditemukan.")
        
    #     # 4. Buat payment register
    #     payment_register = self.env['account.payment.register'].with_context(
    #         active_model='account.move',
    #         active_ids=invoice.ids
    #     ).create({
    #         'payment_date': fields.Date.today(),
    #         'journal_id': journal.id,
    #         # 'amount': invoice.amount_total,
    #         'amount': invoice.amount_residual,
    #     })
        
    #     # 5. Buat payment menggunakan _create_payments() dari payment register
    #     try:
    #         payment = payment_register._create_payments()
    #         _logger.info(f"Payment successfully created for invoice {invoice.name}")
            
    #         # 6. Reload invoice untuk mendapatkan status terbaru
    #         invoice = self.env['account.move'].browse(invoice.id)
    #         _logger.info(f"Invoice payment state after payment: {invoice.payment_state}")
            
    #         return True
    #     except Exception as e:
    #         _logger.error(f"Error during payment creation: {e}")
    #         raise UserError(f"Gagal membuat pembayaran: {e}")

    def _bayar_dengan_saku(self, invoice, partner, jumlah_bayar):
        # 1. Catat transaksi uang saku
        self.env['cdn.uang_saku'].sudo().create({
            'tgl_transaksi': fields.Datetime.now(),
            'siswa_id': partner.id,
            'jns_transaksi': 'keluar',
            'amount_out': jumlah_bayar,
            'validasi_id': self.env.user.id,
            'validasi_time': fields.Datetime.now(),
            'keterangan': f'Pembayaran otomatis sebagian invoice {invoice.name}',
            'state': 'confirm',
        })
        
        # 2. Update saldo uang saku
        partner.saldo_uang_saku = partner.calculate_saku()
        
        # 3. Cari jurnal bertipe bank/cash
        journal = self.env['account.journal'].search([
            ('type', 'in', ['bank', 'cash']),
            ('company_id', '=', invoice.company_id.id)
        ], limit=1)

        if not journal:
            raise UserError(f"Jurnal bertipe 'bank' atau 'cash' untuk perusahaan {invoice.company_id.name} tidak ditemukan.")
        
        # 4. Buat payment register
        payment_register = self.env['account.payment.register'].with_context(
            active_model='account.move',
            active_ids=invoice.ids
        ).create({
            'payment_date': fields.Date.today(),
            'journal_id': journal.id,
            'amount': jumlah_bayar,
        })
        
        try:
            payment = payment_register._create_payments()
            _logger.info(f"Payment sebagian sebesar {jumlah_bayar} berhasil untuk invoice {invoice.name}")
            return True
        except Exception as e:
            _logger.error(f"Error saat membuat pembayaran sebagian: {e}")
            raise UserError(f"Gagal membayar sebagian invoice: {e}")


