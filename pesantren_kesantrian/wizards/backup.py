    # def action_checkout(self):
    #     if not self.siswa_id:
    #        return self.toast_notification("Kolom Santri Belum Diisi")

    #     if not self.keperluan:
    #         return self.toast_notification("Kolom Keperluan Belum Diisi")
            
    #     if not self.penjemput:
    #         return self.toast_notification("Kolom penjemput Belum Diisi")

    #     santri_name = self.siswa_id.name
        
    #     # Simpan nilai terakhir keperluan, penjemput, dan tgl_kembali sebagai class variable
    #     if self.keperluan:
    #         self.__class__._last_keperluan_id = self.keperluan.id
        
    #     if self.penjemput:
    #         self.__class__._last_penjemput = self.penjemput
            
    #     # Tambahkan penyimpanan tgl_kembali
    #     if self.tgl_kembali:
    #         self.__class__._last_tgl_kembali = self.tgl_kembali

    #     # Cari perijinan yang sudah ada untuk santri
    #     existing_permissions = self.env['cdn.perijinan'].search([
    #         ('siswa_id', '=', self.siswa_id.id),
    #         ('state', 'in', ['Approved', 'Permission']),
    #         '|',
    #         ('waktu_keluar', '=', False),
    #         ('waktu_kembali', '=', False)
    #     ], limit=1)
        
    #     # Persiapkan nilai untuk perijinan
    #     permission_vals = {
    #         'barcode' : self.barcode,
    #         'siswa_id': self.siswa_id.id,
    #         'tgl_ijin': self.tgl_ijin,
    #         'tgl_kembali': self.tgl_kembali,
    #         'penjemput': self.penjemput or '-',
    #         'keperluan': self.keperluan.id,
    #         'catatan_keamanan': self.catatan_keamanan or '',
    #     }

    #     # Gunakan perijinan yang sudah ada atau buat baru
    #     if existing_permissions and self.has_permission == 'Benar':
    #         self.perijinan_id = existing_permissions[0]
    #         self.perijinan_id.write(permission_vals)
    #     else:   
    #         # Tambahkan state default saat membuat perijinan baru
    #         permission_vals['state'] = 'Approved'
    #         permission = self.env['cdn.perijinan'].create(permission_vals)
    #         self.perijinan_id = permission

    #     # Proses checkout berdasarkan status keluar/masuk
    #     if self.keluar_masuk == 'keluar':
    #         self.perijinan_id.write({
    #             'state': 'Permission',
    #             'waktu_keluar': fields.Datetime.now(),
    #             'catatan_keamanan': self.catatan_keamanan or '',
    #             'keperluan': self.keperluan.id
    #         })
            
    #         message = f"Santri dengan nama {santri_name} keluar dari kawasan pondok."
    #         self.env['bus.bus']._sendone(
    #             self.env.user.partner_id,  
    #             'simple_notification',
    #             {
    #                 'message': message,
    #                 'title': '✅ Data Tersimpan!',
    #                 'sticky': False, 
    #                 'type': 'success',
    #                 'timeout': 150000, 
    #             }
    #         )
            
    #     elif self.keluar_masuk == 'masuk':
    #         self.perijinan_id.write({
    #             'state': 'Return',
    #             'waktu_kembali': fields.Datetime.now(),
    #             'catatan_keamanan': self.catatan_keamanan or '',
    #             'keperluan': self.keperluan.id
    #         })
            
    #         message = f"Santri dengan nama {santri_name} masuk ke kawasan pondok."
    #         self.env['bus.bus']._sendone(
    #             self.env.user.partner_id,  
    #             'simple_notification',
    #             {
    #                 'message': message,
    #                 'title': '✅ Data Tersimpan!',
    #                 'sticky': False, 
    #                 'type': 'success',
    #                 'timeout': 150000, 
    #             }
    #         )

    #     return {
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'cdn.perijinan.checkout',
    #         'view_mode': 'form',
    #         'name': 'Santri Keluar/Masuk', 
    #         'target': 'new',
    #         'context': self.env.context,
    #         'tag' : 'reload',
    #     }

    # def action_checkout(self):
    #     if not self.siswa_id:
    #         return self.toast_notification("Kolom Santri Belum Diisi")

    #     if not self.keperluan:
    #         return self.toast_notification("Kolom Keperluan Belum Diisi")

    #     if not self.penjemput:
    #         return self.toast_notification("Kolom Penjemput Belum Diisi")

    #     santri_name = self.siswa_id.name

    #     # Simpan nilai terakhir keperluan, penjemput, dan tgl_kembali
    #     if self.keperluan:
    #         self.__class__._last_keperluan_id = self.keperluan.id

    #     if self.penjemput:
    #         self.__class__._last_penjemput = self.penjemput

    #     if self.tgl_kembali:
    #         self.__class__._last_tgl_kembali = self.tgl_kembali

    #     # Cari perijinan aktif
    #     existing_permission = self.env['cdn.perijinan'].search([
    #         ('siswa_id', '=', self.siswa_id.id),
    #         ('state', 'in', ['Approved', 'Permission']),
    #         '|',
    #         ('waktu_keluar', '=', False),
    #         ('waktu_kembali', '=', False)
    #     ], limit=1)

    #     # Persiapkan data dasar
    #     permission_vals = {
    #         'barcode': self.barcode,
    #         'siswa_id': self.siswa_id.id,
    #         'tgl_ijin': self.tgl_ijin,
    #         'tgl_kembali': self.tgl_kembali,
    #         'penjemput': self.penjemput or '-',
    #         'keperluan': self.keperluan.id,
    #         'catatan_keamanan': self.catatan_keamanan or '',
    #     }

    #     # === Proses berdasarkan keluar/masuk ===
    #     if self.keluar_masuk == 'keluar':
    #         if existing_permission and self.has_permission == 'Benar':
    #             # Update izin lama
    #             self.perijinan_id = existing_permission
    #             self.perijinan_id.write(permission_vals)
    #         else:
    #             # Buat izin baru
    #             permission_vals['state'] = 'Approved'
    #             permission = self.env['cdn.perijinan'].create(permission_vals)
    #             self.perijinan_id = permission

    #         # Update jadi Permission (keluar)
    #         self.perijinan_id.write({
    #             'state': 'Permission',
    #             'waktu_keluar': fields.Datetime.now(),
    #             'catatan_keamanan': self.catatan_keamanan or '',
    #             'keperluan': self.keperluan.id
    #         })

    #         message = f"Santri dengan nama {santri_name} keluar dari kawasan pondok."

    #     elif self.keluar_masuk == 'masuk':
    #         if existing_permission:
    #             # Pakai izin lama
    #             self.perijinan_id = existing_permission
    #             self.perijinan_id.write({
    #                 'state': 'Return',
    #                 'waktu_kembali': fields.Datetime.now(),
    #                 'catatan_keamanan': self.catatan_keamanan or '',
    #                 'keperluan': self.keperluan.id
    #             })
    #         else:
    #             # Tidak ada izin lama, buat baru khusus masuk
    #             permission_vals.update({
    #                 'state': 'Return',
    #                 'waktu_keluar': fields.Datetime.now(),  # optional: bisa dihapus kalau gak mau isi waktu_keluar
    #                 'waktu_kembali': fields.Datetime.now()
    #             })
    #             permission = self.env['cdn.perijinan'].create(permission_vals)
    #             self.perijinan_id = permission

    #         message = f"Santri dengan nama {santri_name} masuk ke kawasan pondok."

    #     else:
    #         return self.toast_notification("Jenis keluar/masuk tidak valid!")

    #     # Kirim notifikasi kecil
    #     self.env['bus.bus']._sendone(
    #         self.env.user.partner_id,
    #         'simple_notification',
    #         {
    #             'message': message,
    #             'title': '✅ Data Tersimpan!',
    #             'sticky': False,
    #             'type': 'success',
    #             'timeout': 150000,
    #         }
    #     )

    #     # Reload tampilan setelah selesai
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'cdn.perijinan.checkout',
    #         'view_mode': 'form',
    #         'name': 'Santri Keluar/Masuk',
    #         'target': 'new',
    #         'context': self.env.context,
    #         'tag': 'reload',
    #     }

    # def action_checkout(self):
    #     if not self.siswa_id:
    #         return self.toast_notification("Kolom Santri Belum Diisi")
    #     if not self.keperluan:
    #         return self.toast_notification("Kolom Keperluan Belum Diisi")
    #     if not self.penjemput:
    #         return self.toast_notification("Kolom Penjemput Belum Diisi")

    #     santri_name = self.siswa_id.name

    #     # Simpan nilai terakhir keperluan, penjemput, dan tgl_kembali
    #     if self.keperluan:
    #         self.__class__._last_keperluan_id = self.keperluan.id
    #     if self.penjemput:
    #         self.__class__._last_penjemput = self.penjemput
    #     if self.tgl_kembali:
    #         self.__class__._last_tgl_kembali = self.tgl_kembali

    #     # Siapkan data isi
    #     permission_vals = {
    #         'barcode': self.barcode,
    #         'siswa_id': self.siswa_id.id,
    #         'tgl_ijin': self.tgl_ijin,
    #         'tgl_kembali': self.tgl_kembali,
    #         'penjemput': self.penjemput or '-',
    #         'keperluan': self.keperluan.id,
    #         'catatan_keamanan': self.catatan_keamanan or '',
    #     }

    #     if self.keluar_masuk == 'keluar':
    #         # Cari izin yang belum dipakai untuk keluar
    #         existing_permission = self.env['cdn.perijinan'].search([
    #             ('siswa_id', '=', self.siswa_id.id),
    #             ('state', 'in', ['Approved']),
    #             ('waktu_keluar', '=', False),
    #         ], limit=1)

    #         if existing_permission and self.has_permission == 'Benar':
    #             # Update izin lama
    #             self.perijinan_id = existing_permission
    #             self.perijinan_id.write(permission_vals)
    #         else:
    #             # Buat izin baru
    #             permission_vals['state'] = 'Approved'
    #             permission = self.env['cdn.perijinan'].create(permission_vals)
    #             self.perijinan_id = permission

    #         # Update status menjadi Permission
    #         self.perijinan_id.write({
    #             'state': 'Permission',
    #             'waktu_keluar': fields.Datetime.now(),
    #             'catatan_keamanan': self.catatan_keamanan or '',
    #             'keperluan': self.keperluan.id
    #         })

    #         message = f"Santri dengan nama {santri_name} keluar dari kawasan pondok."

    #     elif self.keluar_masuk == 'masuk':
    #         # Cari izin yang sudah keluar tapi belum masuk
    #         existing_permission = self.env['cdn.perijinan'].search([
    #             ('siswa_id', '=', self.siswa_id.id),
    #             ('state', '=', 'Permission'),
    #             ('waktu_keluar', '!=', False),
    #             ('waktu_kembali', '=', False),
    #         ], limit=1)

    #         if existing_permission:
    #             # Update izin lama menjadi kembali
    #             self.perijinan_id = existing_permission
    #             self.perijinan_id.write({
    #                 'state': 'Return',
    #                 'waktu_kembali': fields.Datetime.now(),
    #                 'catatan_keamanan': self.catatan_keamanan or '',
    #                 'keperluan': self.keperluan.id
    #             })
    #         else:
    #             # Tidak ada izin keluar → buat baru langsung state Return
    #             permission_vals.update({
    #                 'state': 'Return',
    #                 'waktu_keluar': fields.Datetime.now(),  # Optional: Bisa dihapus
    #                 'waktu_kembali': fields.Datetime.now()
    #             })
    #             permission = self.env['cdn.perijinan'].create(permission_vals)
    #             self.perijinan_id = permission

    #         message = f"Santri dengan nama {santri_name} masuk ke kawasan pondok."

    #     else:
    #         return self.toast_notification("Jenis keluar/masuk tidak valid!")

    #     # Kirim notifikasi sukses
    #     self.env['bus.bus']._sendone(
    #         self.env.user.partner_id,
    #         'simple_notification',
    #         {
    #             'message': message,
    #             'title': '✅ Data Tersimpan!',
    #             'sticky': False,
    #             'type': 'success',
    #             'timeout': 150000,
    #         }
    #     )

    #     return {
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'cdn.perijinan.checkout',
    #         'view_mode': 'form',
    #         'name': 'Santri Keluar/Masuk',
    #         'target': 'new',
    #         'context': self.env.context,
    #         'tag': 'reload',
    #     }

    # def action_checkout(self):
    #     if not self.siswa_id:
    #         return self.toast_notification("Kolom Santri Belum Diisi")
    #     if not self.keperluan:
    #         return self.toast_notification("Kolom Keperluan Belum Diisi")
    #     if not self.penjemput:
    #         return self.toast_notification("Kolom Penjemput Belum Diisi")

    #     santri_name = self.siswa_id.name

    #     if self.keperluan:
    #         self.__class__._last_keperluan_id = self.keperluan.id
    #     if self.penjemput:
    #         self.__class__._last_penjemput = self.penjemput
    #     if self.tgl_kembali:
    #         self.__class__._last_tgl_kembali = self.tgl_kembali

    #     # Persiapkan isi data perijinan
    #     permission_vals = {
    #         'barcode': self.barcode,
    #         'siswa_id': self.siswa_id.id,
    #         'tgl_ijin': self.tgl_ijin,
    #         'tgl_kembali': self.tgl_kembali,
    #         'penjemput': self.penjemput or '-',
    #         'keperluan': self.keperluan.id,
    #         'catatan_keamanan': self.catatan_keamanan or '',
    #     }

    #     if self.keluar_masuk == 'keluar':
    #         # Cari izin yang masih "Approved" (belum keluar)
    #         existing_permission = self.env['cdn.perijinan'].search([
    #             ('siswa_id', '=', self.siswa_id.id),
    #             ('state', '=', 'Approved'),
    #             ('waktu_keluar', '=', False),
    #         ], limit=1)

    #         if existing_permission:
    #             # Update perijinan lama
    #             self.perijinan_id = existing_permission
    #             self.perijinan_id.write({
    #                 **permission_vals,
    #                 'state': 'Permission',
    #                 'waktu_keluar': fields.Datetime.now(),
    #             })
    #         else:
    #             # Tidak ada → buat baru
    #             permission_vals.update({
    #                 'state': 'Permission',
    #                 'waktu_keluar': fields.Datetime.now(),
    #             })
    #             permission = self.env['cdn.perijinan'].create(permission_vals)
    #             self.perijinan_id = permission

    #         message = f"Santri dengan nama {santri_name} keluar dari kawasan pondok."

    #     elif self.keluar_masuk == 'masuk':
    #         # Cari izin yang "Permission" (sudah keluar) tapi belum "Return"
    #         existing_permission = self.env['cdn.perijinan'].search([
    #             ('siswa_id', '=', self.siswa_id.id),
    #             ('state', '=', 'Permission'),
    #             ('waktu_keluar', '!=', False),
    #             ('waktu_kembali', '=', False),
    #         ], limit=1)

    #         if existing_permission:
    #             # Update perijinan lama
    #             self.perijinan_id = existing_permission
    #             self.perijinan_id.write({
    #                 'waktu_kembali': fields.Datetime.now(),
    #                 'state': 'Return',
    #                 'catatan_keamanan': self.catatan_keamanan or '',
    #                 'keperluan': self.keperluan.id
    #             })
    #         else:
    #             # Tidak ada → buat baru
    #             permission_vals.update({
    #                 'state': 'Return',
    #                 'waktu_keluar': fields.Datetime.now(),  # Optional
    #                 'waktu_kembali': fields.Datetime.now()
    #             })
    #             permission = self.env['cdn.perijinan'].create(permission_vals)
    #             self.perijinan_id = permission

    #         message = f"Santri dengan nama {santri_name} masuk ke kawasan pondok."

    #     else:
    #         return self.toast_notification("Jenis keluar/masuk tidak valid!")

    #     # Kirim notifikasi
    #     self.env['bus.bus']._sendone(
    #         self.env.user.partner_id,
    #         'simple_notification',
    #         {
    #             'message': message,
    #             'title': '✅ Data Tersimpan!',
    #             'sticky': False,
    #             'type': 'success',
    #             'timeout': 150000,
    #         }
    #     )

    #     return {
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'cdn.perijinan.checkout',
    #         'view_mode': 'form',
    #         'name': 'Santri Keluar/Masuk',
    #         'target': 'new',
    #         'context': self.env.context,
    #         'tag': 'reload',
    #     }
