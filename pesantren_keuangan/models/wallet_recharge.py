# from datetime import datetime
# from odoo import api, fields, models


# class WalletRecharge(models.TransientModel):
#     _inherit = 'recharge.wallet'

#     def _get_partner_id(self):
#         context = self._context
#         active_id = context.get('active_id')
#         model = context.get('active_model')

#         partner_id = active_id
#         if model == 'cdn.siswa':
#             Siswa = self.env['cdn.siswa'].browse(active_id)
#             partner_id = Siswa.partner_id.id
#         return partner_id

#     # defaults 
#     def _default_amount(self):
#         Partner = self.env['res.partner'].browse(self.siswa_id.id)
#         dompet = Partner.wallet_balance
#         max_wallet = self.env.user.company_id.max_wallet
#         return max_wallet - dompet if dompet < max_wallet else 0

#     # fields
#     recharge_amount = fields.Float('Recharge Amount', required=True, default=0)
#     siswa_id = fields.Many2one(comodel_name='res.partner', string='Siswa', readonly=True, default=lambda self: self._get_partner_id())
#     wallet_balance = fields.Float(string='Saldo Dompet', related='siswa_id.wallet_balance', readonly=True)
#     saldo_uang_saku = fields.Float(string='Saldo Uang Saku', related='siswa_id.saldo_uang_saku', readonly=True)
#     recharge_type = fields.Selection(selection=[
#         ('manual_based', 'Isi Dompet Manual'),
#         ('saku_based', 'Isi Berdasarkan Saldo'),
#     ], default='saku_based', string='Recharge Type', help="Nilai pilihan saku_based didasarkan pada selisih nilai maksimum wallet dan saldo wallet saat ini.")

#     # override
#     def post(self):
#         if self.recharge_amount <= 1000:
#             raise models.ValidationError('Nilai recharge dompet harus lebih dari 1000 Rupiah.')

#         AccountPayment = self.env['account.payment']
        
#         # Gunakan siswa_id sebagai partner
#         Partner = self.siswa_id

#         # Cek saldo uang saku
#         if self.saldo_uang_saku < self.recharge_amount and self.recharge_type:
#             raise models.ValidationError('Saldo Uang Saku Tidak Cukup!')

#         PosWalletTransaction = self.env['pos.wallet.transaction']
#         date_now = datetime.strftime(datetime.now(), '%Y-%m-%d')
#         timestamp = fields.Datetime.now()

#         payment_create = AccountPayment.sudo().create({
#             'name': self.env['ir.sequence'].with_context(ir_sequence_date=date_now).next_by_code('account.payment.customer.invoice'),
#             'payment_type': "inbound",
#             'amount': self.recharge_amount,
#             'date': datetime.now().date(),
#             'journal_id': self.journal_id.id,
#             'payment_method_id': 1,
#             'partner_type': 'customer',
#             'partner_id': Partner.id,
#         })
#         payment_create.action_post()  # Confirm Account Payment

#         value = {
#             'wallet_type': 'kas',
#             'reference': 'manual',
#             'amount': self.recharge_amount,
#             'partner_id': Partner.id,
#             'currency_id': Partner.property_product_pricelist.currency_id.id,
#         }
#         PosWalletTransaction.sudo().create(value)

#         Partner.write({'wallet_balance': Partner.calculate_wallet()})

#         if self.recharge_type in ['saku_based', 'manual_based']:
#             UangSaku = self.env['cdn.uang_saku'].sudo()
#             UangSaku.create({
#                 'tgl_transaksi': timestamp,
#                 'siswa_id': Partner.id,
#                 'jns_transaksi': 'keluar',
#                 'amount_out': self.recharge_amount,
#                 'validasi_id': self.env.user.id,
#                 'validasi_time': timestamp,
#                 'keterangan': 'Wallet Recharge',
#                 'state': 'confirm',
#             })
#             Partner.write({
#                 'saldo_uang_saku': Partner.calculate_saku(),
#             })
#         return

