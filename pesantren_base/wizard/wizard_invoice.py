# from odoo import models, fields, api, _
# import odoo.addons.decimal_precision as dp
# import time
# from odoo.exceptions import UserError

# class generate_invoice(models.TransientModel):
#     _name           = "generate.invoice"

#     def _default_tahunajaran(self):
#        return self.env['res.company'].search([('id','=',1)]).tahun_ajaran_aktif
 
 
#     tahunajaran_id      = fields.Many2one(comodel_name="cdn.ref_tahunajaran",  string="Tahun Ajaran", default=_default_tahunajaran, readonly=True, store=True)
#     komponen_id         = fields.Many2one('cdn.komponen_biaya', 'Komponen Biaya', required=True)
#     period_from         = fields.Many2one('cdn.periode_tagihan', 'Bulan Awal', required=True, domain="[('tahunajaran_id','=',tahunajaran_id)]")
#     period_to           = fields.Many2one('cdn.periode_tagihan', 'Bulan Akhir', required=True, domain="[('tahunajaran_id','=',tahunajaran_id)]")
#     angkatan_id         = fields.Many2one('cdn.ref_tahunajaran', 'Siswa Angkatan', required=True)
#     partner_ids         = fields.Many2many('cdn.siswa', 'partner_rel', 'siswa_id', 'partner_id', 'Siswa', required=True, domain="[('bebasbiaya', '=', False), ('tahunajaran_id', '=', angkatan_id)]")
#     name                = fields.Float('Harga')
    
#     # kelas_id            = fields.Many2many('cdn.ruang_kelas', string='Kelas',related='partner_ids.ruang_kelas_id')

#     @api.onchange('komponen_id','name')
#     def _onchange_komponen_id(self):
#         if self.komponen_id:
#             harga = self.env['cdn.biaya_tahunajaran'].search([('tahunajaran_id', '=', self.tahunajaran_id.id), ('name', '=', self.komponen_id.id)], limit=1)
#             if not harga:
#                 return {
#                     'value': {'partner_ids': False, 'komponen_id': False, 'name': 0},
#                     'warning': {'title': 'Perhatian', 'message': 'Harga komponen belum di tentukan pada tahun ajaran'}
#                 }

#             self.update({'name': harga.nominal})
    
#     def create_invoice(self):
#         if self.period_from.id > self.period_to.id:
#             raise UserError(("Bulan Awal lebih besar daripada bulan akhir !"))
#         elif not self.partner_ids:
#             raise UserError(("Siswa belum di pilih !"))

#         obj_period = self.env['cdn.periode_tagihan']
#         obj_invoice = self.env['account.move']
#         obj_invoice_line = self.env['account.move.line']

#         produk = self.komponen_id.product_id

#         # comment by Imam Ms
#         # journal_id = obj_invoice.default_get(['journal_id'])['journal_id']
#         period_ids = obj_period.search([('id', '>=', self.period_from.id), ('id', '<=', self.period_to.id)])

#         #Nomor generator Invoice
#         gen_invoice = self.env['ir.sequence'].next_by_code('gen.invoice')

#         for period in period_ids:
#             for x in self.partner_ids:
#                 disc_amount = 0; disc_persen = 0
#                 qty=1
#                 if x.harga_komponen:
#                     disc = self.env['cdn.harga_khusus'].search([('siswa_id', '=', x.id), ('name', '=', self.komponen_id.id)])
#                     # print(disc)
#                     if disc:
#                         disc_amount = disc.disc_amount
#                         disc_persen = disc.disc_persen

#                 # comment by Imam Ms
#                 # sale_journals       = self.env['account.journal'].search([('type','=','sale')])

