# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)

def migrate(cr, version):
    """Post-migration script untuk pesantren_guru 18.0.1.2:
    1. Menyelaraskan company_id cdn_absensi_siswa agar sesuai dengan jenjang kelas (SMP, SMA, SD, TK, dsb).
    2. Menyelaraskan company_id cdn_absensi_siswa_lines.
    3. Memberikan akses semua unit lembaga pesantren di res_company_users_rel untuk seluruh akun guru.
    4. Mengarahkan Default Company (res_users.company_id) guru ke unit tempat mengajarnya.
    """
    _logger.info("Running post-migration script for pesantren_guru 18.0.1.2...")
    from odoo.addons.pesantren_guru.models.absensi_siswa import AbsensiSiswa
    AbsensiSiswa._auto_sync_guru_company(cr)
    _logger.info("Post-migration script for pesantren_guru 18.0.1.2 completed successfully.")