#     # onchange
#     @api.onchange('recharge_amount')
#     def _onchange_recharge_amount(self):
#         if self.recharge_type == 'saku_based' and self.recharge_amount > self.env.user.company_id.max_wallet:
#             return {
#                 'warning': {
#                     'title': 'Warning', 
#                     'message': 'Pengisian saldo dompet melebihi batas maksimal dompet, batas maksimal dompet adalah Rp. ' + str(self.env.user.company_id.max_wallet)
#                 },
#                 'value': {
#                     'recharge_amount': self._default_amount()
#                 },
#             }


#     @api.onchange('recharge_type')
#     def _onchange_recharge_type(self):
#         if self.recharge_type == 'saku_based':
#             self.recharge_amount = self._default_amount()
#         else:
#             self.recharge_amount = 0


from datetime import datetime, timedelta
from odoo import models, fields, api
from odoo.exceptions import UserError
from lxml import etree
import logging

_logger = logging.getLogger(__name__)

class WalletRecharge(models.TransientModel):
    _inherit = 'recharge.wallet'

    def _get_partner_id(self):
        context = self._context or {}
        active_id = context.get('active_id', False)
        model = self._context.get('active_model')
        if not active_id:
            _logger.warning("Tidak ada active_id dalam konteks.")
            return False

        partner_id = active_id
        if model == 'cdn.siswa':
            Siswa = self.env['cdn.siswa'].browse(active_id)
            if not Siswa.partner_id:
                _logger.error(f"Tidak ditemukan partner_id untuk siswa {active_id}")
                return False
            partner_id = Siswa.partner_id.id
            _logger.info("Id Dari Partner %s", partner_id)
        return partner_id


    def _default_amount(self):
        if not self.siswa_id:
            return 0
        
        Partner = self.siswa_id
        dompet = Partner.wallet_balance
        max_wallet = self.env.user.company_id.max_wallet
        return max(0, max_wallet - dompet)

    recharge_amount = fields.Float(
            string='Nominal Saldo', required=True, readonly=False, compute="_compute_recharge_amount", store=True
        )
    siswa_id = fields.Many2one(
        comodel_name='res.partner', string='Siswa', readonly=True, default=lambda self: self._get_partner_id(), ondelete='cascade'
    )
    wallet_balance = fields.Float(string='Saldo Dompet', related='siswa_id.wallet_balance', readonly=True)
    saldo_uang_saku = fields.Float(string='Saldo Santri', related='siswa_id.saldo_uang_saku', readonly=True)
    recharge_type = fields.Selection(selection=[
        ('manual_based', 'Isi Dompet Manual'),
        ('saku_based', 'Isi Berdasarkan Saldo'),
        ('limit_hari', 'Isi dengan Limit Harian'),
        ('limit_minggu', 'Isi dengan Limit Mingguan'),
        ('limit_bulan', 'Isi dengan Limit Bulanan'),
    ], default='manual_based', string='Tipe Isi Saldo', 
       help="Untuk pilihan limit hanya bisa di isi satu kali dan akan ada waktu tunggu penggunaan, untuk isi berdasaarkan saldo akan mengambil keseluruhan saldo yang ada untuk isi dompet.")
    
    
    # Batas maksimal saldo yang bisa diisi ulang
    LIMITS = {
        'limit_hari': 50000,
        'limit_minggu': 200000,
        'limit_bulan': 600000,
    }

    def _get_reset_time(self, last_recharge_time):
        """ Menentukan kapan reset saldo terjadi berdasarkan jenis recharge """
        return {
            'limit_hari': last_recharge_time + timedelta(days=1),  # 24 jam dari transaksi terakhir
            'limit_minggu': last_recharge_time + timedelta(weeks=1),  # 7 hari dari transaksi terakhir
            'limit_bulan': last_recharge_time + timedelta(days=30),  # 30 hari dari transaksi terakhir
        }.get(self.recharge_type, last_recharge_time)


    def _check_recharge_limit(self):
        """ Memeriksa apakah transaksi masih dalam periode pembatasan waktu dan saldo """
        now = datetime.now()

        if not self.siswa_id:
            return  # Jika tidak ada siswa, abaikan pengecekan

        last_recharge = self.env['cdn.uang_saku'].search([
            ('siswa_id', '=', self.siswa_id.id),
            ('jns_transaksi', '=', 'keluar'),
            ('keterangan', 'ilike', self.recharge_type)
        ], order='tgl_transaksi desc', limit=1)

        # Jika belum ada transaksi sebelumnya, langsung izinkan
        if not last_recharge:
            return  

        # Hitung kapan saldo bisa diisi ulang kembali
        reset_time = self._get_reset_time(last_recharge.tgl_transaksi)

        # **PERUBAHAN DI SINI**: Jika masih dalam cooldown, langsung raise error tanpa lanjut ke pengecekan saldo
        if now < reset_time:
            remaining_time = reset_time - now
            days, remainder = divmod(remaining_time.total_seconds(), 86400)  # Konversi ke hari
            hours, remainder = divmod(remainder, 3600)
            minutes, _ = divmod(remainder, 60)

            limit_labels = {
                'limit_hari': 'Waktu limit harian Anda :',
                'limit_minggu': 'Waktu limit mingguan Anda :',
                'limit_bulan': 'Waktu limit bulanan Anda :',
            }
            limit_message = limit_labels.get(self.recharge_type, "Waktu limit tidak diketahui")

            raise UserError(
                f"⚠️ Validasi\n\n"
                f"Anda tidak bisa melakukan pengisian ulang sekarang.\n"
                f"{limit_message} {int(days)} hari {int(hours)} jam {int(minutes)} menit\n"
                f"Silahkan coba lagi jika cooldown limit sudah berakhir."
            )

        # **PERBAIKAN LAINNYA**: Pastikan hanya transaksi dalam periode yang sama dihitung
        batas_saldo = self.LIMITS.get(self.recharge_type, float('inf'))
        total_pengisian = sum(self.env['cdn.uang_saku'].search([
            ('siswa_id', '=', self.siswa_id.id),
            ('jns_transaksi', '=', 'keluar'),
            ('keterangan', 'ilike', self.recharge_type),
            ('tgl_transaksi', '>=', now - timedelta(days=1))  # Hanya transaksi dalam periode ini
        ]).mapped('amount_out')) + self.recharge_amount

        if total_pengisian > batas_saldo:
            raise models.ValidationError(
                f"Total pengisian untuk {self.recharge_type} melebihi batas Rp {batas_saldo}. Sisa yang bisa diisi: Rp {batas_saldo - (total_pengisian - self.recharge_amount)}."
            )


    @api.depends('recharge_type')
    def _compute_recharge_amount(self):
        for record in self:
            if record.recharge_type == 'manual_based':
                record.recharge_amount = 0  # Biarkan pengguna memasukkan secara manual
            elif record.recharge_type == 'saku_based':
                record.recharge_amount = record.saldo_uang_saku 
            else:
                record.recharge_amount = self.LIMITS.get(record.recharge_type, 0)  # Langsung gunakan limit tanpa mempertimbangkan saldo uang saku

    @api.model
    def default_get(self, fields):
        res = super(WalletRecharge, self).default_get(fields)

        # Cari jurnal yang sesuai dengan perusahaan aktif
        default_journal = self.env['account.journal'].search([
            ('name', '=', 'Jurnal Dompet Santri'),
            ('company_id', '=', self.env.company.id)  # Sesuai dengan perusahaan pengguna saat ini
        ], limit=1)

        if default_journal:
            res['journal_id'] = default_journal.id  # Set nilai default

        return res

    def post(self):
        """ Proses pengisian ulang """
        self._check_recharge_limit()

        if self.recharge_amount < 1000:
            raise UserError('⚠️Nilai recharge dompet harus lebih dari 1000 Rupiah.')

        if (self.saldo_uang_saku or 0) < self.recharge_amount:
            raise UserError('⚠️Saldo Uang Saku Tidak Cukup!')

        if not self.journal_id:
            raise UserError("⚠️Journal tidak ditemukan, harap pilih journal yang valid.")

        AccountPayment = self.env['account.payment']
        Partner = self.siswa_id
        date_now = datetime.strftime(datetime.now(), '%Y-%m-%d')
        timestamp = fields.Datetime.now()

        payment_create = AccountPayment.sudo().create({
            'name': self.env['ir.sequence'].with_context(ir_sequence_date=date_now).next_by_code('account.payment.customer.invoice'),
            'payment_type': "inbound",
            'amount': self.recharge_amount,
            'date': datetime.now().date(),
            'journal_id': self.journal_id.id,
            'payment_method_id': 1,
            'partner_type': 'customer',
            'partner_id': Partner.id,
        })
        payment_create.action_post()

        # Buat transaksi dompet
        self.env['pos.wallet.transaction'].sudo().create({
            'wallet_type': 'kas',
            'reference': 'manual',
            'amount': self.recharge_amount,
            'partner_id': Partner.id,
            'currency_id': Partner.property_product_pricelist.currency_id.id,
        })

        Partner.write({'wallet_balance': Partner.calculate_wallet()})

        # Catat transaksi uang saku
        self.env['cdn.uang_saku'].sudo().create({
            'tgl_transaksi': timestamp,
            'siswa_id': Partner.id,
            'jns_transaksi': 'keluar',
            'amount_out': self.recharge_amount,
            'validasi_id': self.env.user.id,
            'validasi_time': timestamp,
            'keterangan': f'Wallet Recharge - {self.recharge_type}',
            'state': 'confirm',
        })

        Partner.write({'saldo_uang_saku': Partner.calculate_saku()})

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Pengisian Saldo Berhasil !',
                'message': f'Nominal Rp {self.recharge_amount:,.0f} telah berhasil ditambahkan ke dompet {Partner.name}.',
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}  # Menutup form setelah notifikasi
            },
        }
       





