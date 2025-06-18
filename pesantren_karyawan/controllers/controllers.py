# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo import http
from odoo.http import request
from datetime import date
import requests
import datetime
import json
import base64
import tempfile
import os
import random
import hashlib
import locale
import logging
_logger = logging.getLogger(__name__)

class PesantrenBeranda(http.Controller):
    @http.route('/beranda', auth='public')
    def index(self, **kw):
        
        # Ambil perusahaan yang aktif (current company)
        company = http.request.env.user.company_id

        # Ambil alamat perusahaan
        alamat_perusahaan = {
            'street': company.street or '',
            'street2': company.street2 or '',
            'city': company.city or '',
            'state': company.state_id.name if company.state_id else '',
            'zip': company.zip or '',
            'country': company.country_id.name if company.country_id else '',
        }

        # Gabungkan alamat menjadi satu string (opsional)
        alamat_lengkap = ', '.join(filter(None, [
            alamat_perusahaan['street'],
            alamat_perusahaan['street2'],
            alamat_perusahaan['city'],
            alamat_perusahaan['state'],
            alamat_perusahaan['zip'],
            alamat_perusahaan['country']
        ]))

         # Ambil nilai dari field konfigurasi
        config_obj = http.request.env['ir.config_parameter'].sudo()

        tgl_mulai_pendaftaran = config_obj.get_param('pesantren_pendaftaran.tgl_mulai_pendaftaran')
        tgl_akhir_pendaftaran = config_obj.get_param('pesantren_pendaftaran.tgl_akhir_pendaftaran')
        tgl_mulai_seleksi = config_obj.get_param('pesantren_pendaftaran.tgl_mulai_seleksi')
        tgl_akhir_seleksi = config_obj.get_param('pesantren_pendaftaran.tgl_akhir_seleksi')
        tgl_pengumuman_hasil_seleksi = config_obj.get_param('pesantren_pendaftaran.tgl_pengumuman_hasil_seleksi')

        # Set nilai default dinamis jika parameter kosong
        if not tgl_mulai_pendaftaran:
            tgl_mulai_pendaftaran_dt = datetime.datetime.now() + datetime.timedelta(days=1)
            tgl_mulai_pendaftaran = tgl_mulai_pendaftaran_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            tgl_mulai_pendaftaran_dt = datetime.datetime.strptime(tgl_mulai_pendaftaran, '%Y-%m-%d %H:%M:%S')

        if not tgl_akhir_pendaftaran:
            tgl_akhir_pendaftaran_dt = tgl_mulai_pendaftaran_dt + datetime.timedelta(days=3)
            tgl_akhir_pendaftaran = tgl_akhir_pendaftaran_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            tgl_akhir_pendaftaran_dt = datetime.datetime.strptime(tgl_akhir_pendaftaran, '%Y-%m-%d %H:%M:%S')

        if not tgl_mulai_seleksi:
            tgl_mulai_seleksi_dt = tgl_akhir_pendaftaran_dt
            tgl_mulai_seleksi = tgl_mulai_seleksi_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            tgl_mulai_seleksi_dt = datetime.datetime.strptime(tgl_mulai_seleksi, '%Y-%m-%d %H:%M:%S')

        if not tgl_akhir_seleksi:
            tgl_akhir_seleksi_dt = tgl_mulai_seleksi_dt + datetime.timedelta(days=3)
            tgl_akhir_seleksi = tgl_akhir_seleksi_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            tgl_akhir_seleksi_dt = datetime.datetime.strptime(tgl_akhir_seleksi, '%Y-%m-%d %H:%M:%S')

        if not tgl_pengumuman_hasil_seleksi:
            tgl_pengumuman_hasil_seleksi_dt = tgl_akhir_seleksi_dt + datetime.timedelta(days=2)
            tgl_pengumuman_hasil_seleksi = tgl_pengumuman_hasil_seleksi_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            tgl_pengumuman_hasil_seleksi_dt = datetime.datetime.strptime(tgl_pengumuman_hasil_seleksi, '%Y-%m-%d %H:%M:%S')

        # Format tanggal manual dalam bahasa Indonesia
        def format_tanggal_manual(dt):
            bulan_indonesia = [
                "Januari", "Februari", "Maret", "April", "Mei", "Juni",
                "Juli", "Agustus", "September", "Oktober", "November", "Desember"
            ]
            return f"{dt.day} {bulan_indonesia[dt.month - 1]} {dt.year}"

        # Format tanggal untuk ditampilkan di halaman
        tgl_mulai_pendaftaran_formatted = format_tanggal_manual(tgl_mulai_pendaftaran_dt)
        tgl_akhir_pendaftaran_formatted = format_tanggal_manual(tgl_akhir_pendaftaran_dt)
        tgl_mulai_seleksi_formatted = format_tanggal_manual(tgl_mulai_seleksi_dt)
        tgl_akhir_seleksi_formatted = format_tanggal_manual(tgl_akhir_seleksi_dt)
        tgl_pengumuman_hasil_seleksi_formatted = format_tanggal_manual(tgl_pengumuman_hasil_seleksi_dt)

        html_content = f"""
                    <!doctype html>
                    <html lang="en">

            <head>
            <!-- Primary Meta Tags --> 
            <title>PSB Daarul Qur`an Istiqomah</title> 
            <meta name="title" content="PSB Daarul Qur`an Istiqomah" /> 
            <meta name="description" content="Pendaftaran Santri Baru PP Daarul Qur`an Istiqomah Tahun pelajaran 2025-2026 Telah dibuka. segera daftarkan anak anda sekarang" /> 
 
            <!-- Open Graph / Facebook --> 
            <meta property="og:type" content="website" /> 
            <meta property="og:url" content="https://aplikasi.dqi.ac.id/pendaftaran" /> 
            <meta property="og:title" content="PSB Daarul Qur`an Istiqomah" /> 
            <meta property="og:description" content="Pendaftaran Santri Baru PP Daarul Qur`an Istiqomah Tahun pelajaran 2025-2026 Telah dibuka. segera daftarkan anak anda sekarang" /> 
            <meta property="og:image" content="https://drive.usercontent.google.com/download?id=1VZRccbFtq82wTNcReEq43piA_GJQddcm" /> 
 
            <!-- Twitter --> 
            <meta property="twitter:card" content="summary_large_image" /> 
            <meta property="twitter:url" content="https://aplikasi.dqi.ac.id/pendaftaran" /> 
            <meta property="twitter:title" content="PSB Daarul Qur`an Istiqomah" /> 
            <meta property="twitter:description" content="Pendaftaran Santri Baru PP Daarul Qur`an Istiqomah Tahun pelajaran 2025-2026 Telah dibuka. segera daftarkan anak anda sekarang" /> 
            <meta property="twitter:image" content="https://drive.usercontent.google.com/download?id=1VZRccbFtq82wTNcReEq43piA_GJQddcm" />

            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Daarul Qur'an Istiqomah</title>
            <link rel="icon" type="image/x-icon" href="/pesantren_pendaftaran/static/img/favicon.ico?v=1">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet"
                integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
            </head>
            <style>
            .bg-body-grenyellow {{ background: linear-gradient(to right, #009688 40%, #ccff33 130%); }}

            .rounded-90 {{ border-radius: 0 0 25% 0; }}

            .p-auto {{ padding: 6% 0; }}

            .stepper {{ justify-content: space-around; align-items: center; margin-top: 50px; }}

            .step {{ text-align: center; position: relative; padding-top: 30px; }}

            .step-circle {{ 
                width: 50px;
                height: 50px;
                background-color: #009688;
                color: white;
                font-size: 1.5rem;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto;
                position: relative;z-index: 1; }}

            .step-line {{ 
                width: 100%;
                height: 2px;
                background-color: #009688;
                position: absolute;
                top: 55px;
                left: 0;
                z-index: -10; }}

            .step:last-child .step-line {{ 
                width: 50%; }}

            .step:first-child .step-line {{ 
                width: 50%;
                left: 50%; }}

            .text-green {{ 
                color: #009688; }}
            .footer {{ 
                background-color: #4a4a4a;
             }}
            .footer h5 {{
                font-weight: bold;
            }}
            .footer p, .footer a {{
            color: #ffffff;
            font-size: 0.9rem;
            }}
            .footer a:hover {{
            text-decoration: underline;
            }}
            .footer hr {{
            border-color: #ffffff;
            opacity: 0.3;
            }}
            .card p{{
            margin: 0;
            }}
            @media(max-width:768px) {{
            h1{{
                font-size:1.5rem;
            }}
            h3{{
                font-size: 1rem;
            }}
            h5{{
                font-size: 0.9rem;
            }}
            .step{{
                padding: 5px;
                padding-top: 20px;
                margin: 30px 0;
                box-shadow: var(--bs-box-shadow) !important;
                border-radius: 10px;
            }}
            .bg-body-grenyellow.rounded-90{{
                border-radius: 0;
            }}
            .w-set-auto{{
                width: 100%;
            }}
            }}

            /* Styling umum */
            .card-item {{
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100%; /* Pastikan tinggi fleksibel */
                text-align: center; /* Pusatkan semua teks */
            }}

            .card-value {{
                font-weight: bold;
                font-size: 2rem; /* Ukuran dasar untuk angka */
                line-height: 1; /* Pastikan tidak ada spasi tambahan */
                margin: 0; /* Hapus margin */
                height: 50px;
            }}

            .card-label {{
                font-weight: 600;
                color: #6c757d; /* Warna teks sekunder */
                font-size: 1.25rem; /* Ukuran dasar untuk label */
                margin: 0; /* Hapus margin */
                line-height: 1.2; /* Sedikit lebih tinggi untuk label */
                height: 30px;
            }}

            /* Responsif untuk layar medium */
            @media (max-width: 768px) {{
                .card-value {{
                    font-size: 1.75rem; /* Lebih kecil untuk tablet */
                }}
                .card-label {{
                    font-size: 1rem; /* Lebih kecil untuk label tablet */
                }}
            }}

            /* Responsif untuk layar kecil */
            @media (max-width: 576px) {{
                .card-value {{
                    font-size: 1.5rem; /* Lebih kecil untuk layar kecil */
                    height: 30px;
                }}
                .card-label {{
                    font-size: 0.875rem; /* Ukuran kecil untuk label */
                }}
            }}

            /* Responsif untuk layar sangat kecil */
            @media (max-width: 400px) {{
                .card-value {{
                    font-size: 1.25rem; /* Ukuran paling kecil */
                }}
                .card-label {{
                    font-size: 0.75rem; /* Ukuran kecil untuk label */
                }}
            }}

            </style>

            <body>
            <!-- Navbar -->
            <nav class="navbar navbar-expand-lg bg-body-grenyellow shadow sticky-top">
            <div class="container d-flex">
                <a class="navbar-brand d-flex text-white fw-bold" href="#">
                <img src="https://i.ibb.co.com/1MFsvMq/1731466812700.png" alt="Icon Daarul Qur’an Istiqomah" class="me-2 d-md-block d-none" width="40" height="40">
                <span class="d-md-block d-none h3">
                    PSB Daarul Qur’an Istiqomah
                </span> 
                <span class="d-md-none d-block h3">
                    PSBDQI
                </span> 
                </a>
                <div class="d-flex justify-content-end" id="navbarSupportedContent">
                <div>
                    <!-- Buttons for Pendaftaran and Login -->
                    <a href="/psb" class="btn btn-light ms-2" type="submit">Pendaftaran</a>
                    <a href="/login" class="btn btn-warning ms-2" type="submit">Login</a>
                </div>
                </div>
            </div>
            </nav>
            <!-- Navbar end -->


            <!-- banner -->
            <div class="bg-body-grenyellow rounded-90">
                <div class="container py-3 d-md-flex d-block text-light justify-content-center align-items-center">
                <div class="me-5 w-set-auto d-flex justify-content-center">
                    <img src="https://i.ibb.co.com/1MFsvMq/1731466812700.png" alt="" width="65%">
                </div>
                <div class="ms-md-3 m-0 text-center text-md-start">
                    <h1 class="fw-bold">Pendaftaran Santri Baru</h1>
                    <h3 class="fw-bold pb-3">Pondok Pesantren Daarul Qur’an Istiqomah</h3>
                    <h5 class="fw-bold">Daarul Qur’an Istiqomah Boarding School for Education and Science</h5>
                    <h5 class="fw-bold">Tahun Ajaran 2024 - 2025</h5>
                    <a href="/psb" class="btn btn-light rounded-5 text-primary mt-2">Daftar Sekarang</a>
                </div>
                </div>
            </div>
            <!-- banner end -->

            <!-- Step Pendaftaran -->
            <!-- <div class="container">
                <div class="row shadow rounded mt-5 mb-5 p-5" style="background-color: #EAF1FB;">
                    <div class="col-3 col-sm-3 col-md-3 col-lg-3">
                        <div class="card-item">
                            <span class="card-value" id="count-kuota">0</span>
                            <span class="card-label">Jumlah Kuota</span>
                        </div>
                    </div>
                    <div class="col-3 col-sm-3 col-md-3 col-lg-3">
                        <div class="card-item">
                            <span class="card-value" id="count-pendaftar">0</span>
                            <span class="card-label">Jumlah Pendaftar</span>
                        </div>
                    </div>
                    <div class="col-3 col-sm-3 col-md-3 col-lg-3">
                        <div class="card-item">
                            <span class="card-value" id="count-diterima">0</span>
                            <span class="card-label">Jumlah Diterima</span>
                        </div>
                    </div>
                    <div class="col-3 col-sm-3 col-md-3 col-lg-3">
                        <div class="card-item">
                            <span class="card-value" id="count-sisa">0</span>
                            <span class="card-label">Sisa Kuota</span>
                        </div>
                    </div>
                </div>
            </div> -->
            
            <div class="container text-center my-3">
                <h1 class="fw-bold"><span class="text-green">Alur</span> Pendaftaran Online</h1>
                <div class="container">
                <div class="stepper d-md-flex d-block">
                    <div class="step">
                    <div class="step-circle">1</div>
                    <div class="step-line d-md-block d-none"></div>
                    <p class="mt-3 fw-bold">Pembuatan Akun</p>
                    <p class="text-muted">Mengisi identitas calon peserta didik sekaligus pembuatan akun untuk mendapatkan Nomor
                        Registrasi.</p>
                    </div>
                    <div class="step">
                    <div class="step-circle">2</div>
                    <div class="step-line d-md-block d-none"></div>
                    <p class="mt-3 fw-bold">Login & Melengkapi Data</p>
                    <p class="text-muted">Melengkapi data peserta didik, data orang tua / wali atau mahram khususnya santri putri.
                    </p>
                    </div>
                    <div class="step">
                    <div class="step-circle">3</div>
                    <div class="step-line d-md-block d-none"></div>
                    <p class="mt-3 fw-bold">Mengunggah Berkas</p>
                    <p class="text-muted">Mengunggah berkas persyaratan dan berkas pendukung lainnya yang berupa gambar / foto.
                    </p>
                    </div>
                    <div class="step">
                    <div class="step-circle">4</div>
                    <div class="step-line d-md-block d-none"></div>
                    <p class="mt-3 fw-bold">Pembayaran</p>
                    <p class="text-muted">Melakukan pembayaran biaya pendaftaran sesuai pendidikan yang telah dipilih.</p>
                    </div>
                    <div class="step">
                    <div class="step-circle">5</div>
                    <div class="step-line d-md-block d-none"></div>
                    <p class="mt-3 fw-bold">Cetak Pendaftaran</p>
                    <p class="text-muted">Cetak atau simpan Nomor Registrasi sebagai bukti pendaftaran untuk ditunjukkan ke
                        petugas PSB.</p>
                    </div>
                </div>
                </div>
            </div>
            <!-- End step pendaftaran -->


            <!-- Syarat Pendaftaran -->
            <div class="container my-5">
                <div class="row align-items-center">
                <!-- Text Section -->
                <div class="col-md-6">
                    <h2 class="fw-bold"><span class="text-green ">Syarat</span> Pendaftaran</h2>
                    <p>Untuk memenuhi persyaratan pendaftaran santri baru, perlu beberapa berkas yang harus disiapkan:</p>
                    <ul class="list-unstyled d-grid gap-2">
                    <li class="d-flex"><i class="bi bi-check-circle-fill me-2 text-warning"></i>
                        <div class="d-flex flex-column"><strong>Fotocopy Akta Kelahiran 2lembar</strong> </div>
                    </li>
                    <li class="d-flex"><i class="bi bi-check-circle-fill me-2 text-warning"></i>
                        <div class="d-flex flex-column"><strong>Fotocopy KK 1lembar</strong></div>
                    </li>
                    <li class="d-flex"><i class="bi bi-check-circle-fill me-2 text-warning"></i>
                        <div class="d-flex flex-column"><strong>Fotocopy KTP Orangtua (Masing-masing 1lembar)</strong></div>
                    </li>
                    <li class="d-flex"><i class="bi bi-check-circle-fill me-2 text-warning"></i>
                        <div class="d-flex flex-column"><strong>Fotocopy Raport Semester akhir (menyusul)</strong>
                        </div>
                    </li>
                    <li class="d-flex"><i class="bi bi-check-circle-fill me-2 text-warning"></i>
                        <div class="d-flex flex-column"><strong>Pas Foto berwarna ukuran 3x4 4lembar</strong> </div>
                    </li>
                    <li class="d-flex"><i class="bi bi-check-circle-fill me-2 text-warning"></i>
                        <div class="d-flex flex-column"><strong>Pas Foto Orangtua masing-masing 1lembar (Khusus Pendaftar KB dan TK)</strong> </div>
                    </li>
                    <li class="d-flex"><i class="bi bi-check-circle-fill me-2 text-warning"></i>
                        <div class="d-flex flex-column"><strong>Berkas dimasukkan dalam Map warna hijau dan diberi nama serta lembaga pendidikan</strong> </div>
                    </li>
                    </ul>
                </div>
                <!-- Image Section -->
                <div class="col-md-6">
                    <img src="pesantren_pendaftaran/static/src/img/PAGE2.44b0e259.png" class="img-fluid rounded-4"
                    alt="Syarat Pendaftaran">
                </div>
                </div>
            </div>
            <!-- Syarat Pendaftaran End -->

            <!-- Alur Penyerahan Santri -->
            <div class="container mt-5">
                <h1 class="fw-bold">Alur <span class="text-green">Penyerahan Santri</span></h1>
                <div class="row justify-content-center">
                <!-- Card 1 -->
                <div class="col-md-4 text-center my-2">
                    <div class="card p-4 shadow border-0 h-100">
                    <div class="circle-icon mb-3">
                        <i class="bi bi-plus-circle-fill h1 text-green"></i>
                    </div>
                    <h2 class="step-number">1</h2>
                    <h5 class="font-weight-bold mt-3">Checkup / Periksa Kesehatan</h5>
                    <p>Pemeriksaan kesehatan dari calon peserta didik oleh petugas klinik Az-Zainiyah.</p>
                    <div class="bottom-icon mt-4">
                        <i class="bi bi-shirt text-info"></i>
                    </div>
                    </div>
                </div>
                <!-- Card 2 -->
                <div class="col-md-4 text-center my-2">
                    <div class="card p-4 shadow border-0 h-100">
                    <div class="circle-icon mb-3">
                        <i class="bi bi-file-earmark-text-fill h1 text-green"></i>
                    </div>
                    <h2 class="step-number">2</h2>
                    <h5 class="font-weight-bold mt-3">Konfirmasi Nomor Registrasi</h5>
                    <p>Menyerahkan Nomor Registrasi dan bukti pendaftaran online kepada petugas PSB.</p>
                    <div class="bottom-icon mt-4">
                        <i class="bi bi-handshake text-success"></i>
                    </div>
                    </div>
                </div>
                <!-- Card 3 -->
                <div class="col-md-4 text-center my-2">
                    <div class="card p-4 shadow border-0 h-100">
                    <div class="circle-icon mb-3">
                        <i class="bi bi-person-check-fill h1 text-green"></i>
                    </div>
                    <h2 class="step-number">3</h2>
                    <h5 class="font-weight-bold mt-3">Ikrar Santri</h5>
                    <p>Melakukan Ikrar Santri dan kesediaan mengikuti aturan yang ditetapkan Pondok.
                    </p>
                    </div>
                </div>
                <!-- Card 4 -->
                <div class="col-md-4 text-center my-2">
                    <div class="card p-4 shadow border-0 h-100">
                    <div class="circle-icon mb-3">
                        <i class="bi bi-box-seam-fill h1 text-green"></i>
                    </div>
                    <h2 class="step-number">4</h2>
                    <h5 class="font-weight-bold mt-3">Pengambilan Seragam</h5>
                    <p>Pengambilan seragam sesuai dengan ukuran yang telah dipilih oleh pendaftar. </p>
                    <div class="bottom-icon mt-4">
                        <i class="bi bi-shirt text-info"></i>
                    </div>
                    </div>
                </div>
                <!-- Card 5 -->
                <div class="col-md-4 text-center my-2">
                    <div class="card p-4 shadow border-0 h-100">
                    <div class="circle-icon mb-3">
                        <i class="bi bi-people h1 text-green"></i>
                    </div>
                    <h2 class="step-number">5</h2>
                    <h5 class="font-weight-bold mt-3">Sowan Pengasuh</h5>
                    <p>Penyerahan calon peserta didik oleh orangtua / wali kepada pengasuh </p>
                    <div class="bottom-icon mt-4">
                        <i class="bi bi-handshake text-success"></i>
                    </div>
                    </div>
                </div>
                <!-- Card 6 -->
                <div class="col-md-4 text-center my-2">
                    <div class="card p-4 shadow border-0 h-100">
                    <div class="circle-icon mb-3">
                        <i class="bi bi-buildings h1 text-green"></i>
                    </div>
                    <h2 class="step-number">6</h2>
                    <h5 class="font-weight-bold mt-3">Asrama Santri</h5>
                    <p>Santri baru menempati asrama yang telah ditetepkan oleh pengurus. </p>
                    </div>
                </div>
                </div>
            </div>
            <!-- Alur Penyerahan Santri end-->

            <!-- Informasi Pelayanan Pendaftaran -->
            <div class="container my-5">
                <div class="row align-items-center">
                <div class="col-md-6">
                    <img src="pesantren_pendaftaran/static/src/img/PAGE3.e3b6d704.png" alt="Image" class="rounded-custom img-fluid" />
                </div>
                <div class="col-md-6 col-sm-12">
                    <h3 class="fw-bold"><span class="text-primary ">Informasi</span> Pelayanan Pendaftaran</h3>
                    <div class="accordion" id="accordionExample">
                    <div class="accordion-item mb-3">
                        <h2 class="accordion-header" id="headingOne">
                        <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapseOne"
                            aria-expanded="true" aria-controls="collapseOne">
                            Pembukaan Pendaftaran & Kantor Layanan:
                        </button>
                        </h2>
                        <div id="collapseOne" class="accordion-collapse collapse show" aria-labelledby="headingOne"
                        data-bs-parent="#accordionExample">
                        <div class="accordion-body">
                            <p class="m-0">Tanggal:</p>
                            <p class="fw-bold">1 Maret s.d. 8 Juli 2024</p>
                            <p class="m-0">Layanan Putra:</p>
                            <p class="fw-bold">Kantor Sekretariat Putra</p>
                            <p class="m-0">Layanan Putri:</p>
                            <p class="fw-bold">Kantor Sekretariat Putri</p>
                        </div>
                        </div>
                    </div>
                    <div class="accordion-item mb-3">
                        <h2 class="accordion-header" id="headingTwo">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse"
                            data-bs-target="#collapseTwo" aria-expanded="false" aria-controls="collapseTwo">
                            Verifikasi Berkas:
                        </button>
                        </h2>
                        <div id="collapseTwo" class="accordion-collapse collapse" aria-labelledby="headingTwo"
                        data-bs-parent="#accordionExample">
                        <div class="accordion-body">
                            <!-- Konten untuk Verifikasi Berkas -->
                            <p class="m-0">Tanggal:</p>
                            <p class="fw-bold">{tgl_mulai_pendaftaran_formatted} s.d {tgl_akhir_pendaftaran_formatted}</p>
                            <p class="m-0">Tempat Penerimaan:</p>
                            <p class="fw-bold">Pondok Pesantren Daarul Qur'an Istiqomah, {alamat_lengkap} </p>
                        </div>
                        </div>
                    </div>
                    <div class="accordion-item">
                        <h2 class="accordion-header" id="headingThree">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse"
                            data-bs-target="#collapseThree" aria-expanded="false" aria-controls="collapseThree">
                            Waktu Pelayanan:
                        </button>
                        </h2>
                        <div id="collapseThree" class="accordion-collapse collapse" aria-labelledby="headingThree"
                        data-bs-parent="#accordionExample">
                        <div class="accordion-body">
                            <!-- Konten untuk Waktu Pelayanan -->
                            <p class="m-0">Pagi:</p>
                            <p class="fw-bold">08.00 ~ 12.00 WIB</p>
                            <p class="m-0">Siang:</p>
                            <p class="fw-bold">13.00 ~ 16.00 WIB</p>
                        </div>
                        </div>
                    </div>
                    </div>
                </div>
                </div>
            </div>
            <!-- Informasi Pelayanan Pendaftaran end-->

            <!-- Footer -->
            <footer class="footer py-4">
                <div class="container">
                <div class="row text-white">
                    <div class="col-md-4">
                    <h5>Pondok Pesantren Daarul Qur’an Istiqomah</h5>
                    <p>
                        {alamat_lengkap} <br>
                        Telp. (0888-307-7077)
                    </p>
                    </div>
                    <div class="col-md-4">
                    <h5>Social</h5>
                    <ul class="list-unstyled">
                        <li><a href="https://www.facebook.com/daquistiqomah?mibextid=ZbWKwL" class="text-white"><i class="bi bi-facebook"></i> Facebook</a></li>
                        <li><a href="https://www.instagram.com/dqimedia?igsh=NTVwdWlwd3o5MTF1" class="text-white"><i class="bi bi-instagram"></i> Instagram</a></li>
                        <li><a href="https://youtube.com/@dqimedia?si=6_A8Vr3nysaegI7B" class="text-white"><i class="bi bi-youtube"></i> Youtube</a></li>
                    </ul>
                    </div>
                    <div class="col-md-4">
                    <h5><i class="bi bi-telephone"></i> Pusat Layanan Informasi</h5>
                    <p>
                        0822 5207 9785
                    </p>
                    </div>
                </div>
                <div class="text-center text-white mt-4">
                    <hr class="border-white">
                    <p>©Copyright 2024 - Daarul Qur’an Istiqomah</p>
                </div>
                </div>
            </footer>
            
            <!-- Footer end -->
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"
                integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz"
                crossorigin="anonymous"></>

                <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
                <script>

                // Fungsi easing: Memulai lambat, kemudian cepat (Ease In Out Cubic)
                // function easeInOutCubic(t) {{
                //    return t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1;
                // }}

                // Fungsi untuk animasi menghitung dengan ancang-ancang yang lebih lama
                // function animateCount(elementId) {{
                //    const element = document.getElementById(elementId);
                //    const targetValue = parseInt(element.getAttribute('data-value'), 10);
                //    let currentValue = 0;

                    // Durasi animasi (ms)
                    // const duration = 2500; // Menambah durasi sedikit untuk memberi efek ancang-ancang yang lebih lama
                    // let startTime = null;

                    // Fungsi untuk update angka setiap frame
                    // function updateNumber(currentTime) {{
                    // if (!startTime) startTime = currentTime; // Inisialisasi waktu mulai animasi
                    // let elapsedTime = currentTime - startTime; // Waktu yang telah berlalu
                    // let progress = elapsedTime / duration; // Normalisasi progress waktu antara 0 dan 1

                    // if (progress > 1) progress = 1; // Membatasi progress agar tidak melebihi 1

                    // Membuat animasi "ancang-ancang" yang lebih lama
                    // let easingProgress = easeInOutCubic(progress);
                    // Memberikan sedikit "slow start" di awal untuk memperpanjang transisi awal
                    // let dynamicProgress = progress < 0.4 ? easingProgress * 0.6 : easingProgress; // 40% pertama lebih lambat

                    // Hitung nilai yang akan ditampilkan berdasarkan progress
                    // let increment = Math.floor(targetValue * dynamicProgress);

                    // Update nilai elemen
                    // element.textContent = increment;

                    // Jika progress sudah mencapai 100%, hentikan animasi
                    // if (progress < 1) {{
                    //    requestAnimationFrame(updateNumber);
                    //}}
                    //}}

                    // Mulai animasi dengan requestAnimationFrame
                    //requestAnimationFrame(updateNumber);
                //}}

                // Panggil fungsi untuk setiap elemen setelah halaman dimuat
                // document.addEventListener("DOMContentLoaded", () => {{
                    // animateCount("count-kuota");
                    // animateCount("count-pendaftar");
                    // animateCount("count-diterima");
                    // animateCount("count-sisa");
                //}});

                function easeInOutCubic(t) {{
    return t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1;
}}

function animateCount(elementId, targetValue) {{
    const element = document.getElementById(elementId);
    let currentValue = parseInt(element.textContent, 10) || 0;

    const duration = 2500; // Durasi animasi (ms)
    let startTime = null;

    function updateNumber(currentTime) {{
        if (!startTime) startTime = currentTime;
        const elapsedTime = currentTime - startTime;
        const progress = Math.min(elapsedTime / duration, 1);
        const dynamicValue = currentValue + (targetValue - currentValue) * easeInOutCubic(progress);

        element.textContent = Math.round(dynamicValue);

        if (progress < 1) {{
            requestAnimationFrame(updateNumber);
        }}
    }}

    requestAnimationFrame(updateNumber);
}}




                </script>
            </body>

            </html>
        """
        return request.make_response(html_content, headers=[('Content-Type', 'text/html')])

