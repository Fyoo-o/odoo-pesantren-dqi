# -*- coding: utf-8 -*-

from . import controllers
from . import models
from . import wizards


def _post_init_fix_absensi_malam_filters(env):
    """
    Dipanggil setelah modul selesai di-install/upgrade.
    Memperbaiki filter 'Absensi Malam Santri Per kamar' di database:
    1. Matikan is_default agar tidak otomatis terpasang
    2. Perbaiki context group_by agar TANPA tanggal
    """
    filters = env['ir.filters'].sudo().search([
        ('model_id', '=', 'cdn.absensi_malam')
    ])
    for f in filters:
        vals = {'is_default': False}
        # Perbaiki context filter 'Per kamar' agar tanpa tgl
        if f.name and 'per kamar' in f.name.lower():
            vals['context'] = "{'group_by': ['kamar_id', 'musyrif_id']}"
        f.write(vals)
