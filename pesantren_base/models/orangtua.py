#!/usr/bin/python
#-*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class OrangTua(models.Model):

    _name               = "cdn.orangtua"
    _description        = "Tabel Data Akun Orang Tua"
    _inherit            = ['mail.thread', 'mail.activity.mixin']
    _inherits           = {"res.partner": "partner_id"}

    partner_id          = fields.Many2one('res.partner', 'Partner', required=True, ondelete="cascade")
    nik                 = fields.Char( string="NIK",  help="")
    hubungan            = fields.Selection(selection=[('ayah','Ayah'),('ibu','Ibu'),('wali','Wali')],  string="Hubungan",  help="")
    label               = fields.Many2many('res.partner.category', 'Tag')
    siswa_ids           = fields.One2many(comodel_name="cdn.siswa",  inverse_name="orangtua_id",  string="Siswa",  help="" , ondelete='cascade')
    isLimit             = fields.Boolean(string="Akses Limit", help='Saat Diaktifkan sistem akan memberikan orang tua akses untuk mengatur limit penggunaan saldo anaknya')

    user_id = fields.Many2one(
        'res.users',
        string="User Login",
        help="Akun login yang terhubung dengan orang tua",
        ondelete="cascade"
    )

    password            = fields.Char(string="Password", help="Password login untuk akun orang tua")

    @api.model
    def default_get(self, fields):
       res = super(OrangTua,self).default_get(fields)
       res['jns_partner'] = 'ortu'
       return res


    def _update_user_group_limit(self):
        group_orangtua_limit = self.env.ref('pesantren_kesantrian.group_kesantrian_orang_tua_acces_limit')

        for record in self:
            user = record.partner_id.user_ids[:1]  
            if not user:
                continue

            if record.isLimit:
                if group_orangtua_limit not in user.groups_id:
                    user.groups_id = [(4, group_orangtua_limit.id)] 
            else:
                if group_orangtua_limit in user.groups_id:
                    user.groups_id = [(3, group_orangtua_limit.id)]     

    # @api.model
    # def create(self, vals):
    #     record = super(OrangTua, self).create(vals)

    #     # Buat user login kalau ada password & email
    #     if vals.get("password") and record.partner_id.email:
    #         login = record.partner_id.email

    #         # cek apakah sudah ada user dengan login tsb
    #         existing_user = self.env["res.users"].search([("login", "=", login)], limit=1)

    #         if existing_user:
    #             # kalau sudah ada → sambungkan
    #             record.user_id = existing_user.id
    #             # update password kalau diberikan
    #             existing_user.write({"password": vals.get("password")})
    #             # pastikan group orangtua sudah ada
    #             group_orangtua = self.env.ref("pesantren_kesantrian.group_kesantrian_orang_tua")
    #             if group_orangtua not in existing_user.groups_id:
    #                 existing_user.groups_id = [(4, group_orangtua.id)]
    #         else:
    #             # kalau belum ada → buat user baru
    #             user_vals = {
    #                 "name": record.name,
    #                 "login": login,
    #                 "password": vals.get("password"),
    #                 "partner_id": record.partner_id.id,
    #                 "groups_id": [(6, 0, [self.env.ref("pesantren_kesantrian.group_kesantrian_orang_tua").id])],
    #             }
    #             user = self.env["res.users"].create(user_vals)
    #             record.user_id = user.id

    #     record._update_user_group_limit()
    #     return record

    # def write(self, vals):
    #     res = super(OrangTua, self).write(vals)

    #     for record in self:
    #         # Update password user jika diubah
    #         if vals.get("password") and record.user_id:
    #             record.user_id.write({"password": vals.get("password")})

    #         # Update group limit kalau isLimit berubah
    #         if 'isLimit' in vals:
    #             record._update_user_group_limit()

    #     return res 

    def write(self, vals):
        res = super().write(vals)
        for record in self:
            if vals.get('set_password') and record.user_id:
                record.user_id.write({'password': vals['set_password']})
        return res