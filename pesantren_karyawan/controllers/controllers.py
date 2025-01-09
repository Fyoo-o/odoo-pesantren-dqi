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
        html_response = f"""
        
        """
        return request.make_response(html_response)

class PesantrenPekerjaanKaryawan(http.Controller):
    @http.route('/pekerjaan', auth='public')
    def index(self, **kw):
        
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
                        <a class="navbar-text" href="#" data-aos="fade-right">Pesantren DQI</a>
                        <button class="navbar-toggler bg-white" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNavDropdown">
                            <span class="navbar-toggler-icon border-white text-white"></span>
                        </button>
                        <div class="collapse navbar-collapse justify-content-end" id="navbarNavDropdown">
                            <ul class="navbar-nav" data-aos="fade-left">
                                <li class="nav-item">
                                    <a class="nav-link m-0 mt-1 mb-1 mt-md-0 mb-md-0" href="/beranda_karyawan">Beranda</a>
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
                    <!-- Guru -->
                    <div class="job-card" data-aos="fade-up" data-aos-delay="100">
                        <div class="row">
                            <div class="col-11">
                                <h2 class="job-title">Guru</h2>
                                <p class="job-location">Kalimantan, Indonesia</p>
                                <p class="job-salary">Rp5.000.000 - Rp8.000.000 per bulan</p>
                                <p class="job-description">
                                    Mencari guru berpengalaman dengan minimal 3 tahun mengajar. Bertanggung jawab untuk mengembangkan kurikulum, 
                                    memberikan pembelajaran yang efektif, dan membimbing siswa dalam pengembangan akademik dan karakter. 
                                    Kualifikasi: S1 Pendidikan, mampu menggunakan teknologi pembelajaran modern, dan memiliki sertifikasi guru.
                                </p>
                            </div>
                        </div>
                    </div>

                    <!-- Kesehatan -->
                    <div class="job-card" data-aos="fade-up" data-aos-delay="200">
                        <div class="row">
                            <div class="col-11">
                                <h2 class="job-title">Petugas Kesehatan</h2>
                                <p class="job-location">Kalimantan, Indonesia</p>
                                <p class="job-description">
                                    Dibutuhkan tenaga kesehatan untuk unit kesehatan sekolah. Bertanggung jawab atas pemeriksaan kesehatan rutin, 
                                    penanganan pertolongan pertama, dan edukasi kesehatan kepada siswa. Kualifikasi: D3/S1 Keperawatan, 
                                    memiliki STR aktif, dan pengalaman minimal 2 tahun di bidang kesehatan.
                                </p>
                            </div>
                        </div>
                    </div>

                    <!-- Keamanan -->
                    <div class="job-card" data-aos="fade-up" data-aos-delay="300">
                        <div class="row">
                            <div class="col-11">
                                <h2 class="job-title">Petugas Keamanan</h2>
                                <p class="job-location">Kalimantan, Indonesia</p>
                                <p class="job-description">
                                    Mencari petugas keamanan profesional untuk menjaga keamanan lingkungan sekolah. Bertanggung jawab atas 
                                    pengawasan CCTV, patroli rutin, dan penanganan situasi darurat. Kualifikasi: Minimal SMA/SMK, 
                                    memiliki sertifikat Gada Pratama, dan pengalaman minimal 2 tahun sebagai security.
                                </p>
                            </div>
                        </div>
                    </div>

                    <!-- Musyrif -->
                    <div class="job-card" data-aos="fade-up" data-aos-delay="400">
                        <div class="row">
                            <div class="col-11">
                                <h2 class="job-title">Musyrif</h2>
                                <p class="job-location">Kalimantan, Indonesia</p>
                                <p class="job-description">
                                    Dibutuhkan Musyrif untuk asrama santri. Bertanggung jawab membimbing dan mengawasi kegiatan santri, 
                                    memastikan kedisiplinan, dan membina akhlak santri. Kualifikasi: Minimal S1 dari perguruan tinggi Islam, 
                                    hafal minimal 5 juz Al-Quran, dan memiliki pengalaman sebagai pembimbing asrama.
                                </p>
                            </div>
                        </div>
                    </div>

                    <!-- Ustadz -->
                    <div class="job-card" data-aos="fade-up" data-aos-delay="500">
                        <div class="row">
                            <div class="col-11">
                                <h2 class="job-title">Ustadz</h2>
                                <p class="job-location">Kalimantan, Indonesia</p>
                                <p class="job-description">
                                    Mencari Ustadz untuk mengajar ilmu agama Islam. Bertanggung jawab memberikan pengajaran Al-Quran, 
                                    Hadist, Fiqih, dan materi keislaman lainnya. Kualifikasi: S1/S2 Syariah atau Ushuluddin, 
                                    hafal minimal 10 juz Al-Quran, dan memiliki pengalaman mengajar minimal 3 tahun di pesantren.
                                </p>
                            </div>
                        </div>
                    </div>
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
                        <a class="navbar-text" href="#" data-aos="fade-right">Pesantren DQI</a>
                        <button class="navbar-toggler bg-white" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNavDropdown">
                            <span class="navbar-toggler-icon border-white text-white"></span>
                        </button>
                        <div class="collapse navbar-collapse justify-content-end" id="navbarNavDropdown">
                            <ul class="navbar-nav" data-aos="fade-left">
                                <li class="nav-item">
                                    <a class="nav-link m-0 mt-1 mb-1 mt-md-0 mb-md-0" href="/beranda_karyawan">Beranda</a>
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
    @http.route('/beranda_karyawan', auth='public')
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
                        <a class="navbar-text" href="#" data-aos="fade-right">Pesantren DQI</a>
                        <button class="navbar-toggler bg-white" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNavDropdown">
                            <span class="navbar-toggler-icon border-white text-white"></span>
                        </button>
                        <div class="collapse navbar-collapse justify-content-end" id="navbarNavDropdown">
                            <ul class="navbar-nav" data-aos="fade-left">
                                <li class="nav-item">
                                    <a class="nav-link m-0 mt-1 mb-1 mt-md-0 mb-md-0" href="/beranda_karyawan">Beranda</a>
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
                                        <h1>Lamar Bekerja Pada Pesantren DQI</h1>
                                        <p>Bergabunglah bersama kami dan jadilah bagian dari keluarga besar Pesantren DQI. Kami mencari individu yang berdedikasi, berintegritas, dan siap berkontribusi untuk mencetak generasi yang unggul dan berakhlak mulia.</p>
                                    </div>
                                    <div class="hero-image col-lg-6" data-aos="fade-left">
                                        <img src="https://via.placeholder.com/500" alt="Hero Image">
                                    </div>
                                </section>

                    <section class="container">
                        <h5 class="text-uppercase text-center text-success fw-bold" data-aos="fade-up">Perekrutan</h5>
                        <h2 class="text-center" data-aos="fade-up">Jenis Pekerjaan Yang Dibuka Untuk Bekerja Di Pesantren Da'arul Istiqomah</h2>
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

        if not recaptcha_response_token:
            raise UserError("reCAPTCHA tidak terisi. Silakan coba lagi.")

        # Verifikasi token reCAPTCHA
        if not verify_recaptcha(recaptcha_response_token):
            raise UserError("Verifikasi reCAPTCHA gagal. Silakan coba lagi.")
            
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