#                 # zid = obj_invoice.create({
#                 #         'name': '/',
#                 #         'move_type': 'out_invoice',
#                 #         'invoice_origin': x.name,
#                 #         # 'account_id': x.partner_id.property_account_receivable_id.id,
#                 #         'student': True,
#                 #         'invoice_payment_term_id': False,
#                 #         # 'cicil': self.komponen_id.cicil,
#                 #         'komponen_id': self.komponen_id.id,
#                 #         'tahunajaran_id': self.tahunajaran_id.id,
#                 #         'orangtua_id': x.orangtua_id.id,
#                 #         'ruang_kelas_id': x.ruang_kelas_id.id,
#                 #         'siswa_id' : x.id,
#                 #         'partner_id': x.partner_id.id,
#                 #         'partner_shipping_id': x.partner_id.id,
#                 #         #'journal_id': 1,
#                 #         'currency_id': self.env.user.company_id.currency_id.id,
#                 #         'fiscal_position_id': x.partner_id.property_account_position_id.id,
#                 #         'invoice_date': period.start_date,
#                 #         'company_id': self.env.user.company_id.id,
#                 #         'periode_id': period.id,
#                 #         'user_id': self.env.uid or False
#                 #     })

#                 # obj_invoice_line.create({
#                 #         'name': produk.partner_ref,
#                 #         'product_id': produk.id or False,
#                 #         'discount': disc_persen,
#                 #         'discount_amount': disc_amount,
#                 #         'move_id': zid.id,
#                 #         'account_id': produk.property_account_income_id.id or produk.categ_id.property_account_income_categ_id.id,
#                 #         'price_unit': self.name - disc_amount,
#                 #         'quantity': qty,
#                 #         'product_uom_id': produk.uom_id.id,
#                 # })

#                 invoice_vals = {
#                     'name': '/',
#                     'move_type': 'out_invoice',
#                     'invoice_origin': x.name,
#                     'student': True,
#                     'generate_invoice' : gen_invoice,
#                     'invoice_payment_term_id': False,
#                     'komponen_id': self.komponen_id.id,
#                     'tahunajaran_id': self.tahunajaran_id.id,
#                     'orangtua_id': x.orangtua_id.id,
#                     'ruang_kelas_id': x.ruang_kelas_id.id,
#                     'siswa_id' : x.id,
#                     'partner_id': x.partner_id.id,
#                     'partner_shipping_id': x.partner_id.id,
#                     'currency_id': self.env.user.company_id.currency_id.id,
#                     'fiscal_position_id': x.partner_id.property_account_position_id.id,
#                     'invoice_date': period.start_date,
#                     'company_id': self.env.user.company_id.id,
#                     'periode_id': period.id,
#                     'user_id': self.env.uid or False
#                 }

#                 res = obj_invoice.create(invoice_vals)

#                 invoice_line_vals = {
#                     'name': produk.partner_ref,
#                     'product_id' : produk.id or False,
#                     'discount': disc_persen,
#                     'discount_amount': disc_amount,
#                     'account_id': produk.property_account_income_id.id or produk.categ_id.property_account_income_categ_id.id,
#                     'price_unit': self.name - disc_amount,
#                     'quantity': qty,
#                     'product_uom_id': produk.uom_id.id,

#                 }
#                 res1 = res.write({'invoice_line_ids' : ([(0,0,invoice_line_vals)])})
        
#         action = self.env.ref('pesantren_base.action_tagihan_inherit_view').read()[0]
#         action['domain'] = [('generate_invoice','=',gen_invoice)]
#         return action
#         # return True 



# from odoo import models, fields, api, _
# import odoo.addons.decimal_precision as dp
# import time
# from odoo.exceptions import UserError

# class generate_invoice(models.TransientModel):
#     _name           = "generate.invoice"

#     def _default_tahunajaran(self):
#        return self.env['res.company'].search([('id','=',1)]).tahun_ajaran_aktif


