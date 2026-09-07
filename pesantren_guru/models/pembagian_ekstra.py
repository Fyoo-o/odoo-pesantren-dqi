from odoo import models, fields, api
from datetime import date, datetime


class PembagianEkstra(models.Model):
    _name = "cdn.pembagian_ekstra"
    _description = "Tabel untuk Pembagian Ekstrakulikuler untuk Santri"

    def _get_domain_guru(self):
        admin_user_ids = self.env.ref('base.group_system').users.ids

        return [
            '|',
            ('user_id', 'in', admin_user_ids),
            ('jns_pegawai_ids.code', 'in', ['guru', 'walikelas', 'superadmin'])
        ]

    name = fields.Many2one("cdn.ekstrakulikuler", string="Ekstrakulikuler", required=True)
    siswa_ids = fields.Many2many(
        'cdn.siswa', string='Daftar Siswa', ondelete='cascade')
    penanggung_id = fields.Many2one(
        "hr.employee",
        string="Penanggung Jawab",
        help="Guru yang bertanggung jawab membina atau mengelola kegiatan ekstrakurikuler ini",
        domain=lambda self: self.env['cdn.pembagian_ekstra']._get_domain_guru()
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.siswa_ids and rec.name:
                rec.siswa_ids.sudo().write({
                    'ekstrakulikuler_ids': [(4, rec.name.id)]
                })
        return records

    def write(self, vals):
        # Catat snapshot ID siswa lama dan ekskul lama sebelum write
        old_data = {}
        if 'siswa_ids' in vals or 'name' in vals:
            for rec in self:
                old_data[rec.id] = {
                    'siswa_ids': set(rec.siswa_ids.ids),
                    'ekskul_id': rec.name.id if rec.name else False,
                }

        record = super().write(vals)

        if old_data:
            for rec in self:
                old = old_data.get(rec.id, {})
                old_siswa_ids = old.get('siswa_ids', set())
                old_ekskul_id = old.get('ekskul_id')
                new_ekskul_id = rec.name.id if rec.name else False
                new_siswa_ids = set(rec.siswa_ids.ids)

                # Jika master ekskul diubah pada form ini
                if old_ekskul_id and old_ekskul_id != new_ekskul_id:
                    if old_siswa_ids:
                        other = self.env['cdn.pembagian_ekstra'].search([
                            ('id', '!=', rec.id),
                            ('name', '=', old_ekskul_id),
                            ('siswa_ids', 'in', list(old_siswa_ids))
                        ])
                        keep_ids = set(other.mapped('siswa_ids').ids)
                        to_remove_ids = old_siswa_ids - keep_ids
                        if to_remove_ids:
                            self.env['cdn.siswa'].browse(list(to_remove_ids)).sudo().write({
                                'ekstrakulikuler_ids': [(3, old_ekskul_id)]
                            })
                    if rec.siswa_ids and new_ekskul_id:
                        rec.siswa_ids.sudo().write({
                            'ekstrakulikuler_ids': [(4, new_ekskul_id)]
                        })
                else:
                    # Ekskul tetap, lakukan diff siswa
                    current_ekskul_id = new_ekskul_id
                    if current_ekskul_id:
                        removed_ids = old_siswa_ids - new_siswa_ids
                        if removed_ids:
                            other = self.env['cdn.pembagian_ekstra'].search([
                                ('id', '!=', rec.id),
                                ('name', '=', current_ekskul_id),
                                ('siswa_ids', 'in', list(removed_ids))
                            ])
                            keep_ids = set(other.mapped('siswa_ids').ids)
                            to_remove_ids = removed_ids - keep_ids
                            if to_remove_ids:
                                self.env['cdn.siswa'].browse(list(to_remove_ids)).sudo().write({
                                    'ekstrakulikuler_ids': [(3, current_ekskul_id)]
                                })
                        added_ids = new_siswa_ids - old_siswa_ids
                        if added_ids:
                            self.env['cdn.siswa'].browse(list(added_ids)).sudo().write({
                                'ekstrakulikuler_ids': [(4, current_ekskul_id)]
                            })
        return record

    def unlink(self):
        for rec in self:
            if rec.siswa_ids and rec.name:
                other = self.env['cdn.pembagian_ekstra'].search([
                    ('id', '!=', rec.id),
                    ('name', '=', rec.name.id),
                    ('siswa_ids', 'in', rec.siswa_ids.ids)
                ])
                keep_ids = set(other.mapped('siswa_ids').ids)
                to_remove_ids = set(rec.siswa_ids.ids) - keep_ids
                if to_remove_ids:
                    self.env['cdn.siswa'].browse(list(to_remove_ids)).sudo().write({
                        'ekstrakulikuler_ids': [(3, rec.name.id)]
                    })
        return super().unlink()
