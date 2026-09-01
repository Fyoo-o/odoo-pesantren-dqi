# -*- coding: utf-8 -*-

import base64
from odoo import api, fields, models
from odoo.exceptions import UserError


class MasterRPM(models.Model):
    _name = 'cdn.master_rpm'
    _description = 'Data Rencana Pembelajaran Mendalam'

    name = fields.Char(string='Materi', required=True,
                       help="Judul atau topik materi pembelajaran")
    jenjang = fields.Selection([
        ('sd', 'SD/MI'),
        ('smp', 'SMP/MTS'),
        ('sma', 'SMA/MA'),
        ('nonformal', 'Nonformal'),
    ], string='Jenjang')
    matpel_id = fields.Many2one('cdn.mata_pelajaran', string='Mata Pelajaran')
    tingkat_id = fields.Many2one('cdn.tingkat', string='Kelas')
    jurusan_id = fields.Many2one('cdn.master_jurusan', string='Jurusan')
    waktu = fields.Char(string='Alokasi Waktu')
    kd = fields.Char(string='Kompentensi Dasar',
                     help="Kompetensi dasar (KD) yang menjadi acuan")
    dokumen = fields.Binary(string='Dokumen RPM')
    tujuan = fields.Text(
        string='Tujuan', help="Tujuan pembelajaran yang ingin dicapai setelah materi ini disampaikan")

    def _auto_init(self):
        cr = self.env.cr
        cr.execute("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name='cdn_master_rpp'
                ) AND NOT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name='cdn_master_rpm'
                ) THEN
                    ALTER TABLE cdn_master_rpp RENAME TO cdn_master_rpm;
                    ALTER INDEX IF EXISTS cdn_master_rpp_pkey RENAME TO cdn_master_rpm_pkey;
                    ALTER SEQUENCE IF EXISTS cdn_master_rpp_id_seq RENAME TO cdn_master_rpm_id_seq;
                END IF;

                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='cdn_absensi_siswa' AND column_name='rpp_id'
                ) THEN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='cdn_absensi_siswa' AND column_name='rpm_id'
                    ) THEN
                        ALTER TABLE cdn_absensi_siswa RENAME COLUMN rpp_id TO rpm_id;
                    ELSE
                        UPDATE cdn_absensi_siswa SET rpm_id = rpp_id WHERE rpm_id IS NULL AND rpp_id IS NOT NULL;
                        ALTER TABLE cdn_absensi_siswa DROP COLUMN rpp_id;
                    END IF;
                END IF;

                UPDATE ir_model SET model = 'cdn.master_rpm', name = '{"en_US": "Data Rencana Pembelajaran Mendalam", "id_ID": "Data Rencana Pembelajaran Mendalam"}'::jsonb WHERE model = 'cdn.master_rpp';
                UPDATE ir_model SET name = '{"en_US": "Data Rencana Pembelajaran Mendalam", "id_ID": "Data Rencana Pembelajaran Mendalam"}'::jsonb WHERE model = 'cdn.master_rpm';
                UPDATE ir_act_window SET name = '{"en_US": "Rencana Pembelajaran Mendalam", "id_ID": "Rencana Pembelajaran Mendalam"}'::jsonb WHERE res_model = 'cdn.master_rpm';
                UPDATE ir_model_fields SET model = 'cdn.master_rpm' WHERE model = 'cdn.master_rpp';
                UPDATE ir_model_fields SET relation = 'cdn.master_rpm' WHERE relation = 'cdn.master_rpp';
                UPDATE ir_model_fields SET name = 'rpm_id' WHERE model = 'cdn.absensi_siswa' AND name = 'rpp_id';
                UPDATE ir_model_data SET model = 'cdn.master_rpm' WHERE model = 'cdn.master_rpp';
                UPDATE ir_model_data SET name = REPLACE(name, 'master_rpp', 'master_rpm') WHERE name LIKE '%master_rpp%';
                UPDATE ir_ui_view SET arch_db = REPLACE(arch_db::text, 'rpp_id', 'rpm_id')::jsonb WHERE arch_db::text LIKE '%rpp_id%';
                UPDATE ir_ui_view SET arch_fs = REPLACE(arch_fs, 'rpp_id', 'rpm_id') WHERE arch_fs LIKE '%rpp_id%';
                UPDATE ir_attachment SET res_model = 'cdn.master_rpm' WHERE res_model = 'cdn.master_rpp';
            END $$;
        """)
        return super()._auto_init()

    @api.onchange('jenjang')
    def _onchange_jenjang(self):
        for record in self:
            if record.jenjang:
                if record.matpel_id and record.matpel_id.jenjang != record.jenjang:
                    record.matpel_id = False
                if record.tingkat_id and record.tingkat_id.jenjang != record.jenjang:
                    record.tingkat_id = False

    @api.constrains('dokumen')
    def _check_dokumen(self):
        for record in self:
            if record.dokumen:
                try:
                    doc_bytes = base64.b64decode(record.dokumen)
                    if not doc_bytes.startswith(b'%PDF'):
                        raise UserError('Dokumen harus berformat PDF')
                except Exception as e:
                    if isinstance(e, UserError):
                        raise e
                    raise UserError('Dokumen harus berformat PDF')
