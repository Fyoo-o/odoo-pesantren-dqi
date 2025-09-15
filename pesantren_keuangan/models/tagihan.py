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
    is_cancelled = fields.Boolean(
        string="Dibatalkan",
        compute='_compute_is_cancelled',
        store=True
    )
    is_auto_payment = fields.Boolean(string="Pembayaran Otomatis", default=False, help="Menandakan bahwa tagihan ini dibayar secara otomatis")
    auto_payment_date = fields.Date(string="Tanggal Pembayaran Otomatis", readonly=True)
    
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
            
    display_payment_status = fields.Char(
        string="Status  ",
        compute="_compute_display_payment_status",
        store=True
    )

    @api.depends('state', 'payment_state')
    def _compute_display_payment_status(self):
        for rec in self:
            if rec.state == 'cancel':
                rec.display_payment_status = 'Dibatalkan'
            elif rec.payment_state == 'paid':
                rec.display_payment_status = 'Lunas'
            elif rec.payment_state == 'partial':
                rec.display_payment_status = 'Terbayar Sebagian'
            elif rec.payment_state == 'not_paid':
                rec.display_payment_status = 'Belum Bayar'
            else:
                rec.display_payment_status = rec.payment_state
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
        
    @api.depends('state')
    def _compute_is_cancelled(self):
        for rec in self:
            rec.is_cancelled = rec.state == 'cancel'

