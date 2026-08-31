# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)

def migrate(cr, version):
    """Post-migration script untuk pesantren_guruquran:
    1. Membersihkan preferensi pengurutan tampilan kolom lama (ir_ui_view_custom).
    2. Menyelaraskan ustadz_id di cdn_penilaian_quran dengan cdn_absen_halaqoh.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("Running post-migration script for pesantren_guruquran 18.0.1.2...")

    # 1. Clear old saved user view preferences for Penilaian Halaqoh & Absensi Halaqoh
    cr.execute("""
        DELETE FROM ir_ui_view_custom 
        WHERE ref_id IN (
            SELECT id FROM ir_ui_view 
            WHERE model IN ('cdn.penilaian_quran', 'cdn.absen_halaqoh')
        ) OR arch_updated ILIKE '%penilaian_quran%' 
          OR arch_updated ILIKE '%absen_halaqoh%';
    """)

    # 2. Sync ustadz_id from cdn_absen_halaqoh to cdn_penilaian_quran if mismatched
    cr.execute("""
        UPDATE cdn_penilaian_quran pq
        SET ustadz_id = ah.ustadz_id
        FROM cdn_absen_halaqoh ah
        WHERE pq.tanggal = ah.name
          AND pq.halaqoh_id = ah.halaqoh_id
          AND pq.ustadz_id IS DISTINCT FROM ah.ustadz_id;
    """)
    _logger.info("Synced ustadz_id from Absensi to Penilaian records.")