# class PesantrenPendaftaran(http.Controller):
#     @http.route('/psb', auth='public')
#     def index(self, **kw):

#         # Ambil nilai dari field konfigurasi
#         config_obj = http.request.env['ir.config_parameter'].sudo()

#         tgl_mulai_pendaftaran = config_obj.get_param('pesantren_pendaftaran.tgl_mulai_pendaftaran')
#         tgl_akhir_pendaftaran = config_obj.get_param('pesantren_pendaftaran.tgl_akhir_pendaftaran')
#         tgl_mulai_seleksi = config_obj.get_param('pesantren_pendaftaran.tgl_mulai_seleksi')
#         tgl_akhir_seleksi = config_obj.get_param('pesantren_pendaftaran.tgl_akhir_seleksi')
#         tgl_pengumuman_hasil_seleksi = config_obj.get_param('pesantren_pendaftaran.tgl_pengumuman_hasil_seleksi')
#         is_halaman_pendaftaran = config_obj.get_param('pesantren_pendaftaran.is_halaman_pendaftaran')
#         is_halaman_pengumuman = config_obj.get_param('pesantren_pendaftaran.is_halaman_pengumuman')

#         # Set nilai default dinamis jika parameter kosong
#         if not tgl_mulai_pendaftaran:
#             tgl_mulai_pendaftaran_dt = datetime.datetime.now() + datetime.timedelta(days=1)
#             tgl_mulai_pendaftaran = tgl_mulai_pendaftaran_dt.strftime('%Y-%m-%d %H:%M:%S')
#         else:
#             tgl_mulai_pendaftaran_dt = datetime.datetime.strptime(tgl_mulai_pendaftaran, '%Y-%m-%d %H:%M:%S')

