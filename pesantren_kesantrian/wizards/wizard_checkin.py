# from odoo import api, fields, models
# from odoo.exceptions import UserError
# import logging
# from dateutil.relativedelta import relativedelta


# _logger = logging.getLogger(__name__)


# class PerijinanCheckIn(models.TransientModel):
#     _name           = 'cdn.perijinan.checkin'
#     _description    = 'CheckIn Perijinan Santri'

#     tgl_ijin    = fields.Datetime(string='Tgl Ijin', required=True, default=lambda self: fields.Datetime.now())
#     siswa_id    = fields.Many2one('cdn.siswa', string='Siswa', required=True)
#     perijinan_id = fields.Many2one('cdn.perijinan', string='Perijinan', required=True)
#     kelas_id    = fields.Many2one('cdn.ruang_kelas', string='Kelas', related='siswa_id.ruang_kelas_id', readonly=True)
#     kamar_id    = fields.Many2one('cdn.kamar_santri', string='Kamar', related='siswa_id.kamar_id', readonly=True)
#     halaqoh_id  = fields.Many2one('cdn.halaqoh', string='Halaqoh', related='siswa_id.halaqoh_id', readonly=True)
#     musyrif_id  = fields.Many2one('hr.employee', string='Musyrif', related='siswa_id.musyrif_id', readonly=True)
#     keperluan   = fields.Many2one(string='Keperluan', related='perijinan_id.keperluan', readonly=True)
#     lama_ijin   = fields.Integer(string='Lama Ijin', related='perijinan_id.lama_ijin', readonly=True)
#     tgl_kembali = fields.Datetime(string='Tgl Kembali', related='perijinan_id.tgl_kembali', readonly=True, default=lambda self: fields.Datetime.now() + relativedelta(days=1))
#     penjemput   = fields.Char(string='Penjemput', related='perijinan_id.penjemput', readonly=True)

#     barcode = fields.Char(string='Kartu Santri',readonly=False)



#     @api.onchange('siswa_id')
#     def _onchange_siswa(self):
#         if self.siswa_id:
#             self.barcode = self.siswa_id.barcode_santri
 
#     @api.onchange('barcode')
#     def _onchange_barcode(self):
#         """Mengisi siswa_id berdasarkan barcode yang diinput"""
#         _logger.info(f"Cek Barcode: {self.barcode}")
#         if self.barcode:
#             siswa = self.env['cdn.siswa'].search([('barcode', '=', self.barcode)], limit=1)
#             _logger.exception(f"Data Santri: {siswa}")

#             if siswa:
#                 self.siswa_id = siswa.id
#             else:
#                 self.siswa_id = False 
#                 kartu_sementara = self.barcode
#                 self.barcode = False
#                 return {
#                     'warning' : {
#                         'title' : 'Perhatian !',
#                         'message' : f"Tidak dapat menemukan kartu santri dengan kode {kartu_sementara}, silahkan gunakan kartu santri lain"
#                     }
#                 }
                

#     @api.onchange('siswa_id')
#     def _onchange_siswa_id(self):
#         if self.siswa_id:
#             Perijinan = self.env['cdn.perijinan'].search([('siswa_id', '=', self.siswa_id.id), ('state', '=', 'Permission')], limit=1)
           
#             if not Perijinan:
#                 raise UserError('Tidak ada perijinan keluar untuk santri ini, Silakan di cek kembali!')
            
#             self.perijinan_id = Perijinan.id

#     def action_checkin(self):
#         self.perijinan_id.write({
#             'state'         : 'Return',
#             'waktu_kembali' : fields.Datetime.now(),
#         })

#         return {
#             'type' : 'ir.actions.act_window',
#             'name': 'Santri Ijin Masuk',
#             'res_model' : 'cdn.perijinan.checkin',
#             'view_mode' : 'form',
#             'view_id': self.env.ref('pesantren_kesantrian.wizard_perijinan_checkout_form').id,
#             'target' : 'new',
#             'context': {'default_barcode': False},
#             'res_id' : False,
#         }






