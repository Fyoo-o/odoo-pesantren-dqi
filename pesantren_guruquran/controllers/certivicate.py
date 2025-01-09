from odoo import http
from odoo.http import request
from datetime import datetime
import locale

class SiswaController(http.Controller):

    @http.route('/cetak_sertifikat', type='http', auth='public', methods=['GET'])
    def cetak_sertifikat(self, id=None, **kwargs):
        """
        Endpoint to generate and return certificates for multiple students in HTML format.
        """
        # Mendapatkan parameter ID dari request
        record_ids = request.params.get('id')

        # Validasi jika ID tidak diberikan
        if not record_ids:
            return request.not_found()

        # Mengonversi string ID yang dipisahkan dengan koma menjadi list integer
        record_ids = [int(i) for i in record_ids.split(',')]

        # Mencari record siswa berdasarkan ID yang diberikan
        records = request.env['cdn.siswa'].sudo().search([('id', 'in', record_ids)])

        # Jika tidak ditemukan record siswa, return 404
        if not records:
            return request.not_found()

        # Membangun HTML content untuk sertifikat tiap siswa
        content = ""
        for record in records:
            # Mencari absen untuk siswa
            absen = request.env['cdn.absen_tahfidz_quran_line'].sudo().search([('siswa_id', '=', record.id)])
            
            # Inisialisasi dictionary untuk menyimpan jumlah kehadiran
            kehadiran = {
                'izin': 0,
                'sakit': 0,
                'alpa': 0,
                'hadir': 0
            }

            # Iterasi melalui semua record absen dan perbarui jumlah kehadiran
            for data in absen:
                if data.kehadiran == 'Izin':
                    kehadiran['izin'] += 1
                elif data.kehadiran == 'Sakit':
                    kehadiran['sakit'] += 1
                elif data.kehadiran == 'Alpa':
                    kehadiran['alpa'] += 1
                else:
                    kehadiran['hadir'] += 1

            # Format tanggal
            locale.setlocale(locale.LC_TIME, 'id_ID.utf8')
            tanggal_sekarang = datetime.now()
            tanggal_formatted = tanggal_sekarang.strftime('%A, %d %B %Y')

            # Mendapatkan data siswa
            data = {
                'name': record.name,
                'nis': record.nis,
                'kelas': record.ruang_kelas_id.name,
                'halaqoh': record.halaqoh_id.name,
                'penanggung_jawab': record.penanggung_jawab_id.name,
                'orangtua': record.ayah_nama,
                'tahfidz': record.tahfidz_quran_ids,
                'catatan_ortu':record.catatan_ortu or 'Ananda menunjukkan kemajuan baik dalam hafalan, namun perlu memperbaiki tajwid dan memperkuat murojaah harian. Bacaan cukup lancar, dengan sikap yang santun dan disiplin selama belajar. Mohon dukungan orang tua untuk rutin memantau hafalan di rumah.',
                'catatan':record.catatan or 'Disarankan untuk meningkatkan murojaah harian agar hafalan lebih kuat. Dari segi adab, santri sudah menunjukkan sikap yang baik dan disiplin selama sesi halaqoh.' ,
            }

            # Generate konten dinamis dari tahfidz_quran_ids
            content_data = ""
            last_surahs = {}
            nomor_urut = 1

            # Proses untuk menyaring data tahfidz
            for tahfidz in data['tahfidz']:
                if tahfidz.state == 'done':
                    surah_name = tahfidz.surah_id.name
                    surah_start = 1
                    surah_end = int(tahfidz.ayat_akhir)  # Ayat terakhir dari surah
                    surah_range = int(tahfidz.jml_ayat)  # Jumlah total ayat dalam surah

                    # Mengecek apakah surah terakhir (surah_end lebih besar dari range sebelumnya)
                    if surah_name not in last_surahs or surah_end < int(last_surahs[surah_name]['end']):
                        last_surahs[surah_name] = {
                            'range': f"{surah_name} ({surah_start} - {surah_end})",
                            'end': surah_end,
                            'nilai': tahfidz.nilai,
                            'predikat': tahfidz.predikat,
                            'nilai_id_name': tahfidz.nilai_id.name
                        }

            # Menambahkan baris ke content berdasarkan data terakhir untuk setiap surah
            for surah_name, surah_data in last_surahs.items():
                content_data += f"""
                    <tr>
                        <td>{nomor_urut}</td>
                        <td>{surah_data['range']}</td>
                        <td>{surah_data['nilai']}</td>
                        <td>{surah_data['predikat']}</td>
                        <td>{surah_data['nilai_id_name']}</td>
                    </tr>
                """
                nomor_urut += 1

            # Membangun konten HTML sertifikat untuk setiap siswa
            content += f"""
           <!DOCTYPE html>
                <html lang="en">

                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Rapor Halaqah</title>
                    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha3/dist/css/bootstrap.min.css" rel="stylesheet">
                </head>        
                <style>
                    * {{
                        font-family: 'Times New Roman', Times, serif;
                        font-size: 13px;
                    }}

                    th {{
                        padding-left: 4px;
                    }}

                    tr td {{
                        padding-top: 4px;
                        padding-bottom: 4px;
                    }}

                    body {{
                        background-color: transparent;
                        min-height: 100vh;
                        margin: 0;
                        padding: 0;
                    }}

                    .bg {{
                        background-color: transparent;
                    }}

                    .rapor-container {{
                        width: 21cm;
                        /* Ukuran standar A4 */
                        height: 29.7cm;
                        background: url('pesantren_guruquran/static/description/Rapor.jpeg') no-repeat center center;
                        background-size: 100% 100%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                        border: 1px solid #ddd;
                        border-radius: 8px;
                    }}

                    .rapor-content {{
                        width: 90%;
                        height: 90%;
                        overflow: hidden;
                        border-radius: 8px;
                        padding: 10px 45px;
                    }}

                    .ttd div.text-center {{
                        height: 12rem;
                        display: flex;
                        flex-direction: column;
                        justify-content: space-between;
                    }}

                    .ttd .status {{
                        display: flex;
                        align-items: end;
                        justify-content: center;
                        margin: 0;
                        height: 47.94px;
                    }}

                    .data-ttd {{
                        display: flex;
                        justify-content: center;
                        bottom: 51px;
                        width: 100%;
                    }}

                    .ttd-body {{
                        width: 70%;
                    }}
                </style>
                <body class="d-flex justify-content-center align-items-center flex-column">
                    <div class="">
                        <div class="rapor-container position-relative">
                            <div class="rapor-content bg shadow p-5">
                                <div class="text-center mb-5">
                                    <h5 class="fw-bold">HASIL EVALUASI BELAJAR</h5>
                                </div>
                                <div class="d-flex justify-content-between">
                                    <p><strong>Nama Santri:</strong> {data['name']}</p>
                                    <p><strong>Halaqah:</strong> {data['halaqoh']}</p>
                                </div>
                                <div class="container mt-0">
                                    <div class="row px-3">
                                        <div class="col-md-8 m-0 p-0 pe-2">
                                            <table class="table-bordered text-center w-100 h-100">
                                                <thead>
                                                    <tr>
                                                        <th>No</th>
                                                        <th>Materi Tahsin (Tilawati/Juz)<br>Bidang</th>
                                                        <th>Nilai</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    <tr>
                                                        <td>1</td>
                                                        <td>Fashohah</td>
                                                        <td>70</td>
                                                    </tr>
                                                    <tr>
                                                        <td>2</td>
                                                        <td>Tajwid</td>
                                                        <td>70</td>
                                                    </tr>
                                                    <tr>
                                                        <td>3</td>
                                                        <td>Ghorib, Musykilat</td>
                                                        <td>70</td>
                                                    </tr>
                                                    <tr>
                                                        <td>4</td>
                                                        <td>Suara & Lagu</td>
                                                        <td>80</td>
                                                    </tr>
                                                    <tr>
                                                        <td colspan="3" class="text-start">
                                                            <strong>Catatan Khusus:</strong> {data['catatan']}
                                                        </td>
                                                    </tr>
                                                </tbody>
                                            </table>
                                        </div>
                                        <div class="col-md-4 m-0 p-0">
                                            <table class="table-bordered w-100 h-100">
                                                <thead>
                                                    <tr>
                                                        <th colspan="2" class="text-center">Absensi</th>
                                                    </tr>
                                                </thead>
                                                <tbody class="text-start">
                                                    <tr>
                                                        <th>Sakit</th>
                                                        <td class="text-center">{kehadiran['sakit']}</td>
                                                    </tr>
                                                    <tr>
                                                        <th>Izin</th>
                                                        <td class="text-center">{kehadiran['izin']}</td>
                                                    </tr>
                                                    <tr>
                                                        <th>Tanpa Keterangan</th>
                                                        <td class="text-center">{kehadiran['alpa']}</td>
                                                    </tr>
                                                    <tr>
                                                        <th>Pers. Kehadiran</th>
                                                        <td class="text-center">{int((kehadiran['hadir']/sum(kehadiran.values())) * 100)}%</td>
                                                    </tr>
                                                    <tr>
                                                        <th colspan="2" class="text-uppercase text-center">Akhlaq Keseharian</th>
                                                    </tr>
                                                    <tr>
                                                        <th>Adab dengan Guru</th>
                                                        <td class="text-uppercase text-center">B</td>
                                                    </tr>
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>

                                    <table class="table-bordered w-100 mt-3">
                                        <thead>
                                            <tr>
                                                <th>Predikat Tahsin</th>
                                                <th>Naik Ke: Jenjang Qur'an</th>
                                                <th>Adab dengan Teman</th>
                                                <th>B</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr>
                                                <th>Peringkat</th>
                                                <td>(1) Dari 3 Santri/wati</td>
                                                <td>Kedisiplinan</td>
                                                <th>B</th>
                                            </tr>
                                        </tbody>
                                    </table>

                                    <table class="table-bordered text-center mt-3 w-100">
                                        <thead>
                                            <tr>
                                                <th>No</th>
                                                <th>Materi</th>
                                                <th>Hafalan</th>
                                                <th>Nilai</th>
                                                <th>Predikat</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {content_data}
                                            <tr>
                                                <td colspan="5" class="text-start p-2">
                                                    <str  ong>Catatan untuk Orang Tua/Wali:</strong> {data['catatan_ortu']}
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>

                                <div class="d-flex align-items-end flex-column me-3 mt-1">
                                    <div class="">
                                        <p class="m-0">Diberikan di, Pelaihari ...</p>
                                        <p>Hari,tanggal : {tanggal_formatted}</p>
                                    </div>
                                </div>
                                <div class="data-ttd">
                                    <div class="ttd-body w-100">
                                        <h5 class="text-center mb-0 pb-0 w-100">Mengetahui</h5>
                                        <div class="d-flex justify-content-between mt-0 ttd">
                                            <div class="text-center">
                                                <p class="status">Ketua RTQ<br>Daarul Qur'an Istiqomah</p>
                                                <p><strong>Ust. M. Taufik Hidayat, S.Pd <br>NIY:3294934729</strong></p>
                                            </div>
                                            <div class="text-center">
                                                <p class="status">Pembimbing Halaqah</p>
                                                <p><strong>{data['penanggung_jawab']}<br>NIY:3294934729</strong></p>
                                            </div>
                                            <div class="text-center">
                                                <p class="status">Orangtua/Wali Santri</p>
                                                <p class="text-underline">({data['orangtua']})</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <script>
                        window.print()
                    </script>
                </body>

                </html>
            """

        # Kembalikan HTML sebagai respons
        return request.make_response(content, headers=[('Content-Type', 'text/html')])
