# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID

def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    all_companies = env['res.company'].sudo().search([])
    allowed_company_ids = all_companies.ids

    role_walikelas = env['cdn.jenis_pegawai'].sudo().search([('code', '=', 'walikelas')], limit=1)
    if role_walikelas:
        classrooms = env['cdn.ruang_kelas'].sudo().with_context(allowed_company_ids=allowed_company_ids).search([('walikelas_id', '!=', False)])
        walikelas_ids = classrooms.mapped('walikelas_id')
        for employee in walikelas_ids:
            if role_walikelas not in employee.jns_pegawai_ids:
                employee.write({
                    'jns_pegawai_ids': [(4, role_walikelas.id)]
                })
            else:
                employee._sync_user_groups()

    # 2. Recompute company_id (Lembaga) for all historical attendance records
    absensi = env['cdn.absensi_siswa'].sudo().with_context(allowed_company_ids=allowed_company_ids).search([])
    company_dict = {}
    for c in all_companies:
        name_lower = c.name.lower()
        words = name_lower.split()
        if 'kb' in words or 'paud' in name_lower:
            company_dict['paud'] = c.id
        if 'tk' in words or 'tk ' in name_lower:
            company_dict['tk'] = c.id
        if 'sd' in words or 'sd ' in name_lower:
            company_dict['sd'] = c.id
        if 'smp' in words or 'smp ' in name_lower:
            company_dict['smp'] = c.id
        if 'ma' in words or 'sma' in words or 'ma ' in name_lower or 'sma ' in name_lower:
            if 'istiqomah' not in name_lower or 'ma' in words:
                company_dict['sma'] = c.id
        if 'rumah tahf' in name_lower or 'rtq' in name_lower:
            company_dict['rtq'] = c.id

    for rec in absensi:
        if rec.kelas_id and rec.kelas_id.jenjang:
            target_company_id = company_dict.get(rec.kelas_id.jenjang)
            if target_company_id and rec.company_id.id != target_company_id:
                rec.write({'company_id': target_company_id})
