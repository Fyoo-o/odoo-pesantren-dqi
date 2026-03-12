# -*- coding: utf-8 -*-

from odoo import fields, models, _


class AccountJournal(models.Model):
    """Module inherited for adding the reconcile method in the account
    journal"""
    _inherit = "account.journal"

    multiple_invoice_ids = fields.One2many('multiple.invoice',
                                           'journal_id',
                                           string='Multiple Invoice')
    multiple_invoice_type = fields.Selection(
        [('text', 'Text'), ('watermark', 'Watermark')], required=True,
        default='text', string="Display Type")
    text_position = fields.Selection([
        ('header', 'Header'),
        ('footer', 'Footer'),
        ('body', 'Document Body')
    ], required=True, default='header', string='Text Position')
    body_text_position = fields.Selection([
        ('tl', 'Top Left'),
        ('tr', 'Top Right'),
        ('bl', 'Bottom Left'),
        ('br', 'Bottom Right'),
    ], default='tl', string='Body Text Position')
    text_align = fields.Selection([
        ('right', 'Right'),
        ('left', 'Left'),
        ('center', 'Center'),
    ], default='right', string='Center Align Text Position')
    layout = fields.Char(string="Layout",
                         related="company_id.external_report_layout_id.key")

    def action_open_reconcile(self):
        """Open the reconciliation view based on the type of the account journal."""
        self.ensure_one()

    def create_cash_statement(self):
        """for redirecting in to bank statement lines"""
        return {
            'name': _("Statements"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.bank.statement.line',
            'view_mode': 'list,form',
            'context': {'default_journal_id': self.id},
        }