#     tahunajaran_id      = fields.Many2one(comodel_name="cdn.ref_tahunajaran",  string="Tahun Ajaran", default=_default_tahunajaran, readonly=True, store=True)
#     komponen_id         = fields.Many2one('cdn.komponen_biaya', 'Komponen Biaya', required=True)
#     period_from         = fields.Many2one('cdn.periode_tagihan', 'Bulan Awal', required=True, domain="[('tahunajaran_id','=',tahunajaran_id)]")
#     period_to           = fields.Many2one('cdn.periode_tagihan', 'Bulan Akhir', required=True, domain="[('tahunajaran_id','=',tahunajaran_id)]")
#     angkatan_id         = fields.Many2one('cdn.ref_tahunajaran', 'Siswa Angkatan', required=True)
#     partner_ids         = fields.Many2many('cdn.siswa', 'partner_rel', 'siswa_id', 'partner_id', 'Siswa', required=True, domain="[('bebasbiaya', '=', False), ('tahunajaran_id', '=', angkatan_id)]")
#     name                = fields.Float('Harga')
    
    
    
#     kelas_id            = fields.Many2many('cdn.ruang_kelas', string='Kelas', domain="[('tahunajaran_id','=',tahunajaran_id)]")

#     @api.onchange('komponen_id','name')
#     def _onchange_komponen_id(self):
#         if self.komponen_id:
#             harga = self.env['cdn.biaya_tahunajaran'].search([('tahunajaran_id', '=', self.tahunajaran_id.id), ('name', '=', self.komponen_id.id)], limit=1)
#             if not harga:
#                 return {
#                     'value': {'partner_ids': False, 'komponen_id': False, 'name': 0},
#                     'warning': {'title': 'Perhatian', 'message': 'Harga komponen belum di tentukan pada tahun ajaran'}
#                 }

#             self.update({'name': harga.nominal})
    
#     # @api.onchange('kelas_id')
#     # def _onchange_kelas_id(self):
#     #     if self.kelas_id:
#     #         domain = [('bebasbiaya', '=', False), ('tahunajaran_id', '=', self.angkatan_id.id)]
#     #         santri_ids = []
            
#     #         for kelas in self.kelas_id:
#     #             santri_ids.extend(kelas.siswa_ids.ids)
                
#     #         if santri_ids:
#     #             domain.append(('id', 'in', santri_ids))
#     #             santri = self.env['cdn.siswa'].search(domain)
#     #             self.partner_ids = [(6, 0, santri.ids)]
#     #         else:
#     #             self.partner_ids = [(6, 0, [])]
    
      
#     # @api.onchange('kelas_id')
#     # def _onchange_kelas_id(self):
#     #     if self.kelas_id:
#     #         domain = [('bebasbiaya', '=', False), ('tahunajaran_id', '=', self.angkatan_id.id)]
#     #         santri_ids = []
            
#     #         # Ambil santri yang sudah dipilih sebelumnya (jika ada)
#     #         existing_santri_ids = self.partner_ids.ids if self.partner_ids else []
            
#     #         # Kumpulkan santri dari kelas yang dipilih
#     #         for kelas in self.kelas_id:
#     #             santri_ids.extend(kelas.siswa_ids.ids)
            
#     #         if santri_ids:
#     #             # Gabungkan santri dari kelas dengan santri yang sudah dipilih sebelumnya
#     #             combined_santri_ids = list(set(existing_santri_ids + santri_ids))
                
#     #             # Filter santri sesuai domain
#     #             domain.append(('id', 'in', combined_santri_ids))
#     #             santri = self.env['cdn.siswa'].search(domain)
                
#     #             # Update partner_ids dengan operasi penambahan (4), bukan penggantian (6)
#     #             if not existing_santri_ids:  # Jika belum ada santri yang dipilih sebelumnya
#     #                 self.partner_ids = [(6, 0, santri.ids)]
#     #             else:
#     #                 # Tambahkan santri baru tanpa menghapus yang sudah ada
#     #                 new_santri_ids = [sid for sid in santri.ids if sid not in existing_santri_ids]
#     #                 for santri_id in new_santri_ids:
#     #                     self.partner_ids = [(4, santri_id, 0)]
    
    
#     # @api.onchange('kelas_id')
#     # def _onchange_kelas_id(self):
#     #     # Ambil ID kelas yang saat ini dipilih
#     #     current_kelas_ids = self.kelas_id.ids if self.kelas_id else []
        
#     #     # Ambil santri yang sudah dipilih sebelumnya (jika ada)
#     #     existing_santri_ids = self.partner_ids.ids if self.partner_ids else []
        
