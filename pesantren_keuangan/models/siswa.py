from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.exceptions import UserError

class SiswaInherit(models.Model):
    _inherit        = 'cdn.siswa'

    limit           = fields.Selection(selection=[
        ('hari', 'Perhari'),
        ('minggu', 'Perminggu'),
        ('bulan', 'Bulan'),
    ], string='Periode')

    amount              = fields.Float(string="Total", digits=(16, 0))
    used_amount         = fields.Float(string="Jumlah Terpakai", digits=(16, 0), default=0)
    limit_reset_date    = fields.Datetime(string="Tanggal Reset Limit", readonly=True)
    is_limit_active     = fields.Boolean(string="Limit Aktif", default=False)
    remaining_limit     = fields.Float(string="Sisa Limit", digits=(16, 0) ,compute="_compute_remaining_limit")

    total_invoiced      = fields.Monetary(string='Total Tagihan', compute='_compute_invoice_totals',currency_field='currency_id',store=False  )
    total_due           = fields.Monetary(string='Sisa Tagihan', compute='_compute_invoice_totals',currency_field='currency_id', store=False  )
    total_paid          = fields.Monetary(string='Total Dibayar',compute='_compute_invoice_totals',currency_field='currency_id',store=False  )
    currency_id         = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id', readonly=True)    
    saldo_tagihan_formatted = fields.Char(string='Saldo Tagihan Formatted',compute='_compute_formatted_amounts',store=False  )
    uang_saku_formatted = fields.Char(string='Uang Saku Formatted',compute='_compute_formatted_amounts',store=False)

    # Perbaikan: Dependency yang lebih spesifik dan comprehensive
    @api.depends('partner_id','partner_id.invoice_ids','partner_id.invoice_ids.state','partner_id.invoice_ids.amount_total','partner_id.invoice_ids.amount_residual')
    def _compute_invoice_totals(self):
        for siswa in self:
            if not siswa.partner_id:
                siswa.total_invoiced = siswa.total_due = siswa.total_paid = 0.0
                continue

            domain = [
                ('partner_id', '=', siswa.partner_id.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '!=', 'cancel')
            ]
            invoices = self.env['account.move'].search(domain)

            siswa.total_invoiced = sum(invoices.mapped('amount_total_signed'))
            siswa.total_due = sum(invoices.mapped('amount_residual_signed'))
            siswa.total_paid = siswa.total_invoiced - siswa.total_due


    # Perbaikan: Dependency yang benar untuk formatted amounts
    @api.depends('total_due', 'saldo_uang_saku')
    def _compute_formatted_amounts(self):
        for siswa in self:
            siswa.saldo_tagihan_formatted = f"{siswa.total_due:,.0f}".replace(",", ".") if siswa.total_due else "0"
            siswa.uang_saku_formatted = f"{siswa.saldo_uang_saku:,.0f}".replace(",", ".") if siswa.saldo_uang_saku else "0"

    def action_saldo_tagihan(self):
        """Gunakan view dari action preset dan domain partner_id"""
        self.ensure_one()
        if not self.partner_id:
            raise UserError("Santri tidak memiliki partner yang terkait.")

        return {
            'name': f'Tagihan {self.partner_id.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'views': [
                (self.env.ref('pesantren_keuangan.pesantren_tagihan_keuangan_view_tree').id, 'list'),
                (self.env.ref('pesantren_keuangan.pesantren_tagihan_keuangan_view_form').id, 'form'),
            ],
            'search_view_id': self.env.ref('pesantren_keuangan.pesantren_tagihan_keuangan_view_search').id,
            'domain': [
                ('partner_id', '=', self.partner_id.id), 
                ('move_type', '=', 'out_invoice')
            ],
            'context': {
                'default_move_type': 'out_invoice',
                'default_partner_id': self.partner_id.id,
                'default_siswa_id': self.id,
                'search_default_filter_by_blm_lunas': 1,
                # Pastikan form view menggunakan view yang benar
                'form_view_ref': 'pesantren_keuangan.pesantren_tagihan_keuangan_view_form',
                'tree_view_ref': 'pesantren_keuangan.pesantren_tagihan_keuangan_view_tree',
            },
            'target': 'current',
        }


    # Tambahkan method untuk action uang saku
    def action_uang_saku(self):
        self.ensure_one()
        if not self.partner_id:
            raise UserError("Santri ini belum memiliki partner yang terkait.")
        
        return {
            'name': f'Uang Saku - {self.name}',
            'view_mode': 'list,form',
            'res_model': 'cdn.uang_saku',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {
                'default_siswa_id': self.partner_id.id
            },
            'domain': [('siswa_id', '=', self.partner_id.id)],
        }
    
    def _reset_expired_limits(self):
        """Fungsi scheduler untuk reset limit yang sudah expired"""
        now = fields.Datetime.now()
        expired_limits = self.search([
            ('is_limit_active', '=', True),
            ('limit_reset_date', '<=', now)
        ])
        
        for santri in expired_limits:
            reset_date = now
            if santri.limit == 'hari':
                reset_date = now + relativedelta(days=1)
            elif santri.limit == 'minggu':
                reset_date = now + relativedelta(weeks=1)
            elif santri.limit == 'bulan':
                reset_date = now + relativedelta(months=1)
            
            santri.write({
                'used_amount': 0,
                'limit_reset_date': reset_date,
            })


    @api.depends('amount', 'used_amount')
    def _compute_remaining_limit(self):
        for record in self:
            record.remaining_limit = record.amount - record.used_amount

    def create_data_account(self):
        self.partner_id.create_data_account()

    def action_view_pos_order(self):
        action = self.env["ir.actions.actions"]._for_xml_id("pesantren_keuangan.pos_order_action_internal")
        action['domain'] = [('partner_id', '=', self.partner_id.id)]
        action['context'] = {'partner_id': self.partner_id.id}
        return action
        
    pos_order_count = fields.Integer(string='POS Orders', compute='_compute_pos_order_count')
    
    @api.depends('partner_id')
    def _compute_pos_order_count(self):
        for siswa in self:
            siswa.pos_order_count = self.env['pos.order'].search_count([('partner_id', '=', siswa.partner_id.id)])

    def action_setlimit(self):
        context = dict(self.env.context)
        active_ids = context.get('active_ids', [])

        return {
            'name': 'Atur Limit Penggunaan Saldo',
            'type': 'ir.actions.act_window',
            'res_model': 'set.limit.santri',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_partner_ids': active_ids}
        }


