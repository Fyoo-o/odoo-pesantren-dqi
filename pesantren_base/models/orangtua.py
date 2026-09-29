# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class OrangTua(models.Model):

    _name = "cdn.orangtua"
    _description = "Tabel Data Akun Orang Tua"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {"res.partner": "partner_id"}

    partner_id = fields.Many2one(
        'res.partner', 'Partner', required=True, ondelete="cascade")
    nik = fields.Char(string="NIK",  help="Nomor Induk Kependudukan Orang Tua/Wali")
    hubungan = fields.Selection(selection=[(
        'ayah', 'Ayah'), ('ibu', 'Ibu'), ('wali', 'Wali')],  string="Hubungan",  help="Status hubungan dengan siswa (Ayah/Ibu/Wali)")
    label = fields.Many2many('res.partner.category', 'Tag')
    siswa_ids = fields.Many2many(
        comodel_name="cdn.siswa",
        relation="cdn_siswa_orangtua_rel",
        column1="orangtua_id",
        column2="siswa_id",
        string="Siswa",
        help="Daftar santri/siswa yang terhubung dengan akun orang tua ini")
    isLimit = fields.Boolean(
        string="Akses Limit",
        default=True,
        help='Saat Diaktifkan sistem akan memberikan orang tua akses untuk mengatur limit penggunaan saldo anaknya'
    )

    user_id = fields.Many2one(
        'res.users',
        string="User Login",
        help="Akun login yang terhubung dengan orang tua",
        ondelete="cascade"
    )

    password = fields.Char(
        string="Password", help="Password login untuk akun orang tua", store=True)

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if record.user_id and record.partner_id:
            record.partner_id.user_id = record.user_id
        record._update_user_group_limit()
        return record

    def write(self, vals):
        res = super(OrangTua, self).write(vals)
        if 'isLimit' in vals or 'user_id' in vals:
            self._update_user_group_limit()
        return res

    @api.model
    def default_get(self, fields):
        res = super(OrangTua, self).default_get(fields)
        res['jns_partner'] = 'ortu'
        return res

    def _update_user_group_limit(self):
        group_orangtua_limit = self.env.ref(
            'pesantren_kesantrian.group_kesantrian_orang_tua_acces_limit', raise_if_not_found=False)
        if not group_orangtua_limit:
            return

        for record in self:
            users = record.user_id | (record.partner_id.user_ids if record.partner_id else self.env['res.users'])
            if not users and record.email:
                users = self.env['res.users'].sudo().search([('login', '=', record.email)])
            for user in users:
                if record.isLimit:
                    if group_orangtua_limit not in user.groups_id:
                        user.sudo().write({'groups_id': [(4, group_orangtua_limit.id)]})
                else:
                    if group_orangtua_limit in user.groups_id:
                        user.sudo().write({'groups_id': [(3, group_orangtua_limit.id)]})