#     #     if not existing_santri_ids:
#     #         # Jika belum ada santri yang dipilih, tambahkan semua santri dari kelas yang dipilih
#     #         if current_kelas_ids:
#     #             domain = [('bebasbiaya', '=', False), ('tahunajaran_id', '=', self.angkatan_id.id)]
#     #             santri_ids = []
                
#     #             # Kumpulkan santri dari kelas yang dipilih
#     #             for kelas in self.kelas_id:
#     #                 santri_ids.extend(kelas.siswa_ids.ids)
                    
#     #             if santri_ids:
#     #                 # Filter santri sesuai domain
#     #                 domain.append(('id', 'in', santri_ids))
#     #                 santri = self.env['cdn.siswa'].search(domain)
#     #                 self.partner_ids = [(6, 0, santri.ids)]
#     #     else:
#     #         # Jika sudah ada santri yang dipilih, perlu menangani penambahan dan penghapusan
#     #         # Dapatkan semua santri yang ada di kelas-kelas yang dipilih
#     #         all_santri_in_selected_classes = []
#     #         for kelas in self.kelas_id:
#     #             all_santri_in_selected_classes.extend(kelas.siswa_ids.ids)
            
#     #         # Dapatkan semua santri yang eligible sesuai domain
#     #         domain = [('bebasbiaya', '=', False), ('tahunajaran_id', '=', self.angkatan_id.id)]
            
#     #         # Untuk santri yang saat ini dipilih, periksa apakah mereka masih berada di kelas yang dipilih
#     #         santri_to_keep = []
#     #         for santri_id in existing_santri_ids:
#     #             # Cek apakah santri masih di salah satu kelas yang dipilih
#     #             santri = self.env['cdn.siswa'].browse(santri_id)
#     #             kelas_santri = santri.ruang_kelas_id.id
                
#     #             # Jika kelas santri masih dipilih atau santri tidak terkait dengan kelas manapun, tetap tampilkan
#     #             if kelas_santri in current_kelas_ids or not kelas_santri:
#     #                 santri_to_keep.append(santri_id)
            
#     #         # Tambahkan santri baru yang belum ada di list
#     #         santri_to_add = [s_id for s_id in all_santri_in_selected_classes 
#     #                         if s_id not in existing_santri_ids and s_id not in santri_to_keep]
            
#     #         # Filter semua santri dengan domain
#     #         eligible_santri = self.env['cdn.siswa'].search([
#     #             ('id', 'in', santri_to_keep + santri_to_add),
#     #             ('bebasbiaya', '=', False),
#     #             ('tahunajaran_id', '=', self.angkatan_id.id)
#     #         ])
            
#     #         # Update partner_ids dengan santri yang valid
#     #         self.partner_ids = [(6, 0, eligible_santri.ids)]
        
        
#     @api.onchange('kelas_id')
#     def _onchange_kelas_id(self):
#         """
#         Fungsi untuk menangani perubahan pada field kelas_id.
#         - Menambahkan siswa dari kelas yang baru dipilih
#         - Menghapus siswa dari kelas yang dihapus
#         - Mempertahankan siswa yang kelasnya masih dipilih
#         """
#         # Ambil ID kelas yang saat ini dipilih
#         current_kelas_ids = self.kelas_id.ids if self.kelas_id else []
        
#         # Ambil santri yang sudah dipilih sebelumnya (jika ada)
#         existing_santri_ids = self.partner_ids.ids if self.partner_ids else []
        
#         # Jika tidak ada kelas yang dipilih, kosongkan daftar santri
#         if not current_kelas_ids:
#             self.partner_ids = [(6, 0, [])]
#             return
        
#         # Kumpulkan semua santri dari kelas yang dipilih
#         all_santri_in_classes = []
#         for kelas in self.kelas_id:
#             all_santri_in_classes.extend(kelas.siswa_ids.ids)
        