from odoo import api, fields, models
from odoo.exceptions import UserError
import logging
from dateutil.relativedelta import relativedelta


_logger = logging.getLogger(__name__)


class PerijinanCheckIn(models.TransientModel):
    _name           = 'cdn.perijinan.checkin'
    _description    = 'CheckIn Perijinan Santri'

    tgl_ijin     = fields.Datetime(string='Tgl Ijin', required=True, default=lambda self: fields.Datetime.now())
    siswa_id     = fields.Many2one('cdn.siswa', string='Siswa', required=True , ondelete='cascade')
    perijinan_id = fields.Many2one('cdn.perijinan', string='Perijinan', required=False)
    kelas_id     = fields.Many2one('cdn.ruang_kelas', string='Kelas', related='siswa_id.ruang_kelas_id', readonly=True)
    kamar_id     = fields.Many2one('cdn.kamar_santri', string='Kamar', related='siswa_id.kamar_id', readonly=True)
    halaqoh_id   = fields.Many2one('cdn.halaqoh', string='Halaqoh', related='siswa_id.halaqoh_id', readonly=True)
    musyrif_id   = fields.Many2one('hr.employee', string='Musyrif', related='siswa_id.musyrif_id', readonly=True)
    keperluan    = fields.Many2one(string='Keperluan', related='perijinan_id.keperluan', readonly=False)
    lama_ijin    = fields.Char(string='Lama Ijin', related='perijinan_id.lama_ijin', readonly=True)
    tgl_kembali  = fields.Datetime(string='Tgl Kembali', related='perijinan_id.tgl_kembali', readonly=False, default=lambda self: fields.Datetime.now() + relativedelta(days=1))
    penjemput    = fields.Char(string='Penjemput', related='perijinan_id.penjemput', readonly=False)

    barcode = fields.Char(string='Kartu Santri',readonly=False)
 
    @api.onchange('barcode')
    def _onchange_barcode(self):
        """Mengisi siswa_id berdasarkan barcode yang diinput"""
        _logger.info(f"Cek Barcode: {self.barcode}")
        if self.barcode:
            siswa = self.env['cdn.siswa'].search([('barcode', '=', self.barcode)], limit=1)
            _logger.exception(f"Data Santri: {siswa}")

            if siswa:
                self.siswa_id = siswa.id
            else:
                self.siswa_id = False 
                kartu_sementara = self.barcode
                self.barcode = False
                return {
                    'warning' : {
                        'title' : 'Perhatian !',
                        'message' : f"Tidak dapat menemukan kartu santri dengan kode {kartu_sementara}"
                    }
                }
                

    @api.onchange('siswa_id')
    def _onchange_siswa_id(self):
        if self.siswa_id:
            Perijinan = self.env['cdn.perijinan'].search([('siswa_id', '=', self.siswa_id.id), ('state', '=', 'Permission')], limit=1)
           
            if not Perijinan:
                raise UserError('Tidak ada perijinan keluar untuk santri ini, Silakan di cek kembali!')
            
            self.perijinan_id = Perijinan.id
            

    def action_checkin(self):
        self.perijinan_id.write({
            'state'         : 'Return',
            'waktu_kembali' : fields.Datetime.now(),
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'cdn.perijinan',
            'view_mode': 'form',
            'res_id': self.perijinan_id.id,
            'target': 'current',
        }
        
    
    
    @api.depends('tgl_ijin', 'tgl_kembali')
    def _compute_lama_ijin(self):
        for record in self:
            if record.tgl_ijin and record.tgl_kembali:
                # Hitung selisih waktu
                delta = record.tgl_kembali - record.tgl_ijin
                
                # Hitung hari, jam, dan menit
                total_menit = int(delta.total_seconds() / 60)
                hari = total_menit // (24 * 60)
                sisa_menit = total_menit % (24 * 60)
                jam = sisa_menit // 60
                menit = sisa_menit % 60
                
                # Format string untuk menampilkan hari, jam, menit
                record.lama_ijin = f"{hari} hari {jam} jam {menit} menit"