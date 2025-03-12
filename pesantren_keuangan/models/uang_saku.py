from odoo import api, fields, models


class UangSaku(models.Model):
    _name           = 'cdn.uang_saku'
    _description    = 'Uang Saku Santri'
    _order          = 'tgl_transaksi desc'

    name            = fields.Char(string='Name', readonly=True)
    tgl_transaksi   = fields.Datetime(string='Tgl Transaksi', required=True, default=fields.Datetime.now, widget="date")
    siswa_id        = fields.Many2one(comodel_name='res.partner', string='Siswa Partner', required=True, domain=[('siswa_id', '!=', False)])
    siswa           = fields.Many2one(comodel_name='cdn.siswa',compute='_compute_siswa',string='Siswa',store=True)
    va_saku         = fields.Char(string='No. VA Saku', related='siswa_id.va_saku', readonly=True, store=True)
    saldo_awal      = fields.Float(string='Saldo Awal', readonly=True, store=True, compute='_compute_saldo_awal')

    jns_transaksi   = fields.Selection(string='Jenis Transaksi', selection=[
        ('masuk', 'Uang Masuk'),
        ('keluar', 'Uang Keluar'),
    ], required=True, default='masuk')
    amount_in       = fields.Float(string='Nominal Masuk')
    amount_out      = fields.Float(string='Nominal Keluar')

    validasi_id     = fields.Many2one(comodel_name='res.users', string='Validasi', readonly=True)
    validasi_time   = fields.Datetime(string='Tgl Validasi', readonly=False)
    keterangan      = fields.Text(string='Keterangan', states={'confirm': [('readonly', True)]})

    state           = fields.Selection(string='State', selection=[
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
    ], default='draft', readonly=True)
    
    orangtua_id = fields.Many2one(
        comodel_name='cdn.orangtua',
        string='Orang Tua',
        related='siswa.orangtua_id',
        readonly=True,
        store=True
    )
    musyrif_id = fields.Many2one('hr.employee', string='Musyrif', related='siswa.musyrif_id', readonly=True)

    # override
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('cdn.uang_saku') or 'New'
        result = super(UangSaku, self).create(vals)
        return result

    # actions
    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'
            rec.validasi_id = self.env.user.id
            rec.validasi_time = fields.Datetime.now()
            rec.siswa_id.write({
                'saldo_uang_saku': rec.siswa_id.calculate_saku(),
            })
            rec.kirim_email_pemberitahuan()

    def kirim_email_pemberitahuan(self):
        for record in self:
            if record.siswa and record.siswa.orangtua_id and record.siswa.orangtua_id.partner_id.email:
                parent_email = record.siswa.orangtua_id.partner_id.email

                sender_name = "Pengurus Pondok Dqi"
                sender_mail = "ponpesdqi@gmail.com"
                email_from = f'"{sender_name}" <{sender_mail}>'

                amount_in_formatted = f"Rp{'{:,.0f}'.format(record.amount_in).replace(',', '.')}"
                saldo_formatted = f"Rp{'{:,.0f}'.format(record.siswa_id.saldo_uang_saku).replace(',', '.')}"
                
                subject = f"Saldo sudah masuk ke santri bernama {record.siswa.name}"
                body_html = f"""
                   <div style="background-color: #f5f8fa; padding: 30px; font-family: 'Arial', sans-serif;">
                        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow: hidden;">
                            <!-- Header -->
                            <div style="background-color: #005299; color: #ffffff; text-align: center; padding: 30px;">
                                <img src="https://i.ibb.co.com/SmWmBTW/SAVE-20220114-075750-removebg-preview-4.png" alt="Logo" style="margin:0 0 15px 0;box-sizing:border-box;vertical-align:middle;width: 80px; height: 80px; margin-bottom: 15px;" width="80">
                                <h1 style="margin: 0; font-size: 24px; font-weight: 600;">Pesantren Daarul Qur'an Istiqomah</h1>
                            </div>
                            
                            <!-- Content -->
                            <div style="padding: 30px;">
                                <p style="font-size: 16px; line-height: 1.6; color: #333333; margin-top: 0;">Assalamualaikum,</p>
                                
                                <p style="font-size: 16px; line-height: 1.6; color: #333333;">Dengan ini kami informasikan bahwa saldo uang saku sudah masuk ke akun santri:</p>
                                
                                <div style="background-color: #f8f9fa; border-left: 4px solid #005299; padding: 15px; margin: 20px 0; border-radius: 4px;">
                                    <p style="margin: 8px 0; font-size: 15px; color: #333333;"><strong>Nama Santri:</strong> {record.siswa.name}</p>
                                    <p style="margin: 8px 0; font-size: 15px; color: #333333;"><strong>Virtual Account:</strong> {record.va_saku}</p>
                                    <p style="margin: 8px 0; font-size: 15px; color: #333333;"><strong>Jumlah:</strong> {amount_in_formatted}</p>
                                    <p style="margin: 8px 0; font-size: 15px; color: #333333;"><strong>Tanggal:</strong> {record.tgl_transaksi}</p>
                                    <p style="margin: 8px 0; font-size: 15px; color: #333333;"><strong>Saldo Sekarang:</strong> {saldo_formatted}</p>
                                </div>
                                
                                <p style="font-size: 16px; line-height: 1.6; color: #333333;">Terima kasih.</p>
                            </div>
                            
                            <!-- Footer -->
                            <div style="background-color: #f0f4f8; text-align: center; padding: 15px; color: #666666; font-size: 14px; border-top: 1px solid #e7eaec;">
                                <p style="margin: 5px 0;">Pesantren Daarul Qur'an Istiqomah</p>
                            </div>
                        </div>
                    </div>
                """ 
                email_values = {
                    'subject': subject,
                    'email_to': parent_email,
                    'reply_to': email_from,
                    'body_html': body_html,
                    'body': f"""Assalamualaikum,
                    Dengan ini kami informasikan bahwa saldo uang saku sudah masuk ke akun santri:
                    
                        Nama Santri: {record.siswa.name}
                        Virtual Account: {record.va_saku}
                        Jumlah: {amount_in_formatted}
                        Tanggal: {record.tgl_transaksi}
                        Saldo Sekarang: {saldo_formatted}

                    Terima kasih.

                    Pesantren Daarul Qur'an Istiqomah
                    """
                }
                
                self.env['mail.mail'].create(email_values).send()

    # compute
    @api.depends('siswa_id')
    def _compute_saldo_awal(self):
        for record in self:
            if record.siswa_id:
                record.saldo_awal = record.siswa_id.calculate_saku(record.validasi_time)
    # def _compute_saldo_awal(self):
    #     for record in self:
    #         record.saldo_awal = record.siswa_id.calculate_saku(self.validasi_time)
    @api.depends('siswa_id')
    def _compute_siswa(self):
        for record in self:
            Siswa = self.env['cdn.siswa'].search([('partner_id','=',record.siswa_id.id)]) # siswa_id is partner_id
            if Siswa:
                record.siswa = Siswa[0].id
            else:
                record.siswa = False

    