# from datetime import datetime, timedelta
# from odoo import api, fields, models, exceptions

# class WalletRecharge(models.TransientModel):
#     _inherit = 'recharge.wallet'

#     def _get_partner_id(self):
#         context = self._context
#         active_id = context.get('active_id')
#         model = context.get('active_model')

#         partner_id = active_id
#         if model == 'cdn.siswa':
#             Siswa = self.env['cdn.siswa'].browse(active_id)
#             partner_id = Siswa.partner_id.id
#         return partner_id

#     # defaults 
#     def _default_amount(self):
#         Partner = self.env['res.partner'].browse(self.siswa_id.id)
#         dompet = Partner.wallet_balance
#         max_wallet = self.env.user.company_id.max_wallet
#         return max_wallet - dompet if dompet < max_wallet else 0

#     # fields
#     recharge_amount = fields.Float('Recharge Amount', required=True, default=0)
#     siswa_id = fields.Many2one(comodel_name='res.partner', string='Siswa', readonly=True, default=lambda self: self._get_partner_id())
#     wallet_balance = fields.Float(string='Saldo Dompet', related='siswa_id.wallet_balance', readonly=True)
#     saldo_uang_saku = fields.Float(string='Saldo Uang Saku', related='siswa_id.saldo_uang_saku', readonly=True)
#     recharge_type = fields.Selection(selection=[
#         ('manual_based', 'Isi Dompet Manual'),
#         ('saku_based', 'Isi Berdasarkan Saldo'),
#         ('limit_hari', 'Harian'),
#         ('limit_minggu', 'Mingguan'),
#     ], default='saku_based', string='Recharge Type', help="Jenis pengisian saldo dompet.")