#         # Jika belum ada santri yang dipilih, tambahkan semua santri dari kelas
#         if not existing_santri_ids:
#             if all_santri_in_classes:
#                 # Filter santri sesuai domain
#                 santri = self.env['cdn.siswa'].search([
#                     ('id', 'in', all_santri_in_classes),
#                     ('bebasbiaya', '=', False), 
#                     ('tahunajaran_id', '=', self.angkatan_id.id)
#                 ])
#                 self.partner_ids = [(6, 0, santri.ids)]
#         else:
#             # Jika sudah ada santri yang dipilih, perlu menangani penambahan dan penghapusan
            
#             # Periksa santri yang sudah ada, apakah masih berada di kelas yang dipilih
#             santri_to_keep = []
#             for santri_id in existing_santri_ids:
#                 santri = self.env['cdn.siswa'].browse(santri_id)
#                 kelas_santri = santri.ruang_kelas_id.id
                
#                 # Jika kelas santri masih dipilih atau santri tidak terkait dengan kelas manapun, tetap tampilkan
#                 if kelas_santri in current_kelas_ids or not kelas_santri:
#                     santri_to_keep.append(santri_id)
            
#             # Cari santri baru yang perlu ditambahkan (yang ada di kelas terpilih tapi belum ada di daftar)
#             santri_to_add = [s_id for s_id in all_santri_in_classes 
#                             if s_id not in existing_santri_ids]
            
#             # Gabungkan santri yang tetap dan santri baru
#             combined_santri_ids = list(set(santri_to_keep + santri_to_add))
            
#             # Filter semua santri dengan domain
#             if combined_santri_ids:
#                 santri = self.env['cdn.siswa'].search([
#                     ('id', 'in', combined_santri_ids),
#                     ('bebasbiaya', '=', False),
#                     ('tahunajaran_id', '=', self.angkatan_id.id)
#                 ])
                
#                 # Update partner_ids dengan santri yang valid
#                 self.partner_ids = [(6, 0, santri.ids)]
#             else:
#                 # Jika tidak ada santri yang valid, kosongkan daftar
#                 self.partner_ids = [(6, 0, [])]
    
#     def create_invoice(self):
#         if self.period_from.id > self.period_to.id:
#             raise UserError(("Bulan Awal lebih besar daripada bulan akhir !"))
#         elif not self.partner_ids:
#             raise UserError(("Siswa belum di pilih !"))

#         obj_period = self.env['cdn.periode_tagihan']
#         obj_invoice = self.env['account.move']
#         obj_invoice_line = self.env['account.move.line']

#         produk = self.komponen_id.product_id

#         period_ids = obj_period.search([('id', '>=', self.period_from.id), ('id', '<=', self.period_to.id)])

#         #Nomor generator Invoice
#         gen_invoice = self.env['ir.sequence'].next_by_code('gen.invoice')

#         for period in period_ids:
#             for x in self.partner_ids:
#                 disc_amount = 0; disc_persen = 0
#                 qty=1
#                 if x.harga_komponen:
#                     disc = self.env['cdn.harga_khusus'].search([('siswa_id', '=', x.id), ('name', '=', self.komponen_id.id)])
#                     if disc:
#                         disc_amount = disc.disc_amount
#                         disc_persen = disc.disc_persen

#                 invoice_vals = {
#                     'name': '/',
#                     'move_type': 'out_invoice',
#                     'invoice_origin': x.name,
#                     'student': True,
#                     'generate_invoice' : gen_invoice,
#                     'invoice_payment_term_id': False,
#                     'komponen_id': self.komponen_id.id,
#                     'tahunajaran_id': self.tahunajaran_id.id,
#                     'orangtua_id': x.orangtua_id.id,
#                     'ruang_kelas_id': x.ruang_kelas_id.id,
#                     'siswa_id' : x.id,
#                     'partner_id': x.partner_id.id,
#                     'partner_shipping_id': x.partner_id.id,
#                     'currency_id': self.env.user.company_id.currency_id.id,
#                     'fiscal_position_id': x.partner_id.property_account_position_id.id,
#                     'invoice_date': period.start_date,
#                     'company_id': self.env.user.company_id.id,
#                     'periode_id': period.id,
#                     'user_id': self.env.uid or False
#                 }