#         if not tgl_akhir_pendaftaran:
#             tgl_akhir_pendaftaran_dt = tgl_mulai_pendaftaran_dt + datetime.timedelta(days=3)
#             tgl_akhir_pendaftaran = tgl_akhir_pendaftaran_dt.strftime('%Y-%m-%d %H:%M:%S')
#         else:
#             tgl_akhir_pendaftaran_dt = datetime.datetime.strptime(tgl_akhir_pendaftaran, '%Y-%m-%d %H:%M:%S')

#         if not tgl_mulai_seleksi:
#             tgl_mulai_seleksi_dt = tgl_akhir_pendaftaran_dt
#             tgl_mulai_seleksi = tgl_mulai_seleksi_dt.strftime('%Y-%m-%d %H:%M:%S')
#         else:
#             tgl_mulai_seleksi_dt = datetime.datetime.strptime(tgl_mulai_seleksi, '%Y-%m-%d %H:%M:%S')

#         if not tgl_akhir_seleksi:
#             tgl_akhir_seleksi_dt = tgl_mulai_seleksi_dt + datetime.timedelta(days=3)
#             tgl_akhir_seleksi = tgl_akhir_seleksi_dt.strftime('%Y-%m-%d %H:%M:%S')
#         else:
#             tgl_akhir_seleksi_dt = datetime.datetime.strptime(tgl_akhir_seleksi, '%Y-%m-%d %H:%M:%S')

#         if not tgl_pengumuman_hasil_seleksi:
#             tgl_pengumuman_hasil_seleksi_dt = tgl_akhir_seleksi_dt + datetime.timedelta(days=2)
#             tgl_pengumuman_hasil_seleksi = tgl_pengumuman_hasil_seleksi_dt.strftime('%Y-%m-%d %H:%M:%S')
#         else:
#             tgl_pengumuman_hasil_seleksi_dt = datetime.datetime.strptime(tgl_pengumuman_hasil_seleksi, '%Y-%m-%d %H:%M:%S')

#         # Format tanggal manual dalam bahasa Indonesia
#         def format_tanggal_manual(dt):
#             bulan_indonesia = [
#                 "Januari", "Februari", "Maret", "April", "Mei", "Juni",
#                 "Juli", "Agustus", "September", "Oktober", "November", "Desember"
#             ]
#             return f"{dt.day} {bulan_indonesia[dt.month - 1]} {dt.year}"

#         # Format tanggal untuk ditampilkan di halaman
#         tgl_mulai_pendaftaran_formatted = format_tanggal_manual(tgl_mulai_pendaftaran_dt)
#         tgl_akhir_pendaftaran_formatted = format_tanggal_manual(tgl_akhir_pendaftaran_dt)
#         tgl_mulai_seleksi_formatted = format_tanggal_manual(tgl_mulai_seleksi_dt)
#         tgl_akhir_seleksi_formatted = format_tanggal_manual(tgl_akhir_seleksi_dt)
#         tgl_pengumuman_hasil_seleksi_formatted = format_tanggal_manual(tgl_pengumuman_hasil_seleksi_dt)


#         html_response = f"""
#             <!DOCTYPE html>
# <html lang="en">
#             <head>
#             <!-- Primary Meta Tags --> 
#             <title>PSB Daarul Qur`an Istiqomah</title> 
#             <meta name="title" content="PSB Daarul Qur`an Istiqomah" /> 
#             <meta name="description" content="Pendaftaran Santri Baru PP Daarul Qur`an Istiqomah Tahun pelajaran 2025-2026 Telah dibuka. segera daftarkan anak anda sekarang" /> 
 
#             <!-- Open Graph / Facebook --> 
#             <meta property="og:type" content="website" /> 
#             <meta property="og:url" content="https://aplikasi.dqi.ac.id/pendaftaran" /> 
#             <meta property="og:title" content="PSB Daarul Qur`an Istiqomah" /> 
#             <meta property="og:description" content="Pendaftaran Santri Baru PP Daarul Qur`an Istiqomah Tahun pelajaran 2025-2026 Telah dibuka. segera daftarkan anak anda sekarang" /> 
#             <meta property="og:image" content="https://drive.usercontent.google.com/download?id=1VZRccbFtq82wTNcReEq43piA_GJQddcm" /> 
 
#             <!-- Twitter --> 
#             <meta property="twitter:card" content="summary_large_image" /> 
#             <meta property="twitter:url" content="https://aplikasi.dqi.ac.id/pendaftaran" /> 
#             <meta property="twitter:title" content="PSB Daarul Qur`an Istiqomah" /> 
#             <meta property="twitter:description" content="Pendaftaran Santri Baru PP Daarul Qur`an Istiqomah Tahun pelajaran 2025-2026 Telah dibuka. segera daftarkan anak anda sekarang" /> 
#             <meta property="twitter:image" content="https://drive.usercontent.google.com/download?id=1VZRccbFtq82wTNcReEq43piA_GJQddcm" />
#                 <meta charset="UTF-8">
#                 <meta name="viewport" content="width=device-width, initial-scale=1.0">
#                 <title>PSB - Daarul Qur'an Istiqomah</title>
#                 <link rel="icon" type="image/x-icon" href="/pesantren_pendaftaran/static/img/favicon.ico?v=1">
#                 <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
#                 <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.6.0/css/all.min.css" integrity="sha512-Kc323vGBEqzTmouAECnVceyQqyqdsSiqLQISBL29aUW4U/M7pSPA/gEUZQqv1cwx4OnYxTxve5UMg5GT6L4JJg==" crossorigin="anonymous" referrerpolicy="no-referrer" />
#                 <link href=" https://cdn.jsdelivr.net/npm/sweetalert2@11.14.5/dist/sweetalert2.min.css " rel="stylesheet">
#                 <style>

#                     body {{
#                         background: linear-gradient(to bottom left, #065c5c 18%, #f5e505 100%) !important;
#                     }}

#                     .offcanvas.offcanvas-end {{
                        
#                         width: 250px; /* Lebar kustom untuk offcanvas */
#                     }}
                    
#                     .offcanvas .nav-link {{
#                         color: #ffffff; /* teks warna putih */
#                     }}
                    
#                     .offcanvas .btn-close {{
#                         position: absolute;
#                         top: 10px;
#                         right: 10px;
#                         filter: invert(1);
#                     }}

#                     .judul {{
#                         height: 81px;
#                         display: flex;
#                         align-items: end;
#                     }}

#                     .teks-judul {{
#                         height: 72px;
#                     }}

#                     .background {{
# 					    background: linear-gradient(to bottom left, #065c5c 18%, #f5e505 100%) !important;
# 					}}

# 					a.effect {{
# 						transition: .1s !important;
# 					}}

# 					a.effect:hover {{
# 						box-shadow: 0 3px 10px rgba(0,0,0,0.2) !important;
# 					}}

#                     /* Desain Dropdown */
#                     .dropdown {{
#                         position: relative;
#                     }}

#                     .dropdown-link {{
#                         cursor: pointer;
#                     }}

#                     .dropdown-content {{
#                         display: none;
#                         position: absolute;
#                         top: 100%;
#                         right: 0;
#                         background-color: #ffffff;
#                         box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
#                         border-radius: 5px;
#                         min-width: 150px;
#                         z-index: 1;
#                         overflow: hidden;
#                     }}

#                     .dropdown-content a {{
#                         color: #333;
#                         padding: 10px 15px;
#                         display: block;
#                         text-decoration: none;
#                         transition: background-color 0.2s;
#                     }}

#                     .dropdown-content a:hover {{
#                         background-color: #f1f1f1;
#                     }}

#                     /* Menampilkan dropdown saat hover */
#                     .dropdown:hover .dropdown-content {{
#                         display: block;
#                         animation: fadeIn 0.3s;
#                     }}

#                     #daftar {{
#                         transition: .3s;
#                     }}

#                     #daftar:hover {{ 
#                         background-color: #f5407d !important;
#                     }}

#                     /* Animasi fade-in */
#                     @keyframes fadeIn {{
#                         from {{
#                         opacity: 0;
#                         transform: translateY(-10px);
#                         }}
#                         to {{
#                         opacity: 1;
#                         transform: translateY(0);
#                         }}
#                     }}

#                 </style>
#             </head>
#             <body>

#             <nav class="navbar navbar-expand-lg" style="height: 65px;">
#                 <div class="container-fluid">
#                     <a class="navbar-brand ms-5 text-white fw-semibold" href="/psb">
#                     	<img src="https://i.ibb.co.com/SmWmBTW/SAVE-20220114-075750-removebg-preview-4.png" alt="1731466812700" width="50" alt="Logo Pesantren">       Daarul Qur'an Istiqomah
#                 	</a>
#                     <button class="navbar-toggler ms-auto" type="button" data-bs-toggle="offcanvas" data-bs-target="#offcanvasNavbar" aria-controls="offcanvasNavbar">
#                         <span class="navbar-toggler-icon"></span>
#                     </button>
#                     <div class="collapse navbar-collapse" id="navbarNav">
#                         <ul class="navbar-nav ms-auto">
#                             <li class="nav-item me-3">
#                                 <a class="nav-link text-white" href="/psb"><i class="fa-solid fa-house me-2"></i>Beranda</a>
#                             </li>
#                             {f'<li class="nav-item me-3">'
#                             f'<a class="nav-link text-white" href="/pendaftaran" {"data-bs-toggle='modal' data-bs-target='#modalPendaftaranTutup'" if not is_halaman_pendaftaran else ""}>'
#                             f'<i class="fa-solid fa-note-sticky me-2"></i>Pendaftaran</a>'
#                             f'</li>'}
#                             <li class="nav-item dropdown">
#                                 <a href="#" class="dropdown-link nav-link"
#                                     style="color: white !important;">
#                                     <i class="fa-solid fa-fingerprint me-2"></i>Login</a>
#                                 <div class="dropdown-content">
#                                     <a href="/login">Login PSB</a>
#                                     <a href="/web/login">Login Orang Tua</a>
#                                 </div>
#                             </li>
#                             <li class="nav-item me-3">
#                                 <a class="nav-link text-white" href="/bantuan"><i class="fa-solid fa-lock me-2"></i>Bantuan</a>
#                             </li>
#                             {f'<li class="nav-item dropdown">'
#                             f'<a href="#" class="dropdown-link nav-link text-white"><i class="fa-solid fa-bullhorn me-2"></i>Pengumuman</a>'
#                             f'<div class="dropdown-content">'
#                             f'<a href="/pengumuman/sd-mi">SD / MI</a>'
#                             f'<a href="/pengumuman/smp-mts">SMP / MTS</a>'
#                             f'<a href="/pengumuman/sma-ma">SMA / MA</a>'
#                             f'</div>'
#                             f'</li>' if is_halaman_pengumuman else ''}
#                         </ul>
#                     </div>
#                 </div>
#             </nav>

