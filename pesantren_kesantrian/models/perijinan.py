from odoo import api, fields, models
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class Perijinan(models.Model):
    _name = 'cdn.perijinan'
    _description = 'Data Perijinan Santri'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc' 

    name = fields.Char(string='Nama', readonly=True)
    tgl_ijin = fields.Datetime(string='Tgl Ijin', required=True,
        states={
            'Draft': [('readonly', False)],
            'Check': [('readonly', True)],
            'Approved': [('readonly', True)],
            'Rejected': [('readonly', True)],
            'Permission': [('readonly', True)],
            'Return': [('readonly', True)],
        }, default=lambda self: fields.Datetime.now())

    tgl_kembali = fields.Datetime(string='Tgl Kembali', required=True,
        states={
            'Draft': [('readonly', False)],
            'Check': [('readonly', False)],
            'Approved': [('readonly', True)],
            'Rejected': [('readonly', True)],
            'Permission': [('readonly', True)],
            'Return': [('readonly', True)],
        },  default=lambda self: fields.Datetime.now() + relativedelta(days=1))
    waktu_keluar = fields.Datetime(string='Waktu Keluar', readonly=True)
    waktu_kembali = fields.Datetime(string='Waktu Kembali', readonly=True)

    penjemput = fields.Char(string='Penjemput', required=True,
        states={
            'Draft': [('readonly', False)],
            'Check': [('readonly', False)],
            'Approved': [('readonly', True)],
            'Rejected': [('readonly', True)],
            'Permission': [('readonly', True)],
            'Return': [('readonly', True)],
        }) 
    siswa_id = fields.Many2one('cdn.siswa', string='Santri', required=True,
        states={
            'Draft': [('readonly', False)],
            'Check': [('readonly', True)],
            'Approved': [('readonly', True)],
            'Rejected': [('readonly', True)],
            'Permission': [('readonly', True)],
            'Return': [('readonly', True)],
        }, ondelete='cascade')
    barcode = fields.Char(string='Kartu Santri', states= {
        'Draft': [('readonly', False)],
        'Check': [('readonly', True)],  
        'Approved': [('readonly', True)],
        'Rejected': [('readonly', True)],
        'Permission': [('readonly', True)],
        'Return': [('readonly', True)],
    })
    kelas_id = fields.Many2one('cdn.ruang_kelas', string='Kelas',related='siswa_id.ruang_kelas_id', readonly=True)
    kamar_id = fields.Many2one('cdn.kamar_santri', string='Kamar', related='siswa_id.kamar_id', readonly=True)
    halaqoh_id = fields.Many2one('cdn.halaqoh', string='Halaqoh', related='siswa_id.halaqoh_id', readonly=True)
    musyrif_id = fields.Many2one('hr.employee', string='Musyrif', related='siswa_id.musyrif_id', readonly=True)
    foto_bukti = fields.Binary(string="Foto Bukti", attachment=True, readonly=False,states={
        'Draft': [('readonly', False)],
        'Check': [('readonly', False)],
        'Approved': [('readonly', True)],
        'Rejected': [('readonly', True)],
        'Permission': [('readonly', True)],
        'Return': [('readonly', True)],
    })

    catatan = fields.Text(string='Catatan', readonly=False,
        states={
            'Draft': [('readonly', False)],
            'Check': [('readonly', False)],
            'Approved': [('readonly', True)],
            'Rejected': [('readonly', True)],
            'Permission': [('readonly', True)],
            'Return': [('readonly', True)],
        }) 
    
    catatan_keamanan = fields.Text(string='Catatan', readonly=False, 
        states={
            'Draft': [('readonly', False)],
            'Check': [('readonly', False)],
            'Approved': [('readonly', False)],
            'Rejected': [('readonly', False)],
            'Permission': [('readonly', False)],
            'Return': [('readonly', False)],
        })
    
    keperluan = fields.Many2one('master.keterangan',string='Keperluan', required=True ,states={
            'Draft': [('readonly', False)], 
            'Check': [('readonly', False)],
            'Approved': [('readonly', True)],
            'Rejected': [('readonly', True)],
            'Permission': [('readonly', True)],
            'Return': [('readonly', True)],
        }, tracking=True )


    # lama_ijin = fields.Integer(string='Lama Ijin', readonly=True, compute='_compute_lama_ijin', store=True)

    # jatuh_tempo = fields.Integer(string='Terlambat (hari)', readonly=True, compute='_compute_jatuh_tempo', store=True)


    lama_ijin = fields.Char(
        string='Lama Ijin', 
        readonly=True, 
        compute='_compute_lama_ijin', 
        store=True
    )

    jatuh_tempo = fields.Char(
        string='Terlambat', 
        readonly=True, 
        compute='_compute_jatuh_tempo', 
        store=True
    )

    cek_terlambat = fields.Boolean(string='Cek Terlambat', default=False, compute='_compute_jatuh_tempo', store=True)

    state = fields.Selection([
        ('Draft', 'Pengajuan'),
        ('Check', 'Diperiksa'),
        ('Approved', 'Disetujui'),
        ('Rejected', 'Ditolak'),
        ('Permission', 'Ijin Keluar'),
        ('Return', 'Kembali'),
    ], string='Status', default='Draft',
        track_visibility='onchange')
    
    musyrif_id = fields.Many2one(
        comodel_name='hr.employee', 
        string='Musyrif', 
        related='siswa_id.musyrif_id', 
        readonly=True, 
        store=True
    )   

    def action_save_record(self):
        self.state = 'Draft'

    
    @api.onchange('siswa_id')
    def _onchange_siswa_id(self):
        if self.siswa_id:
            self.barcode = self.siswa_id.barcode_santri
        else:
            self.barcode = False

            
 
    @api.onchange('barcode')
    def _onchange_barcode(self):
        if self.barcode:
            siswa = self.env['cdn.siswa'].search([('barcode_santri', '=', self.barcode)], limit=1)
            _logger.info(f"Data Santri: {siswa}")
            if siswa:
                self.siswa_id = siswa.id
            else:
                self.siswa_id = False
                barcode_sementara = self.barcode
                self.barcode = False
                return {
                    'warning': {
                        'title': "Perhatian !",
                        'message': f"Data Santri dengan Kartu Santri {barcode_sementara} tidak ditemukan."
                    }
                }
        else:
            self.barcode = False
            self.siswa_id = False


    # @api.depends('tgl_ijin', 'tgl_kembali')
    # def _compute_lama_ijin(self):
    #     for record in self:
    #         if record.tgl_ijin and record.tgl_kembali:
    #             record.lama_ijin = (record.tgl_kembali - record.tgl_ijin).days

    # @api.depends('waktu_kembali')
    # def _compute_jatuh_tempo(self):
    #     print('compute jatuh tempo')
    #     for record in self:
    #         if record.waktu_kembali:
    #             kembali = record.waktu_kembali.date()
    #             print('waktu kembali')
    #             print(record.tgl_kembali,kembali,(kembali - record.tgl_kembali).days)
    #             if record.tgl_kembali < kembali:
    #                 record.jatuh_tempo = (kembali- record.tgl_kembali).days
    #             else:
    #                 record.jatuh_tempo = 0

    #             record.cek_terlambat = True if record.jatuh_tempo > 0 else False

    # @api.depends('waktu_kembali')
    # def _compute_jatuh_tempo(self):
    #     for record in self:
    #         if record.waktu_kembali:
    #             kembali = record.waktu_kembali.date()
    #             tgl_kembali_date = record.tgl_kembali.date()

    #             selisih_hari = (kembali - tgl_kembali_date).days
    #             _logger.info("tgl_kembali: %s, waktu_kembali: %s, selisih hari: %s", tgl_kembali_date, kembali, selisih_hari)

    #             if tgl_kembali_date < kembali:
    #                 record.jatuh_tempo = selisih_hari
    #             else:
    #                 record.jatuh_tempo = 0

    #             record.cek_terlambat = record.jatuh_tempo > 0
    #         else:
    #             record.jatuh_tempo = 0
    #             record.cek_terlambat = False


    @api.onchange('waktu_kembali')
    def _onchange_waktu_kembali(self):
        for record in self:
            if record.waktu_kembali and not record.waktu_keluar:
                # Jika hanya ada waktu_kembali tanpa waktu_keluar
                # Maka isi tgl_kembali dengan nilai yang sama dengan tgl_ijin
                record.tgl_kembali = record.tgl_ijin


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

    @api.depends('waktu_kembali')
    def _compute_jatuh_tempo(self):
        for record in self:
            if record.waktu_kembali:
                # Hitung selisih waktu
                if record.tgl_kembali < record.waktu_kembali:
                    delta = record.waktu_kembali - record.tgl_kembali
                    
                    # Hitung hari, jam, dan menit
                    total_menit = int(delta.total_seconds() / 60)
                    hari = total_menit // (24 * 60)
                    sisa_menit = total_menit % (24 * 60)
                    jam = sisa_menit // 60
                    menit = sisa_menit % 60
                    
                    # Format string untuk menampilkan hari, jam, menit
                    record.jatuh_tempo = f"{hari} hari {jam} jam {menit} menit"
                    record.cek_terlambat = True
                else:
                    record.jatuh_tempo = "0 hari 0 jam 0 menit"
                    record.cek_terlambat = False


    def action_checked(self):
        self.state = 'Check'
    def action_approved(self):
        self.state = 'Approved'
    def action_rejected(self):
        self.state = 'Rejected'
    def action_permission(self):
        self.state = 'Permission'
        self.waktu_keluar = fields.Datetime.now()
    def action_return(self):
        self.state = 'Return'
        self.waktu_kembali = fields.Datetime.now()
        
        if not self.waktu_keluar:
            self.tgl_kembali = self.tgl_ijin


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('cdn.perijinan')
        return super(Perijinan, self).create(vals)

    # @api.model
    # def _search(self, domain, offset=0, limit=None, order=None, count=False):
    #     # Handle empty domain
    #     if not domain:
    #         return super(Perijinan, self)._search(domain, offset=offset, limit=limit, order=order, )
        
    #     # Periksa domain untuk mencegah error
    #     if isinstance(domain, list):

    #         new_domain = []
    #         for item in domain:
    #             if isinstance(item, (list, tuple)) and len(item) == 3:
    #                 field, operator, value = item
                    
    #                 # Handle selection fields untuk pencarian label dan bukan hanya value
    #                 if field == 'state' and operator == 'ilike' and value:
    #                     if 'pengajuan' in value.lower():
    #                         new_domain.append(('state', '=', 'Draft'))
    #                     elif 'diperiksa' in value.lower() or 'periksa' in value.lower():
    #                         new_domain.append(('state', '=', 'Check'))
    #                     elif 'disetujui' in value.lower() or 'setuju' in value.lower():
    #                         new_domain.append(('state', '=', 'Approved'))
    #                     elif 'ditolak' in value.lower() or 'tolak' in value.lower():
    #                         new_domain.append(('state', '=', 'Rejected'))
    #                     elif 'keluar' in value.lower():
    #                         new_domain.append(('state', '=', 'Permission'))
    #                     elif 'kembali' in value.lower() or 'masuk' in value.lower():
    #                         new_domain.append(('state', '=', 'Return'))
    #                     else: 
    #                         new_domain.append(item)
                            
    #                 # Handle tanggal
    #                 elif field in ['tgl_ijin'] and operator == 'ilike' and value:
    #                     try:
    #                         # Coba parsing format tanggal yang umum
    #                         date_formats = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d.%m.%Y']
    #                         parsed_date = None
                            
    #                         for fmt in date_formats:
    #                             try:
    #                                 parsed_date = datetime.strptime(value, fmt)
    #                                 break
    #                             except ValueError:
    #                                 continue
                            
    #                         if parsed_date:
    #                             start_date = datetime.combine(parsed_date.date(), datetime.min.time())
    #                             end_date = datetime.combine(parsed_date.date(), datetime.max.time())
    #                             new_domain.append('&')
    #                             new_domain.append((field, '>=', start_date))
    #                             new_domain.append((field, '<=', end_date))
    #                         else:
    #                             # Jika tidak bisa diparsing sebagai tanggal, gunakan pencarian biasa
    #                             new_domain.append(item)
    #                     except Exception:
    #                         # Fallback ke pencarian biasa jika ada error
    #                         new_domain.append(item)
                    
    #                 else:
    #                     new_domain.append(item)
    #             else:
    #                 new_domain.append(item)
            
    #         domain = new_domain

    #         # Filter hanya domain valid (list/tuple dengan panjang 3)
    #         valid_domain = []
    #         or_count = 0
            
    #         for item in domain:
    #             if isinstance(item, (list, tuple)) and len(item) == 3:
    #                 valid_domain.append(item)
    #             elif isinstance(item, str) and item in ['&', '|', '!']:
    #                 if item == '|':
    #                     or_count += 1
    #                 valid_domain.append(item)
            
    #         # Ensure proper balancing for OR operators
    #         if or_count > 0 and len(valid_domain) < (or_count * 2 + 1):
    #             # Domain is invalid, fall back to simple name search
    #             return super(Perijinan, self)._search([('name', 'ilike', '')], offset=offset, limit=limit, order=order, )
            
    #         domain = valid_domain if valid_domain else domain
        
    #     return super(Perijinan, self)._search(domain, offset=offset, limit=limit, order=order, )