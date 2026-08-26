# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID

def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    role_walikelas = env['cdn.jenis_pegawai'].sudo().search([('code', '=', 'walikelas')], limit=1)
    if role_walikelas:
        classrooms = env['cdn.ruang_kelas'].search([('walikelas_id', '!=', False)])
        walikelas_ids = classrooms.mapped('walikelas_id')
        for employee in walikelas_ids:
            if role_walikelas not in employee.jns_pegawai_ids:
                employee.write({
                    'jns_pegawai_ids': [(4, role_walikelas.id)]
                })
            else:
                employee._sync_user_groups()
