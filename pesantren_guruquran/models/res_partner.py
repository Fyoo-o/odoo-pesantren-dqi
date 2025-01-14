from odoo import models, fields, api

class CdnSiswa(models.Model):
    _inherit = 'cdn.siswa'

    
    catatan_ortu = fields.Char(string='Catatan Orang Tua', 
    default='Ananda menunjukkan kemajuan baik dalam hafalan, namun perlu memperbaiki tajwid dan memperkuat murojaah harian. Bacaan cukup lancar, dengan sikap yang santun dan disiplin selama belajar. Mohon dukungan orang tua untuk rutin memantau hafalan di rumah.'
    )
    catatan = fields.Char(string='Catatan', 
    default='Disarankan untuk meningkatkan murojaah harian agar hafalan lebih kuat. Dari segi adab, santri sudah menunjukkan sikap yang baik dan disiplin selama sesi halaqoh.'
    )
    adab_ke_guru = fields.Selection(
        string='Adab Kepada Guru',
        selection=[('+a', 'A+'), ('a', 'A'), ('+b', 'B+'), ('b', 'B'), ('+c', 'C+'), ('c', 'C')],
        default='b'
    )

    adab_ke_teman = fields.Selection(
        string='Adab Kepada Teman',
        selection=[('+a', 'A+'), ('a', 'A'), ('+b', 'B+'), ('b', 'B'), ('+c', 'C+'), ('c', 'C')],
        default='b'
    )

    kedisiplinan = fields.Selection(
        string='Kedisiplinan',
        selection=[('+a', 'A+'), ('a', 'A'), ('+b', 'B+'), ('b', 'B'), ('+c', 'C+'), ('c', 'C')],
        default='b')
    
    peringkat = fields.Integer(
        string='Peringkat dalam Kelas',
        default=0
    )
    

    def action_print_sertifikat(self):
        """
        Action to generate and print a certificate for multiple students.
        """
        for record in self:
            # Ambil ID siswa yang ingin dicetak sertifikatnya
            student_ids = self.ids  # Ambil semua ID dari record yang ada dalam context
            return {
                'type': 'ir.actions.act_url',
                'url': f'/cetak_sertifikat?id={",".join(map(str, student_ids))}',  # Kirim ID dalam bentuk list ke URL
                'target': 'new',  # Membuka di tab baru
            }