#     # Modified post method without extra fields (Fixed)
#     def post(self):
#         if self.recharge_amount <= 1000:
#             raise models.ValidationError('Nilai recharge dompet harus lebih dari 1000 Rupiah.')

#         AccountPayment = self.env['account.payment']
#         PosWalletTransaction = self.env['pos.wallet.transaction']
#         UangSaku = self.env['cdn.uang_saku'].sudo()
        
#         date_now = fields.Date.today()
#         timestamp = fields.Datetime.now()
#         start_of_today = datetime.combine(date_now, datetime.min.time())
#         start_of_week = date_now - timedelta(days=date_now.weekday())
#         start_of_week = datetime.combine(start_of_week, datetime.min.time())

#         for partner in self.partner_ids:
#             # **Mengecek transaksi terakhir siswa**
#             transaksi_terakhir = PosWalletTransaction.search([
#                 ('partner_id', '=', partner.id)
#             ], order="create_date desc", limit=1)  # Ambil transaksi terbaru

#             is_limit_hari_terakhir = False
#             is_limit_minggu_terakhir = False

#             if transaksi_terakhir:
#                 last_date = transaksi_terakhir.create_date.date()
#                 is_limit_hari_terakhir = last_date == date_now
#                 is_limit_minggu_terakhir = last_date >= start_of_week.date()  # Perbaikan disini

