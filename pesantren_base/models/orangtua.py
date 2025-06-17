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

    def write(self, vals):
        res = super(OrangTua, self).write(vals)
        if 'isLimit' in vals:
            self._update_user_group_limit()
        return res

    @api.model
    def create(self, vals):
        record = super(OrangTua, self).create(vals)
        record._update_user_group_limit()
        return record
        



    