#             <div class="offcanvas offcanvas-end background" tabindex="-1" id="offcanvasNavbar" aria-labelledby="offcanvasNavbarLabel">
#                 <button type="button" class="btn-close btn-close-white" data-bs-dismiss="offcanvas" aria-label="Close"></button>
#                 <a class="navbar-brand mt-1 text-white fw-semibold" href="/psb" style="display: flex; flex-direction: column; align-items: center;">
#                     <img src="https://i.ibb.co.com/SmWmBTW/SAVE-20220114-075750-removebg-preview-4.png" alt="1731466812700" width="50" alt="Logo Pesantren">
#                     Daarul Qur'an Istiqomah
#                 </a>
#                 <div class="offcanvas-body">
#                     <ul class="navbar-nav justify-content-end flex-grow-1 pe-3">
#                         <li class="nav-item me-3">
#                             <a class="nav-link text-white" href="/psb"><i class="fa-solid fa-house me-2"></i>Beranda</a>
#                         </li>
#                         {f'<li class="nav-item me-3">'
#                         f'<a class="nav-link text-white" href="/pendaftaran" {"data-bs-toggle='modal' data-bs-target='#modalPendaftaranTutup'" if not is_halaman_pendaftaran else ""}>'
#                         f'<i class="fa-solid fa-note-sticky me-2"></i>Pendaftaran</a>'
#                         f'</li>'}
#                         <li class="nav-item dropdown">
#                             <a href="#" class="dropdown-link nav-link"
#                                 style="color: white !important;">
#                                 <i class="fa-solid fa-fingerprint me-2"></i>Login</a>
#                             <div class="dropdown-content">
#                                 <a href="/login">Login PSB</a>
#                                 <a href="/web/login">Login Orang Tua</a>
#                             </div>
#                         </li>
#                         <li class="nav-item me-3">
#                             <a class="nav-link text-white" href="/bantuan"><i class="fa-solid fa-lock me-2"></i>Bantuan</a>
#                         </li>
#                         {f'<li class="nav-item dropdown">'
#                         f'<a href="#" class="dropdown-link nav-link text-white"><i class="fa-solid fa-bullhorn me-2"></i>Pengumuman</a>'
#                         f'<div class="dropdown-content">'
#                         f'<a href="/pengumuman/sd-mi">SD / MI</a>'
#                         f'<a href="/pengumuman/smp-mts">SMP / MTS</a>'
#                         f'<a href="/pengumuman/sma-ma">SMA / MA</a>'
#                         f'</div>'
#                         f'</li>' if is_halaman_pengumuman else ''}
#                     </ul>
#                 </div>
#             </div>

#             <div style="display: flex; justify-content: center;" class="mt-5">
#                 <div class="text-center text-white">
#                     <h4 class="fs-2 fw-semibold mb-2">Aplikasi penerimaan santri baru</h4>
#                     <span>Daarul Qur'an Istiqomah Tanah Laut Kalimantan Selatan</span> <br><br>
#                     <a href="/pendaftaran" style="background-color: #e91e63; color: white; text-decoration: none; padding: 10px 20px; border-radius: 5px;" class=" id="daftar">Daftar Sekarang</a>
#                 </div>
#             </div>

#             <div class="container mt-5 mb-5">
#                 <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 10px;">
#                     <div class="bg-white shadow-lg rounded p-3" style="width: 270px; display: flex; flex-direction: column; align-items: center; justify-content: space-between;">
#                         <span class="text-uppercase text-secondary mb-3">Program Pendidikan</span>
#                         <div>
#                             <i class="fa-solid fa-graduation-cap fs-1 border rounded-circle p-5" style="color: #e91e63 !important;"></i>
#                         </div>
#                         <span class="text-uppercase text-center fs-3 judul">Jenjang Pendidikan</span>
#                         <div class="text-center mb-4 teks-judul">
#                             <span class="text-secondary" style="font-size: 14px;">1. Paud baby Qu (KB dan TK)</span>
#                             <span class="text-secondary" style="font-size: 14px;">2. SD Tahfizh bilingual</span>
#                             <span class="text-secondary" style="font-size: 14px;">3. SMP Tahfizh bilingual</span>
#                             <span class="text-secondary" style="font-size: 14px;">4. MA Tahfizh bilingual</span>
#                         </div>
#                         <div class="text-uppercase">
#                             <a href="" data-bs-toggle="modal" data-bs-target="#detailProgramPendidikan" class="effect" style="background-color: #9F1FB2 !important; padding: 10px 20px; border-radius: 20px; text-decoration: none; color: white;">Detail</a>
#                         </div>
#                     </div>
#                     <div class="bg-white shadow-lg rounded p-3" style="width: 270px; display: flex; flex-direction: column; align-items: center; justify-content: space-between;">
#                         <span class="text-uppercase text-secondary mb-3">Jadwal Kegiatan</span>
#                         <div>
#                             <i class="fa-regular fa-calendar fs-1 border rounded-circle p-5" style="color: #e91e63 !important;"></i>
#                         </div>
#                         <span class="text-uppercase fs-3 judul">Jadwal Kegiatan</span>
#                         <div class="text-center mb-4 teks-judul">
#                             <span class="text-secondary" style="font-size: 14px;">Jadwal kegiatan PSB dan Kuota Test </span>
#                         </div>
#                         <div class="text-uppercase">
#                             <a href="" data-bs-toggle="modal" data-bs-target="#detailJadwalKegiatan" class="effect" style="background-color: #9F1FB2 !important; padding: 10px 20px; border-radius: 20px; text-decoration: none; color: white;">Detail</a>
#                         </div>
#                     </div>
#                     <div class="bg-white shadow-lg rounded p-3" style="width: 270px; display: flex; flex-direction: column; align-items: center; justify-content: space-between;">
#                         <span class="text-uppercase text-secondary mb-3">Persyaratan</span>
#                         <div>
#                             <i class="fa-solid fa-clipboard-list fs-1 border rounded-circle p-5" style="color: #e91e63 !important;"></i>
#                         </div>
#                         <span class="text-uppercase fs-3 text-center judul">Syarat pendaftaran</span>
#                         <div class="text-center mb-4 teks-judul">
#                             <span class="text-secondary" style="font-size: 14px;">Persyaratan Pendaftaran dapat dilihat disini</span>
#                         </div>
#                         <div class="text-uppercase">
#                             <a href="" data-bs-toggle="modal" data-bs-target="#detailPersyaratan" class="effect" style="background-color: #9F1FB2 !important; padding: 10px 20px; border-radius: 20px; text-decoration: none; color: white;">Detail</a>
#                         </div>
#                     </div>
#                     <div class="bg-white shadow-lg rounded p-3" style="width: 270px; display: flex; flex-direction: column; align-items: center; justify-content: space-between;">
#                         <span class="text-uppercase text-secondary mb-3">Bantuan</span>
#                         <div>
#                             <i class="fa-solid fa-lock fs-1 border rounded-circle p-5" style="color: #e91e63 !important;"></i>
#                         </div>
#                         <span class="text-uppercase fs-3 judul">Hubungi Kami</span>
#                         <div class="text-center mb-4 teks-judul">
#                             <span class="text-secondary" style="font-size: 14px;">Jika memerlukan bantuan : Telp / WA : 0853-9051-1124 </span>
#                         </div>
#                         <div class="text-uppercase">
#                             <a href="/bantuan" class="effect" style="background-color: #9F1FB2 !important; padding: 10px 20px; border-radius: 20px; text-decoration: none; color: white;">Detail</a>
#                         </div>
#                     </div>
#                 </div>
                
#             </div>

#             <footer class="text-white p-2" style="display: flex; justify-content: space-between; flex-wrap: wrap;">
#             	<div class="ms-5">
#             		<ul style="list-style-type: none; display: flex; text-transform: uppercase; font-size: 13px;" class="fw-semibold">
#             			<li><a href="/psb" class="me-4" style="text-decoration: none; color: white;">Home</a></li>
#             			<li><a href="/beranda" class="me-4" style="text-decoration: none; color: white;" target="_blank">Info Pondok</a></li>
#             			<li><a href="https://drive.google.com/drive/mobile/folders/1EYat5411joyoOmH_DkJ3g2DeJKgyyuBQ?usp=share_link&fbclid=IwY2xjawGflGlleHRuA2FlbQIxMQABHTusVv9hD3VRDSLW9-671QhOL86e3KMv30smsAYW0DHkkWf7zwPlcBlbeA_aem_XXofAY-ay0syx043L5BLvw" class="me-4" style="text-decoration: none; color: white;" target="_blank">Brosur</a></li>
#             			<li><a href="" class="me-4" style="text-decoration: none; color: white;">Panduan</a></li>
#             		</ul>
#             	</div>
#             	<div class="me-5">
#             		<p class="text-center mt-1">© 2024 TIM IT PPIB</p>
#             	</div>
#             </footer>


#             <div class="modal fade" id="detailProgramPendidikan" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true">
#             <div class="modal-dialog">
#                 <div class="modal-content">
#                 <div class="modal-header">
#                     <h1 class="modal-title fs-5 text-secondary" id="exampleModalLabel">Pendaftaran Santri Baru</h1>
#                     <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
#                 </div>
# <div class="modal-body">
#                     <div class="row mb-3">
#                         <div class="col-md-8">
#                             <div>
#                                 <span class="fw-semibold">PEMBUKAAN PROGRAM PENDIDIKAN (Putra dan Putri)</span>
#                                 <ul class="text-secondary">                                   
#                                     <li>KB (2 - 3tahun)</li>
#                                     <li>TK ( 4 - 5tahun)</li>
#                                     <li>SD Tahfizh Bilinglual</li>
#                                     <li>SMP Tahfizh bilingual</li>
#                                     <li>MA Tahfizh bilingual</li>
#                                 </ul>
#                             </div>
#                         </div>
#                         <div class="col-md-4">
#                             <img src="https://i.ibb.co.com/wRNC9B0/img1.jpg" alt="Gambar Pondok" width="150"
#                                 class="rounded">
#                         </div>
#                     </div>
#                     <div class="row mb-3">
#                         <div class="col-md-8">
#                             <div>
#                                 <span class="fw-semibold">PELAKSANAAN TEST MASUK</span>
#                                 <p class="text-secondary">Seluruh test dilaksanakan dalam 2 Gelombang <br>
#                                     Test
#                                     dilaksanakan secara OFFLINE</p>
#                             </div>
#                         </div>
#                         <div class="col-md-4">
#                             <img src="https://i.ibb.co.com/hW8F8Qs/img2.jpg" alt="Gambar Pondok" width="150"
#                                 class="rounded">
#                         </div>
#                     </div>
#                     <div class="row mb-3">
#                         <div class="col-md-8">
#                             <div>
#                                 <span class="fw-semibold">MATERI UJIAN SELEKSI</span>
#                                 <ul>
#                                     <li>Membaca Al Qur’an dan Tulis Arab</li>
#                                     <li>Tes wawancara anak dan wawancara orangtua</li>
#                                 </ul>
#                             </div>
#                         </div>
#                         <div class="col-md-4">
#                             <img src="https://i.ibb.co.com/jZznN6Q/img3.jpg" alt="Gambar Pondok" width="150"
#                                 class="rounded">
#                         </div>
#                     </div>
#                 </div>
#                 </div>
#             </div>
#             </div>

# <div class="modal fade" id="detailJadwalKegiatan" tabindex="-1" aria-labelledby="exampleModalLabel"
#         aria-hidden="true">
#         <div class="modal-dialog">
#             <div class="modal-content">
#                 <div class="modal-header">
#                     <h1 class="modal-title fs-5 text-secondary" id="exampleModalLabel">Jadwal Pelaksanaan PSB</h1>
#                     <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
#                 </div>
#                 <div class="modal-body">
#                     <div class="row mb-3">
#                         <div class="col-md-8">
#                             <div>
#                                 <span class="fw-semibold">1. Pendaftaran Online</span>
#                                 <p class="text-secondary">Pendaftaran dilaksanakan pada: <br>
#                                         Gel 1: {tgl_mulai_pendaftaran_formatted} - {tgl_akhir_pendaftaran_formatted} <br>
#                                         Gel 2: {tgl_mulai_pendaftaran_formatted} - {tgl_akhir_pendaftaran_formatted} <br> melalui website <a href="/pendaftaran"
#                                     class="text-decoration-none text-primary">https://aplikasi.dqi.ac.id/psb</a></p>
#                             </div>
#                         </div>
#                         <div class="col-md-4">
#                             <img src="https://i.ibb.co.com/KKKwWG1/img4.jpg" alt="Gambar Pondok" width="150"
#                                 class="rounded">
#                         </div>
#                     </div>
#                     <div class="row mb-3">
#                         <div class="col-md-8">
#                             <div>
#                                 <span class="fw-semibold">2. Pelaksanaan Test Masuk</span>
#                                 <p class="text-secondary">Gel 1: {tgl_mulai_seleksi_formatted} - {tgl_akhir_seleksi_formatted} <br> Gel 2: {tgl_mulai_seleksi_formatted} - {tgl_akhir_seleksi_formatted}</p>
#                             </div>
#                         </div>
#                         <div class="col-md-4">
#                             <img src="https://i.ibb.co.com/s9g5nM2/img5.jpg" alt="Gambar Pondok" width="150"
#                                 class="rounded">
#                         </div>
#                     </div>
#                     <div>
#                         <span class="fw-semibold">4. Pengumuman Hasil Seleksi</span>
#                         <p class="text-secondary">Gel 1: {tgl_pengumuman_hasil_seleksi_formatted} <br>
#                                                 Gel 2: {tgl_pengumuman_hasil_seleksi_formatted}
#                         </p>
#                     </div>
#                     <div>
#                         <p class="text-secondary">Catatan : Seluruh kegiatan akan mengikuti protokol kesehatan sesuai
#                             ketentuan dari pemerintah.</p>
#                     </div>
#                 </div>
#             </div>
#         </div>
#     </div>

