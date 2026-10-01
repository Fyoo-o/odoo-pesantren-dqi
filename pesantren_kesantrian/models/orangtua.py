from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class OrangTua(models.Model):
    _inherit = 'cdn.orangtua'

    password = fields.Char(store=True)
    santri_count = fields.Integer(string="Jumlah Santri", compute="_compute_santri_count")

    @api.depends('siswa_ids')
    def _compute_santri_count(self):
        for rec in self:
            rec.santri_count = len(rec.siswa_ids)

    def action_view_santri(self):
        self.ensure_one()
        return {
            'name': _('Santri'),
            'type': 'ir.actions.act_window',
            'res_model': 'cdn.siswa',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.siswa_ids.ids)],
            'context': {'default_orangtua_ids': [(4, self.id)]},
        }

    def _sync_to_santri(self):
        """Menyelaraskan data orang tua ke data identitas santri (Ayah/Ibu/Wali)"""
        for record in self:
            if not record.siswa_ids or not record.hubungan:
                continue
            for santri in record.siswa_ids:
                vals_santri = {}
                if record.hubungan == 'ayah':
                    if not santri.ayah_id:
                        vals_santri['ayah_id'] = record.id
                    if not santri.ayah_nama:
                        vals_santri['ayah_nama'] = record.name
                    if not santri.ayah_telp:
                        vals_santri['ayah_telp'] = record.mobile or record.phone
                    if not santri.ayah_email:
                        vals_santri['ayah_email'] = record.email
                elif record.hubungan == 'ibu':
                    if not santri.ibu_id:
                        vals_santri['ibu_id'] = record.id
                    if not santri.ibu_nama:
                        vals_santri['ibu_nama'] = record.name
                    if not santri.ibu_telp:
                        vals_santri['ibu_telp'] = record.mobile or record.phone
                    if not santri.ibu_email:
                        vals_santri['ibu_email'] = record.email
                elif record.hubungan == 'wali':
                    if not santri.wali_id:
                        vals_santri['wali_id'] = record.id
                    if not santri.wali_nama:
                        vals_santri['wali_nama'] = record.name
                    if not santri.wali_telp:
                        vals_santri['wali_telp'] = record.mobile or record.phone
                    if not santri.wali_email:
                        vals_santri['wali_email'] = record.email

                # Pastikan orangtua_ids pada santri memuat record ini
                cur_parent_ids = santri.orangtua_ids.ids
                if record.id not in cur_parent_ids:
                    vals_santri['orangtua_ids'] = [(4, record.id)]

                if vals_santri:
                    santri.with_context(skip_sync_orangtua=True).sudo().write(vals_santri)

    @api.model
    def create(self, vals):
        # Membuat record 'OrangTua' menggunakan inheritance
        res = super(OrangTua, self).create(vals)

        #  VALIDASI DUPLIKAT EMAIL DI res.users
        if res.email:
            existing_user = self.env['res.users'].sudo().search(
                [('login', '=', res.email)], limit=1)
            if existing_user:
                # Jika user sudah ada, gunakan user tersebut (sharing)
                res.user_id = existing_user.id
                if res.partner_id:
                    res.partner_id.user_id = existing_user.id

                # Pastikan user memiliki group yang diperlukan dan tidak konflik tipe user
                group_portal = self.env.ref(
                    'base.group_portal', raise_if_not_found=False)
                group_public = self.env.ref(
                    'base.group_public', raise_if_not_found=False)

                group_ids = [
                    self.env.ref('base.group_user').id,
                    self.env.ref(
                        'pesantren_kesantrian.group_kesantrian_orang_tua').id,
                    self.env.ref('pesantren_base.group_sekolah_user').id,
                    self.env.ref(
                        'pesantren_kesantrian.group_kesantrian_user').id,
                    self.env.ref('pesantren_guru.group_guru_user').id,
                    self.env.ref('pesantren_keuangan.group_keuangan_user').id,
                    self.env.ref('account.group_account_readonly').id,
                ]
                group_limit = self.env.ref(
                    'pesantren_kesantrian.group_kesantrian_orang_tua_acces_limit', raise_if_not_found=False)
                if res.isLimit and group_limit:
                    group_ids.append(group_limit.id)

                commands = []
                if group_portal:
                    commands.append((3, group_portal.id))  # Remove Portal
                if group_public:
                    commands.append((3, group_public.id))  # Remove Public
                commands += [(4, gid)
                             for gid in group_ids]  # Add required groups

                existing_user.sudo().write({
                    'groups_id': commands
                })
                res._update_user_group_limit()
                res._sync_to_santri()
                return res

        login_str = res.email or res.mobile or res.phone
        if not login_str:
            return res

        # VALIDASI & SET DEFAULT PASSWORD (FIX ERROR BOOLEAN)
        if not res.password or not isinstance(res.password, str):
            # Set default password (bisa dari email atau fixed)
            # Ambil 8 char pertama email, atau default
            res.password = login_str[:8] if login_str else 'default123'

        user_groups = [
            # Assign grup internal user (standard)
            self.env.ref('base.group_user').id,
            # Assign grup orang tua
            self.env.ref(
                'pesantren_kesantrian.group_kesantrian_orang_tua').id,
            # Assign grup sekolah user
            self.env.ref('pesantren_base.group_sekolah_user').id,
            # Assign grup sekolah user
            self.env.ref('pesantren_kesantrian.group_kesantrian_user').id,
            # Assign grup guru user
            self.env.ref('pesantren_guru.group_guru_user').id,
            # Assign grup keuangan user
            self.env.ref('pesantren_keuangan.group_keuangan_user').id,
            self.env.ref('account.group_account_readonly').id,
        ]
        group_limit = self.env.ref(
            'pesantren_kesantrian.group_kesantrian_orang_tua_acces_limit', raise_if_not_found=False)
        if res.isLimit and group_limit:
            user_groups.append(group_limit.id)

        # Membuat user baru dengan login berbasis email/hp dan password default
        user = self.env['res.users'].with_context(no_reset_password=True).sudo().create({
            'login': login_str,  # Menggunakan email atau no hp
            'name': res.name,  # Nama pengguna
            # Mengatur perusahaan default
            'company_id': self.env.ref('base.main_company').id,
            'partner_id': res.partner_id.id,  # Hubungkan dengan partner terkait
            # Password default (sekarang pasti string)
            'password': res.password,
            'groups_id': [(6, 0, user_groups)]
        })

        res.user_id = user.id

        if res.partner_id:
            res.partner_id.user_id = user.id

        res._update_user_group_limit()
        res._sync_to_santri()

        return res

    def unlink(self):
        for orangtua in self:
            users = self.env['res.users'].search(
                [('partner_id', '=', orangtua.partner_id.id)])
            if users:
                partner = users.partner_id
                users.unlink()
                partner.unlink()
        return super(OrangTua, self).unlink()

    def update_user_groups(self):
        """Update groups for the related user using batch operations."""
        group_ids = [
            self.env.ref('base.group_user', raise_if_not_found=False),
            self.env.ref('pesantren_kesantrian.group_kesantrian_orang_tua', raise_if_not_found=False),
            self.env.ref('pesantren_base.group_sekolah_user', raise_if_not_found=False),
            self.env.ref('pesantren_kesantrian.group_kesantrian_user', raise_if_not_found=False),
            self.env.ref('pesantren_guru.group_guru_user', raise_if_not_found=False),
            self.env.ref('pesantren_keuangan.group_keuangan_user', raise_if_not_found=False),
            self.env.ref('account.group_account_readonly', raise_if_not_found=False),
        ]
        group_ids = [g.id for g in group_ids if g]
        group_limit = self.env.ref(
            'pesantren_kesantrian.group_kesantrian_orang_tua_acces_limit', raise_if_not_found=False)

        # Batch find users
        users = self.mapped('user_id')
        
        # Check by email for records without user_id
        recs_without_user = self.filtered(lambda r: not r.user_id and r.email)
        if recs_without_user:
            emails = recs_without_user.mapped('email')
            found_users = self.env['res.users'].sudo().search([('login', 'in', emails)])
            users |= found_users

        if users:
            users.sudo().write({
                'groups_id': [(4, gid) for gid in group_ids]
            })
            if group_limit:
                for rec in self:
                    rec_users = rec.user_id | (rec.partner_id.user_ids if rec.partner_id else self.env['res.users'])
                    if not rec_users and rec.email:
                        rec_users = self.env['res.users'].sudo().search([('login', '=', rec.email)])
                    for u in rec_users:
                        if rec.isLimit:
                            u.sudo().write({'groups_id': [(4, group_limit.id)]})
                        else:
                            u.sudo().write({'groups_id': [(3, group_limit.id)]})

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '✅ Berhasil',
                'message': f'Hak Akses untuk {len(users)} user sudah diperbarui.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_sync_user_id(self):
        """Synchronize user_id from cdn.orangtua to partner_id.user_id using high-performance SQL."""
        query = """
            UPDATE res_partner p
            SET user_id = o.user_id
            FROM cdn_orangtua o
            WHERE p.id = o.partner_id 
            AND o.user_id IS NOT NULL
            AND (p.user_id IS DISTINCT FROM o.user_id)
        """
        self._cr.execute(query)
        count = self._cr.rowcount
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '✅ Sinkronisasi Berhasil',
                'message': f'Berhasil menyelaraskan {count} data user secara instan.',
                'type': 'success',
                'sticky': False,
            }
        }

    def write(self, vals):
        # Simpan dulu nilai password sebelum super().write()
        password_changed = 'password' in vals
        new_password = vals.get('password') if password_changed else None

        # Panggil super write terlebih dahulu
        res = super(OrangTua, self).write(vals)

        # Setelah record ter-update, baru update password user
        if password_changed and new_password:
            for record in self:
                if record.user_id:
                    # Update password user menggunakan sudo
                    record.user_id.sudo().write({'password': new_password})

        if 'user_id' in vals:
            for record in self:
                if record.partner_id:
                    record.partner_id.sudo().write({'user_id': record.user_id.id})

        # Update user login jika email diubah
        if 'email' in vals and vals.get('email'):
            for record in self:
                if record.user_id and record.user_id.login != vals['email']:
                    conflict = self.env['res.users'].sudo().search([('login', '=', vals['email']), ('id', '!=', record.user_id.id)], limit=1)
                    if not conflict:
                        record.user_id.sudo().write({'login': vals['email'], 'email': vals['email']})

        # Update nama user jika nama diubah
        if 'name' in vals and vals.get('name'):
            for record in self:
                if record.user_id and record.user_id.name != vals['name']:
                    record.user_id.sudo().write({'name': vals['name']})

        # Sinkronisasi ke santri jika ada penambahan santri atau perubahan hubungan
        if 'siswa_ids' in vals or 'hubungan' in vals:
            self._sync_to_santri()

        return res
