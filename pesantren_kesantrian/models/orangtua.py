from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class OrangTua(models.Model):
    _inherit = 'cdn.orangtua'

    password = fields.Char(store=True)

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
                return res

        # VALIDASI & SET DEFAULT PASSWORD (FIX ERROR BOOLEAN)
        if not res.password or not isinstance(res.password, str):
            # Set default password (bisa dari email atau fixed)
            # Ambil 8 char pertama email, atau default
            res.password = res.email[:8] if res.email else 'default123'

        # Membuat user baru dengan login berbasis email dan password default
        user = self.env['res.users'].with_context(no_reset_password=True).sudo().create({
            'login': res.email,  # Menggunakan email dari field model
            'name': res.name,  # Nama pengguna
            # Mengatur perusahaan default
            'company_id': self.env.ref('base.main_company').id,
            'partner_id': res.partner_id.id,  # Hubungkan dengan partner terkait
            # Password default (sekarang pasti string)
            'password': res.password,
            'groups_id': [(6, 0, [
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
            ])]
        })

        res.user_id = user.id

        if res.partner_id:
            res.partner_id.user_id = user.id

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
        """Update groups for the related user."""
        for orangtua in self:
            user = self.env['res.users'].search(
                [('login', '=', orangtua.email)], limit=1)
            if not user:
                raise ValueError(
                    _("No user associated with this OrangTua record."))

            # Remove existing groups
            user.groups_id = [(5, 0, 0)]  # Clear all groups

            # Add new groups
            user.groups_id = [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref(
                    'pesantren_kesantrian.group_kesantrian_orang_tua').id,
                self.env.ref('pesantren_base.group_sekolah_user').id,
                self.env.ref('pesantren_kesantrian.group_kesantrian_user').id,
                self.env.ref('pesantren_guru.group_guru_user').id,
                self.env.ref('pesantren_keuangan.group_keuangan_user').id,
                self.env.ref('account.group_account_readonly').id,
            ])]

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '✅ Berhasil',
                'message': f'Hak Akses Sudah Diperbarui',
                'type': 'success',
                'sticky': False,
            }
        }
        # return {
        #     'type': 'ir.actions.client',
        #     'tag': 'display_notification',
        #     'params': {
        #         'title': _("Warning head"),
        #         'type': 'notification',
        #         'message': _("This is the detailed warning"),
        #         'sticky': True,
        #     },
        # }

    # def write(self, vals):
    #     res = super(OrangTua, self).write(vals)
    #     for record in self:
    #         # Jika field password diubah, update password user terkait
    #         if vals.get('password') and record.user_id:
    #             record.user_id.sudo().write({'password': vals['password']})
    #     return res
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

        return res