#                 # **Jika sebelumnya harian lalu sekarang pilih mingguan, ubah limit ke mingguan**
#                 if transaksi_terakhir.reference == 'limit_hari' and self.recharge_type == 'limit_minggu':
#                     is_limit_hari_terakhir = False  # Abaikan batas harian
#                     is_limit_minggu_terakhir = True  # Terapkan batas mingguan

#             # **Validasi berdasarkan tipe recharge yang aktif**
#             if self.recharge_type == 'limit_hari' and is_limit_hari_terakhir:
#                 raise models.ValidationError(f"{partner.name} hanya dapat mengisi dompet sekali dalam sehari. Coba lagi besok.")

#             if self.recharge_type == 'limit_minggu':
#                 transaksi_minggu_ini = PosWalletTransaction.search_count([
#                     ('partner_id', '=', partner.id),
#                     ('create_date', '>=', start_of_week),
#                     ('reference', '=', 'limit_minggu')  # Pastikan hanya menghitung limit_minggu
#                 ])
#                 max_per_minggu = 2
#                 if transaksi_minggu_ini >= max_per_minggu:
#                     raise models.ValidationError(f"{partner.name} hanya dapat mengisi dompet maksimal {max_per_minggu} kali dalam seminggu.")

#             # **Proses pengisian saldo**
#             payment_create = AccountPayment.sudo().create({
#                 'name': self.env['ir.sequence'].with_context(ir_sequence_date=date_now).next_by_code('account.payment.customer.invoice'),
#                 'payment_type': "inbound",
#                 'amount': self.recharge_amount,
#                 'date': fields.Date.today(),
#                 'journal_id': self.journal_id.id,
#                 'payment_method_id': 1,
#                 'partner_type': 'customer',
#                 'partner_id': partner.id,
#             })
#             payment_create.action_post()

#             # **Membuat transaksi dompet**
#             PosWalletTransaction.sudo().create({
#                 'wallet_type': 'kas',
#                 'reference': self.recharge_type,  # Menyimpan tipe recharge untuk tracking
#                 'amount': self.recharge_amount,
#                 'partner_id': partner.id,
#                 'currency_id': partner.property_product_pricelist.currency_id.id,
#             })

#             # **Update saldo dompet**
#             partner.write({'wallet_balance': partner.calculate_wallet()})

#             # **Membuat transaksi uang saku**
#             UangSaku.create({
#                 'tgl_transaksi': timestamp,
#                 'siswa_id': partner.id,
#                 'jns_transaksi': 'keluar',
#                 'amount_out': self.recharge_amount,
#                 'validasi_id': self.env.user.id,
#                 'validasi_time': timestamp,
#                 'keterangan': 'Wallet Recharge',
#                 'state': 'confirm',
#             })
#             partner.write({
#                 'saldo_uang_saku': partner.calculate_saku(),
#             })

#         return {'type': 'ir.actions.act_window_close'}

#     # onchange
#     @api.onchange('recharge_amount')
#     def _onchange_recharge_amount(self):
#         if self.recharge_type == 'saku_based' and self.recharge_amount > self.env.user.company_id.max_wallet:
#             return {
#                 'warning': {
#                     'title': 'Warning', 
#                     'message': 'Pengisian saldo dompet melebihi batas maksimal dompet, batas maksimal dompet adalah Rp. ' + str(self.env.user.company_id.max_wallet)
#                 },
#                 'value': {
#                     'recharge_amount': self._default_amount()
#                 },
#             }

#     @api.onchange('recharge_type')
#     def _onchange_recharge_type(self):
#         if self.recharge_type == 'saku_based':
#             self.recharge_amount = self._default_amount()
#         elif self.recharge_type == 'limit_hari':
#             self.recharge_amount = 50000  # Batasan harian
#         elif self.recharge_type == 'limit_minggu':
#             self.recharge_amount = 200000  # Batasan mingguan
#         else:
#             self.recharge_amount = 0