#                 res = obj_invoice.create(invoice_vals)

#                 invoice_line_vals = {
#                     'name': produk.partner_ref,
#                     'product_id' : produk.id or False,
#                     'discount': disc_persen,
#                     'discount_amount': disc_amount,
#                     'account_id': produk.property_account_income_id.id or produk.categ_id.property_account_income_categ_id.id,
#                     'price_unit': self.name - disc_amount,
#                     'quantity': qty,
#                     'product_uom_id': produk.uom_id.id,

#                 }
#                 res1 = res.write({'invoice_line_ids' : ([(0,0,invoice_line_vals)])})
        
#         action = self.env.ref('pesantren_base.action_tagihan_inherit_view').read()[0]
#         action['domain'] = [('generate_invoice','=',gen_invoice)]
#         return action

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class generate_invoice(models.TransientModel):
    _name = "generate.invoice"
    _description = "Wizard Generate Invoice Santri"

    # Default Tahun Ajaran dari Company
    def _default_tahunajaran(self):
        return self.env['res.company'].search([('id', '=', 1)]).tahun_ajaran_aktif

    # === Fields ===
    tahunajaran_id = fields.Many2one(
        comodel_name="cdn.ref_tahunajaran",
        string="Tahun Ajaran",
        default=_default_tahunajaran,
        readonly=True,
        store=True
    )

    komponen_id = fields.Many2one(
        'cdn.komponen_biaya',
        'Komponen Biaya',
        required=True
    )

    period_from = fields.Many2one(
        'cdn.periode_tagihan',
        'Bulan Awal',
        required=True,
        domain="[('tahunajaran_id','=',tahunajaran_id)]"
    )

    period_to = fields.Many2one(
        'cdn.periode_tagihan',
        'Bulan Akhir',
        required=True,
        domain="[('tahunajaran_id','=',tahunajaran_id)]"
    )

    angkatan_id = fields.Many2one(
        'cdn.ref_tahunajaran',
        'Siswa Angkatan',
        required=True
    )

    partner_ids = fields.Many2many(
        'cdn.siswa',
        'partner_rel',
        'siswa_id',
        'partner_id',
        'Siswa',
        required=True,
        domain="[('bebasbiaya', '=', False), ('ruang_kelas_id.tahunajaran_id', '=', tahunajaran_id)]"
    )

    name = fields.Float('Harga')

    kelas_id = fields.Many2many(
        'cdn.ruang_kelas',
        string='Kelas',
        domain="[('tahunajaran_id','=',angkatan_id), ('aktif_tidak', '=', 'aktif'), ('status','=','konfirm')]"
    )

    # === Onchange Methods ===

    @api.onchange('komponen_id', 'name')
    def _onchange_komponen_id(self):
        if self.komponen_id:
            harga = self.env['cdn.biaya_tahunajaran'].search([
                ('tahunajaran_id', '=', self.tahunajaran_id.id),
                ('name', '=', self.komponen_id.id)
            ], limit=1)
            if not harga:
                return {
                    'value': {'partner_ids': False, 'komponen_id': False, 'name': 0},
                    'warning': {
                        'title': 'Perhatian',
                        'message': 'Harga komponen belum ditentukan pada tahun ajaran.'
                    }
                }
            self.name = harga.nominal

    @api.onchange('kelas_id')
    def _onchange_kelas_id(self):
        current_kelas_ids = self.kelas_id.ids if self.kelas_id else []
        if not current_kelas_ids:
            self.partner_ids = [(6, 0, [])]
            return

        all_santri = []
        for kelas in self.kelas_id:
            valid_santri = kelas.siswa_ids.filtered(lambda s: 
                s.active and 
                not s.bebasbiaya and 
                s.ruang_kelas_id.tahunajaran_id.id == self.tahunajaran_id.id
            )
            all_santri.extend(valid_santri.ids)

        self.partner_ids = [(6, 0, all_santri)] if all_santri else [(6, 0, [])]

    @api.onchange('angkatan_id')
    def _onchange_angkatan_id(self):
        self.kelas_id = [(6, 0, [])]
        self.partner_ids = [(6, 0, [])]
        return {
            'domain': {
                'partner_ids': [
                    ('bebasbiaya', '=', False),
                    ('ruang_kelas_id.tahunajaran_id', '=', self.tahunajaran_id.id),
                    ('active', '=', True)
                ]
            }
        }

    # === Pembuatan Invoice ===

    def create_invoice(self):
        if self.period_from.id > self.period_to.id:
            raise UserError(_("Bulan Awal lebih besar daripada Bulan Akhir!"))

        if not self.partner_ids:
            raise UserError(_("Siswa belum dipilih!"))

        obj_period = self.env['cdn.periode_tagihan']
        obj_invoice = self.env['account.move']
        produk = self.komponen_id.product_id
        gen_invoice = self.env['ir.sequence'].next_by_code('gen.invoice')

        period_ids = obj_period.search([
            ('id', '>=', self.period_from.id),
            ('id', '<=', self.period_to.id)
        ])

        for period in period_ids:
            for siswa in self.partner_ids:
                # === Validasi: Cek tagihan ganda ===
                existing_invoice = obj_invoice.search([
                    ('siswa_id', '=', siswa.id),
                    ('periode_id', '=', period.id),
                    ('komponen_id', '=', self.komponen_id.id),
                    ('move_type', '=', 'out_invoice'),
                    ('state', '!=', 'cancel')
                ], limit=1)

                if existing_invoice:
                    raise UserError(_(
                        f"Tagihan untuk santri {siswa.name}, komponen '{self.komponen_id.name}', dan periode '{period.name}' sudah pernah dibuat."
                    ))

                # === Lewat Validasi ===
                if not siswa.ruang_kelas_id or siswa.ruang_kelas_id.tahunajaran_id.id != self.tahunajaran_id.id:
                    continue

                disc_amount = 0
                disc_persen = 0
                qty = 1

                if siswa.harga_komponen:
                    disc = self.env['cdn.harga_khusus'].search([
                        ('siswa_id', '=', siswa.id),
                        ('name', '=', self.komponen_id.id)
                    ])
                    if disc:
                        disc_amount = disc.disc_amount
                        disc_persen = disc.disc_persen

                invoice_vals = {
                    'name': '/',
                    'move_type': 'out_invoice',
                    'invoice_origin': siswa.name,
                    'student': True,
                    'generate_invoice': gen_invoice,
                    'invoice_payment_term_id': False,
                    'komponen_id': self.komponen_id.id,
                    'tahunajaran_id': self.tahunajaran_id.id,
                    'orangtua_id': siswa.orangtua_id.id,
                    'ruang_kelas_id': siswa.ruang_kelas_id.id,
                    'siswa_id': siswa.id,
                    'partner_id': siswa.partner_id.id,
                    'partner_shipping_id': siswa.partner_id.id,
                    'currency_id': self.env.user.company_id.currency_id.id,
                    'fiscal_position_id': siswa.partner_id.property_account_position_id.id,
                    'invoice_date': period.start_date,
                    'company_id': self.env.user.company_id.id,
                    'periode_id': period.id,
                    'user_id': self.env.uid
                }

                res_invoice = obj_invoice.create(invoice_vals)

                invoice_line_vals = {
                    'name': produk.partner_ref,
                    'product_id': produk.id or False,
                    'discount': disc_persen,
                    'discount_amount': disc_amount,
                    'account_id': produk.property_account_income_id.id or produk.categ_id.property_account_income_categ_id.id,
                    'price_unit': self.name - disc_amount,
                    'quantity': qty,
                    'product_uom_id': produk.uom_id.id,
                }

                res_invoice.write({
                    'invoice_line_ids': [(0, 0, invoice_line_vals)]
                })

        # Redirect ke daftar invoice yang baru dibuat
        action = self.env.ref('pesantren_base.action_tagihan_inherit_view').read()[0]
        action['domain'] = [('generate_invoice', '=', gen_invoice)]
        return action
