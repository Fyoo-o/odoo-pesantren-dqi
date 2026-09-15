import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Migration script: Fix Absensi Malam Santri
    1. Set is_default = False pada SEMUA filter cdn.absensi_malam
    2. Perbaiki context filter 'Per kamar' agar tanpa group by tanggal
    3. Hapus search_default context dari action window cdn.absensi_malam
    """
    _logger.info("=== Fixing Absensi Malam filters & action windows ===")

    # 1. Matikan SEMUA is_default pada filter cdn.absensi_malam
    cr.execute("""
        UPDATE ir_filters
        SET is_default = false
        WHERE model_id = 'cdn.absensi_malam'
          AND is_default = true
    """)
    _logger.info("Disabled is_default on %d filter(s)", cr.rowcount)

    # 2. Perbaiki context filter 'Per kamar' agar tanpa tgl
    cr.execute("""
        UPDATE ir_filters
        SET context = $${'group_by': ['kamar_id', 'musyrif_id']}$$,
            is_default = false
        WHERE model_id = 'cdn.absensi_malam'
          AND LOWER(name) LIKE '%%per kamar%%'
    """)
    _logger.info("Fixed context for %d 'Per kamar' filter(s)", cr.rowcount)

    # 3. Hapus search_default dari SEMUA action window cdn.absensi_malam
    cr.execute("""
        UPDATE ir_act_window
        SET context = '{}'
        WHERE res_model = 'cdn.absensi_malam'
          AND context LIKE '%%search_default%%'
    """)
    _logger.info("Cleared search_default from %d action window(s)", cr.rowcount)

    _logger.info("=== Done fixing Absensi Malam ===")