#     <div class="modal fade" id="detailPersyaratan" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true">
#         <div class="modal-dialog">
#             <div class="modal-content">
#                 <div class="modal-header">
#                     <h1 class="modal-title fs-5 text-secondary" id="exampleModalLabel">Persyaratan Test Masuk</h1>
#                     <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
#                 </div>
#                 <div class="modal-body">
#                     <div class="row mb-3">
#                         <div class="col-md-12">
#                             <div>
#                                 <span class="fw-semibold">SYARAT UTAMA PENDAFTARAN :</span>
#                                 <ol class="text-secondary">
#                                     <li>Mengisi formulir online secara lengkap dan benar melalui laman https://dqi.ac.id/psb</li>
#                                     <li>Membayar biaya pendaftran untuk program Paud baby Qu KB A & B(usia 2 - 3th) sebesar Rp.350.000</li>
#                                     <li>Membayar biaya pendaftran untuk program TK sebesar Rp.300.000</li>
#                                     <li>Membayar biaya pendaftran untuk program SD Tahfizh bilingual sebesar Rp.300.000</li>
#                                     <li>Membayar biaya pendaftran untuk program SMP Tahfizh bilingual sebesar Rp.300.000</li>
#                                     <li>Membayar biaya pendaftran untuk program MA Tahfizh bilingual sebesar Rp.300.000</li>
#                                     <li>
#                                         Syarat Pendaftaran :
#                                         <ul type="disc" class="text-secondary">
#                                             <li>Fotocopy Akta Kelahiran 2 lembar</li>
#                                             <li>Fotocopy KK 1 lembar</li>
#                                             <li>Fotocopy KTP Orangtua (Masing-masing 1 lembar)</li>
#                                             <li>Fotocopy Raport Semester akhir (menyusul)</li>
#                                             <li>Pas Foto berwarna ukuran 3x4 4lembar</li>
#                                             <li>Pas Foto Orangtua masing-masing 1lembar (Khusus Pendaftar KB dan TK)</li>
#                                             <li>Berkas dimasukkan dalam Map warna hijau dan diberi nama serta lembaga pendidikan</li>
#                                         </ul>
#                                     </li>
#                                 </ol>
#                             </div>
#                         </div>
#                     </div>
#                     <div>
#                         <p class="text-secondary">Seluruh persyaratan yang harus di upload / diunggah ke website
#                             pendaftaran
#                             harus sesuai format yang ditentukan</p>
#                     </div>
#                 </div>
#                 </div>
#             </div>
#             </div>


#                         <!-- Modal -->
#             <div class="modal fade" id="modalPendaftaranTutup" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true">
#             <div class="modal-dialog">
#                 <div class="modal-content">
#                 <div class="modal-header">
#                     <h1 class="modal-title fs-5" id="exampleModalLabel">Pendaftaran ditutup!</h1>
#                     <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
#                 </div>
#                 <div class="modal-body">
#                     <p>Mohon maaf, pendaftaran telah ditutup.</p>
#                 </div>
#                 <div class="modal-footer">
#                     <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Tutup</button>
#                 </div>
#                 </div>
#             </div>
#             </div>



#             <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
#             <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
#             <script src=" https://cdn.jsdelivr.net/npm/sweetalert2@11.14.5/dist/sweetalert2.all.min.js "></script>


#             </body>
#             </html>
#         """
#         return request.make_response(html_response)

