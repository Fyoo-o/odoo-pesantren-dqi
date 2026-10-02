import os
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class JamPelajaran(models.Model):
    _name = 'cdn.ref_jam_pelajaran'
    _description = 'Data Jam Pelajaran'
    _order = 'name asc'

    name = fields.Char(string='Nama', required=True)
    company_id = fields.Many2one('res.company', string='Lembaga', default=lambda self: self.env.company)
    start_time = fields.Float(string='Jam Mulai', required=True)
    end_time = fields.Float(string='Jam Selesai', required=True)
    active = fields.Boolean(string='Active', default=True)

    def _register_hook(self):
        super()._register_hook()
        cr = self.env.cr
        try:
            # 1. Otomatis buat kolom active jika belum ada
            cr.execute("""
                ALTER TABLE cdn_ref_jam_pelajaran 
                ADD COLUMN IF NOT EXISTS active boolean DEFAULT true;
                
                UPDATE cdn_ref_jam_pelajaran 
                SET active = true 
                WHERE active IS NULL;
            """)
            # 2. Otomatis buat kolom company_id jika belum ada
            cr.execute("""
                ALTER TABLE cdn_ref_jam_pelajaran 
                ADD COLUMN IF NOT EXISTS company_id integer REFERENCES res_company(id) ON DELETE SET NULL;
            """)
            # 3. Reload view XML secara otomatis jika ada
            try:
                from odoo.tools import convert_file
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                xml_view = os.path.join(base_dir, 'views', 'ref_jam_pelajaran.xml')
                if os.path.exists(xml_view):
                    convert_file(cr, 'pesantren_base', 'views/ref_jam_pelajaran.xml', idref={}, mode='update', noupdate=False, kind='data')
            except Exception as ex_view:
                _logger.debug("Auto reload view ref_jam_pelajaran skipped/failed: %s", ex_view)

        except Exception as e:
            _logger.warning("Auto DDL migration cdn_ref_jam_pelajaran failed: %s", e)

    # onchange
    @api.onchange('start_time', 'end_time')
    def onchange_start_time(self):
        if self.start_time > self.end_time:
            self.end_time = self.start_time
            return {'warning': {'title': 'Warning', 'message': 'Jam Mulai tidak boleh lebih besar dari Jam Selesai'}}
        else:
            return {}
