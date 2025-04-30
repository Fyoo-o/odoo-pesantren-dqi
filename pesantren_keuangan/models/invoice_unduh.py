# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.http import request
import werkzeug.urls
import base64
from odoo.exceptions import UserError

class InvoiceDownloadWizard(models.TransientModel):
    _name = 'invoice.download.wizard'
    _description = 'Wizard Konfirmasi Unduh Faktur'

    invoice_id = fields.Many2one('account.move', string='Faktur', required=True)
    invoice_name = fields.Char(string='Nomor Faktur')
    
    def action_preview(self):
        """Aksi untuk melihat pratinjau faktur"""
        self.ensure_one()
        return self.invoice_id.with_context(force_website=True).preview_invoice()
        
    def action_download(self):
        """Aksi untuk mengunduh faktur"""
        self.ensure_one()
        
        # Gunakan method preview_invoice yang sudah ada tapi tambahkan parameter download=True
        return {
            'type': 'ir.actions.act_url',
            'url': '/my/invoices/%s?report_type=pdf&download=true' % (self.invoice_id.id),
            'target': 'self',
        }