class PesantrenPekerjaanKaryawan(http.Controller):
    @http.route('/pekerjaan', auth='public')
    def index(self, **kw):

        job_posts = request.env['hr.job'].search([])  # Ambil semua job posts
        html = ''
        for job in job_posts:
             # Pastikan salary_range dan address_id.name memiliki nilai default jika None
            salary_range = f'<i class="fas fa-coins me-1"></i>{job.salary_range}' if job.salary_range else ''
            location = f'<a href="https://maps.app.goo.gl/LacL72R5as9ivzDC6" target="_blank"><i class="fas fa-map-marker-alt me-1"></i>{job.address_id.name}</a>' if job.address_id else 'Online'

            html += f"""
            <div class="job-card" data-aos="fade-up" data-aos-delay="200">
                <div class="row">
                    <div class="col-11">
                        <h2 class="job-title">{job.name}</h2>
                        <p class="tag tag-recrutment">{job.no_of_recruitment} Kuota Daftar</p>
                        <p class="tag tag-range">{salary_range}</p>
                        <p class="job-location">{location}</p>
                        <p class="job-description">{job.description}</p>
                    </div>
                </div>
            </div>
            """
        
        thn_sekarang = datetime.datetime.now().year
        
        html_response = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Pekerjaan</title>
                <link rel="icon" type="image/x-icon" href="/pesantren_pendaftaran/static/img/favicon.ico?v=1">
                <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.2/css/bootstrap.min.css" rel="stylesheet">
                <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" rel="stylesheet">
                <link href="https://cdnjs.cloudflare.com/ajax/libs/aos/2.3.4/aos.css" rel="stylesheet">
                <link
                    href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Montserrat:wght@700;800;900&display=swap"
                    rel="stylesheet">
                <style>
                    body {{
                        font-family: 'Poppins', sans-serif;
                        overflow-x: hidden;
                    }}
                    /* Navbar Styles */
                    .navbar {{
                        background: linear-gradient(to right, #009688 80%, #ccff33 150%);
                        padding: clamp(0.5rem, 2vw, 1rem);
                        transition: all 0.3s ease;
                    }}

                    .tag.tag-recrutment{{
                        background-color: #d354545c;
                        padding: 2px 5px;
                        width: max-content;
                        border-radius: 5px;
                    }}

                    .navbar-text {{
                        font-size: clamp(1.2rem, 2.5vw, 1.4rem);
                        text-decoration: none;
                        font-weight: 600;
                        color: #fff;
                        font-family: 'Montserrat', sans-serif;
                    }}

                    .navbar-nav .nav-link {{
                        color: #fff;
                        margin-left: 20px;
                        font-weight: 500;
                        position: relative;
                        padding: 5px 0;
                    }}

                    .navbar-nav .nav-link::after {{
                        content: '';
                        position: absolute;
                        width: 0;
                        height: 2px;
                        background-color: #ccff33;
                        bottom: 0;
                        left: 0;
                        transition: width 0.3s ease;
                    }}

                    .navbar-nav .nav-link:hover::after {{
                        width: 100%;
                    }}

                    /* Hero Section */
                    .hero-section {{
                        background: linear-gradient(to right, rgba(0, 150, 136, 0.3) 70%, rgba(204, 255, 51, 0.3) 150%),
                            url('https://cdn.antaranews.com/cache/1200x800/2021/12/07/IMG_0690.jpg');
                        background-size: cover;
                        background-position: center;
                        min-height: 70vh;
                        display: flex;
                        align-items: center;
                        justify-content: left;
                        position: relative;
                        overflow: hidden;
                        border-radius: 0 0 clamp(50px, 10vw, 200px) 0;
                    }}

                    .hero-title {{
                        font-family: 'Montserrat', sans-serif;
                        font-size: clamp(2.5rem, 8vw, 5rem);
                        font-weight: 800;
                        color: #fff;
                        text-shadow: 2px 2px 4px rgba(0, 0, 0, 1);
                    }}

                    .job-card {{
                        background: white;
                        border-radius: 8px;
                        padding: 24px;
                        margin-bottom: 20px;
                        border: 1px solid #e5e7eb;
                        transition: all 0.3s ease;
                    }}

                    .job-card:hover {{
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.6);
                    }}

                    .job-title {{
                        color: #1f2937;
                        font-size: 1.25rem;
                        font-weight: 600;
                        margin-bottom: 8px;
                    }}

                    .job-location {{
                        color: #6b7280;
                        font-size: 0.9rem;
                        margin-bottom: 8px;
                    }}

                    .job-salary {{
                        color: #374151;
                        font-size: 0.9rem;
                        margin-bottom: 16px;
                    }}

                    .job-description {{
                        color: #6b7280;
                        font-size: 0.95rem;
                        margin-bottom: 20px;
                        line-height: 1.6;
                    }}

                    .apply-btn {{
                        background-color: #00ffd5;
                        border: none;
                        width: 40px;
                        height: 40px;
                        border-radius: 8px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        float: right;
                        transition: all 0.3s ease;
                        cursor: pointer;
                    }}

                    .apply-btn:hover {{
                        background-color: #00e6c0;
                    }}

                    .arrow-icon {{
                        color: #000;
                    }}

                    /* FOOTER */
                    .footer {{
                        background-color: #009688;
                        color: white;
                        padding: 20px 0;

                        bottom: 0;
                        width: 100%;
                    }}

                    .footer-text {{
                        color: #ffffff;
                        font-weight: 500;
                    }}

                    .designer-text {{
                        color: #fff;
                        text-align: right;
                    }}
                </style>
            </head>
            <body>

                <nav class="navbar navbar-expand-lg sticky-top">
                    <div class="container">
                        <a class="navbar-text" href="#" data-aos="fade-right">Yayasan DQI</a>
                        <button class="navbar-toggler bg-white" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNavDropdown">
                            <span class="navbar-toggler-icon border-white text-white"></span>
                        </button>
                        <div class="collapse navbar-collapse justify-content-end" id="navbarNavDropdown">
                            <ul class="navbar-nav" data-aos="fade-left">
                                <li class="nav-item">
                                    <a class="nav-link m-0 mt-1 mb-1 mt-md-0 mb-md-0" href="/karyawan">Beranda</a>
                                </li>
                                <li class="nav-item">
                                    <a class="nav-link m-0 mt-1 mb-1 mt-md-0 mb-md-0" href="/tentang">Tentang Kami</a>
                                </li>
                                <li class="nav-item">
                                    <a class="nav-link m-0 mt-1 mb-1 mt-md-0 mb-md-0" href="/pekerjaan">Pekerjaan</a>
                                </li>
                                <li class="nav-item ms-md-3 ms-0 mt-2 mb-2  mt-md-0 mb-md-0">
                                    <a class="btn btn-success" href="/pendaftaran_karyawan">Lamar <i class="fa fa-arrow-right"></i></a>
                                </li>
                            </ul>
                        </div>
                    </div>
                </nav>

                <section class="hero-section">
                    <div class="container">
                        <h1 class="hero-title" data-aos="fade-up" data-aos-delay="100" data-aos-duration="1000">Pekerjaan</h1>
                    </div>
                </section>

                <div class="container my-5 pb-5">
                { html }
                </div>

    <!-- Footer -->
    <footer class="footer py-4">
        <div class="container">
            <div class="row text-white">
                <div class="col-md-4">
                    <h5>Pondok Pesantren Daarul Qur’an Istiqomah</h5>
                    <p><br>
                        Telp. (0888-307-7077)
                    </p>
                </div>
                <div class="col-md-4">

                    <ul class="list-unstyled">
                        <li><a href="https://www.facebook.com/daquistiqomah?mibextid=ZbWKwL" class="text-white"><i
                                    class="bi bi-facebook"></i> Facebook</a></li>
                        <li><a href="https://www.instagram.com/dqimedia?igsh=NTVwdWlwd3o5MTF1" class="text-white"><i
                                    class="bi bi-instagram"></i> Instagram</a></li>
                        <li><a href="https://youtube.com/@dqimedia?si=6_A8Vr3nysaegI7B" class="text-white"><i
                                    class="bi bi-youtube"></i> Youtube</a></li>
                    </ul>
                </div>
                <div class="col-md-4">
                    <h5><i class="bi bi-telephone"></i> Pusat Layanan Informasi</h5>
                    <p>
                        0822 5207 9785
                    </p>
                </div>
            </div>
            <div class="text-center text-white mt-4">
                <hr class="border-white">
                <p>©Copyright {thn_sekarang} - Daarul Qur’an Istiqomah</p>
            </div>
        </div>
    </footer>

                <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.2/js/bootstrap.bundle.min.js"></script>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/aos/2.3.4/aos.js"></script>
                <script>
                    AOS.init({{
                        duration: 800,
                        once: true,
                        mirror: false
                    }});
                </script>
            </body>
            </html>
        """
        return request.make_response(html_response)

class PesantrenTentangKaryawan(http.Controller):
    @http.route('/tentang', auth='public')
    def index(self, **kw):
        
        thn_sekarang = datetime.datetime.now().year
        
        html_response = f"""
            <!DOCTYPE html>
            <html lang="en">

            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Tentang Kami</title>
                <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.2/css/bootstrap.min.css" rel="stylesheet">
                <link href="https://cdnjs.cloudflare.com/ajax/libs/aos/2.3.4/aos.css" rel="stylesheet">
                <link rel="icon" type="image/x-icon" href="/pesantren_pendaftaran/static/img/favicon.ico?v=1">
                <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" rel="stylesheet">
                <link
                    href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Montserrat:wght@700;800;900&display=swap"
                    rel="stylesheet">
                <style>
                    body {{
                        font-family: 'Poppins', sans-serif;
                        overflow-x: hidden;
                    }}

                    /* Navbar Styles */
                    .navbar {{
                        background: linear-gradient(to right, #009688 80%, #ccff33 150%);
                        padding: clamp(0.5rem, 2vw, 1rem);
                        transition: all 0.3s ease;
                    }}

                    .navbar-text {{
                        font-size: clamp(1.2rem, 2.5vw, 1.4rem);
                        text-decoration: none;
                        font-weight: 600;
                        color: #fff;
                        font-family: 'Montserrat', sans-serif;
                    }}

                    .navbar-nav .nav-link {{
                        color: #fff;
                        margin-left: 20px;
                        font-weight: 500;
                        position: relative;
                        padding: 5px 0;
                    }}

                    .navbar-nav .nav-link::after {{
                        content: '';
                        position: absolute;
                        width: 0;
                        height: 2px;
                        background-color: #ccff33;
                        bottom: 0;
                        left: 0;
                        transition: width 0.3s ease;
                    }}

                    .navbar-nav .nav-link:hover::after {{
                        width: 100%;
                    }}

                    .daftar-text {{
                        font-size: clamp(1.2rem, 2.5vw, 1.4rem);
                        text-decoration: none;
                        font-weight: 200;
                        color: #fff;
                        font-family: 'Montserrat', sans-serif;
                    }}

                    .daftar-text .daftar-link {{
                        color: #000000;
                        text-decoration: none;
                        margin-left: 20px;
                        font-weight: 200;
                        position: relative;
                        padding: 5px 0;
                    }}

                    .daftar-text .daftar-link::after {{
                        content: '';
                        position: absolute;
                        width: 0;
                        height: 2px;
                        background-color: #009688;
                        bottom: 0;
                        left: 0;
                        transition: width 0.3s ease;
                    }}

                    .daftar-text .daftar-link:hover::after {{
                        width: 100%;
                    }}

                    /* Hero Section */
                    .hero-section {{
                        background: linear-gradient(to right, rgba(0, 150, 136, 0.3) 70%, rgba(204, 255, 51, 0.3) 150%),
                            url('https://cdn.antaranews.com/cache/1200x800/2021/12/07/IMG_0690.jpg');
                        background-size: cover;
                        background-position: center;
                        min-height: 70vh;
                        display: flex;
                        align-items: center;
                        justify-content: left;
                        position: relative;
                        overflow: hidden;
                        border-radius: 0 0 clamp(50px, 10vw, 200px) 0;
                    }}

                    .hero-title {{
                        font-family: 'Montserrat', sans-serif;
                        font-size: clamp(2.5rem, 8vw, 5rem);
                        font-weight: 800;
                        color: #fff;
                        text-shadow: 2px 2px 4px rgba(0, 0, 0, 1);
                    }}

                    /* Message Section */
                    .message-section {{
                        padding: clamp(3rem, 8vw, 6rem) 0;
                        background-color: #f8f9fa;
                    }}

                    .message-title {{
                        color: #009688;
                        font-size: clamp(0.8rem, 1.5vw, 1rem);
                        font-weight: 600;
                        text-transform: uppercase;
                        margin-bottom: 1.5rem;
                        letter-spacing: 2px;
                    }}

                    .message-heading {{
                        color: #00796b;
                        font-size: clamp(2rem, 4vw, 3rem);
                        font-weight: 700;
                        margin-bottom: clamp(1.5rem, 3vw, 2rem);
                        font-family: 'Montserrat', sans-serif;
                        line-height: 1.2;
                    }}

                    .message-content {{
                        color: #546e7a;
                        line-height: 1.9;
                        font-size: clamp(1rem, 1.5vw, 1.1rem);
                    }}

                    .ceo-image {{
                        border-radius: 30px;
                        width: 100%;
                        height: auto;
                        box-shadow: 20px 20px 60px rgba(0, 150, 136, 0.1);
                        margin-top: clamp(2rem, 5vw, 0);
                    }}

                    /* Team Section */
                    .team-section {{
                        padding: clamp(3rem, 6vw, 5rem) 0;
                        background-color: #fff;
                    }}

                    .team-title {{
                        color: #009688;
                        font-weight: 600;
                        letter-spacing: 2px;
                        font-size: clamp(0.8rem, 1.5vw, 1rem);
                    }}

                    .team-heading {{
                        color: #00796b;
                        font-size: clamp(1.8rem, 4vw, 2.5rem);
                        font-weight: 700;
                        margin-bottom: clamp(2rem, 5vw, 3rem);
                        font-family: 'Montserrat', sans-serif;
                    }}

                    .team-card {{
                        border: none;
                        border-radius: 15px;
                        overflow: hidden;
                        transition: transform 0.3s ease, box-shadow 0.3s ease;
                        margin-bottom: clamp(1.5rem, 3vw, 2rem);
                    }}

                    .team-card:hover {{
                        transform: translateY(-10px);
                        box-shadow: 0 10px 30px rgba(0, 150, 136, 0.1);
                    }}

                    .team-card img {{
                        height: clamp(180px, 30vw, 200px);
                        object-fit: cover;
                        width: 100%;
                    }}

                    .team-card .card-body {{
                        padding: clamp(1rem, 2vw, 1.5rem);
                    }}

                    .team-card .card-title {{
                        color: #00796b;
                        font-size: clamp(1.1rem, 1.8vw, 1.3rem);
                        margin-bottom: 5px;
                        font-family: 'Montserrat', sans-serif;
                    }}

                    .team-card .card-text {{
                        font-size: clamp(0.8rem, 1.2vw, 0.9rem);
                        color: #009688;
                    }}

                    /* Responsive Container Padding */
                    @media (max-width: 768px) {{
                        .container {{
                            padding-left: clamp(1rem, 4vw, 2rem);
                            padding-right: clamp(1rem, 4vw, 2rem);
                        }}

                        .message-section .col-lg-7 {{
                            padding-right: 15px !important;
                            margin-bottom: 2rem;
                        }}
                    }}

                    /* Dropdown Styles */
                    .dropdown-menu {{
                        background-color: #fff;
                        border: none;
                        border-radius: 10px;
                        box-shadow: 0 10px 30px rgba(0, 150, 136, 0.1);
                    }}

                    .dropdown-item {{
                        color: #00796b;
                        font-weight: 500;
                        padding: clamp(8px, 1.5vw, 10px) clamp(15px, 2vw, 20px);
                        font-size: clamp(0.9rem, 1.2vw, 1rem);
                    }}

                    /* footer */
                    .contact-section {{
                        background-color: #ffffff;
                    }}

                    .contact-title {{
                        color: #00796b;
                        font-weight: bold;
                        font-size: 2.5rem;
                        margin-bottom: 20px;
                    }}

                    .contact-text {{
                        color: rgb(107, 114, 128);
                        margin-bottom: 30px;
                        max-width: 400px;
                    }}

                    .form-control {{
                        border-radius: 8px;
                        padding: 12px;
                        margin-bottom: 20px;
                        border: 1px solid #e5e7eb;
                    }}

                    .submit-btn {{
                        background-color: #00ffd5;
                        border: none;
                        padding: 12px 30px;
                        border-radius: 8px;
                        color: bl;
                        font-weight: 500;
                        transition: all 0.3s ease;
                    }}

                    .submit-btn:hover {{
                        background-color: #00e6c0;
                    }}

                    .footer {{
                        background-color: #009688;
                        color: white;
                        padding: 20px 0;

                        bottom: 0;
                        width: 100%;
                    }}

                    .footer-text {{
                        color: #ffffff;
                        font-weight: 500;
                    }}

                    .designer-text {{
                        color: #fff;
                        text-align: right;
                    }}
                </style>
            </head>

            <body>
                <!-- Rest of the HTML remains the same -->
                <nav class="navbar navbar-expand-lg sticky-top">
                    <div class="container">
                        <a class="navbar-text" href="#" data-aos="fade-right">Yayasan DQI</a>
                        <button class="navbar-toggler bg-white" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNavDropdown">
                            <span class="navbar-toggler-icon border-white text-white"></span>
                        </button>
                        <div class="collapse navbar-collapse justify-content-end" id="navbarNavDropdown">
                            <ul class="navbar-nav" data-aos="fade-left">
                                <li class="nav-item">
                                    <a class="nav-link m-0 mt-1 mb-1 mt-md-0 mb-md-0" href="/karyawan">Beranda</a>
                                </li>
                                <li class="nav-item">
                                    <a class="nav-link m-0 mt-1 mb-1 mt-md-0 mb-md-0" href="/tentang">Tentang Kami</a>
                                </li>
                                <li class="nav-item">
                                    <a class="nav-link m-0 mt-1 mb-1 mt-md-0 mb-md-0" href="/pekerjaan">Pekerjaan</a>
                                </li>
                                <li class="nav-item ms-md-3 ms-0 mt-2 mb-2  mt-md-0 mb-md-0">
                                    <a class="btn btn-success" href="/pendaftaran_karyawan">Lamar <i class="fa fa-arrow-right"></i></a>
                                </li>
                            </ul>
                        </div>
                    </div>
                </nav>

                <section class="hero-section">
                    <div class="container">
                        <h1 class="hero-title" data-aos="fade-up" data-aos-delay="100" data-aos-duration="1000">TENTANG KAMI</h1>
                    </div>
                </section>

                <section class="message-section">
                    <div class="container">
                        <div class="row align-items-center">
                            <div class="col-lg-7 pe-5" data-aos="fade-right" data-aos-duration="1000">
                                <div class="message-title">PESAN DARI PONPES</div>
                                <h2 class="message-heading">Kami Membuka<br>Lowongan Pekerjaan</h2>
                                <div class="job-opening">
                                    <h2>Bergabunglah Bersama Pesantren DQI!</h2>
                                    <p>Pesantren DQI membuka kesempatan bagi Anda untuk bergabung sebagai:</p>
                                    <ul>
                                        <li><strong>Guru:</strong> Membimbing siswa dengan pendekatan islami.</li>
                                        <li><strong>Tenaga Kesehatan:</strong> Mendukung kesehatan santri.</li>
                                        <li><strong>Petugas Keamanan:</strong> Menjaga lingkungan yang aman.</li>
                                        <li><strong>Musyrif/Musyrifah:</strong> Membimbing kehidupan sehari-hari santri.</li>
                                        <li><strong>Ustadz/Ustadzah:</strong> Mengajar ilmu agama dan akhlak mulia.</li>
                                    </ul>
                                    <p>Jadilah bagian dari keluarga besar Pesantren DQI! Hubungi kami untuk informasi lebih lanjut.
                                    </p>
                                </div>

                                <p class="fw-bold mt-4">Daarul Qur'an Istiqomah<br>Tanah Laut</p>
                            </div>
                            <div class="col-lg-5" data-aos="fade-left" data-aos-duration="1000">
                                <img src="https://th.bing.com/th/id/OIP.13ebyAjdUwL3ZKQeVLYD6QHaE8?rs=1&pid=ImgDetMain"
                                    alt="CEO Portrait" class="ceo-image">
                            </div>
                        </div>
                    </div>
                </section>

                <section class="team-section mb-5">
                    <div class="container text-center">
                        <p class="team-title" data-aos="fade-up">TIM KAMI</p>
                        <h2 class="team-heading" data-aos="fade-up" data-aos-delay="100">Kami Adalah Pengurs Ponpes DQI</h2>
                        <div class="row g-4">
                            <!-- Team cards remain the same -->
                            <div class="col-md-4 col-sm-6" data-aos="fade-up" data-aos-delay="100">
                                <div class="team-card">
                                    <img src="https://via.placeholder.com/450" alt="Emil Yancy">
                                    <div class="card-body">
                                        <h5 class="card-title">Emil Yancy</h5>
                                        <p class="card-text">Team Leader</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4 col-sm-6" data-aos="fade-up" data-aos-delay="200">
                                <div class="team-card">
                                    <img src="https://via.placeholder.com/450" alt="Emil Yancy">
                                    <div class="card-body">
                                        <h5 class="card-title">Emil Yancy</h5>
                                        <p class="card-text">Team Leader</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4 col-sm-6" data-aos="fade-up" data-aos-delay="300">
                                <div class="team-card">
                                    <img src="https://via.placeholder.com/450" alt="Emil Yancy">
                                    <div class="card-body">
                                        <h5 class="card-title">Emil Yancy</h5>
                                        <p class="card-text">Team Leader</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4 col-sm-6" data-aos="fade-up" data-aos-delay="100">
                                <div class="team-card">
                                    <img src="https://via.placeholder.com/450" alt="Emil Yancy">
                                    <div class="card-body">
                                        <h5 class="card-title">Emil Yancy</h5>
                                        <p class="card-text">Team Leader</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4 col-sm-6" data-aos="fade-up" data-aos-delay="200">
                                <div class="team-card">
                                    <img src="https://via.placeholder.com/450" alt="Emil Yancy">
                                    <div class="card-body">
                                        <h5 class="card-title">Emil Yancy</h5>
                                        <p class="card-text">Team Leader</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4 col-sm-6" data-aos="fade-up" data-aos-delay="300">
                                <div class="team-card">
                                    <img src="https://via.placeholder.com/450" alt="Emil Yancy">
                                    <div class="card-body">
                                        <h5 class="card-title">Emil Yancy</h5>
                                        <p class="card-text">Team Leader</p>
                                    </div>
                                </div>
                            </div>
                            <!-- Repeat for other team members -->
                        </div>
                    </div>
                </section>

    <!-- Footer -->
    <footer class="footer py-4">
        <div class="container">
            <div class="row text-white">
                <div class="col-md-4">
                    <h5>Pondok Pesantren Daarul Qur’an Istiqomah</h5>
                    <p><br>
                        Telp. (0888-307-7077)
                    </p>
                </div>
                <div class="col-md-4">

                    <ul class="list-unstyled">
                        <li><a href="https://www.facebook.com/daquistiqomah?mibextid=ZbWKwL" class="text-white"><i
                                    class="bi bi-facebook"></i> Facebook</a></li>
                        <li><a href="https://www.instagram.com/dqimedia?igsh=NTVwdWlwd3o5MTF1" class="text-white"><i
                                    class="bi bi-instagram"></i> Instagram</a></li>
                        <li><a href="https://youtube.com/@dqimedia?si=6_A8Vr3nysaegI7B" class="text-white"><i
                                    class="bi bi-youtube"></i> Youtube</a></li>
                    </ul>
                </div>
                <div class="col-md-4">
                    <h5><i class="bi bi-telephone"></i> Pusat Layanan Informasi</h5>
                    <p>
                        0822 5207 9785
                    </p>
                </div>
            </div>
            <div class="text-center text-white mt-4">
                <hr class="border-white">
                <p>©Copyright {thn_sekarang} - Daarul Qur’an Istiqomah</p>
            </div>
        </div>
    </footer>

                <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.2/js/bootstrap.bundle.min.js"></script>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/aos/2.3.4/aos.js"></script>
                <script>
                    AOS.init({{
                        duration: 800,
                        once: true,
                        mirror: false
                    }});
                </script>
            </body>

            </html>
        """
        return request.make_response(html_response)
    
    
class PesantrenBerandaKaryawan(http.Controller):
    @http.route('/karyawan', auth='public')
    def index(self, **kw):
        
        thn_sekarang = datetime.datetime.now().year
        
        html_response = f"""
            <!doctype html>
            <html lang="en">

            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>Daarul Qur'an Istiqomah</title>
                <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.2/css/bootstrap.min.css" rel="stylesheet">
                <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" rel="stylesheet">
                <link href="https://cdnjs.cloudflare.com/ajax/libs/aos/2.3.4/aos.css" rel="stylesheet">
                <link rel="icon" type="image/x-icon" href="/pesantren_pendaftaran/static/img/favicon.ico?v=1">
                <link
                    href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Montserrat:wght@700;800;900&display=swap"
                    rel="stylesheet">
                <link rel="stylesheet" href="style.css">
            </head>
            <style>
                .recruitment-hero {{
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin-bottom: 3rem;
                }}

                .recruitment-hero .hero-text {{
                    max-width: 100%;
                }}

                .recruitment-hero .hero-image img {{
                    border-radius: 10px;
                    max-width: 100%;
                    height: auto;
                }}

                .recruitment-card {{
                    text-align: center;
                    background-color: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 10px;
                    padding: 1.5rem;
                    transition: transform 0.2s;
                    cursor: pointer;
                }}

                .recruitment-card:hover {{
                    transform: scale(1.05);
                }}

                .recruitment-card i {{
                    font-size: 2rem;
                    color: #20c997;
                    margin-bottom: 0.5rem;
                }}

                body {{
                    font-family: 'Poppins', sans-serif;
                    overflow-x: hidden;
                }}

                /* Navbar Styles */
                .navbar {{
                    background: linear-gradient(to right, #009688 80%, #ccff33 150%);
                    padding: clamp(0.5rem, 2vw, 1rem);
                    transition: all 0.3s ease;
                }}

                .navbar-text {{
                    font-size: clamp(1.2rem, 2.5vw, 1.4rem);
                    text-decoration: none;
                    font-weight: 600;
                    color: #fff;
                    font-family: 'Montserrat', sans-serif;
                }}

                .navbar-nav .nav-link {{
                    color: #fff;
                    margin-left: 20px;
                    font-weight: 500;
                    position: relative;
                    padding: 5px 0;
                }}

                .navbar-nav .nav-link::after {{
                    content: '';
                    position: absolute;
                    width: 0;
                    height: 2px;
                    background-color: #ccff33;
                    bottom: 0;
                    left: 0;
                    transition: width 0.3s ease;
                }}

                .navbar-nav .nav-link:hover::after {{
                    width: 100%;
                }}

                /* Hero Section */
                .hero-section {{
                    background: linear-gradient(to right, rgba(0, 150, 136, 0.3) 70%, rgba(204, 255, 51, 0.3) 150%),
                        url('https://cdn.antaranews.com/cache/1200x800/2021/12/07/IMG_0690.jpg');
                    background-size: cover;
                    background-position: center;
                    min-height: 70vh;
                    display: flex;
                    align-items: center;
                    justify-content: left;
                    position: relative;
                    overflow: hidden;
                    border-radius: 0 0 clamp(50px, 10vw, 200px) 0;
                }}

                .hero-title {{
                    font-family: 'Montserrat', sans-serif;
                    font-size: clamp(2.5rem, 8vw, 5rem);
                    font-weight: 800;
                    color: #fff;
                    text-shadow: 2px 2px 4px rgba(0, 0, 0, 1);
                }}

                .title {{
                    max-width: 5rem;
                    font-size: 3rem;
                    font-family: 'Archivo Black', sans-serif;
                }}

                .font {{
                    font-family: 'Archivo Black', sans-serif;
                }}

                .c1 {{
                    color: #32FFCE;
                }}

                .b1 {{
                    background-color: #32FFCE;
                }}

                .banner {{
                    position: relative;
                    /* Tambahkan ini agar ::before bisa mengacu ke .banner */
                    height: 30rem;
                    background-image: url('https://cdn.antaranews.com/cache/1200x800/2021/12/07/IMG_0690.jpg');
                    background-position: center;
                    background-repeat: no-repeat;
                    background-size: cover;
                }}

                .banner::before {{
                    content: "";
                    /* Tambahkan konten kosong untuk menampilkan pseudo-elemen */
                    background-color: #18581894;
                    /* Gunakan transparansi untuk overlay */
                    position: absolute;
                    /* Perbaiki posisi agar sesuai dengan elemen induk */
                    top: 0;
                    left: 0;
                    z-index: 1;
                    /* Pastikan pseudo-elemen berada di bawah elemen lainnya */
                    width: 100%;
                    height: 100%;
                }}

                .daftar-text {{
                    font-size: clamp(1.2rem, 2.5vw, 1.4rem);
                    text-decoration: none;
                    font-weight: 200;
                    color: #fff;
                    font-family: 'Montserrat', sans-serif;
                }}

                .daftar-text .daftar-link {{
                    color: #000000;
                    text-decoration: none;
                    margin-left: 20px;
                    font-weight: 200;
                    position: relative;
                    padding: 5px 0;
                }}

                .daftar-text .daftar-link::after {{
                    content: '';
                    position: absolute;
                    width: 0;
                    height: 2px;
                    background-color: #009688;
                    bottom: 0;
                    left: 0;
                    transition: width 0.3s ease;
                }}

                .daftar-text .daftar-link:hover::after {{
                    width: 100%;
                }}

                .banner .container {{
                    z-index: 2;
                }}

                .l1 {{
                    max-width: 25rem;
                }}

                .col-md-6 img {{
                    max-width: 70%;
                }}

                .contact-section {{
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    background-color: #fff;
                }}

                .contact-container {{
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    max-width: 1200px;
                    width: 100%;
                    padding: 20px;
                }}

                .contact-info {{
                    max-width: 50%;
                }}

                .contact-info h1 {{
                    font-size: 2.5rem;
                    font-weight: bold;
                    margin-bottom: 20px;
                }}

                .contact-info p {{
                    color: #6c757d;
                    line-height: 1.6;
                }}

                .form-section {{
                    max-width: 40%;
                    width: 100%;
                    background-color: #f8f9fa;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}

                .form-control {{
                    margin-bottom: 20px;
                    padding: 15px;
                    font-size: 1rem;
                }}

                .submit-btn {{
                    background-color: #20c997;
                    border: none;
                    color: white;
                    padding: 10px 20px;
                    font-size: 1rem;
                    border-radius: 5px;
                    cursor: pointer;
                    width: 100%;
                }}

                .submit-btn:hover {{
                    background-color: #17a889;
                }}

                /* footer */
                .contact-section {{
                    background-color: #ffffff;
                }}

                .contact-title {{
                    color: #00796b;
                    font-weight: bold;
                    font-size: 2.5rem;
                    margin-bottom: 20px;
                }}

                .contact-text {{
                    color: rgb(107, 114, 128);
                    margin-bottom: 30px;
                    max-width: 400px;
                }}

                .form-control {{
                    border-radius: 8px;
                    padding: 12px;
                    margin-bottom: 20px;
                    border: 1px solid #e5e7eb;
                }}

                .submit-btn {{
                    background-color: #00ffd5;
                    border: none;
                    padding: 12px 30px;
                    border-radius: 8px;
                    color: bl;
                    font-weight: 500;
                    transition: all 0.3s ease;
                }}

                .submit-btn:hover {{
                    background-color: #00e6c0;
                }}

                .footer {{
                    background-color: #009688;
                    color: white;
                    padding: 20px 0;
                    bottom: 0;
                    width: 100%;
                }}

                .footer-text {{
                    color: #ffffff;
                    font-weight: 500;
                }}

                .designer-text {{
                    color: #fff;
                    text-align: right;
                }}
            </style>

            <body>
                <nav class="navbar navbar-expand-lg sticky-top">
                    <div class="container">
                        <a class="navbar-text" href="#" data-aos="fade-right">Yayasan DQI</a>
                        <button class="navbar-toggler bg-white" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNavDropdown">
                            <span class="navbar-toggler-icon border-white text-white"></span>
                        </button>
                        <div class="collapse navbar-collapse justify-content-end" id="navbarNavDropdown">
                            <ul class="navbar-nav" data-aos="fade-left">
                                <li class="nav-item">
                                    <a class="nav-link m-0 mt-1 mb-1 mt-md-0 mb-md-0" href="/karyawan">Beranda</a>
                                </li>
                                <li class="nav-item">
                                    <a class="nav-link m-0 mt-1 mb-1 mt-md-0 mb-md-0" href="/tentang">Tentang Kami</a>
                                </li>
                                <li class="nav-item">
                                    <a class="nav-link m-0 mt-1 mb-1 mt-md-0 mb-md-0" href="/pekerjaan">Pekerjaan</a>
                                </li>
                                <li class="nav-item ms-md-3 ms-0 mt-2 mb-2 mt-md-0 mb-md-0">
                                    <a class="btn btn-success" href="/pendaftaran_karyawan">Lamar <i class="fa fa-arrow-right"></i></a>
                                </li>
                            </ul>
                        </div>
                    </div>
                </nav>

                            <section class="hero-section">
                                <div class="container">
                                    <h1 class="hero-title" data-aos="fade-up" data-aos-delay="100" data-aos-duration="1000">Perekrutan</h1>
                                </div>
                            </section>
                            <div class="container py-5 px-5">
                                <section class="recruitment-hero row">
                                    <div class="hero-text col-lg-6 mb-3 mb-lg-0 text-center text-lg-start" data-aos="fade-right">
                                        <h5 class="text-uppercase text-success fw-bold">Perekrutan</h5>
                                        <h1>Lamar Bekerja Pada Yayasan DQI</h1>
                                        <p>Bergabunglah bersama kami dan jadilah bagian dari keluarga besar Pesantren DQI. Kami mencari individu yang berdedikasi, berintegritas, dan siap berkontribusi untuk mencetak generasi yang unggul dan berakhlak mulia.</p>
                                    </div>
                                    <div class="hero-image col-lg-6" data-aos="fade-left">
                                        <img src="https://via.placeholder.com/500" alt="Hero Image">
                                    </div>
                                </section>

                    <section class="container">
                        <h5 class="text-uppercase text-center text-success fw-bold" data-aos="fade-up">Perekrutan</h5>
                        <h2 class="text-center" data-aos="fade-up">Jenis Pekerjaan Yang Dibuka Untuk Bekerja Di Yayasan Da'arul Istiqomah</h2>
                        <div class="row mt-4 g-4 d-flex justify-content-center">
                            <div class="col-lg-4 col-md-6" data-aos="fade-up">
                                <div class="recruitment-card">
                                    <i class="fas fa-user"></i>
                                    <h5>Ustadz</h5>
                                    <p>Perekrutan ustaz bertujuan untuk menjaring pendidik berkualitas yang mampu membimbing santri dalam aspek akademik dan
                                    spiritual sesuai nilai-nilai pesantren.</p>
                                </div>
                            </div>
                            <div class="col-lg-4 col-md-6" data-aos="fade-up">
                                <div class="recruitment-card">
                                    <i class="fas fa-users"></i>
                                    <h5>Musyrif</h5>
                                    <p>Perekrutan musyrif bertujuan untuk memilih pendamping santri yang memiliki kompetensi, akhlak mulia, dan dedikasi dalam
                                    mendukung kehidupan pesantren.</p>
                                </div>
                            </div>
                            <div class="col-lg-4 col-md-6" data-aos="fade-up">
                                <div class="recruitment-card">
                                    <i class="fas fa-heart"></i>
                                    <h5>Kesehatan</h5>
                                    <p>Perekrutan tenaga kesehatan di pesantren dilakukan untuk memastikan pelayanan kesehatan santri berjalan optimal dengan
                                    tenaga profesional yang kompeten.</p>
                                </div>
                            </div>
                            <div class="col-lg-4 col-md-6" data-aos="fade-up">
                                <div class="recruitment-card">
                                    <i class="fas fa-shield-alt"></i>
                                    <h5>Keamanan</h5>
                                    <p>Perekrutan tenaga keamanan di pesantren bertujuan untuk menjaga keamanan, ketertiban, dan kenyamanan lingkungan
                                    pesantren.</p>
                                </div>
                            </div>
                            <div class="col-lg-4 col-md-6" data-aos="fade-up">
                                <div class="recruitment-card">
                                    <i class="fas fa-graduation-cap"></i>
                                    <h5>Guru</h5>
                                    <p>Perekrutan guru adalah proses seleksi untuk menemukan dan menempatkan tenaga pendidik yang berkualitas sesuai kebutuhan
                                    lembaga pendidikan.</p>
                                </div>
                            </div>
                        </div>
                    </section>
                </div>

                <footer class="footer py-4">
                    <div class="container">
                        <div class="row text-white">
                            <div class="col-md-4">
                                <h5>Pondok Pesantren Daarul Qur’an Istiqomah</h5>
                                <p><br>
                                    Telp. (0888-307-7077)
                                </p>
                            </div>
                            <div class="col-md-4">

                                <ul class="list-unstyled">
                                    <li><a href="https://www.facebook.com/daquistiqomah?mibextid=ZbWKwL" class="text-white"><i
                                                class="bi bi-facebook"></i> Facebook</a></li>
                                    <li><a href="https://www.instagram.com/dqimedia?igsh=NTVwdWlwd3o5MTF1" class="text-white"><i
                                                class="bi bi-instagram"></i> Instagram</a></li>
                                    <li><a href="https://youtube.com/@dqimedia?si=6_A8Vr3nysaegI7B" class="text-white"><i
                                                class="bi bi-youtube"></i> Youtube</a></li>
                                </ul>
                            </div>
                            <div class="col-md-4">
                                <h5><i class="bi bi-telephone"></i> Pusat Layanan Informasi</h5>
                                <p>
                                    0822 5207 9785
                                </p>
                            </div>
                        </div>
                        <div class="text-center text-white mt-4">
                            <hr class="border-white">
                            <p>©Copyright {thn_sekarang} - Daarul Qur’an Istiqomah</p>
                        </div>
                    </div>
                </footer>
                <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js" crossorigin="anonymous"></script>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/aos/2.3.4/aos.js"></script>
                <script>
                    AOS.init({{
                        duration: 800,
                        once: true,
                        mirror: false
                    }});
                </script>
            </body>

            </html>
        """
        return request.make_response(html_response)

class UbigKaryawanController(http.Controller):
    @http.route('/pendaftaran_karyawan', type='http', auth='public')
    def pendaftaran_karyawan_form(self, **kwargs):

        job_id_list = request.env['hr.job'].sudo().search([('name', '!=', 'Kepala Kepesantrenan')])
        gelar_list = request.env['hr.recruitment.degree'].sudo().search([])
        category_list = request.env['hr.applicant.category'].sudo().search([])
        skill_types = request.env['hr.skill.type'].sudo().search([])
        skills = request.env['hr.skill'].sudo().search([])

        # Mengelompokkan skill berdasarkan skill_id
        skills_by_type = {}
        skills_dict = {}

        # Mengelompokkan skill berdasarkan skill_type
        for skill_type in skill_types:
            skills_by_type[skill_type.id] = {
                'id': skill_type.id,
                'name': skill_type.name,
                'skills': [{'id': skill.id, 'skill_type_id': skill.skill_type_id.id, 'name': skill.name} for skill in skills if skill.skill_type_id.id == skill_type.id]
            }

        # Convert skills_by_type to a serializable format
        serializable_skills = {}
        for skill_type_id, data in skills_by_type.items():
            serializable_skills[skill_type_id] = {
                'id': data['id'],
                'name': data['name'],
                'skills': data['skills']
            }


        # Menyimpan skill berdasarkan id dan name
        for skill in skills:
            skills_dict[skill.id] = {'id': skill.id, 'name': skill.name}


        # Log untuk memeriksa hasil
        _logger.info("Skills by type: %s", skills_by_type)
        _logger.info("Skills dict: %s", skills_dict)

        return request.render('pesantren_karyawan.pendaftaran_karyawan_form_template', {
            'job_id_list': job_id_list,
            'gelar_list': gelar_list,
            'category_list': category_list,
            'skill_types': skill_types,
            'skills_by_type': skills_by_type,  # Menambahkan data ini
        })

    
    @http.route('/pendaftaran_karyawan/submit', type='http', auth='public', methods=['POST'], csrf=True)
    def pendaftaran_karyawan_submit(self, **post):

        def verify_recaptcha(response_token):
            secret_key = '6LfoWrIqAAAAADQdz3rMzi5QSJu_Zv9pZ-B5XW2H'

            payload = {
                'secret': secret_key,
                'response': response_token,
            }

            # Kirim permintaan ke API Google reCAPTCHA
            verify_url = 'https://www.google.com/recaptcha/api/siteverify'
            response = requests.post(verify_url, data=payload)
            result = response.json()

            # Kembalikan status verifikasi
            return result.get('success')
        
        # Ambil token reCAPTCHA dari form
        recaptcha_response_token = post.get('g-recaptcha-response')

        # if not recaptcha_response_token:
            # raise UserError("reCAPTCHA tidak terisi. Silakan coba lagi.")

        # Verifikasi token reCAPTCHA
        # if not verify_recaptcha(recaptcha_response_token):
        #     raise UserError("Verifikasi reCAPTCHA gagal. Silakan coba lagi.")
            
        # Ambil data dari form
        name                   = post.get('name')
        email_kantor           = post.get('email_kantor')
        no_ktp                 = post.get('no_ktp')
        no_telp                = post.get('no_telp')
        tgl_lahir_str          = request.params.get('tgl_lahir')
        # Mengonversi format tanggal dd/mm/yyyy menjadi date
        tgl_lahir              = datetime.datetime.strptime(tgl_lahir_str, '%d/%m/%Y').date()
        alamat                 = post.get('alamat')
        tmp_lahir              = post.get('tmp_lahir')
        gender                 = request.params.get('gender')
        lembaga                = request.params.get('lembaga')
        job_id                 = request.params.get('job_id')
        profil_linkedin        = post.get('profile_linkedin')
        gelar                  = request.params.get('gelar')
        selected_categories    = [key for key in post.keys() if key.startswith('category_')]
        category_ids           = [int(key.split('_')[1]) for key in selected_categories]

        # Data Berkas
        # Ambil file dari request
        uploaded_files = request.httprequest.files

        # Ambil setiap file, konversi ke Base64, dan proses
        cv                      = uploaded_files.get('cv')
        ktp                     = uploaded_files.get('ktp')
        npwp                    = uploaded_files.get('npwp')
        ijazah                  = uploaded_files.get('ijazah')
        pas_foto                = uploaded_files.get('pas_foto')
        sertifikat              = uploaded_files.get('sertifikat')
        surat_pengalaman        = uploaded_files.get('surat_pengalaman')
        surat_kesehatan         = uploaded_files.get('surat_kesehatan')

        # Fungsi bantu untuk memproses file
        def process_file(file):
            if file:
                # Baca file dan konversi ke Base64
                file_content = file.read()
                file_base64 = base64.b64encode(file_content)
                return file_base64
            return None

        # Konversi file yang diunggah
        cv_b64 = process_file(cv)
        ktp_b64 = process_file(ktp)
        npwp_b64 = process_file(npwp)
        ijazah_b64 = process_file(ijazah)
        pas_foto_b64 = process_file(pas_foto)
        sertifikat_b64 = process_file(sertifikat)
        surat_pengalaman_b64 = process_file(surat_pengalaman)
        surat_kesehatan_b64 = process_file(surat_kesehatan)

        partner_vals = {
            'name'  : name,
            'email' : email_kantor,  # Asumsi field email ada di model Pendaftaran
            'phone' : no_telp,
        }
        
        # Membuat data partner
        partner = request.env['res.partner'].sudo().create(partner_vals)

        if partner:
            # Buat record di hr.candidate
            candidate = request.env['hr.candidate'].sudo().create({
                'partner_name'          : name,
                'email_from'            : email_kantor,
                'partner_id'            : partner.id,
                'partner_phone'         : no_telp,
                'no_ktp'                : no_ktp,
                'lembaga'               : lembaga,
                'tgl_lahir'             : tgl_lahir,
                'job_id'                : int(job_id),
                'tmp_lahir'             : tmp_lahir,
                'gender'                : gender,
                'alamat'                : alamat,
                'linkedin_profile'      : profil_linkedin,
                'type_id'               : gelar,
                # 'categ_ids'             : [(6, 0, category_ids)],  # Gunakan command (6, 0, ids) untuk Many2many
                
                # Data Berkas
                'cv'                     : cv_b64 if cv_b64 else False,
                'ktp'                    : ktp_b64 if ktp_b64 else False,
                'npwp'                   : npwp_b64 if npwp_b64 else False,
                'ijazah'                 : ijazah_b64 if ijazah_b64 else False,
                'pas_foto'               : pas_foto_b64 if pas_foto_b64 else False,
                'sertifikat'             : sertifikat_b64 if sertifikat_b64 else False,
                'surat_kesehatan'        : surat_kesehatan_b64 if surat_kesehatan_b64 else False,
                'surat_pengalaman'       : surat_pengalaman_b64 if surat_pengalaman_b64 else False,
            })

            if candidate:
                data_vals = {
                    'candidate_id'          : candidate.id,
                    'job_id'                : int(job_id),
                    'partner_name'          : name,
                    'email_from'            : email_kantor,
                    'partner_id'            : partner.id,
                    'partner_phone'         : no_telp,
                    'no_ktp'                : no_ktp,
                    'lembaga'               : lembaga,
                    'tgl_lahir'             : tgl_lahir,
                    'tmp_lahir'             : tmp_lahir,
                    'gender'                : gender,
                    'alamat'                : alamat,
                    'linkedin_profile'      : profil_linkedin,
                    'type_id'               : gelar,
                    # 'categ_ids'             : [(6, 0, category_ids)],  # Gunakan command (6, 0, ids) untuk Many2many
                    
                    # Data Berkas
                    'cv'                     : cv_b64 if cv_b64 else False,
                    'ktp'                    : ktp_b64 if ktp_b64 else False,
                    'npwp'                   : npwp_b64 if npwp_b64 else False,
                    'ijazah'                 : ijazah_b64 if ijazah_b64 else False,
                    'pas_foto'               : pas_foto_b64 if pas_foto_b64 else False,
                    'sertifikat'             : sertifikat_b64 if sertifikat_b64 else False,
                    'surat_kesehatan'        : surat_kesehatan_b64 if surat_kesehatan_b64 else False,
                    'surat_pengalaman'       : surat_pengalaman_b64 if surat_pengalaman_b64 else False,
                }
                request.env['hr.applicant'].sudo().create(data_vals)


        # Simpan data ke model ubig.karyawan
        # pendaftaran = request.env['ubig.karyawan'].sudo().create({
        #     # 'kode_akses'             : kode_akses,
        #     'name'                   : name,
        #     'email_kantor'           : email_kantor,
        #     'no_ktp'                 : no_ktp,
        #     'no_telp'                : no_telp,
        #     'tgl_lahir'              : tgl_lahir,
        #     'alamat'                 : alamat,
        #     'tmp_lahir'              : tmp_lahir,
        #     'gender'                 : gender,
        #     'lembaga'                : lembaga,
        #     'job_id'                 : job_id,

        #     # Data Berkas
        #     'cv'                     : cv_b64 if cv_b64 else False,
        #     'ktp'                    : ktp_b64 if ktp_b64 else False,
        #     'npwp'                   : npwp_b64 if npwp_b64 else False,
        #     'ijazah'                 : ijazah_b64 if ijazah_b64 else False,
        #     'pas_foto'               : pas_foto_b64 if pas_foto_b64 else False,
        #     'sertifikat'             : sertifikat_b64 if sertifikat_b64 else False,
        #     'surat_kesehatan'        : surat_kesehatan_b64 if surat_kesehatan_b64 else False,
        #     'surat_pengalaman'       : surat_pengalaman_b64 if surat_pengalaman_b64 else False,
        #     'state'                  : 'draft'  # set status awal menjadi 'terdaftar'
        # })

        token = candidate.token

        # Redirect ke halaman sukses atau halaman lain yang diinginkan
        return request.redirect(f'/pendaftaran_karyawan/success?token={token}')
    
    @http.route('/pendaftaran_karyawan/success', type='http', auth='public')
    def pendaftaran_karyawan_success(self, token=None, **kwargs):

        Pendaftaran = request.env['hr.applicant']

        # Menangkap Token pendaftaran dari URL
        token = request.params.get('token')

        if not token:
            return request.not_found()

        # Cari pendaftaran berdasarkan token
        pendaftaran = Pendaftaran.sudo().search([('token', '=', token)], limit=1)
        if not pendaftaran:
            return request.not_found()

        # Kirim email
        if pendaftaran.email_from:
            thn_sekarang = datetime.datetime.now().year
            email_values = {
                'subject': "Informasi Pendaftaran Karyawan Pesantren Daarul Qur'an Istiqomah",
                'email_to': pendaftaran.email_from,
                'body_html': f'''
                    <div style="background-color: #d9eaf7; padding: 20px; font-family: Arial, sans-serif;">
                        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden;">
                            <!-- Header -->
                            <div style="background-color: #0066cc; color: #ffffff; text-align: center; padding: 20px;">
                                <h1 style="margin: 0; font-size: 24px;">Pesantren Daarul Qur'an Istiqomah</h1>
                            </div>
                            <!-- Body -->
                            <div style="padding: 20px; color: #555555;">
                                <p style="margin: 0 0 10px;">Assalamualaikum Wr. Wb,</p>
                                <p style="margin: 0 0 20px;">
                                    Bapak/Ibu <strong>{pendaftaran.partner_name}</strong>,<br>
                                    Terima kasih anda telah melamar di pesantren kami. Berikut adalah informasi data pendaftaran anda:
                                </p>
                                <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">

                                    <h3>Data Pendaftaran Karyawan</h3>
                                    <table style="width: 100%; border-collapse: collapse;">
                                        <tr>
                                            <td style="padding: 8px; font-weight: bold; color: #333333;">Nama :</td>
                                            <td style="padding: 8px; color: #555555;">{pendaftaran.partner_name}</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px; font-weight: bold; color: #333333;">TTL :</td>
                                            <td style="padding: 8px; color: #555555;">{pendaftaran.tmp_lahir}, {pendaftaran.get_formatted_tanggal_lahir()}</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px; font-weight: bold; color: #333333;">Alamat :</td>
                                            <td style="padding: 8px; color: #555555;">{pendaftaran.alamat}</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px; font-weight: bold; color: #333333;">Lembaga :</td>
                                            <td style="padding: 8px; color: #555555;">{pendaftaran.lembaga.replace('paud', 'PAUD').replace('tk', 'TK').replace('sd', 'SD').replace('smpmts', 'SMP / MTS').replace('smama', 'SMA / MA').replace('smk', 'SMK')}</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px; font-weight: bold; color: #333333;">Jabatan Kerja :</td>
                                            <td style="padding: 8px; color: #555555;">{pendaftaran.job_id.name}</td>
                                        </tr>
                                    </table>

                                </div>
                                <p style="margin: 20px 0;">
                                    Apabila terdapat kesulitan atau membutuhkan bantuan, silakan hubungi tim teknis kami melalui nomor:
                                </p>
                                <ul style="margin: 0; padding-left: 20px; color: #555555;">
                                    <li>0822 5207 9785</li>
                                    <li>0853 9051 1124</li>
                                </ul>
                                <p style="margin: 20px 0;">
                                    Kami berharap portal ini dapat membantu Bapak/Ibu memantau perkembangan putra/putri selama berada di pesantren.
                                </p>
                            </div>
                            <!-- Footer -->
                            <div style="background-color: #f1f1f1; text-align: center; padding: 10px;">
                                <p style="font-size: 12px; color: #888888; margin: 0;">
                                    &copy; {thn_sekarang} Pesantren Tahfizh Daarul Qur'an Istiqomah. All rights reserved.
                                </p>
                            </div>
                        </div>
                    </div>
                ''',
            }

            mail = request.env['mail.mail'].sudo().create(email_values)
            mail.send()

        return request.render('pesantren_karyawan.pendaftaran_karyawan_success_template', {
            'pendaftaran': pendaftaran,
        })


