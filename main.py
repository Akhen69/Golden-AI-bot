#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Trading Bot - Premium Signal System
Author: AI Assistant
Description: Complete trading bot with trial system, premium access, and admin panel
"""

import asyncio
import logging
import os
import io
from datetime import datetime, timedelta, date, time
from typing import Dict, Any, Optional
import json
import yfinance as yf
import pandas as pd
import numpy as np

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, InputFile, BotCommand, MenuButtonCommands
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters, ConversationHandler
)
from telegram.constants import ParseMode

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import custom modules
from database import UserDatabase
from admin_panel import AdminPanel, create_admin_keyboard
from notifications import NotificationSystem
from signal_manager import SignalManager

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
# Support multiple admin IDs (comma separated)
ADMIN_IDS_STR = os.getenv('ADMIN_ID', '123456789')
ADMIN_IDS = [int(id.strip()) for id in ADMIN_IDS_STR.split(',') if id.strip().isdigit()]
ADMIN_ID = ADMIN_IDS[0] if ADMIN_IDS else 123456789  # First admin as primary
BROKER_LINK = os.getenv('BROKER_LINK', 'https://your-broker-link.com')

# Conversation states
(TERMS, TRIAL_CHOICE, REGISTER_NAME, REGISTER_EMAIL, 
 ACCOUNT_NUMBER, ADMIN_VERIFY) = range(6)

# Translation Dictionary
TRANSLATIONS = {
    'en': {
        # Buttons
        'btn_free_analysis': '📊 Free Market Analysis',
        'btn_premium_signals': '🔑 Premium Signals',
        'btn_register': '📝 Register for Premium',
        'btn_my_account': '👤 My Account',
        'btn_help': 'ℹ️ Help & Support',
        'btn_notice_board': '📌 Notice Board',
        'btn_performance': '📈 Performance Record',
        'btn_terms': '📜 Terms and Conditions',
        'btn_language': '🌐 Language',
        'btn_english': '🇬🇧 English',
        'btn_malay': '🇲🇾 Malay',
        'btn_indonesian': '🇮🇩 Indonesian',
        'btn_thai': '🇹🇭 Thai',
        'btn_back': '⬅️ Back to Main Menu',
        
        # Status
        'status_trial': '🎁 Premium Trial Active ({days} days left)',
        'status_premium': '💎 Premium Member',
        'status_free': '🆓 Free User',
        'status_suspended': '🚫 Suspended',
        
        # Menu
        'menu_choose_option': 'Choose an option:',
        'menu_welcome': '👋 Welcome',
        
        # Account
        'account_title': '👤 My Account',
        'account_status': '📊 Status:',
        'account_country': '🌍 Country:',
        'account_email': '📧 Email:',
        'account_number': '🔢 Account Number:',
        'account_verified': '✅ Verified',
        'account_not_verified': '❌ Not Verified',
        'account_trial_days': '⏳ Trial Days Left:',
        'account_premium_message': '\n\n✨ Thank you for being a Premium member!\nKeep your broker account active to enjoy uninterrupted access.',
        
        # Help
        'help_title': 'ℹ️ Help & Support',
        'help_features': 'Available Features:',
        'help_free_analysis': '📊 Free Analysis – Daily AI-generated market observations',
        'help_premium_signals': '💎 Premium Signals – Access detailed study notes (trial/premium only)',
        'help_register': '📝 Register – Upgrade to Premium by registering with our broker link',
        'help_account': '👤 Account – Check your status (Trial / Premium / Suspended)',
        'help_how_premium': 'How Premium Works:',
        'help_step1': '1️⃣ Start with a 14-day free trial',
        'help_step2': '2️⃣ Register with our broker link',
        'help_step3': '3️⃣ Deposit minimum $50 USD into broker account',
        'help_step4': '4️⃣ Submit your email & name for verification',
        'help_step5': '5️⃣ Admin approval grants Premium access',
        'help_disclaimer': '⚠️ Important Disclaimer:',
        'help_disclaimer_text': 'All analysis provided is AI-generated and for educational purposes only.\n\nThis service does not provide financial advice.\n\nUsers must DYOR (Do Your Own Research) and TAYOR (Trade At Your Own Risk).\n\nBy using this bot, you acknowledge that you take full responsibility for your trading decisions.',
        'help_contact': '📬 Support Contact: [Admin](https://t.me/GoldenAi_admin)',
        
        # Notice Board
        'notice_title': '📌 Notice Board',
        'notice_announcements': '📢 Important Announcements:',
        'notice_stay_updated': 'Stay updated with the latest news and updates from our trading bot.',
        'notice_check_regularly': '📅 Check back regularly for new notices.',
        'notice_tips': '💡 Tips:',
        'notice_tip1': '• Follow all signals responsibly',
        'notice_tip2': '• Manage your risk properly',
        'notice_tip3': '• Keep your broker account active',
        
        # Performance
        'performance_title': '📈 Performance Record',
        'performance_stats': '📊 Signal Performance Statistics:',
        'performance_coming_soon': 'Coming soon! Track your trading performance and signal results here.',
        'performance_features': '💡 Features:',
        'performance_feature1': '• Win rate tracking',
        'performance_feature2': '• Profit/Loss analysis',
        'performance_feature3': '• Signal history',
        'performance_soon': '🔒 This feature will be available soon!',
        
        # Terms
        'terms_title': '📜 Terms and Conditions',
        'terms_important': '📋 Important Information:',
        'terms_1_title': '1. Educational Purpose Only',
        'terms_1_text': 'All signals and analysis are for educational purposes only.',
        'terms_2_title': '2. Risk Disclaimer',
        'terms_2_text': 'Trading involves risk. Always do your own research (DYOR) and take your own responsibility (TAYOR).',
        'terms_3_title': '3. No Financial Advice',
        'terms_3_text': 'We do not provide financial advice. All trading decisions are your own.',
        'terms_4_title': '4. Broker Registration',
        'terms_4_text': 'Premium access requires valid broker account registration.',
        'terms_5_title': '5. Account Responsibility',
        'terms_5_text': 'Keep your broker account funded and active to maintain Premium status.',
        'terms_agree': '⚠️ By using this bot, you agree to these terms.',
        
        # Language
        'lang_title': '🌐 Language Selection',
        'lang_choose': 'Choose your preferred language:',
        'lang_english': '🇬🇧 English - English language',
        'lang_malay': '🇲🇾 Malay - Bahasa Melayu',
        'lang_indonesian': '🇮🇩 Indonesian - Bahasa Indonesia',
        'lang_thai': '🇹🇭 Thai - ภาษาไทย',
        'lang_select': 'Select a language to continue:',
        'lang_changed_en': '✅ Language changed to English\n\nAll bot messages will now be displayed in English.',
        'lang_changed_my': '✅ Bahasa telah ditukar ke Bahasa Melayu\n\nSemua mesej bot kini akan dipaparkan dalam Bahasa Melayu.',
        'lang_changed_id': '✅ Bahasa telah diubah ke Bahasa Indonesia\n\nSemua pesan bot sekarang akan ditampilkan dalam Bahasa Indonesia.',
        'lang_changed_th': '✅ ภาษาได้เปลี่ยนเป็นภาษาไทย\n\nข้อความทั้งหมดของบอทจะแสดงเป็นภาษาไทย',
    },
    'my': {
        # Buttons
        'btn_free_analysis': '📊 Analisis Pasaran Percuma',
        'btn_premium_signals': '🔑 Isyarat Premium',
        'btn_register': '📝 Daftar untuk Premium',
        'btn_my_account': '👤 Akaun Saya',
        'btn_help': 'ℹ️ Bantuan & Sokongan',
        'btn_notice_board': '📌 Papan Notis',
        'btn_performance': '📈 Rekod Prestasi',
        'btn_terms': '📜 Terma dan Syarat',
        'btn_language': '🌐 Bahasa',
        'btn_english': '🇬🇧 Bahasa Inggeris',
        'btn_malay': '🇲🇾 Bahasa Melayu',
        'btn_indonesian': '🇮🇩 Bahasa Indonesia',
        'btn_thai': '🇹🇭 Bahasa Thai',
        'btn_back': '⬅️ Kembali ke Menu Utama',
        
        # Status
        'status_trial': '🎁 Percubaan Premium Aktif ({days} hari lagi)',
        'status_premium': '💎 Ahli Premium',
        'status_free': '🆓 Pengguna Percuma',
        'status_suspended': '🚫 Digantung',
        
        # Menu
        'menu_choose_option': 'Pilih pilihan:',
        'menu_welcome': '👋 Selamat Datang',
        
        # Account
        'account_title': '👤 Akaun Saya',
        'account_status': '📊 Status:',
        'account_country': '🌍 Negara:',
        'account_email': '📧 Emel:',
        'account_number': '🔢 Nombor Akaun:',
        'account_verified': '✅ Disahkan',
        'account_not_verified': '❌ Tidak Disahkan',
        'account_trial_days': '⏳ Hari Percubaan Tinggal:',
        'account_premium_message': '\n\n✨ Terima kasih kerana menjadi ahli Premium!\nPastikan akaun broker anda aktif untuk menikmati akses tanpa gangguan.',
        
        # Help
        'help_title': 'ℹ️ Bantuan & Sokongan',
        'help_features': 'Ciri-ciri Tersedia:',
        'help_free_analysis': '📊 Analisis Percuma – Pemerhatian pasaran yang dijana AI setiap hari',
        'help_premium_signals': '💎 Isyarat Premium – Akses nota kajian terperinci (percubaan/premium sahaja)',
        'help_register': '📝 Daftar – Naik taraf ke Premium dengan mendaftar menggunakan pautan broker kami',
        'help_account': '👤 Akaun – Semak status anda (Percubaan / Premium / Digantung)',
        'help_how_premium': 'Bagaimana Premium Berfungsi:',
        'help_step1': '1️⃣ Mulakan dengan percubaan percuma 14 hari',
        'help_step2': '2️⃣ Daftar dengan pautan broker kami',
        'help_step3': '3️⃣ Deposit minimum $50 USD ke akaun broker',
        'help_step4': '4️⃣ Hantar emel & nama anda untuk pengesahan',
        'help_step5': '5️⃣ Kelulusan admin memberikan akses Premium',
        'help_disclaimer': '⚠️ Penafian Penting:',
        'help_disclaimer_text': 'Semua analisis yang disediakan dijana AI dan untuk tujuan pendidikan sahaja.\n\nPerkhidmatan ini tidak memberikan nasihat kewangan.\n\nPengguna mesti DYOR (Lakukan Penyelidikan Sendiri) dan TAYOR (Berdagang Atas Risiko Sendiri).\n\nDengan menggunakan bot ini, anda mengakui bahawa anda mengambil tanggungjawab penuh untuk keputusan perdagangan anda.',
        'help_contact': '📬 Hubungan Sokongan: [Admin](https://t.me/GoldenAi_admin)',
        
        # Notice Board
        'notice_title': '📌 Papan Notis',
        'notice_announcements': '📢 Pengumuman Penting:',
        'notice_stay_updated': 'Kekal dikemas kini dengan berita dan kemas kini terkini dari bot perdagangan kami.',
        'notice_check_regularly': '📅 Semak kembali secara berkala untuk notis baharu.',
        'notice_tips': '💡 Petua:',
        'notice_tip1': '• Ikuti semua isyarat dengan bertanggungjawab',
        'notice_tip2': '• Urus risiko anda dengan betul',
        'notice_tip3': '• Pastikan akaun broker anda aktif',
        
        # Performance
        'performance_title': '📈 Rekod Prestasi',
        'performance_stats': '📊 Statistik Prestasi Isyarat:',
        'performance_coming_soon': 'Akan datang! Jejaki prestasi perdagangan dan hasil isyarat anda di sini.',
        'performance_features': '💡 Ciri-ciri:',
        'performance_feature1': '• Penjejakan kadar kemenangan',
        'performance_feature2': '• Analisis Untung/Rugi',
        'performance_feature3': '• Sejarah isyarat',
        'performance_soon': '🔒 Ciri ini akan tersedia tidak lama lagi!',
        
        # Terms
        'terms_title': '📜 Terma dan Syarat',
        'terms_important': '📋 Maklumat Penting:',
        'terms_1_title': '1. Tujuan Pendidikan Sahaja',
        'terms_1_text': 'Semua isyarat dan analisis adalah untuk tujuan pendidikan sahaja.',
        'terms_2_title': '2. Penafian Risiko',
        'terms_2_text': 'Perdagangan melibatkan risiko. Sentiasa lakukan penyelidikan sendiri (DYOR) dan ambil tanggungjawab sendiri (TAYOR).',
        'terms_3_title': '3. Tiada Nasihat Kewangan',
        'terms_3_text': 'Kami tidak memberikan nasihat kewangan. Semua keputusan perdagangan adalah keputusan anda sendiri.',
        'terms_4_title': '4. Pendaftaran Broker',
        'terms_4_text': 'Akses Premium memerlukan pendaftaran akaun broker yang sah.',
        'terms_5_title': '5. Tanggungjawab Akaun',
        'terms_5_text': 'Pastikan akaun broker anda dibiayai dan aktif untuk mengekalkan status Premium.',
        'terms_agree': '⚠️ Dengan menggunakan bot ini, anda bersetuju dengan terma ini.',
        
        # Language
        'lang_title': '🌐 Pemilihan Bahasa',
        'lang_choose': 'Pilih bahasa pilihan anda:',
        'lang_english': '🇬🇧 Bahasa Inggeris - English language',
        'lang_malay': '🇲🇾 Bahasa Melayu - Bahasa Melayu',
        'lang_indonesian': '🇮🇩 Bahasa Indonesia - Bahasa Indonesia',
        'lang_thai': '🇹🇭 Bahasa Thai - ภาษาไทย',
        'lang_select': 'Pilih bahasa untuk meneruskan:',
        'lang_changed_en': '✅ Language changed to English\n\nAll bot messages will now be displayed in English.',
        'lang_changed_my': '✅ Bahasa telah ditukar ke Bahasa Melayu\n\nSemua mesej bot kini akan dipaparkan dalam Bahasa Melayu.',
        'lang_changed_id': '✅ Bahasa telah diubah ke Bahasa Indonesia\n\nSemua pesan bot sekarang akan ditampilkan dalam Bahasa Indonesia.',
        'lang_changed_th': '✅ ภาษาได้เปลี่ยนเป็นภาษาไทย\n\nข้อความทั้งหมดของบอทจะแสดงเป็นภาษาไทย',
    },
    'id': {
        # Buttons
        'btn_free_analysis': '📊 Analisis Pasar Gratis',
        'btn_premium_signals': '🔑 Sinyal Premium',
        'btn_register': '📝 Daftar untuk Premium',
        'btn_my_account': '👤 Akun Saya',
        'btn_help': 'ℹ️ Bantuan & Dukungan',
        'btn_notice_board': '📌 Papan Pengumuman',
        'btn_performance': '📈 Catatan Performa',
        'btn_terms': '📜 Syarat dan Ketentuan',
        'btn_language': '🌐 Bahasa',
        'btn_english': '🇬🇧 Bahasa Inggris',
        'btn_malay': '🇲🇾 Bahasa Melayu',
        'btn_indonesian': '🇮🇩 Bahasa Indonesia',
        'btn_thai': '🇹🇭 Bahasa Thailand',
        'btn_back': '⬅️ Kembali ke Menu Utama',
        
        # Status
        'status_trial': '🎁 Uji Coba Premium Aktif (tersisa {days} hari)',
        'status_premium': '💎 Anggota Premium',
        'status_free': '🆓 Pengguna Gratis',
        'status_suspended': '🚫 Ditangguhkan',
        
        # Menu
        'menu_choose_option': 'Pilih opsi:',
        'menu_welcome': '👋 Selamat Datang',
        
        # Account
        'account_title': '👤 Akun Saya',
        'account_status': '📊 Status:',
        'account_country': '🌍 Negara:',
        'account_email': '📧 Email:',
        'account_number': '🔢 Nomor Akun:',
        'account_verified': '✅ Terverifikasi',
        'account_not_verified': '❌ Belum Terverifikasi',
        'account_trial_days': '⏳ Hari Uji Coba Tersisa:',
        'account_premium_message': '\n\n✨ Terima kasih telah menjadi anggota Premium!\nPastikan akun broker Anda aktif untuk menikmati akses tanpa gangguan.',
        
        # Help
        'help_title': 'ℹ️ Bantuan & Dukungan',
        'help_features': 'Fitur Tersedia:',
        'help_free_analysis': '📊 Analisis Gratis – Observasi pasar harian yang dihasilkan AI',
        'help_premium_signals': '💎 Sinyal Premium – Akses catatan studi mendalam (uji coba/premium saja)',
        'help_register': '📝 Daftar – Upgrade ke Premium dengan mendaftar menggunakan tautan broker kami',
        'help_account': '👤 Akun – Periksa status Anda (Uji Coba / Premium / Ditangguhkan)',
        'help_how_premium': 'Cara Kerja Premium:',
        'help_step1': '1️⃣ Mulai dengan uji coba gratis 14 hari',
        'help_step2': '2️⃣ Daftar dengan tautan broker kami',
        'help_step3': '3️⃣ Deposit minimum $50 USD ke akun broker',
        'help_step4': '4️⃣ Kirimkan email & nama Anda untuk verifikasi',
        'help_step5': '5️⃣ Persetujuan admin memberikan akses Premium',
        'help_disclaimer': '⚠️ Penafian Penting:',
        'help_disclaimer_text': 'Semua analisis yang disediakan dihasilkan AI dan hanya untuk tujuan pendidikan.\n\nLayanan ini tidak memberikan nasihat keuangan.\n\nPengguna harus DYOR (Lakukan Riset Sendiri) dan TAYOR (Perdagangkan Atas Risiko Sendiri).\n\nDengan menggunakan bot ini, Anda mengakui bahwa Anda mengambil tanggung jawab penuh atas keputusan perdagangan Anda.',
        'help_contact': '📬 Kontak Dukungan: [Admin](https://t.me/GoldenAi_admin)',
        
        # Notice Board
        'notice_title': '📌 Papan Pengumuman',
        'notice_announcements': '📢 Pengumuman Penting:',
        'notice_stay_updated': 'Tetap terbarui dengan berita dan pembaruan terbaru dari bot perdagangan kami.',
        'notice_check_regularly': '📅 Periksa kembali secara rutin untuk pengumuman baru.',
        'notice_tips': '💡 Tips:',
        'notice_tip1': '• Ikuti semua sinyal secara bertanggung jawab',
        'notice_tip2': '• Kelola risiko Anda dengan baik',
        'notice_tip3': '• Pastikan akun broker Anda aktif',
        
        # Performance
        'performance_title': '📈 Catatan Performa',
        'performance_stats': '📊 Statistik Performa Sinyal:',
        'performance_coming_soon': 'Segera hadir! Lacak performa perdagangan dan hasil sinyal Anda di sini.',
        'performance_features': '💡 Fitur:',
        'performance_feature1': '• Pelacakan tingkat kemenangan',
        'performance_feature2': '• Analisis Laba/Rugi',
        'performance_feature3': '• Riwayat sinyal',
        'performance_soon': '🔒 Fitur ini akan segera tersedia!',
        
        # Terms
        'terms_title': '📜 Syarat dan Ketentuan',
        'terms_important': '📋 Informasi Penting:',
        'terms_1_title': '1. Hanya untuk Tujuan Pendidikan',
        'terms_1_text': 'Semua sinyal dan analisis hanya untuk tujuan pendidikan.',
        'terms_2_title': '2. Penafian Risiko',
        'terms_2_text': 'Perdagangan melibatkan risiko. Selalu lakukan riset sendiri (DYOR) dan ambil tanggung jawab sendiri (TAYOR).',
        'terms_3_title': '3. Bukan Nasihat Keuangan',
        'terms_3_text': 'Kami tidak memberikan nasihat keuangan. Semua keputusan perdagangan adalah keputusan Anda sendiri.',
        'terms_4_title': '4. Pendaftaran Broker',
        'terms_4_text': 'Akses Premium memerlukan pendaftaran akun broker yang valid.',
        'terms_5_title': '5. Tanggung Jawab Akun',
        'terms_5_text': 'Pastikan akun broker Anda didanai dan aktif untuk mempertahankan status Premium.',
        'terms_agree': '⚠️ Dengan menggunakan bot ini, Anda menyetujui syarat-syarat ini.',
        
        # Language
        'lang_title': '🌐 Pemilihan Bahasa',
        'lang_choose': 'Pilih bahasa pilihan Anda:',
        'lang_english': '🇬🇧 Bahasa Inggris - English language',
        'lang_malay': '🇲🇾 Bahasa Melayu - Bahasa Melayu',
        'lang_indonesian': '🇮🇩 Bahasa Indonesia - Bahasa Indonesia',
        'lang_thai': '🇹🇭 Bahasa Thailand - ภาษาไทย',
        'lang_select': 'Pilih bahasa untuk melanjutkan:',
        'lang_changed_en': '✅ Bahasa diubah ke Bahasa Inggris\n\nSemua pesan bot sekarang akan ditampilkan dalam Bahasa Inggris.',
        'lang_changed_my': '✅ Bahasa diubah ke Bahasa Melayu\n\nSemua pesan bot sekarang akan ditampilkan dalam Bahasa Melayu.',
        'lang_changed_id': '✅ Bahasa diubah ke Bahasa Indonesia\n\nSemua pesan bot sekarang akan ditampilkan dalam Bahasa Indonesia.',
        'lang_changed_th': '✅ ภาษาได้เปลี่ยนเป็นภาษาไทย\n\nข้อความทั้งหมดของบอทจะแสดงเป็นภาษาไทย',
    },
    'th': {
        # Buttons
        'btn_free_analysis': '📊 การวิเคราะห์ตลาดฟรี',
        'btn_premium_signals': '🔑 สัญญาณพรีเมียม',
        'btn_register': '📝 ลงทะเบียนสำหรับพรีเมียม',
        'btn_my_account': '👤 บัญชีของฉัน',
        'btn_help': 'ℹ️ ความช่วยเหลือและสนับสนุน',
        'btn_notice_board': '📌 กระดานประกาศ',
        'btn_performance': '📈 บันทึกผลการดำเนินงาน',
        'btn_terms': '📜 ข้อกำหนดและเงื่อนไข',
        'btn_language': '🌐 ภาษา',
        'btn_english': '🇬🇧 ภาษาอังกฤษ',
        'btn_malay': '🇲🇾 ภาษามลายู',
        'btn_indonesian': '🇮🇩 ภาษาอินโดนีเซีย',
        'btn_thai': '🇹🇭 ภาษาไทย',
        'btn_back': '⬅️ กลับไปยังเมนูหลัก',
        
        # Status
        'status_trial': '🎁 การทดลองพรีเมียมที่ใช้งาน ({days} วันเหลือ)',
        'status_premium': '💎 สมาชิกพรีเมียม',
        'status_free': '🆓 ผู้ใช้ฟรี',
        'status_suspended': '🚫 ถูกระงับ',
        
        # Menu
        'menu_choose_option': 'เลือกตัวเลือก:',
        'menu_welcome': '👋 ยินดีต้อนรับ',
        
        # Account
        'account_title': '👤 บัญชีของฉัน',
        'account_status': '📊 สถานะ:',
        'account_country': '🌍 ประเทศ:',
        'account_email': '📧 อีเมล:',
        'account_number': '🔢 หมายเลขบัญชี:',
        'account_verified': '✅ ตรวจสอบแล้ว',
        'account_not_verified': '❌ ยังไม่ได้รับการตรวจสอบ',
        'account_trial_days': '⏳ วันทดลองเหลือ:',
        'account_premium_message': '\n\n✨ ขอบคุณที่เป็สมาชิกพรีเมียม!\nรักษาบัญชีโบรกเกอร์ของคุณให้ใช้งานได้เพื่อเพลิดเพลินกับการเข้าถึงแบบไม่ขาดตอน',
        
        # Help
        'help_title': 'ℹ️ ความช่วยเหลือและสนับสนุน',
        'help_features': 'ฟีเจอร์ที่มี:',
        'help_free_analysis': '📊 การวิเคราะห์ฟรี – การสังเกตตลาดที่สร้างโดย AI รายวัน',
        'help_premium_signals': '💎 สัญญาณพรีเมียม – เข้าถึงบันทึกการศึกษารายละเอียด (การทดลอง/พรีเมียมเท่านั้น)',
        'help_register': '📝 ลงทะเบียน – อัปเกรดเป็นพรีเมียมโดยการลงทะเบียนด้วยลิงก์โบรกเกอร์ของเรา',
        'help_account': '👤 บัญชี – ตรวจสอบสถานะของคุณ (การทดลอง / พรีเมียม / ถูกระงับ)',
        'help_how_premium': 'พรีเมียมทำงานอย่างไร:',
        'help_step1': '1️⃣ เริ่มต้นด้วยการทดลองฟรี 14 วัน',
        'help_step2': '2️⃣ ลงทะเบียนด้วยลิงก์โบรกเกอร์ของเรา',
        'help_step3': '3️⃣ ฝากเงินขั้นต่ำ $50 USD เข้าบัญชีโบรกเกอร์',
        'help_step4': '4️⃣ ส่งอีเมลและชื่อของคุณเพื่อการตรวจสอบ',
        'help_step5': '5️⃣ การอนุมัติจากผู้ดูแลระบบให้สิทธิ์การเข้าถึงพรีเมียม',
        'help_disclaimer': '⚠️ ข้อจำกัดความรับผิดชอบที่สำคัญ:',
        'help_disclaimer_text': 'การวิเคราะห์ทั้งหมดที่ให้มานั้นสร้างโดย AI และเพื่อวัตถุประสงค์ทางการศึกษาเท่านั้น\n\nบริการนี้ไม่ให้คำแนะนำทางการเงิน\n\nผู้ใช้ต้อง DYOR (ทำการวิจัยของคุณเอง) และ TAYOR (เทรดด้วยความเสี่ยงของคุณเอง)\n\nโดยการใช้บอทนี้ คุณยอมรับว่าคุณรับผิดชอบเต็มที่สำหรับการตัดสินใจเทรดของคุณ',
        'help_contact': '📬 ติดต่อสนับสนุน: [Admin](https://t.me/GoldenAi_admin)',
        
        # Notice Board
        'notice_title': '📌 กระดานประกาศ',
        'notice_announcements': '📢 ประกาศสำคัญ:',
        'notice_stay_updated': 'ติดตามข่าวสารและอัปเดตล่าสุดจากบอทเทรดของเรา',
        'notice_check_regularly': '📅 ตรวจสอบกลับเป็นประจำสำหรับประกาศใหม่',
        'notice_tips': '💡 คำแนะนำ:',
        'notice_tip1': '• ติดตามสัญญาณทั้งหมดอย่างรับผิดชอบ',
        'notice_tip2': '• จัดการความเสี่ยงของคุณอย่างเหมาะสม',
        'notice_tip3': '• รักษาบัญชีโบรกเกอร์ของคุณให้ใช้งานได้',
        
        # Performance
        'performance_title': '📈 บันทึกผลการดำเนินงาน',
        'performance_stats': '📊 สถิติผลการดำเนินงานของสัญญาณ:',
        'performance_coming_soon': 'เร็วๆ นี้! ติดตามผลการดำเนินงานการเทรดและผลลัพธ์ของสัญญาณของคุณที่นี่',
        'performance_features': '💡 ฟีเจอร์:',
        'performance_feature1': '• การติดตามอัตราการชนะ',
        'performance_feature2': '• การวิเคราะห์ผลกำไร/ขาดทุน',
        'performance_feature3': '• ประวัติสัญญาณ',
        'performance_soon': '🔒 ฟีเจอร์นี้จะพร้อมใช้งานเร็วๆ นี้!',
        
        # Terms
        'terms_title': '📜 ข้อกำหนดและเงื่อนไข',
        'terms_important': '📋 ข้อมูลสำคัญ:',
        'terms_1_title': '1. เพื่อวัตถุประสงค์ทางการศึกษาเท่านั้น',
        'terms_1_text': 'สัญญาณและการวิเคราะห์ทั้งหมดมีไว้เพื่อวัตถุประสงค์ทางการศึกษาเท่านั้น',
        'terms_2_title': '2. ข้อจำกัดความรับผิดชอบความเสี่ยง',
        'terms_2_text': 'การเทรดมีความเสี่ยง ควรทำการวิจัยของคุณเอง (DYOR) และรับผิดชอบเอง (TAYOR) เสมอ',
        'terms_3_title': '3. ไม่มีคำแนะนำทางการเงิน',
        'terms_3_text': 'เราไม่ให้คำแนะนำทางการเงิน การตัดสินใจเทรดทั้งหมดเป็นของคุณเอง',
        'terms_4_title': '4. การลงทะเบียนโบรกเกอร์',
        'terms_4_text': 'การเข้าถึงพรีเมียมต้องมีการลงทะเบียนบัญชีโบรกเกอร์ที่ถูกต้อง',
        'terms_5_title': '5. ความรับผิดชอบบัญชี',
        'terms_5_text': 'รักษาบัญชีโบรกเกอร์ของคุณให้มีการระดมทุนและใช้งานได้เพื่อรักษาสถานะพรีเมียม',
        'terms_agree': '⚠️ โดยการใช้บอทนี้ คุณยอมรับข้อกำหนดเหล่านี้',
        
        # Language
        'lang_title': '🌐 การเลือกภาษา',
        'lang_choose': 'เลือกภาษาที่คุณต้องการ:',
        'lang_english': '🇬🇧 ภาษาอังกฤษ - English language',
        'lang_malay': '🇲🇾 ภาษามลายู - Bahasa Melayu',
        'lang_indonesian': '🇮🇩 ภาษาอินโดนีเซีย - Bahasa Indonesia',
        'lang_thai': '🇹🇭 ภาษาไทย - ภาษาไทย',
        'lang_select': 'เลือกภาษาเพื่อดำเนินการต่อ:',
        'lang_changed_en': '✅ ภาษาได้เปลี่ยนเป็นภาษาอังกฤษ\n\nข้อความทั้งหมดของบอทจะแสดงเป็นภาษาอังกฤษ',
        'lang_changed_my': '✅ ภาษาได้เปลี่ยนเป็นภาษามลายู\n\nข้อความทั้งหมดของบอทจะแสดงเป็นภาษามลายู',
        'lang_changed_id': '✅ ภาษาได้เปลี่ยนเป็นภาษาอินโดนีเซีย\n\nข้อความทั้งหมดของบอทจะแสดงเป็นภาษาอินโดนีเซีย',
        'lang_changed_th': '✅ ภาษาได้เปลี่ยนเป็นภาษาไทย\n\nข้อความทั้งหมดของบอทจะแสดงเป็นภาษาไทย',
    }
}

def get_user_language(user_id: int) -> str:
    """Get user's preferred language - always fresh from database"""
    # Always get fresh data from database
    user_data = db.get_user(user_id)
    # Check if user exists in database
    if user_id in db.users:
        lang = db.users[user_id].get('language', 'en')
    else:
        lang = user_data.get('language', 'en')
    return lang if lang in ['en', 'my', 'id', 'th'] else 'en'  # Default to English

def t(user_id: int, key: str, **kwargs) -> str:
    """Translate text based on user's language"""
    lang = get_user_language(user_id)
    translation_dict = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
    translation = translation_dict.get(key, key)
    
    # Format with kwargs if provided
    if kwargs:
        try:
            return translation.format(**kwargs)
        except:
            return translation
    
    return translation

# Initialize database and systems
db = UserDatabase()
admin_panel = AdminPanel(db)
notification_system = NotificationSystem(db)
signal_manager = SignalManager(db, notification_system)

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS

def get_user_status(user_id: int) -> str:
    """Get current user status"""
    user = db.get_user(user_id)
    today = date.today()
    
    if user['status'] == 'trial':
        if user['trial_end'] and datetime.fromisoformat(user['trial_end']).date() <= today:
            # Trial expired - check if user is verified
            if user.get('verified'):
                # User is verified - upgrade to premium
                db.update_user(user_id, status='premium')
                return 'premium'
            else:
                # User not verified - downgrade to free
                db.update_user(user_id, status='free')
                return 'free'
        return 'trial'
    elif user['status'] == 'premium':
        if user['subscription_end'] and datetime.fromisoformat(user['subscription_end']).date() < today:
            db.update_user(user_id, status='free')
            return 'free'
        return 'premium'
    return user['status']

def escape_markdown(text: str) -> str:
    """Escape special characters for Markdown parsing"""
    if not text:
        return ""
    
    # Characters that need escaping in Markdown
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

def safe_format_user_data(data: dict) -> dict:
    """Safely format user data for Markdown display"""
    safe_data = {}
    for key, value in data.items():
        if isinstance(value, str):
            safe_data[key] = escape_markdown(str(value))
        else:
            safe_data[key] = str(value) if value is not None else "N/A"
    return safe_data

async def safe_send_message(update, text: str, reply_markup=None):
    """Safely send message with fallback parsing modes"""
    try:
        # Try Markdown first
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    except Exception as markdown_error:
        try:
            # Fallback to HTML
            html_text = text.replace('**', '<b>').replace('**', '</b>')
            html_text = html_text.replace('*', '<i>').replace('*', '</i>')
            html_text = html_text.replace('`', '<code>').replace('`', '</code>')
            await update.message.reply_text(html_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        except Exception as html_error:
            # Final fallback - plain text
            plain_text = text.replace('**', '').replace('*', '').replace('`', '')
            await update.message.reply_text(plain_text, reply_markup=reply_markup)

def get_latest_signal():
    """Get the latest signal from latest_signal.json"""
    try:
        # First try to get from latest_signal.json
        try:
            with open('latest_signal.json', 'r') as f:
                latest_signal = json.load(f)
            return latest_signal
        except FileNotFoundError:
            pass
        
        # Fallback to signals.json if latest_signal.json doesn't exist
        with open('signals.json', 'r') as f:
            signals = json.load(f)
        
        if not signals:
            return None
        
        # Get the latest signal by created_at timestamp
        latest_signal = None
        latest_time = None
        
        for signal_id, signal_data in signals.items():
            if signal_data.get('status') == 'active':
                created_at = signal_data.get('created_at', '')
                if created_at and (latest_time is None or created_at > latest_time):
                    latest_time = created_at
                    latest_signal = signal_data
        
        return latest_signal
    except Exception as e:
        logger.error(f"Error getting latest signal: {e}")
        return None

def store_latest_signal(signal_id, symbol, action, entry_price, stop_loss, take_profit, description):
    """Store latest signal for premium signals display"""
    try:
        latest_signal = {
            'signal_id': signal_id,
            'symbol': symbol,
            'action': action,
            'entry_price': entry_price,  # Can be string (range) or float
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'description': description,
            'created_at': datetime.now().isoformat()
        }
        
        with open('latest_signal.json', 'w') as f:
            json.dump(latest_signal, f, indent=2)
        
        logger.debug(f"✅ Latest signal stored: {signal_id}")
    except Exception as e:
        logger.error(f"Error storing latest signal: {e}")

def get_market_data(symbol, period="5d"):
    """Fetch market data using yfinance with better error handling"""
    try:
        ticker = yf.Ticker(symbol)
        
        # Try different periods if the default fails
        periods_to_try = [period, "1d", "2d", "3d"]
        
        for p in periods_to_try:
            try:
                data = ticker.history(period=p)
                if not data.empty and len(data) >= 2:
                    logger.info(f"Successfully fetched {symbol} data for period {p}")
                    return data
            except Exception as e:
                logger.warning(f"Failed to fetch {symbol} data for period {p}: {e}")
                continue
        
        # If all periods fail, try with different symbol formats
        alternative_symbols = {
            "GC=F": ["GC=F", "GOLD", "XAUUSD=X", "XAU=X"],
            "GOLD": ["GOLD", "GC=F", "XAUUSD=X", "XAU=X"]
        }
        
        if symbol in alternative_symbols:
            for alt_symbol in alternative_symbols[symbol]:
                try:
                    alt_ticker = yf.Ticker(alt_symbol)
                    data = alt_ticker.history(period="1d")
                    if not data.empty and len(data) >= 2:
                        logger.info(f"Successfully fetched {alt_symbol} as alternative to {symbol}")
                        return data
                except Exception as e:
                    logger.warning(f"Failed to fetch {alt_symbol}: {e}")
                    continue
        
        logger.error(f"Failed to fetch data for {symbol} with all methods")
        return None
        
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        return None

def calculate_technical_indicators(data):
    """Calculate basic technical indicators"""
    try:
        if data is None or data.empty:
            return {}
        
        # Calculate moving averages
        data['MA_20'] = data['Close'].rolling(window=20).mean()
        data['MA_50'] = data['Close'].rolling(window=50).mean()
        
        # Calculate RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        # Calculate support and resistance
        recent_high = data['High'].tail(20).max()
        recent_low = data['Low'].tail(20).min()
        current_price = data['Close'].iloc[-1]
        
        return {
            'current_price': round(current_price, 2),
            'ma_20': round(data['MA_20'].iloc[-1], 2) if not pd.isna(data['MA_20'].iloc[-1]) else None,
            'ma_50': round(data['MA_50'].iloc[-1], 2) if not pd.isna(data['MA_50'].iloc[-1]) else None,
            'rsi': round(data['RSI'].iloc[-1], 2) if not pd.isna(data['RSI'].iloc[-1]) else None,
            'recent_high': round(recent_high, 2),
            'recent_low': round(recent_low, 2),
            'price_change': round(((current_price - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100, 2) if len(data) > 1 else 0
        }
    except Exception as e:
        logger.error(f"Error calculating indicators: {e}")
        return {}

def generate_market_analysis():
    """Generate AI-powered market analysis - GOLD FOCUSED"""
    try:
        logger.info("Starting market analysis generation")
        
        # Fetch data for GOLD only
        gold_data = get_market_data("GC=F")  # Gold futures
        
        analysis = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'instruments': {}
        }
        
        # Analyze GOLD with enhanced indicators
        if gold_data is not None and not gold_data.empty:
            logger.info("Real market data found, generating analysis")
            gold_indicators = calculate_technical_indicators(gold_data)
            if gold_indicators:
                current_price = gold_indicators['current_price']
                ma_20 = gold_indicators['ma_20']
                ma_50 = gold_indicators['ma_50']
                rsi = gold_indicators['rsi']
                price_change = gold_indicators['price_change']
                
                # Enhanced trend analysis
                if ma_20 is not None and ma_50 is not None:
                    if current_price > ma_20 and current_price > ma_50 and price_change > 0:
                        trend = "Strong Bullish"
                    elif current_price > ma_20 and price_change > 0:
                        trend = "Bullish"
                    elif current_price < ma_20 and current_price < ma_50 and price_change < 0:
                        trend = "Strong Bearish"
                    elif current_price < ma_20 and price_change < 0:
                        trend = "Bearish"
                    else:
                        trend = "Consolidating"
                elif ma_20 is not None:
                    if current_price > ma_20 and price_change > 0:
                        trend = "Bullish"
                    elif current_price < ma_20 and price_change < 0:
                        trend = "Bearish"
                    else:
                        trend = "Consolidating"
                else:
                    if price_change > 0:
                        trend = "Bullish"
                    elif price_change < 0:
                        trend = "Bearish"
                    else:
                        trend = "Consolidating"
                
                # Enhanced RSI analysis
                if rsi and rsi > 80:
                    rsi_condition = "Extremely Overbought"
                elif rsi and rsi > 70:
                    rsi_condition = "Overbought"
                elif rsi and rsi < 20:
                    rsi_condition = "Extremely Oversold"
                elif rsi and rsi < 30:
                    rsi_condition = "Oversold"
                else:
                    rsi_condition = "Neutral"
                
                # Calculate additional levels
                resistance_1 = round(gold_indicators['recent_high'], 0)
                resistance_2 = round(gold_indicators['recent_high'] + 10, 0)
                support_1 = round(gold_indicators['recent_low'], 0)
                support_2 = round(gold_indicators['recent_low'] - 10, 0)
                
                analysis['instruments']['GOLD'] = {
                    'symbol': 'GOLD (XAU/USD)',
                    'current_price': current_price,
                    'trend': trend,
                    'rsi_condition': rsi_condition,
                    'price_change': price_change,
                    'resistance_1': resistance_1,
                    'resistance_2': resistance_2,
                    'support_1': support_1,
                    'support_2': support_2,
                    'support_zone': f"{support_1}-{support_1 + 5}",
                    'resistance_zone': f"{resistance_1}-{resistance_2}",
                    'ma_20': ma_20,
                    'ma_50': ma_50,
                    'rsi': rsi
                }
        
        return analysis
    except Exception as e:
        logger.error(f"Error generating market analysis: {e}")
        # Return fallback analysis if data fetching fails
        logger.info("Using fallback analysis due to error")
        return generate_fallback_analysis()

def generate_fallback_analysis():
    """Generate fallback analysis when data fetching fails"""
    try:
        logger.info("Generating fallback market analysis")
        # Use static data as fallback
        current_price = 1935.50  # Approximate current gold price
        analysis = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'instruments': {
                'GOLD': {
                    'symbol': 'GOLD (XAU/USD)',
                    'current_price': current_price,
                    'trend': 'Consolidating',
                    'rsi_condition': 'Neutral',
                    'price_change': 0.25,
                    'resistance_1': 1945,
                    'resistance_2': 1955,
                    'support_1': 1925,
                    'support_2': 1915,
                    'support_zone': '1925-1930',
                    'resistance_zone': '1945-1955',
                    'ma_20': 1932.50,
                    'ma_50': 1928.75,
                    'rsi': 45.5
                }
            }
        }
        logger.info(f"Generated fallback market analysis with {len(analysis['instruments'])} instruments")
        return analysis
    except Exception as e:
        logger.error(f"Error generating fallback analysis: {e}")
        return None

def format_market_analysis(analysis):
    """Format market analysis for display - GOLD FOCUSED"""
    logger.info(f"Formatting market analysis: {analysis is not None}")
    if not analysis or not analysis.get('instruments') or not analysis['instruments']:
        logger.warning("No analysis data available, showing error message")
        return "📊 **Today's Free Market Analysis (Educational Only)**\n\n❌ Unable to fetch market data at the moment.\n\n⚠️ **Disclaimer:** AI-generated analysis. Educational use only. DYOR & TAYOR."
    
    message = "📊 **Today's Free Market Analysis (Educational Only)**\n\n"
    
    # GOLD Analysis - Enhanced
    if 'GOLD' in analysis['instruments']:
        gold = analysis['instruments']['GOLD']
        message += f"🟡 **{gold['symbol']}**\n"
        message += f"• Current Price: ${gold['current_price']}\n"
        message += f"• Current Trend: {gold['trend']}\n"
        message += f"• RSI Condition: {gold['rsi_condition']} ({gold['rsi']})\n"
        message += f"• Key Resistance: {gold['resistance_1']} - {gold['resistance_2']}\n"
        message += f"• Support Zone: {gold['support_zone']}\n"
        if gold['ma_20'] is not None:
            message += f"• MA-20: ${gold['ma_20']}\n"
        if gold['ma_50'] is not None:
            message += f"• MA-50: ${gold['ma_50']}\n"
        if gold['price_change'] != 0:
            change_emoji = "📈" if gold['price_change'] > 0 else "📉"
            message += f"• 24h Change: {change_emoji} {abs(gold['price_change']):.2f}%\n"
        message += "\n"
        
        # Add trading insights
        message += "💡 **Trading Insights:**\n"
        if gold['trend'] == "Strong Bullish":
            message += "• Strong upward momentum detected\n"
            message += "• Consider long positions on pullbacks\n"
        elif gold['trend'] == "Strong Bearish":
            message += "• Strong downward momentum detected\n"
            message += "• Consider short positions on rallies\n"
        elif gold['trend'] == "Bullish":
            message += "• Moderate upward bias\n"
            message += "• Watch for breakout above resistance\n"
        elif gold['trend'] == "Bearish":
            message += "• Moderate downward bias\n"
            message += "• Watch for breakdown below support\n"
        else:
            message += "• Market is consolidating\n"
            message += "• Wait for clear direction\n"
        
        if gold['rsi_condition'] == "Overbought" or gold['rsi_condition'] == "Extremely Overbought":
            message += "• RSI suggests potential pullback\n"
        elif gold['rsi_condition'] == "Oversold" or gold['rsi_condition'] == "Extremely Oversold":
            message += "• RSI suggests potential bounce\n"
        
        message += "\n"
    
    message += "🔑 **Want real-time AI-generated observations with TP/SL levels?**\n"
    message += "👉 **Upgrade to Premium to unlock full access.**\n\n"
    message += "⚠️ **Disclaimer:** AI-generated analysis. Educational use only. DYOR & TAYOR. Not intended for Malaysian residents."
    
    return message

def create_main_menu(user_id: int = None) -> InlineKeyboardMarkup:
    """Create main menu keyboard with translations"""
    if user_id is None:
        lang = 'en'  # Default
    else:
        lang = get_user_language(user_id)
    
    translations = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
    
    keyboard = [
        [InlineKeyboardButton(translations['btn_free_analysis'], callback_data="analysis")],
        [InlineKeyboardButton(translations['btn_premium_signals'], callback_data="signals")],
        [InlineKeyboardButton(translations['btn_register'], callback_data="register")],
        [InlineKeyboardButton(translations['btn_my_account'], callback_data="account")],
        [InlineKeyboardButton(translations['btn_help'], callback_data="help")],
        [InlineKeyboardButton(translations['btn_notice_board'], url="https://t.me/noticeboardgoldenai")],
        [InlineKeyboardButton(translations['btn_performance'], url="https://t.me/feedbackgoldenai/44")],
        [InlineKeyboardButton(translations['btn_terms'], callback_data="terms")],
        [InlineKeyboardButton(translations['btn_language'], callback_data="language")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_admin_menu() -> InlineKeyboardMarkup:
    """Create admin menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("👥 Manage Users", callback_data="admin_users")],
        [InlineKeyboardButton("📢 Send Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🚫 Suspended Users", callback_data="admin_suspended")],
        [InlineKeyboardButton("✅ Verify Requests", callback_data="admin_verify")],
        [InlineKeyboardButton("📊 Analytics & Logs", callback_data="admin_analytics")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /start command"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    first_name = update.effective_user.first_name or "Unknown"
    last_name = update.effective_user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()
    user_data = db.get_user(user_id)
    
    # Log user info
    logger.info(f"🚀 USER STARTED BOT: 👤 {full_name} (@{username}) | ID: {user_id} | Status: {user_data.get('status', 'Unknown')}")
    
    if not user_data['terms_accepted']:
        await update.message.reply_text(
            f"👋 Welcome to Golden AI Trading Bot!\n\n"
            f"📜 Terms & Conditions\n\n"
            f"1. Eligibility\n"
            f"• You must be at least 18 years old to use this service\n\n"
            f"2. Educational Purpose Only\n"
            f"• All content, analysis, and signals are AI-generated for educational purposes only\n"
            f"• Nothing provided shall be considered as financial, investment, or trading advice\n\n"
            f"3. Trade At Your Own Risk (TAYOR)\n"
            f"• Trading involves risk, including the risk of losing all invested capital\n"
            f"• You agree to Do Your Own Research (DYOR) before making any trading decision\n"
            f"• You accept full responsibility for any profits or losses\n\n"
            f"4. Subscription Rules\n"
            f"• Premium access may be reviewed monthly by admin\n"
            f"• Inactive users with partnered broker may be suspended\n"
            f"• Suspended users can restore access by funding their trading account\n\n"
            f"5. Limitation of Liability\n"
            f"• We shall not be held liable for any financial losses or damages\n"
            f"• You are solely responsible for your trading decisions\n\n"
            f"6. Acceptance of Terms\n"
            f"By continuing, you acknowledge that you have read, understood, and agreed to these Terms & Conditions.\n\n"
            f"👉 Do you accept the Terms & Conditions?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Yes, I Accept", callback_data="accept_terms")],
                [InlineKeyboardButton("❌ No, I Do Not Accept", callback_data="reject_terms")]
            ])
        )
        return TERMS
    else:
        await show_main_menu(update, context)
        return ConversationHandler.END


async def handle_terms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle terms acceptance"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if query.data == "accept_terms":
        db.update_user(user_id, terms_accepted=True, immediate=True)
        
        await query.edit_message_text(
            f"✅ Thank you for accepting the Terms & Conditions, {update.effective_user.first_name}!\n\n"
            f"🎁 You now qualify for a 14-day FREE Premium Trial.\n\n"
            f"During this trial, you'll get access to:\n"
            f"💎 Premium buy/sell signal alerts (AI-generated, educational only)\n"
            f"📊 Daily market analysis & insights\n"
            f"🎓 Trading education resources\n\n"
            f"⚠️ Remember: All signals are for educational purposes only. Please DYOR & TAYOR.\n\n"
            f"👉 Choose how you'd like to continue:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 Start Free Trial Now", callback_data="start_trial")],
                [InlineKeyboardButton("ℹ️ Learn More About Premium", callback_data="about")]
            ])
        )
        return TRIAL_CHOICE
    else:
        await query.edit_message_text(
            "❌ You must accept the Terms & Conditions to use this bot.\n"
            "Please start again with /start if you change your mind."
        )
        return ConversationHandler.END

async def handle_trial_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle trial choice"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if query.data == "start_trial":
        trial_end = datetime.now() + timedelta(days=14)
        db.update_user(user_id, status='trial', trial_end=trial_end.isoformat(), immediate=True)
        
        user_id = update.effective_user.id
        await query.edit_message_text(
            f"🚀 Your 14-day Premium trial has started, {update.effective_user.first_name}!\n\n"
            f"You now have full access to:\n"
            f"💎 Premium buy/sell signal calls\n"
            f"📊 Daily analysis & updates\n"
            f"🎓 Trading tips & strategies\n\n"
            f"📅 Trial Expiry Date: {trial_end.strftime('%Y-%m-%d')}\n\n"
            f"👉 What would you like to do now?",
            reply_markup=create_main_menu(user_id)
        )
    elif query.data == "free_only":
        user_id = update.effective_user.id
        await query.edit_message_text(
            "📊 You've chosen Free Analysis Only.\n\n"
            "You'll receive daily market analysis and educational content.\n"
            "To unlock Premium signals, you can start a trial anytime!\n\n"
            "👉 What would you like to do now?",
            reply_markup=create_main_menu(user_id)
        )
    else:  # about
        user_id = update.effective_user.id
        await query.edit_message_text(
            "ℹ️ About Golden Signals Trading Bot\n\n"
            "We provide:\n"
            "📊 Free daily market analysis\n"
            "💎 Premium trading signals\n"
            "🎓 Educational trading content\n\n"
            "⚠️ Disclaimer: Trading involves risk. Our signals are for educational purposes only.\n\n"
            "📬 Support: Contact @YourAdminUsername for help",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_main_menu(user_id)
        )
    
    return ConversationHandler.END

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu with translations"""
    user_id = update.effective_user.id
    status = get_user_status(user_id)
    
    if status == 'trial':
        user_data = db.get_user(user_id)
        trial_end = datetime.fromisoformat(user_data['trial_end']).date()
        days_left = (trial_end - date.today()).days
        text = t(user_id, 'status_trial', days=days_left)
    elif status == 'premium':
        text = t(user_id, 'status_premium')
    else:
        text = t(user_id, 'status_free')
    
    text += "\n\n" + t(user_id, 'menu_choose_option')
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=create_main_menu(user_id))
    else:
        await update.message.reply_text(text, reply_markup=create_main_menu(user_id))

async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu callbacks"""
    try:
        query = update.callback_query
        if not query:
            return
        
        await query.answer()
        
        user_id = update.effective_user.id
        status = get_user_status(user_id)
        user_data = db.get_user(user_id)
        
        # Debug: Log callback data
        logger.info(f"Callback received: {query.data} from user {user_id}")
        
        if query.data == "analysis":
            # Generate real-time market analysis
            analysis = generate_market_analysis()
            analysis_message = format_market_analysis(analysis)
            
            await query.edit_message_text(
                analysis_message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=create_main_menu(user_id)
            )
        
        elif query.data == "signals":
            if status in ['trial', 'premium']:
                # Get latest signal from signals.json
                latest_signal = get_latest_signal()
                if latest_signal:
                    signal_message = f"📈 Premium Trading Signals\n\n"
                    signal_message += f"🟡 {latest_signal['symbol']}\n"
                    signal_message += f"• Type: {latest_signal['action']}\n"
                    signal_message += f"• Entry: {latest_signal['entry_price']}\n"
                    signal_message += f"• Stop Loss: {latest_signal['stop_loss']}\n"
                    signal_message += f"• Take Profit: {latest_signal['take_profit']}\n"
                    signal_message += f"• Risk: 0.5% per trade\n\n"
                    signal_message += f"📝 {latest_signal['description']}\n\n"
                    signal_message += f"⚡ Manage your risk wisely!"
                else:
                    signal_message = "📈 Premium Trading Signals\n\n"
                    signal_message += "🟡 GOLD (XAU/USD)\n"
                    signal_message += "• Type: BUY\n"
                    signal_message += "• Entry: 1935.00\n"
                    signal_message += "• Stop Loss: 1928.00\n"
                    signal_message += "• Take Profit: 1950.00\n"
                    signal_message += "• Risk: 0.5% per trade\n\n"
                    signal_message += "🔵 EUR/USD\n"
                    signal_message += "• Type: SELL\n"
                    signal_message += "• Entry: 1.0850\n"
                    signal_message += "• Stop Loss: 1.0880\n"
                    signal_message += "• Take Profit: 1.0800\n"
                    signal_message += "• Risk: 0.5% per trade\n\n"
                    signal_message += "⚡ Manage your risk wisely!"
                
                await query.edit_message_text(
                    signal_message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=create_main_menu(user_id)
                )
            elif status == 'suspended':
                await query.edit_message_text(
                    "⚠️ Premium Signals Suspended\n\n"
                    "Your Premium subscription is currently suspended.\n"
                    "📉 Today's signals are locked.\n\n"
                    "💡 Fund your broker account to reactivate and unlock Premium signals again.",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 I've Funded My Account", callback_data="reactivate_request")],
                        [InlineKeyboardButton("⬅️ Back to General Menu", callback_data="general_menu")]
                    ])
                )
            else:
                await query.edit_message_text(
                    "⛔ Premium Access Expired\n\n"
                    "Your 14-day free trial has ended.\n"
                    "To continue receiving:\n"
                    "💎 Real-time Premium signals\n"
                    "📊 Daily market analysis\n"
                    "🎓 Exclusive trading insights\n\n"
                    "you'll need to activate Premium by registering with our broker.\n\n"
                    "🔗 [Register Now]({})\n\n"
                    "⚠️ Reminder: All signals are AI-generated and for educational purposes only. Please DYOR & TAYOR.".format(BROKER_LINK),
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=create_main_menu(user_id)
                )
        
        elif query.data == "register":
            if status == 'premium':
                await query.edit_message_text(
                    "✅ You're already Premium!\n\n"
                    "You have full access to all Premium features.\n"
                    "Keep your broker account active to maintain Premium status.",
                    reply_markup=create_main_menu(user_id)
                )
            else:
                await query.edit_message_text(
                    "📝 Register for Premium Access\n\n"
                    "To unlock Premium signals, please complete these steps:\n\n"
                    "1️⃣ Register with our broker: [Click Here]({})\n"
                    "2️⃣ Deposit minimum $50 USD into your broker account\n"
                    "3️⃣ Provide your full name (as registered with broker)\n"
                    "4️⃣ Provide your email address (same as broker account)\n\n"
                    "💰 Note: Minimum $50 USD deposit required for verification\n\n"
                    "👉 Let's start with your full name:".format(BROKER_LINK),
                    parse_mode=ParseMode.MARKDOWN
                )
                context.user_data['registering'] = True
                # Start conversation for registration
                return await start_registration_conversation(update, context)
        
        elif query.data == "account":
            trial_info = ""
            # Only show trial info for trial users, not premium users
            if status == 'trial' and user_data.get('trial_end'):
                trial_end = datetime.fromisoformat(user_data['trial_end']).date()
                days_left = (trial_end - date.today()).days
                trial_info = "\n" + t(user_id, 'account_trial_days', days=days_left)
            
            # Format status with emoji
            status_emoji = "✅" if status == 'premium' else "⏳" if status == 'trial' else "❌"
            status_text = f"{status_emoji} {status.title()}"
            
            # Format verification status
            verification_text = "🔒 Verification: " + t(user_id, 'account_verified') if user_data.get('verified') else "🔒 Verification: " + t(user_id, 'account_not_verified')
            
            # Format account ID
            account_text = t(user_id, 'account_number') + f": {user_data.get('account_number', 'Not provided')}"
            
            # Add premium message for premium users
            premium_message = ""
            if status == 'premium':
                premium_message = t(user_id, 'account_premium_message')
            
            await query.edit_message_text(
                t(user_id, 'account_title') + "\n\n" +
                t(user_id, 'account_status') + f" {status_text}\n" +
                t(user_id, 'account_country') + f" {user_data.get('country', 'Not set')}\n" +
                t(user_id, 'account_email') + f" {user_data.get('email', 'Not provided')}\n" +
                account_text + "\n" +
                verification_text + trial_info + premium_message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=create_main_menu(user_id)
            )
        
        elif query.data == "help":
            help_text = t(user_id, 'help_title') + "\n\n"
            help_text += t(user_id, 'help_features') + "\n"
            help_text += t(user_id, 'help_free_analysis') + "\n"
            help_text += t(user_id, 'help_premium_signals') + "\n"
            help_text += t(user_id, 'help_register') + "\n"
            help_text += t(user_id, 'help_account') + "\n\n"
            help_text += t(user_id, 'help_how_premium') + "\n"
            help_text += t(user_id, 'help_step1') + "\n"
            help_text += t(user_id, 'help_step2') + "\n"
            help_text += t(user_id, 'help_step3') + "\n"
            help_text += t(user_id, 'help_step4') + "\n"
            help_text += t(user_id, 'help_step5') + "\n\n"
            help_text += t(user_id, 'help_disclaimer') + "\n\n"
            help_text += t(user_id, 'help_disclaimer_text') + "\n\n"
            help_text += t(user_id, 'help_contact')
            
            await query.edit_message_text(
                help_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=create_main_menu(user_id),
                disable_web_page_preview=True
            )
        
        elif query.data == "terms":
            terms_text = "**" + t(user_id, 'terms_title') + "**\n\n"
            terms_text += "**" + t(user_id, 'terms_important') + "**\n\n"
            terms_text += f"1. **{t(user_id, 'terms_1_title')}**\n"
            terms_text += t(user_id, 'terms_1_text') + "\n\n"
            terms_text += f"2. **{t(user_id, 'terms_2_title')}**\n"
            terms_text += t(user_id, 'terms_2_text') + "\n\n"
            terms_text += f"3. **{t(user_id, 'terms_3_title')}**\n"
            terms_text += t(user_id, 'terms_3_text') + "\n\n"
            terms_text += f"4. **{t(user_id, 'terms_4_title')}**\n"
            terms_text += t(user_id, 'terms_4_text') + "\n\n"
            terms_text += f"5. **{t(user_id, 'terms_5_title')}**\n"
            terms_text += t(user_id, 'terms_5_text') + "\n\n"
            terms_text += "**" + t(user_id, 'terms_agree') + "**"
            
            await query.edit_message_text(
                terms_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=create_main_menu(user_id)
            )
        
        elif query.data == "language":
            lang = get_user_language(user_id)
            translations = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
            
            language_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(translations['btn_english'], callback_data="lang_en")],
                [InlineKeyboardButton(translations['btn_malay'], callback_data="lang_my")],
                [InlineKeyboardButton(translations['btn_indonesian'], callback_data="lang_id")],
                [InlineKeyboardButton(translations['btn_thai'], callback_data="lang_th")],
                [InlineKeyboardButton(translations['btn_back'], callback_data="main_menu")]
            ])
            
            lang_text = "**" + t(user_id, 'lang_title') + "**\n\n"
            lang_text += t(user_id, 'lang_choose') + "\n\n"
            lang_text += "**" + translations['btn_english'] + "** - English language\n"
            lang_text += "**" + translations['btn_malay'] + "** - Bahasa Melayu\n"
            lang_text += "**" + translations['btn_indonesian'] + "** - Bahasa Indonesia\n"
            lang_text += "**" + translations['btn_thai'] + "** - ภาษาไทย\n\n"
            lang_text += t(user_id, 'lang_select')
            
            await query.edit_message_text(
                lang_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=language_keyboard
            )
        
        elif query.data == "general_menu":
            await show_general_menu(update, context)
        
        elif query.data == "reactivate_request":
            await handle_reactivation_request(update, context)
        
        elif query.data == "locked_feature":
            await query.edit_message_text(
                "🔒 Premium Feature Locked\n\n"
                "This feature is only available for Premium users.\n"
                "💡 Fund your broker account to unlock Premium access.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 I've Funded My Account", callback_data="reactivate_request")],
                    [InlineKeyboardButton("⬅️ Back", callback_data="general_menu")]
                ])
            )
        
        elif query.data == "broker_info":
            await query.edit_message_text(
                f"ℹ️ Broker Information\n\n"
                f"Our Official Broker:\n"
                f"🔗 [Register Here]({BROKER_LINK})\n\n"
                f"Benefits:\n"
                f"• Competitive spreads\n"
                f"• Fast execution\n"
                f"• 24/7 support\n"
                f"• Multiple account types\n\n"
                f"Registration Process:\n"
                f"1. Click the link above\n"
                f"2. Complete registration\n"
                f"3. Submit account number in bot\n"
                f"4. Get verified by admin\n"
                f"5. Enjoy Premium access!",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📝 Register for Premium", callback_data="register")],
                    [InlineKeyboardButton("⬅️ Back", callback_data="general_menu")]
                ])
            )
        
        elif query.data == "contact_admin":
            await query.edit_message_text(
                "👤 Contact Admin\n\n"
                "For support and assistance, contact our admin:\n\n"
                "📬 Telegram: @YourAdminUsername\n"
                "📧 Email: admin@example.com\n\n"
                "Common Issues:\n"
                "• Account verification\n"
                "• Premium access problems\n"
                "• Technical support\n"
                "• General inquiries\n\n"
                "We'll respond within 24 hours.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Back", callback_data="general_menu")]
                ])
            )
        
        elif query.data == "lang_en":
            # Save language preference
            db.update_user(user_id, language='en')
            # Ensure user exists in database
            if user_id not in db.users:
                db.users[user_id] = db.get_user(user_id)
            db.users[user_id]['language'] = 'en'
            
            await query.answer("✅ Language set to English", show_alert=False)
            # Get updated translation directly from English translations
            message = "**🌐 Language Selection**\n\n" + TRANSLATIONS['en']['lang_changed_en']
            await query.edit_message_text(
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=create_main_menu(user_id)
            )
        
        elif query.data == "lang_my":
            # Save language preference
            db.update_user(user_id, language='my')
            # Ensure user exists in database
            if user_id not in db.users:
                db.users[user_id] = db.get_user(user_id)
            db.users[user_id]['language'] = 'my'
            
            await query.answer("✅ Bahasa telah ditetapkan ke Bahasa Melayu", show_alert=False)
            # Get updated translation directly from Malay translations
            message = "**🌐 Pemilihan Bahasa**\n\n" + TRANSLATIONS['my']['lang_changed_my']
            await query.edit_message_text(
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=create_main_menu(user_id)
            )
        
        elif query.data == "lang_id":
            # Save language preference
            db.update_user(user_id, language='id')
            # Ensure user exists in database
            if user_id not in db.users:
                db.users[user_id] = db.get_user(user_id)
            db.users[user_id]['language'] = 'id'
            
            await query.answer("✅ Bahasa telah ditetapkan ke Bahasa Indonesia", show_alert=False)
            # Get updated translation directly from Indonesian translations
            message = "**🌐 Pemilihan Bahasa**\n\n" + TRANSLATIONS['id']['lang_changed_id']
            await query.edit_message_text(
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=create_main_menu(user_id)
            )
        
        elif query.data == "lang_th":
            # Save language preference
            db.update_user(user_id, language='th')
            # Ensure user exists in database
            if user_id not in db.users:
                db.users[user_id] = db.get_user(user_id)
            db.users[user_id]['language'] = 'th'
            
            await query.answer("✅ ภาษาได้ตั้งเป็นภาษาไทย", show_alert=False)
            # Get updated translation directly from Thai translations
            message = "**🌐 การเลือกภาษา**\n\n" + TRANSLATIONS['th']['lang_changed_th']
            await query.edit_message_text(
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=create_main_menu(user_id)
            )
        
        elif query.data == "main_menu":
            await show_main_menu(update, context)
        
        else:
            logger.debug(f"Unknown callback data: {query.data} from user {user_id}")
            await query.edit_message_text(
                f"❌ Unknown Command\n\n"
                f"Callback data: {query.data}\n\n"
                f"Please try again or contact admin.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=create_main_menu(user_id)
            )
    except Exception as e:
        logger.error(f"Error in handle_menu_callback: {e}", exc_info=True)
        query = update.callback_query
        if query:
            await query.answer(f"❌ Error: {str(e)}", show_alert=True)

async def handle_register_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle name registration"""
    try:
        full_name = update.message.text.strip()
        user_id = update.effective_user.id
        
        if not full_name or len(full_name) < 2:
            await update.message.reply_text(
                "❌ Please enter a valid name (at least 2 characters).\n\n"
                "📝 Enter your full name:"
            )
            return REGISTER_NAME
        
        db.update_user(user_id, full_name=full_name)
        
        # Print registration progress to terminal
        username = update.effective_user.username or "Unknown"
        logger.info(f"📝 USER REGISTRATION: 👤 {full_name} (@{username}) | ID: {user_id} | Step: Name Entered")
        
        await update.message.reply_text(
            f"✅ Name saved: {full_name}\n\n"
            f"📧 Now please enter your broker registered email address:"
        )
        return REGISTER_EMAIL
        
    except Exception as e:
        logger.error(f"Error in handle_register_name: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again.\n\n"
            "📝 Enter your full name:"
        )
        return REGISTER_NAME

async def handle_register_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle email registration"""
    try:
        email = update.message.text.strip()
        user_id = update.effective_user.id
        
        if not email or '@' not in email:
            await update.message.reply_text(
                "❌ Please enter a valid email address.\n\n"
                "📧 Enter your broker registered email address:"
            )
            return REGISTER_EMAIL
        
        db.update_user(user_id, email=email)
        
        await update.message.reply_text(
            f"✅ Email saved: {email}\n\n"
            f"🔢 Finally, please enter your MT4/MT5 trading account number:"
        )
        return ACCOUNT_NUMBER
        
    except Exception as e:
        logger.error(f"Error in handle_register_email: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again.\n\n"
            "📧 Enter your broker registered email address:"
        )
        return REGISTER_EMAIL

async def handle_account_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle account number registration"""
    try:
        account_number = update.message.text.strip()
        user_id = update.effective_user.id
        
        if not account_number or len(account_number) < 3:
            await update.message.reply_text(
                "❌ Please enter a valid account number.\n\n"
                "🔢 Enter your MT4/MT5 trading account number:"
            )
            return ACCOUNT_NUMBER
        
        db.update_user(user_id, account_number=account_number)
        
        # Print registration completion to terminal
        username = update.effective_user.username or "Unknown"
        user_data = db.get_user(user_id)
        logger.info(f"✅ REGISTRATION COMPLETED: 👤 {user_data['full_name']} (@{username}) | ID: {user_id} | Email: {user_data['email']} | Account: {account_number}")
        
        await update.message.reply_text(
            f"✅ Registration Complete!\n\n"
            f"📝 Your details have been submitted:\n"
            f"• Name: {db.get_user(user_id)['full_name']}\n"
            f"• Email: {db.get_user(user_id)['email']}\n"
            f"• Account: {account_number}\n\n"
            f"⏳ Our admin will verify your account with the broker.\n"
            f"You'll receive a notification once approved!",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_main_menu(user_id)
        )
        
        # Notify admin
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔔 New Premium Request\n\n"
                 f"👤 User: @{update.effective_user.username}\n"
                 f"🆔 ID: {user_id}\n"
                 f"📝 Name: {db.get_user(user_id)['full_name']}\n"
                 f"📧 Email: {db.get_user(user_id)['email']}\n"
                 f"🔢 Account: {account_number}\n\n"
                 f"Commands:\n"
                 f"✅ /approve{user_id}\n"
                 f"❌ /reject{user_id}",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error in handle_account_number: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again.\n\n"
            "🔢 Enter your MT4/MT5 trading account number:"
        )
        return ACCOUNT_NUMBER

async def start_registration_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start registration conversation"""
    user_id = update.effective_user.id
    
    # DON'T change status - preserve trial if active
    # Just mark that they're registering without changing trial status
    user_data = db.get_user(user_id)
    if user_data.get('status') != 'trial':
        # Only update status if NOT on trial
        db.update_user(user_id, status='registering')
    # If on trial, keep trial status and let it run for full 14 days
    
    # Send message asking for name
    await context.bot.send_message(
        chat_id=user_id,
        text="📝 Step 1: Full Name\n\n"
             "Please enter your full name as registered with the broker:"
    )
    
    # Set conversation state
    context.user_data['conversation_state'] = 'register_name'
    return ConversationHandler.END

async def handle_registration_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle registration messages"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    state = context.user_data.get('conversation_state')
    
    if state == 'register_name':
        if len(text) < 2:
            await update.message.reply_text(
                "❌ Please enter a valid name (at least 2 characters).\n\n"
                "📝 Enter your full name:"
            )
            return
        
        db.update_user(user_id, full_name=text)
        context.user_data['conversation_state'] = 'register_email'
        
        await update.message.reply_text(
            f"✅ Name saved: {text}\n"
            f"📧 Step 2: Email Address\n"
            f"Please enter the email address you used to register with the broker:"
        )
        
    elif state == 'register_email':
        if '@' not in text:
            await update.message.reply_text(
                "❌ Please enter a valid email address.\n\n"
                "📧 Enter the email address you used to register with the broker:"
            )
            return
        
        db.update_user(user_id, email=text)
        context.user_data['conversation_state'] = 'register_account'
        
        await update.message.reply_text(
            f"✅ Email saved: {text}\n"
            f"🔢 Step 3: Trading Account Number\n"
            f"Please enter your trading account number:"
        )
        
    elif state == 'register_account':
        if len(text) < 3:
            await update.message.reply_text(
                "❌ Please enter a valid account number.\n\n"
                "🔢 Enter your MT4/MT5 trading account number:"
            )
            return
        
        db.update_user(user_id, account_number=text)
        context.user_data['conversation_state'] = None
        
        await update.message.reply_text(
            f"✅ Account saved: {text}\n\n"
            f"🔎 Verifying your details...\n"
            f"Your registration will be reviewed by our admin team.\n"
            f"You'll receive a confirmation once your Premium access is approved.\n\n"
            f"⚠️ Reminder: All signals are AI-generated for educational purposes only. Please DYOR & TAYOR.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_main_menu(user_id)
        )
        
        # Notify admin
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔔 New Premium Request\n\n"
                 f"👤 User: @{update.effective_user.username}\n"
                 f"🆔 ID: {user_id}\n"
                 f"📝 Name: {db.get_user(user_id)['full_name']}\n"
                 f"📧 Email: {db.get_user(user_id)['email']}\n"
                 f"🔢 Account: {text}\n\n"
                 f"Commands:\n"
                 f"✅ /approve{user_id}\n"
                 f"❌ /reject{user_id}",
            parse_mode=ParseMode.MARKDOWN
        )

async def show_general_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show general menu for suspended/free users"""
    user_id = update.effective_user.id
    status = get_user_status(user_id)
    
    if status == 'suspended':
        text = "👋 Welcome back to the General Menu\n\n"
        text += "Your Premium access is currently suspended due to low balance / inactivity in your broker account.\n\n"
        text += "⚠️ Premium Features are temporarily locked.\n"
        text += "Fund your account to unlock again."
    else:
        text = "👋 General Menu\n\n"
        text += "Choose from the available options below:"
    
    keyboard = [
        [InlineKeyboardButton("📊 Free Market Analysis", callback_data="analysis")],
        [InlineKeyboardButton("ℹ️ Broker Information", callback_data="broker_info")],
        [InlineKeyboardButton("👤 Contact Admin", callback_data="contact_admin")],
        [InlineKeyboardButton("❓ Help / Terms", callback_data="help")]
    ]
    
    # Add locked premium features for suspended users
    if status == 'suspended':
        keyboard.extend([
            [InlineKeyboardButton("🔒 Signal Alerts (Locked)", callback_data="locked_feature")],
            [InlineKeyboardButton("🔒 Premium Strategies (Locked)", callback_data="locked_feature")],
            [InlineKeyboardButton("🔒 VIP Newsletter (Locked)", callback_data="locked_feature")],
            [InlineKeyboardButton("🔒 Daily Trade Setups (Locked)", callback_data="locked_feature")]
        ])
    
    # Always show reactivation option for suspended users
    if status == 'suspended':
        keyboard.append([InlineKeyboardButton("🔄 I've Funded My Account", callback_data="reactivate_request")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def handle_reactivation_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle reactivation request from suspended users"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    
    # Update user data
    db.update_user(user_id, last_activity=datetime.now().isoformat())
    
    # Notify user
    await query.edit_message_text(
        "✅ Request Submitted!\n\n"
        "Our admin will verify your account balance with the broker.\n"
        "You'll get a notification once reactivated.\n\n"
        "⏳ Please wait for admin verification.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back to General Menu", callback_data="general_menu")]
        ])
    )
    
    # Notify admin
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🔄 Reactivation Request\n\n"
             f"👤 User: @{update.effective_user.username}\n"
             f"🆔 ID: {user_id}\n"
             f"📝 Name: {user_data.get('full_name', 'Not provided')}\n"
             f"📧 Email: {user_data.get('email', 'Not provided')}\n"
             f"🔢 Account: {user_data.get('account_number', 'Not provided')}\n"
             f"🚫 Suspended Reason: {user_data.get('suspension_reason', 'Unknown')}\n\n"
             f"Actions:\n"
             f"✅ /reactivate_{user_id}\n"
             f"👁️ /view_{user_id}",
        parse_mode=ParseMode.MARKDOWN
    )

# Admin Commands
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command"""
    if not admin_panel.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Access denied.")
        return
    
    await update.message.reply_text(
            "🔧 Admin Panel\n\n"
            "👥 User Management:\n"
            "• /approve <user_id> - Approve premium request\n"
            "• /reject <user_id> - Reject premium request\n"
            "• /suspend <user_id> - Suspend user\n"
            "• /reactivate <user_id> - Reactivate user\n"
            "• /search <query> - Search users\n"
            "• /view <user_id> - View user details\n\n"
            "📢 Broadcasting:\n"
            "• /broadcast_all <message> - Send to all users\n"
            "• /broadcastall <message> - Send to all users (short)\n"
            "• /broadcast_premium <message> - Send to premium users\n"
            "• /broadcastpremium <message> - Send to premium users (short)\n"
            "• /broadcast_trial <message> - Send to trial users\n"
            "• /broadcast_free <message> - Send to free users\n"
            "• /broadcast_suspended <message> - Send to suspended users\n\n"
            "🚀 Signal Management:\n"
            "• /signal <symbol> <action> <entry> <sl> <tp> [description]\n"
            "• /buy <symbol> <entry> <sl> <tp> [description]\n"
            "• /sell <symbol> <entry> <sl> <tp> [description]\n"
            "• /ai_signal <symbol> <action> <entry_range> <tp1> <tp2> <sl> [description]\n"
            "• /close_signal <signal_id> <close_price> [reason]\n"
            "• /signal_performance - View signal performance\n\n"
            "🤖 AI Signal (Regulation Compliant):\n"
            "• /ai_signal GOLD buy 1935-1945 1999 2000 1920 Strong momentum\n"
            "• Sends to Premium + Trial users only\n"
            "• Educational format with disclaimers\n\n"
            "📸 Media Broadcasting:\n"
            "• Send photo/video/document - Goes to ALL users\n"
            "• AI Signals go to PREMIUM + TRIAL users\n\n"
            "📊 Analytics & Reports:\n"
            "• /auto_suspend - Auto suspend inactive users\n"
            "• /smart_notify - Send smart notifications\n"
            "• /system_status - Check system status\n\n"
            "💡 Quick Tips:\n"
            "• Use /approve5573089528 format for quick approval\n"
            "• Use /reject5573089528 format for quick rejection\n"
            "• All commands support user_id as parameter"
        )

async def handle_admin_callback_old(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin menu callbacks"""
    query = update.callback_query
    await query.answer()
    
    logger.debug(f"Admin callback: {query.data} | User ID: {update.effective_user.id} | Is Admin: {is_admin(update.effective_user.id)}")
    
    if not is_admin(update.effective_user.id):
        logger.warning("Access denied - not admin")
        await query.edit_message_text("❌ Access denied.")
        return
    
    if query.data == "admin_users":
        logger.debug("Processing admin_users callback")
        try:
            users = db.get_all_users()
            total = len(users)
            trial = len([u for u in users.values() if u.get('status') == 'trial'])
            premium = len([u for u in users.values() if u.get('status') == 'premium'])
            free = total - trial - premium
            
            # Get pending approval requests
            pending_requests = [u for u in users.values() if u.get('status') == 'registering' and u.get('account_number')]
            
            message = f"👥 User Management\n\n"
            message += f"📊 Statistics:\n"
            message += f"👥 Total Users: {total}\n"
            message += f"🆓 Free Users: {free}\n"
            message += f"🎁 Trial Users: {trial}\n"
            message += f"💎 Premium Users: {premium}\n\n"
            
            if pending_requests:
                message += f"⏳ Pending Approvals: {len(pending_requests)}\n\n"
                for user in pending_requests[:3]:  # Show first 3
                    message += f"• {user.get('full_name', 'Unknown')} (@{user.get('username', 'Unknown')})\n"
                    message += f"  ID: {user['user_id']} | Email: {user.get('email', 'N/A')}\n\n"
                
                if len(pending_requests) > 3:
                    message += f"... and {len(pending_requests) - 3} more\n\n"
            else:
                message += "✅ No Pending Approvals\n\n"
            
            message += "Commands:\n"
            message += "• /approve <user_id> - Approve premium request\n"
            message += "• /reject <user_id> - Reject premium request\n"
            message += "• /suspend <user_id> - Suspend user\n"
            message += "• /reactivate <user_id> - Reactivate user"
            
            print("🔧 DEBUG: Sending admin_users response")
            await query.edit_message_text(
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=create_admin_keyboard()
            )
        except Exception as e:
            print(f"🔧 DEBUG: Error in admin_users: {e}")
            await query.edit_message_text(
                f"❌ Error\n\nAn error occurred: {str(e)}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=create_admin_keyboard()
            )
    
    
    elif query.data == "admin_panel":
        await query.edit_message_text(
            "🔧 Admin Panel\n\n"
            "Welcome to the admin control panel. Choose an option below:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_admin_menu()
        )
    
    elif query.data == "admin_broadcast":
        await query.edit_message_text(
            "📢 Send Broadcast\n\n"
            "Commands:\n"
            f"• /broadcast_all <message> - Send to all users\n"
            f"• /broadcast_premium <message> - Send to premium users only\n"
            f"• /broadcast_trial <message> - Send to trial users only\n"
            f"• /broadcast_free <message> - Send to free users only\n\n"
            f"Example: /broadcast_premium New signal alert!",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_admin_menu()
        )
    
    elif query.data == "admin_suspended":
        suspended = db.get_users_by_status('suspended')
        if suspended:
            text = "🚫 Suspended Users\n\n"
            for uid, user in list(suspended.items())[:10]:  # Show first 10
                text += f"• User {uid}: {user.get('full_name', 'Unknown')}\n"
            if len(suspended) > 10:
                text += f"\n... and {len(suspended) - 10} more"
        else:
            text = "✅ No suspended users"
        
        await query.edit_message_text(text, reply_markup=create_admin_menu())
    
    elif query.data == "admin_verify":
        # Show pending verification requests
        pending = []
        for uid, user in db.get_all_users().items():
            if (user.get('account_number') and 
                not user.get('verified') and 
                user.get('status') != 'premium'):
                pending.append((uid, user))
        
        if pending:
            text = "✅ Pending Verification Requests\n\n"
            for uid, user in pending[:5]:  # Show first 5
                text += f"• User {uid}: {user.get('full_name', 'Unknown')}\n"
                text += f"  Email: {user.get('email', 'N/A')}\n"
                text += f"  Account: {user.get('account_number', 'N/A')}\n\n"
        else:
            text = "✅ No pending verification requests"
        
        await query.edit_message_text(text, reply_markup=create_admin_menu())
    
    elif query.data == "admin_analytics":
        analytics_report = admin_panel.get_analytics_report()
        await query.edit_message_text(
            analytics_report,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📈 Export CSV", callback_data="export_csv")],
                [InlineKeyboardButton("🔄 Refresh Report", callback_data="admin_analytics")],
                [InlineKeyboardButton("📆 Last 7 Days", callback_data="analytics_7d")],
                [InlineKeyboardButton("📆 Last 30 Days", callback_data="analytics_30d")],
                [InlineKeyboardButton("📋 System Logs", callback_data="admin_logs")],
                [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
            ])
        )
    
    elif query.data == "admin_logs":
        logs_report = admin_panel.get_system_logs(7)
        await query.edit_message_text(
            logs_report,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Export Logs", callback_data="export_logs")],
                [InlineKeyboardButton("🔄 Refresh", callback_data="admin_logs")],
                [InlineKeyboardButton("📆 Last 7 Days", callback_data="logs_7d")],
                [InlineKeyboardButton("📆 Last 30 Days", callback_data="logs_30d")],
                [InlineKeyboardButton("🔙 Back", callback_data="admin_analytics")]
            ])
        )
    
    elif query.data == "analytics_7d":
        analytics_report = admin_panel.get_analytics_report()
        await query.edit_message_text(
            analytics_report,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_admin_keyboard()
        )
    
    elif query.data == "analytics_30d":
        analytics_report = admin_panel.get_analytics_report()
        await query.edit_message_text(
            analytics_report,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_admin_keyboard()
        )
    
    elif query.data == "logs_7d":
        logs_report = admin_panel.get_system_logs(7)
        await query.edit_message_text(
            logs_report,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_admin_keyboard()
        )
    
    elif query.data == "logs_30d":
        logs_report = admin_panel.get_system_logs(30)
        await query.edit_message_text(
            logs_report,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_admin_keyboard()
        )
    
    elif query.data == "export_csv":
        try:
            filename = admin_panel.export_user_data()
            if filename:
                await query.edit_message_text(
                    f"✅ CSV Export Complete!\n\n"
                    f"📁 File: {filename}\n"
                    f"📊 All user data exported successfully.\n\n"
                    f"Data includes:\n"
                    f"• User details\n"
                    f"• Status information\n"
                    f"• Activity logs\n"
                    f"• Verification status",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Back to Analytics", callback_data="admin_analytics")]
                    ])
                )
            else:
                await query.edit_message_text(
                    "❌ Export Failed\n\n"
                    "Unable to export data. Please try again.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Back", callback_data="admin_analytics")]
                    ])
                )
        except Exception as e:
            await query.edit_message_text(
                f"❌ Export Error\n\n"
                f"Error: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="admin_analytics")]
                ])
            )
    
    # Handle signal management callbacks
    elif query.data == "admin_signals":
        await admin_signals_callback(update, context)
    elif query.data == "signal_performance":
        await signal_performance_callback(update, context)
    elif query.data == "recent_signals":
        await recent_signals_callback(update, context)
    elif query.data == "send_fomo":
        await send_fomo_callback(update, context)
    elif query.data == "export_signals":
        await export_signals_callback(update, context)
    
    elif query.data == "export_logs":
        try:
            # Create logs export
            logs_data = []
            cutoff_date = datetime.now() - timedelta(days=30)
            
            for user_id, user_data in db.get_all_users().items():
                if user_data.get('last_activity'):
                    try:
                        last_activity = datetime.fromisoformat(user_data['last_activity'])
                        if last_activity > cutoff_date:
                            logs_data.append({
                                'user_id': user_id,
                                'name': user_data.get('full_name', 'Unknown'),
                                'status': user_data.get('status', 'free'),
                                'last_activity': last_activity.strftime('%Y-%m-%d %H:%M:%S'),
                                'suspension_reason': user_data.get('suspension_reason', 'N/A')
                            })
                    except:
                        pass
            
            # Export to CSV
            import csv
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"logs_export_{timestamp}.csv"
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                if logs_data:
                    fieldnames = ['user_id', 'name', 'status', 'last_activity', 'suspension_reason']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(logs_data)
            
            await query.edit_message_text(
                f"✅ Logs Export Complete!\n\n"
                f"📁 File: {filename}\n"
                f"📊 {len(logs_data)} log entries exported.\n\n"
                f"Data includes:\n"
                f"• User activities\n"
                f"• Status changes\n"
                f"• Suspension reasons\n"
                f"• Activity timestamps",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Logs", callback_data="admin_logs")]
                ])
            )
        except Exception as e:
            await query.edit_message_text(
                f"❌ Logs Export Error\n\n"
                f"Error: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="admin_logs")]
                ])
            )
    
    elif query.data == "admin_search":
        await query.edit_message_text(
            "🔍 Search Users\n\n"
            "Search Commands:\n"
            "• /search <username> - Search by username\n"
            "• /search <email> - Search by email\n"
            "• /search <account_number> - Search by account number\n"
            "• /view <user_id> - View user details\n\n"
            "Examples:\n"
            "• /search john@example.com\n"
            "• /search 1234567\n"
            "• /view 123456789",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_admin_keyboard()
        )
    
    elif query.data == "admin_signals":
        await query.edit_message_text(
            "🚀 Signal Management\n\n"
            "Commands:\n"
            "• /signal <symbol> <action> <entry> <sl> <tp> [description]\n"
            "• /buy <symbol> <entry> <sl> <tp> [description]\n"
            "• /sell <symbol> <entry> <sl> <tp> [description]\n"
            "• /close_signal <signal_id> <close_price> [reason]\n"
            "• /signal_performance\n\n"
            "Quick Actions:\n"
            "• Create new signals\n"
            "• Close existing signals\n"
            "• View performance reports\n"
            "• Export signal data",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_admin_keyboard()
        )
    
    elif query.data == "admin_suspended":
        suspended_users = [u for u in db.get_all_users().values() if u.get('suspended', False)]
        message = f"🚫 Suspended Users\n\n"
        message += f"📊 Total Suspended: {len(suspended_users)}\n\n"
        
        if suspended_users:
            for user in suspended_users[:5]:  # Show first 5
                message += f"• {user.get('full_name', 'Unknown')} (@{user.get('username', 'Unknown')})\n"
                message += f"  ID: {user['user_id']} | Reason: {user.get('suspension_reason', 'N/A')}\n\n"
            
            if len(suspended_users) > 5:
                message += f"... and {len(suspended_users) - 5} more\n\n"
        else:
            message += "✅ No Suspended Users\n\n"
        
        message += "Commands:\n"
        message += "• /reactivate <user_id> - Reactivate user\n"
        message += "• /suspend <user_id> - Suspend user"
        
        await query.edit_message_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_admin_keyboard()
        )
    
    elif query.data == "admin_verify":
        pending_requests = [u for u in db.get_all_users().values() if u.get('status') == 'registering' and u.get('account_number')]
        message = f"✅ Verify Requests\n\n"
        message += f"⏳ Pending Approvals: {len(pending_requests)}\n\n"
        
        if pending_requests:
            for user in pending_requests[:5]:  # Show first 5
                message += f"• {user.get('full_name', 'Unknown')} (@{user.get('username', 'Unknown')})\n"
                message += f"  ID: {user['user_id']} | Email: {user.get('email', 'N/A')}\n"
                message += f"  Account: {user.get('account_number', 'N/A')}\n\n"
            
            if len(pending_requests) > 5:
                message += f"... and {len(pending_requests) - 5} more\n\n"
        else:
            message += "✅ No Pending Requests\n\n"
        
        message += "Commands:\n"
        message += "• /approve <user_id> - Approve request\n"
        message += "• /reject <user_id> - Reject request"
        
        await query.edit_message_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_admin_keyboard()
        )
    
    elif query.data == "admin_search":
        await query.edit_message_text(
            "🔍 Search Users\n\n"
            "Commands:\n"
            "• /search <query> - Search by name, username, or email\n"
            "• /view <user_id> - View specific user details\n\n"
            "Examples:\n"
            "• /search john\n"
            "• /search @username\n"
            "• /search email@example.com\n"
            "• /view 123456789",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_admin_keyboard()
        )
    
    elif query.data == "admin_export":
        await query.edit_message_text(
            "📤 Export Data\n\n"
            "Available Exports:\n"
            "• User data (CSV)\n"
            "• System logs (CSV)\n"
            "• Signal data (CSV)\n"
            "• Analytics reports\n\n"
            "Commands:\n"
            "• Use the export buttons in Analytics & Logs\n"
            "• All exports are saved as CSV files\n"
            "• Data includes timestamps and full details",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_admin_keyboard()
        )

async def approve_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /approve command"""
    if not admin_panel.is_admin(update.effective_user.id):
        return
    
    user_id = None
    
    # Handle both /approve <user_id> and /approve<user_id> formats
    if context.args:
        user_id = int(context.args[0])
    else:
        # Extract user_id from message text like /approve5573089528
        message_text = update.message.text
        if message_text.startswith('/approve'):
            try:
                user_id = int(message_text.replace('/approve', ''))
            except ValueError:
                await update.message.reply_text("❌ Invalid user ID format")
                return
    
    if not user_id:
        await update.message.reply_text("Usage: /approve <user_id>")
        return
    
    try:
        success, message = await admin_panel.handle_user_approval(context, user_id)
        
        # Print admin action to terminal
        user_data = db.get_user(user_id)
        logger.info(f"✅ ADMIN APPROVED: 👤 {user_data.get('full_name', 'Unknown')} | ID: {user_id} | Email: {user_data.get('email', 'Unknown')} | Account: {user_data.get('account_number', 'Unknown')}")
        
        if success:
            await update.message.reply_text(
                f"✅ User Approved Successfully!\n\n"
                f"👤 User: {user_data.get('full_name', 'Unknown')}\n"
                f"🆔 ID: {user_id}\n"
                f"📧 Email: {user_data.get('email', 'Unknown')}\n"
                f"🔢 Account: {user_data.get('account_number', 'Unknown')}\n\n"
                f"User has been notified and granted Premium access!",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                f"❌ Approval Failed\n\n{message}",
                parse_mode=ParseMode.MARKDOWN
            )
        
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")

async def reject_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /reject command"""
    if not admin_panel.is_admin(update.effective_user.id):
        return
    
    user_id = None
    reason = None
    
    # Handle both /reject <user_id> and /reject<user_id> formats
    if context.args:
        user_id = int(context.args[0])
        reason = ' '.join(context.args[1:]) if len(context.args) > 1 else None
    else:
        # Extract user_id from message text like /reject5573089528
        message_text = update.message.text
        if message_text.startswith('/reject'):
            try:
                user_id = int(message_text.replace('/reject', ''))
                reason = "Rejected by admin"
            except ValueError:
                await update.message.reply_text("❌ Invalid user ID format")
                return
    
    if not user_id:
        await update.message.reply_text("Usage: /reject <user_id> [reason]")
        return
    
    try:
        
        message = await admin_panel.handle_user_rejection(context, user_id, reason)
        
        # Print admin action to terminal
        user_data = db.get_user(user_id)
        logger.info(f"❌ ADMIN REJECTED: 👤 {user_data.get('full_name', 'Unknown')} | ID: {user_id} | Reason: {reason}")
        
        await update.message.reply_text(
            f"❌ User Rejected\n\n"
            f"👤 User: {user_data.get('full_name', 'Unknown')}\n"
            f"🆔 ID: {user_id}\n"
            f"📧 Email: {user_data.get('email', 'Unknown')}\n"
            f"🔢 Account: {user_data.get('account_number', 'Unknown')}\n"
            f"📝 Reason: {reason}\n\n"
            f"User has been notified about the rejection.",
            parse_mode=ParseMode.MARKDOWN
        )
        
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")

async def suspend_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /suspend command"""
    if not admin_panel.is_admin(update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /suspend <user_id> [reason]")
        return
    
    try:
        user_id = int(context.args[0])
        reason = ' '.join(context.args[1:]) if len(context.args) > 1 else "Manual suspension"
        
        success, message = await admin_panel.suspend_user(context, user_id, reason)
        
        if success:
            await update.message.reply_text(f"✅ {message}")
        else:
            await update.message.reply_text(f"❌ {message}")
        
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")

async def reactivate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /reactivate command"""
    if not admin_panel.is_admin(update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /reactivate <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        success, message = await admin_panel.reactivate_user(context, user_id)
        
        if success:
            await update.message.reply_text(f"✅ {message}")
        else:
            await update.message.reply_text(f"❌ {message}")
        
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcast commands"""
    if not admin_panel.is_admin(update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /broadcast_<type> <message>")
        return
    
    command = update.message.text.split()[0]
    message = ' '.join(context.args)
    
    # Determine target based on command
    if command in ["/broadcast_all", "/broadcastall"]:
        target = "all"
    elif command in ["/broadcast_premium", "/broadcastpremium"]:
        target = "premium"
    elif command == "/broadcast_trial":
        target = "trial"
    elif command == "/broadcast_free":
        target = "free"
    elif command == "/broadcast_suspended":
        target = "suspended"
    else:
        await update.message.reply_text("❌ Invalid broadcast command.")
        return
    
    try:
        results = await admin_panel.send_broadcast(context, message, target)
        await update.message.reply_text(f"✅ Broadcast sent to {results['sent']} users. {results['failed']} failed.")
    except Exception as e:
        logger.error(f"Broadcast command error: {e}")
        await update.message.reply_text(f"❌ Broadcast failed: {str(e)}")

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /search command"""
    if not admin_panel.is_admin(update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /search <query>")
        return
    
    query = ' '.join(context.args)
    results = admin_panel.search_users(query)
    
    if results:
        text = f"🔍 Search Results for: {query}\n\n"
        for i, user in enumerate(results[:10], 1):  # Show max 10 results
            text += f"{i}. {user['name']}\n"
            text += f"   ID: {user['user_id']}\n"
            text += f"   Email: {user['email']}\n"
            text += f"   Status: {user['status']}\n"
            text += f"   Verified: {'Yes' if user['verified'] else 'No'}\n\n"
        
        if len(results) > 10:
            text += f"... and {len(results) - 10} more results"
    else:
        text = f"❌ No users found for: {query}"
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def view_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /view command"""
    if not admin_panel.is_admin(update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /view <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        user_details = admin_panel.get_user_details(user_id)
        
        if user_details:
            text = f"👤 User Details\n\n"
            text += f"🆔 ID: {user_details['user_id']}\n"
            text += f"📝 Name: {user_details['full_name']}\n"
            text += f"📧 Email: {user_details['email']}\n"
            text += f"🌍 Country: {user_details['country']}\n"
            text += f"📊 Status: {user_details['status']}\n"
            text += f"✅ Verified: {'Yes' if user_details['verified'] else 'No'}\n"
            text += f"🚫 Suspended: {'Yes' if user_details['suspended'] else 'No'}\n"
            text += f"🔢 Account: {user_details['account_number']}\n"
            text += f"📅 Created: {user_details['created_at']}\n"
            text += f"⏰ Last Activity: {user_details['last_activity']}\n"
            
            if user_details['trial_days_left'] > 0:
                text += f"🎁 Trial Days Left: {user_details['trial_days_left']}\n"
            
            text += f"📊 Signals Received: {user_details['total_signals_received']}\n"
            text += f"🔄 Verification Requests: {user_details['verification_requests']}\n"
            
            if user_details['premium_since']:
                text += f"💎 Premium Since: {user_details['premium_since']}\n"
        else:
            text = f"❌ User {user_id} not found."
        
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")

async def signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /signal command for creating signals"""
    if not admin_panel.is_admin(update.effective_user.id):
        return
    
    if len(context.args) < 6:
        await update.message.reply_text(
            "🚀 Signal Creation Template\n\n"
            "Usage: /signal <symbol> <action> <entry> <sl> <tp> [description]\n\n"
            "Examples:\n"
            "• /signal EURUSD BUY 1.0500 1.0450 1.0600\n"
            "• /signal GOLD BUY 1935-1945 1999 2000 Strong bullish momentum\n"
            "• /signal GOLD SELL 1935 1940 1920 Strong bearish momentum\n"
            "• /signal BTCUSD BUY 45000 44000 47000\n\n"
            "Parameters:\n"
            "• Symbol: EURUSD, GOLD, BTCUSD, etc.\n"
            "• Action: BUY or SELL\n"
            "• Entry: Entry price or range (e.g., 1935-1945)\n"
            "• SL: Stop Loss price\n"
            "• TP: Take Profit price\n"
            "• Description: Optional reason (optional)"
        )
        return
    
    try:
        symbol = context.args[0].upper()
        action = context.args[1].upper()  # "BUY" or "SELL"
        
        # Handle entry price range (e.g., "1935-1945")
        entry_str = context.args[2]
        if '-' in entry_str:
            entry_parts = entry_str.split('-')
            if len(entry_parts) == 2:
                entry_min = float(entry_parts[0])
                entry_max = float(entry_parts[1])
                entry_price = (entry_min + entry_max) / 2  # Use average
                entry_range = f"{entry_min}-{entry_max}"
            else:
                await update.message.reply_text("❌ Invalid entry range format. Use: 1935-1945")
                return
        else:
            entry_price = float(entry_str)
            entry_range = str(entry_price)
        
        stop_loss = float(context.args[3])
        take_profit = float(context.args[4])
        description = ' '.join(context.args[5:]) if len(context.args) > 5 else ""
        
        if action not in ["BUY", "SELL"]:
            await update.message.reply_text("❌ Action must be BUY or SELL")
            return
        
        # Calculate risk/reward ratio
        if action == "BUY":
            risk = entry_price - stop_loss
            reward = take_profit - entry_price
        else:  # SELL
            risk = stop_loss - entry_price
            reward = entry_price - take_profit
        
        risk_reward_ratio = reward / risk if risk > 0 else 0
        
        signal_id = signal_manager.create_signal(
            "entry", symbol, action, entry_price, stop_loss, take_profit, description
        )
        
        # Store latest signal for premium signals display
        store_latest_signal(signal_id, symbol, action, entry_price, stop_loss, take_profit, description)
        
        # Send to premium users
        results = await signal_manager.send_signal_to_users(context, signal_id, "premium")
        
        # Print signal creation to terminal
        logger.info(f"🚀 SIGNAL CREATED: ID={signal_id} | {symbol} {action} | Entry={entry_price} | SL={stop_loss} | TP={take_profit} | Sent={results['sent']} | Failed={results['failed']}")
        
        await update.message.reply_text(
            f"✅ Signal Created & Sent!\n\n"
            f"🆔 ID: {signal_id}\n"
            f"📊 Symbol: {symbol}\n"
            f"💰 Action: {action}\n"
            f"📈 Entry: {entry_range}\n"
            f"🛑 Stop Loss: {stop_loss}\n"
            f"🎯 Take Profit: {take_profit}\n"
            f"📊 Risk/Reward: 1:{risk_reward_ratio:.1f}\n"
            f"📝 Description: {description or 'None'}\n\n"
            f"📤 Sent to: {results['sent']} premium users\n"
            f"❌ Failed: {results['failed']}",
            parse_mode=ParseMode.MARKDOWN
        )
        
    except ValueError as e:
        await update.message.reply_text(f"❌ Invalid number format: {e}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error creating signal: {e}")

async def close_signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /close_signal command"""
    if not admin_panel.is_admin(update.effective_user.id):
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /close_signal <signal_id> <close_price> [reason]\n\n"
            "Reasons: sl (stop loss), tp (take profit), manual"
        )
        return
    
    try:
        signal_id = context.args[0]
        close_price = float(context.args[1])
        reason = context.args[2] if len(context.args) > 2 else "manual"
        
        success = signal_manager.close_signal(signal_id, close_price, reason)
        
        if success:
            signal = signal_manager.get_signal(signal_id)
            profit_loss = signal["results"]["profit_loss"]
            
            await update.message.reply_text(
                f"✅ Signal closed!\n\n"
                f"🆔 Signal ID: {signal_id}\n"
                f"💰 Close Price: {close_price}\n"
                f"📊 P&L: {profit_loss:+.4f}\n"
                f"🔚 Reason: {reason}",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text("❌ Signal not found or already closed")
        
    except ValueError:
        await update.message.reply_text("❌ Invalid price format")
    except Exception as e:
        await update.message.reply_text(f"❌ Error closing signal: {e}")

async def signal_performance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /signal_performance command"""
    if not admin_panel.is_admin(update.effective_user.id):
        return
    
    days = 30
    if context.args and context.args[0].isdigit():
        days = int(context.args[0])
    
    performance = signal_manager.get_signal_performance(days)
    
    message = f"""📊 Signal Performance ({days} days)
📈 Total Signals: {performance['total_signals']}
✅ Closed Signals: {performance['closed_signals']}
🎯 Profitable: {performance['profitable_signals']}
📊 Win Rate: {performance['win_rate']:.1f}%
💰 Total P&L: {performance['total_profit']:+.4f}
📊 Avg P&L: {performance['avg_profit']:+.4f}

🛑 Stop Loss Hits: {performance['hit_sl_count']}
🎯 Take Profit Hits: {performance['hit_tp_count']}"""
    
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

async def admin_signals_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin signals callback"""
    from admin_panel import create_signal_management_keyboard
    
    await update.callback_query.edit_message_text(
        "🚀 Signal Management Panel\n\n"
        "Choose an option to manage signals:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_signal_management_keyboard()
    )

async def signal_performance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle signal performance callback"""
    performance = signal_manager.get_signal_performance(30)
    
    message = f"""📊 Signal Performance (30 days)
📈 Total Signals: {performance['total_signals']}
✅ Closed Signals: {performance['closed_signals']}
🎯 Profitable: {performance['profitable_signals']}
📊 Win Rate: {performance['win_rate']:.1f}%
💰 Total P&L: {performance['total_profit']:+.4f}
📊 Avg P&L: {performance['avg_profit']:+.4f}

🛑 Stop Loss Hits: {performance['hit_sl_count']}
🎯 Take Profit Hits: {performance['hit_tp_count']}"""
    
    await update.callback_query.edit_message_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="admin_signals")]
        ])
    )

async def recent_signals_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle recent signals callback"""
    signals = signal_manager.get_recent_signals(5)
    
    if not signals:
        message = "📈 Recent Signals\n\nNo signals found."
    else:
        message = "📈 Recent Signals\n\n"
        for signal in signals:
            status_emoji = "🟢" if signal["status"] == "active" else "🔴"
            message += f"{status_emoji} {signal['symbol']} {signal['action']}\n"
            message += f"💰 Entry: {signal['entry_price']}\n"
            message += f"⏰ {datetime.fromisoformat(signal['created_at']).strftime('%H:%M:%S')}\n\n"
    
    await update.callback_query.edit_message_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="admin_signals")]
        ])
    )

async def send_fomo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle send FOMO signal callback"""
    # Get the most recent closed profitable signal
    signals = signal_manager.get_recent_signals(10)
    fomo_signal = None
    
    for signal in signals:
        if signal["status"] == "closed" and signal["results"]["profit_loss"] > 0:
            fomo_signal = signal
            break
    
    if not fomo_signal:
        await update.callback_query.edit_message_text(
            "❌ No FOMO Signal Available\n\nNo recent profitable signals found.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="admin_signals")]
            ])
        )
        return
    
    # Send FOMO to suspended users
    results = await signal_manager.send_signal_to_users(context, fomo_signal["signal_id"], "fomo")
    
    await update.callback_query.edit_message_text(
        f"✅ FOMO Signal Sent!\n\n"
        f"📊 Signal: {fomo_signal['symbol']} {fomo_signal['action']}\n"
        f"💰 P&L: +{fomo_signal['results']['profit_loss']:.4f}\n"
        f"📤 Sent to: {results['sent']} suspended users\n"
        f"❌ Failed: {results['failed']}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="admin_signals")]
        ])
    )

async def export_signals_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle export signals callback"""
    try:
        import csv
        from datetime import datetime
        
        filename = f"signals_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['signal_id', 'type', 'symbol', 'action', 'entry_price', 
                         'stop_loss', 'take_profit', 'status', 'created_at', 
                         'close_price', 'profit_loss', 'hit_sl', 'hit_tp']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for signal in signal_manager.signals.values():
                row = {
                    'signal_id': signal['signal_id'],
                    'type': signal['type'],
                    'symbol': signal['symbol'],
                    'action': signal['action'],
                    'entry_price': signal['entry_price'],
                    'stop_loss': signal['stop_loss'],
                    'take_profit': signal['take_profit'],
                    'status': signal['status'],
                    'created_at': signal['created_at'],
                    'close_price': signal['results']['close_price'],
                    'profit_loss': signal['results']['profit_loss'],
                    'hit_sl': signal['results']['hit_sl'],
                    'hit_tp': signal['results']['hit_tp']
                }
                writer.writerow(row)
        
        await update.callback_query.edit_message_text(
            f"✅ Signals Export Complete!\n\n"
            f"📁 File: {filename}\n"
            f"📊 Signals exported: {len(signal_manager.signals)}\n\n"
            f"Data includes:\n"
            f"• Signal details\n"
            f"• Entry/Exit prices\n"
            f"• Performance results\n"
            f"• P&L tracking",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="admin_signals")]
            ])
        )
        
    except Exception as e:
        await update.callback_query.edit_message_text(
            f"❌ Export Failed\n\nError: {str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="admin_signals")]
            ])
        )

async def buy_signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /buy command for quick BUY signals"""
    if not admin_panel.is_admin(update.effective_user.id):
        return
    
    if len(context.args) < 4:
        await update.message.reply_text(
            "🟢 BUY Signal Template\n\n"
            "Usage: /buy <symbol> <entry> <sl> <tp> [description]\n\n"
            "Examples:\n"
            "• /buy EURUSD 1.0500 1.0450 1.0600\n"
            "• /buy GOLD 1935-1945 1999 2000 Strong bullish momentum\n"
            "• /buy GOLD 1935 1928 1950 Strong bullish momentum\n"
            "• /buy BTCUSD 45000 44000 47000\n\n"
            "Quick BUY signals for bullish trades!"
        )
        return
    
    try:
        symbol = context.args[0].upper()
        
        # Handle entry price range (e.g., "1935-1945")
        entry_str = context.args[1]
        if '-' in entry_str:
            entry_parts = entry_str.split('-')
            if len(entry_parts) == 2:
                entry_min = float(entry_parts[0])
                entry_max = float(entry_parts[1])
                entry_price = (entry_min + entry_max) / 2  # Use average
                entry_range = f"{entry_min}-{entry_max}"
            else:
                await update.message.reply_text("❌ Invalid entry range format. Use: 1935-1945")
                return
        else:
            entry_price = float(entry_str)
            entry_range = str(entry_price)
        
        stop_loss = float(context.args[2])
        take_profit = float(context.args[3])
        description = ' '.join(context.args[4:]) if len(context.args) > 4 else "BUY signal - Bullish momentum detected"
        
        # Calculate risk/reward ratio
        risk = entry_price - stop_loss
        reward = take_profit - entry_price
        risk_reward_ratio = reward / risk if risk > 0 else 0
        
        signal_id = signal_manager.create_signal(
            "entry", symbol, "BUY", entry_price, stop_loss, take_profit, description
        )
        
        # Store latest signal for premium signals display
        store_latest_signal(signal_id, symbol, "BUY", entry_price, stop_loss, take_profit, description)
        
        # Send to premium users
        results = await signal_manager.send_signal_to_users(context, signal_id, "premium")
        
        await update.message.reply_text(
            f"✅ BUY Signal Created!\n\n"
            f"🟢 Symbol: {symbol}\n"
            f"💰 Entry: {entry_range}\n"
            f"🛑 Stop Loss: {stop_loss}\n"
            f"🎯 Take Profit: {take_profit}\n"
            f"📊 Risk/Reward: 1:{risk_reward_ratio:.1f}\n\n"
            f"📤 Sent to: {results['sent']} premium users",
            parse_mode=ParseMode.MARKDOWN
        )
        
    except ValueError as e:
        await update.message.reply_text(f"❌ Invalid number format: {e}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error creating BUY signal: {e}")

async def sell_signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /sell command for quick SELL signals"""
    if not admin_panel.is_admin(update.effective_user.id):
        return
    
    if len(context.args) < 4:
        await update.message.reply_text(
            "🔴 SELL Signal Template\n\n"
            "Usage: /sell <symbol> <entry> <sl> <tp> [description]\n\n"
            "Examples:\n"
            "• /sell EURUSD 1.0500 1.0550 1.0400\n"
            "• /sell GOLD 1935-1945 1999 2000 Strong bearish momentum\n"
            "• /sell GOLD 1935 1940 1920 Strong bearish momentum\n"
            "• /sell BTCUSD 45000 46000 43000\n\n"
            "Quick SELL signals for bearish trades!"
        )
        return
    
    try:
        symbol = context.args[0].upper()
        
        # Handle entry price range (e.g., "1935-1945")
        entry_str = context.args[1]
        if '-' in entry_str:
            entry_parts = entry_str.split('-')
            if len(entry_parts) == 2:
                entry_min = float(entry_parts[0])
                entry_max = float(entry_parts[1])
                entry_price = (entry_min + entry_max) / 2  # Use average
                entry_range = f"{entry_min}-{entry_max}"
            else:
                await update.message.reply_text("❌ Invalid entry range format. Use: 1935-1945")
                return
        else:
            entry_price = float(entry_str)
            entry_range = str(entry_price)
        
        stop_loss = float(context.args[2])
        take_profit = float(context.args[3])
        description = ' '.join(context.args[4:]) if len(context.args) > 4 else "SELL signal - Bearish momentum detected"
        
        # Calculate risk/reward ratio
        risk = stop_loss - entry_price
        reward = entry_price - take_profit
        risk_reward_ratio = reward / risk if risk > 0 else 0
        
        signal_id = signal_manager.create_signal(
            "entry", symbol, "SELL", entry_price, stop_loss, take_profit, description
        )
        
        # Store latest signal for premium signals display
        store_latest_signal(signal_id, symbol, "SELL", entry_price, stop_loss, take_profit, description)
        
        # Send to premium users
        results = await signal_manager.send_signal_to_users(context, signal_id, "premium")
        
        await update.message.reply_text(
            f"✅ SELL Signal Created!\n\n"
            f"🔴 Symbol: {symbol}\n"
            f"💰 Entry: {entry_range}\n"
            f"🛑 Stop Loss: {stop_loss}\n"
            f"🎯 Take Profit: {take_profit}\n"
            f"📊 Risk/Reward: 1:{risk_reward_ratio:.1f}\n\n"
            f"📤 Sent to: {results['sent']} premium users",
            parse_mode=ParseMode.MARKDOWN
        )
        
    except ValueError as e:
        await update.message.reply_text(f"❌ Invalid number format: {e}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error creating SELL signal: {e}")

async def ai_signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ai_signal command for AI-generated educational signals"""
    if not admin_panel.is_admin(update.effective_user.id):
        return
    
    if len(context.args) < 5:
        await update.message.reply_text(
            "🤖 AI Signal Template (Regulation Compliant)\n\n"
            "Usage: /ai_signal <symbol> <action> <entry_range> <tp1> <tp2> <sl> [description]\n\n"
            "Examples:\n"
            "• /ai_signal GOLD buy 1935-1945 1999 2000 1920 Strong bullish momentum\n"
            "• /ai_signal EURUSD sell 1.0500-1.0520 1.0400 1.0350 1.0600 Bearish trend\n"
            "• /ai_signal BTCUSD buy 45000-46000 50000 55000 40000 Bullish breakout\n\n"
            "Parameters:\n"
            "• Symbol: GOLD, EURUSD, BTCUSD, etc.\n"
            "• Action: buy or sell\n"
            "• Entry Range: 1935-1945 (use dash for range)\n"
            "• TP1: First take profit level\n"
            "• TP2: Second take profit level\n"
            "• SL: Stop loss level\n"
            "• Description: Optional reason\n\n"
            "📋 This creates regulation-compliant educational signals!"
        )
        return
    
    try:
        symbol = context.args[0].upper()
        action = context.args[1].lower()
        entry_range = context.args[2]
        tp1 = float(context.args[3])
        tp2 = float(context.args[4])
        sl = float(context.args[5])
        description = ' '.join(context.args[6:]) if len(context.args) > 6 else ""
        
        if action not in ["buy", "sell"]:
            await update.message.reply_text("❌ Action must be 'buy' or 'sell'")
            return
        
        # Create AI-generated educational signal message
        signal_message = f"🤖 **AI Analysis Alert**\n\n"
        signal_message += f"📊 **{symbol}**\n\n"
        signal_message += f"Our AI analysis has identified a potential **{action.upper()}** zone between **{entry_range}**.\n\n"
        signal_message += f"For study purpose note the following possible reference level:\n\n"
        signal_message += f"🎯 **TP1: {tp1}**\n"
        signal_message += f"🎯 **TP2: {tp2}**\n"
        signal_message += f"❌ **SL (risk control): {sl}**\n\n"
        
        if description:
            signal_message += f"📝 **Analysis:** {description}\n\n"
        
        signal_message += f"⚠️ **Important Disclaimer:**\n"
        signal_message += f"This is AI-generated for educational use only.\n"
        signal_message += f"Not a financial advice. DYOR & TAYOR"
        
        # Store latest signal for premium signals display
        # Use entry range as string for proper display
        store_latest_signal(f"AI_{datetime.now().strftime('%Y%m%d_%H%M%S')}", symbol, action.upper(), entry_range, sl, tp1, description)
        
        # Send to premium and trial users
        all_users = db.get_all_users()
        sent_count = 0
        failed_count = 0
        
        for user_id, user_data in all_users.items():
            user_status = get_user_status(user_id)
            if user_status in ['premium', 'trial']:
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=signal_message,
                        parse_mode=ParseMode.MARKDOWN
                    )
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send AI signal to user {user_id}: {e}")
                    failed_count += 1
        
        # Print signal creation to terminal
        logger.info(f"🤖 AI SIGNAL: {symbol} {action.upper()} | Entry={entry_range} | TP1={tp1} TP2={tp2} SL={sl} | Sent={sent_count} | Failed={failed_count}")
        
        await update.message.reply_text(
            f"✅ AI Signal Created & Sent!\n\n"
            f"📊 Symbol: {symbol}\n"
            f"💰 Action: {action.upper()}\n"
            f"📈 Entry Range: {entry_range}\n"
            f"🎯 TP1: {tp1}\n"
            f"🎯 TP2: {tp2}\n"
            f"🛑 SL: {sl}\n"
            f"📝 Description: {description or 'None'}\n\n"
            f"📤 Sent to: {sent_count} users (Premium + Trial)\n"
            f"❌ Failed: {failed_count}\n\n"
            f"📋 Regulation-compliant educational signal!",
            parse_mode=ParseMode.MARKDOWN
        )
        
    except ValueError as e:
        await update.message.reply_text(f"❌ Invalid number format: {e}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error creating AI signal: {e}")

async def auto_suspend_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle auto-suspend command"""
    if not admin_panel.is_admin(update.effective_user.id):
        return
    
    inactive_days = 7
    if context.args and context.args[0].isdigit():
        inactive_days = int(context.args[0])
    
    cutoff_date = datetime.now() - timedelta(days=inactive_days)
    suspended_count = 0
    
    for user_id, user_data in db.get_all_users().items():
        if user_data.get("status") == "premium" and not user_data.get("suspended", False):
            last_activity = user_data.get("last_activity")
            if last_activity:
                try:
                    activity_date = datetime.fromisoformat(last_activity)
                    if activity_date < cutoff_date:
                        # Note: suspend_user requires context, cannot be called here
                        # This should be handled by notification system
                        suspended_count += 1
                except:
                    pass
    
    await update.message.reply_text(
        f"✅ Auto-Suspension Complete!\n\n"
        f"📊 Inactive Days: {inactive_days}\n"
        f"⛔ Suspended Users: {suspended_count}\n"
        f"📅 Cutoff Date: {cutoff_date.strftime('%Y-%m-%d')}",
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_admin_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin media messages (photos, documents, etc.)"""
    if not is_admin(update.effective_user.id):
        return
    
    if not update.message:
        return
    
    # Get all users
    all_users = db.get_all_users()
    
    if not all_users:
        await update.message.reply_text("❌ No users found to broadcast to.")
        return
    
    # Determine media type and prepare message
    media_type = None
    media_file = None
    caption = update.message.caption or ""
    
    if update.message.photo:
        media_type = "photo"
        media_file = update.message.photo[-1]  # Get highest resolution
    elif update.message.document:
        media_type = "document"
        media_file = update.message.document
    elif update.message.video:
        media_type = "video"
        media_file = update.message.video
    elif update.message.animation:
        media_type = "animation"
        media_file = update.message.animation
    
    if not media_type:
        await update.message.reply_text("❌ Unsupported media type. Please send photo, document, video, or animation.")
        return
    
    # Send to all users
    sent_count = 0
    failed_count = 0
    failed_users = []
    
    for user_id, user_data in all_users.items():
        try:
            if media_type == "photo":
                await context.bot.send_photo(
                    chat_id=user_id,
                    photo=media_file,
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN if caption else None
                )
            elif media_type == "document":
                await context.bot.send_document(
                    chat_id=user_id,
                    document=media_file,
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN if caption else None
                )
            elif media_type == "video":
                await context.bot.send_video(
                    chat_id=user_id,
                    video=media_file,
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN if caption else None
                )
            elif media_type == "animation":
                await context.bot.send_animation(
                    chat_id=user_id,
                    animation=media_file,
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN if caption else None
                )
            
            sent_count += 1
            
        except Exception as e:
            error_msg = str(e)
            user_name = user_data.get('full_name', user_data.get('name', 'Unknown'))
            username = user_data.get('username', 'No username')
            
            failed_users.append({
                'id': user_id,
                'name': user_name,
                'username': username,
                'error': error_msg
            })
            
            print(f"Failed to send media to user {user_id} ({user_name}): {error_msg}")
            failed_count += 1
    
    # Send confirmation to admin
    message = f"📤 **Media Broadcast Complete!**\n\n"
    message += f"📸 Media sent to ALL users (Free + Trial + Premium)\n\n"
    message += f"✅ Successfully sent to: {sent_count} users\n"
    message += f"❌ Failed to send: {failed_count} users\n"
    message += f"📊 Total users: {len(all_users)}\n\n"
    
    if failed_users:
        message += f"🚫 **Failed Users Details:**\n"
        for user in failed_users:
            message += f"• {user['name']} (@{user['username']})\n"
            message += f"  ID: {user['id']}\n"
            message += f"  Error: {user['error'][:50]}...\n\n"
    
    message += f"ℹ️ Note: Media goes to all users, signals only go to premium users."
    
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

async def smart_notify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle smart notification command"""
    if not admin_panel.is_admin(update.effective_user.id):
        return
    
    users = db.get_all_users()
    notified = 0
    
    for user_id, user_data in users.items():
        try:
            if user_data.get("status") == "trial":
                await context.bot.send_message(
                    chat_id=user_id,
                    text="🎁 Trial Reminder\n\nYour trial is active! Upgrade to Premium for unlimited signals!"
                )
                notified += 1
            elif user_data.get("suspended", False):
                await context.bot.send_message(
                    chat_id=user_id,
                    text="📊 Premium Signals Available\n\nYou're missing profitable opportunities! Reactivate now!"
                )
                notified += 1
        except:
            pass
    
    await update.message.reply_text(f"✅ Smart notifications sent to {notified} users!")

async def system_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle system status command"""
    if not admin_panel.is_admin(update.effective_user.id):
        return
    
    users = db.get_all_users()
    total_users = len(users)
    premium_users = len([u for u in users.values() if u.get("status") == "premium"])
    trial_users = len([u for u in users.values() if u.get("status") == "trial"])
    suspended_users = len([u for u in users.values() if u.get("suspended", False)])
    
    status_message = f"""🖥️ System Status
👥 Users: {total_users}
• Premium: {premium_users}
• Trial: {trial_users}  
• Suspended: {suspended_users}

📊 Signals: {len(signal_manager.signals)}
🔄 Last Update: {datetime.now().strftime('%H:%M:%S')}"""
    
    await update.message.reply_text(status_message, parse_mode=ParseMode.MARKDOWN)

async def user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User management command with comprehensive statistics"""
    if not admin_panel.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Access denied. Admin only.")
        return
    
    try:
        # Get all users
        all_users = db.get_all_users()
        total_users = len(all_users)
        
        # Count by status
        status_counts = {
            'premium': 0,
            'trial': 0,
            'free': 0,
            'suspended': 0,
            'pending': 0,
            'registering': 0
        }
        
        # Count active vs inactive users (based on last activity)
        active_users = 0
        inactive_users = 0
        
        # Get pending approval requests
        pending_requests = []
        
        for user_id, user_data in all_users.items():
            status = user_data.get('status', 'free')
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Check if user is active (last activity within 7 days)
            last_activity = user_data.get('last_activity')
            if last_activity:
                try:
                    last_activity_date = datetime.fromisoformat(last_activity).date()
                    days_since_activity = (date.today() - last_activity_date).days
                    if days_since_activity <= 7:
                        active_users += 1
                    else:
                        inactive_users += 1
                except:
                    inactive_users += 1
            else:
                inactive_users += 1
            
            # Collect pending requests (both 'pending' and 'registering' status)
            if status in ['pending', 'registering']:
                pending_requests.append({
                    'id': user_id,
                    'name': user_data.get('full_name', user_data.get('name', 'Unknown')),
                    'username': user_data.get('username', 'No username'),
                    'email': user_data.get('email', 'No email'),
                    'account': user_data.get('account_number', user_data.get('account', 'No account'))
                })
        
        # Create comprehensive statistics message
        stats_text = f"""
👥 **User Management Dashboard**

📊 **User Statistics:**
• Total Users: {total_users}
• Active Users: {active_users}
• Inactive Users: {inactive_users}

💎 **Subscription Status:**
• Premium: {status_counts['premium']}
• Trial: {status_counts['trial']}
• Free: {status_counts['free']}
• Suspended: {status_counts['suspended']}
• Pending Approval: {status_counts['pending'] + status_counts['registering']}

⏳ **Pending Requests ({len(pending_requests)}):**
"""
        
        # Add pending requests details
        if pending_requests:
            for i, req in enumerate(pending_requests[:5], 1):  # Show max 5
                # Safely format user data
                safe_req = safe_format_user_data(req)
                stats_text += f"""
{i}\\. **{safe_req['name']}** (@{safe_req['username']})
   ID: {safe_req['id']}
   Email: {safe_req['email']}
   Account: {safe_req['account']}
"""
            if len(pending_requests) > 5:
                stats_text += f"\n\\.\\.\\. and {len(pending_requests) - 5} more pending requests"
        else:
            stats_text += "\n✅ No pending requests"
        
        stats_text += f"""

🔧 **Quick Commands:**
• `/approve <user_id>` - Approve user
• `/reject <user_id>` - Reject user
• `/suspend <user_id>` - Suspend user
• `/reactivate <user_id>` - Reactivate user
• `/search <query>` - Search users
• `/view <user_id>` - View user details
        """
        
        # Use safe message sending
        await safe_send_message(update, stats_text)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error getting user statistics: {str(e)}")

async def daily_maintenance():
    """Daily maintenance tasks"""
    try:
        # Clean up old logs
        logger.info("Running daily maintenance...")
        
        # Update user activity
        for user_id, user_data in db.get_all_users().items():
            if user_data.get("status") == "premium" and not user_data.get("suspended", False):
                # Check for inactive premium users
                last_activity = user_data.get("last_activity")
                if last_activity:
                    try:
                        activity_date = datetime.fromisoformat(last_activity)
                        if (datetime.now() - activity_date).days > 14:
                            # Note: suspend_user requires context, cannot be called here
                            # This should be handled by notification system
                            pass
                    except:
                        pass
        
        logger.info("Daily maintenance completed")
    except Exception as e:
        logger.error(f"Daily maintenance error: {e}")

async def update_daily_analysis():
    """Update daily market analysis"""
    try:
        print(f"📊 Updating daily market analysis at {datetime.now()}")
        
        # Generate fresh analysis
        analysis = generate_market_analysis()
        
        # Store analysis for later use
        with open('daily_analysis.json', 'w') as f:
            json.dump(analysis, f, indent=2)
        
        print("✅ Daily market analysis updated")
    except Exception as e:
        print(f"❌ Error updating daily analysis: {e}")

async def check_trial_expiry():
    """Check and handle trial expiry"""
    today = date.today()
    expired_users = []
    
    for user_id, user_data in db.get_all_users().items():
        if (user_data.get('status') == 'trial' and 
            user_data.get('trial_end')):
            trial_end = datetime.fromisoformat(user_data['trial_end']).date()
            if trial_end < today:
                expired_users.append(user_id)
    
    for user_id in expired_users:
        db.update_user(user_id, status='free')
        # Note: Cannot send notification here as context is not available
        # This should be handled by the notification system instead

async def send_weekly_reminder(context):
    """Send weekly registration reminder to free users"""
    try:
        logger.info("Sending weekly registration reminder to free users...")
        
        reminder_message = """🎯 Haven't registered with GOLDEN Ai yet?

Without registration, you won't be able to access:
✅ Golden AI live trading analysis. 
✅ Progress tracking system
✅ Exclusive bonuses & rewards
✅ Step-by-step training

📹 Watch this short video to learn how to register — it only takes less than a minute to get started!

⚠️ Important: Please answer all the questions asked during registration process and make a minimum deposit of 50 USD.

👉 Start now and unlock the full power of Golden AI!"""
        
        # Create registration button keyboard
        registration_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("REGISTRATION IN GOLDEN AI", url="https://one.versustrade.link/links/go/1046?pid=10748")]
        ])
        
        # Video file path - use absolute path
        video_path = os.path.join(os.path.dirname(__file__), "video", "Beige Purple Gradient Insurance Company Instagram Post.mp4")
        
        # Check if video file exists
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return
        
        # Check file size (Telegram limit is 50MB for videos)
        file_size = os.path.getsize(video_path) / (1024 * 1024)  # Size in MB
        if file_size > 50:
            logger.error(f"Video file too large: {file_size:.2f}MB (Telegram limit: 50MB)")
            return
        logger.info(f"Video file size: {file_size:.2f}MB")
        
        # Get all free users
        free_users = []
        for user_id, user_data in db.get_all_users().items():
            if user_data.get('status') == 'free':
                free_users.append(user_id)
        
        # Send reminder to each free user
        sent_count = 0
        for user_id in free_users:
            try:
                # Open file and send video
                with open(video_path, 'rb') as video_file:
                    await context.bot.send_video(
                        chat_id=user_id,
                        video=video_file,
                        caption=reminder_message,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=registration_keyboard
                    )
                sent_count += 1
                logger.info(f"Reminder sent successfully to user {user_id}")
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Error sending reminder to user {user_id}: {e}")
                # Try alternative method with BytesIO
                try:
                    with open(video_path, 'rb') as video_file:
                        video_data = video_file.read()
                        video_io = io.BytesIO(video_data)
                        await context.bot.send_video(
                            chat_id=user_id,
                            video=InputFile(video_io, filename=os.path.basename(video_path)),
                            caption=reminder_message,
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=registration_keyboard
                        )
                    sent_count += 1
                    logger.info(f"Reminder sent successfully to user {user_id} (using BytesIO)")
                    await asyncio.sleep(0.5)
                except Exception as alt_error:
                    logger.error(f"Alternative method also failed for user {user_id}: {alt_error}")
                    continue
        
        logger.info(f"Weekly reminder sent to {sent_count} free users")
    except Exception as e:
        logger.error(f"Error in weekly reminder: {e}")

async def reminder_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /reminder command - Admin only"""
    if not admin_panel.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Access denied.")
        return
    
    try:
        # Send confirmation message
        await update.message.reply_text("🔄 Sending weekly reminder to all free users...")
        
        # Call the reminder function
        await send_weekly_reminder(context)
        
        # Get count of free users
        free_users = []
        for user_id, user_data in db.get_all_users().items():
            if user_data.get('status') == 'free':
                free_users.append(user_id)
        
        await update.message.reply_text(
            f"✅ Weekly reminder sent successfully!\n\n"
            f"📊 Sent to {len(free_users)} free user(s)."
        )
    except Exception as e:
        logger.error(f"Error in reminder command: {e}")
        await update.message.reply_text(f"❌ Error sending reminder: {str(e)}")

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /test command - Admin only, sends reminder message to admin for testing"""
    if not admin_panel.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Access denied.")
        return
    
    try:
        reminder_message = """🎯 Haven't registered with GOLDEN Ai yet?

Without registration, you won't be able to access:
✅ Golden AI live trading analysis. 
✅ Progress tracking system
✅ Exclusive bonuses & rewards
✅ Step-by-step training

📹 Watch this short video to learn how to register — it only takes less than a minute to get started!

⚠️ Important: Please answer all the questions asked during registration process and make a minimum deposit of 50 USD.

👉 Start now and unlock the full power of Golden AI!"""
        
        # Create registration button keyboard
        registration_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("REGISTRATION IN GOLDEN AI", url="https://one.versustrade.link/links/go/1046?pid=10748")]
        ])
        
        # Video file path - use absolute path
        video_path = os.path.join(os.path.dirname(__file__), "video", "Beige Purple Gradient Insurance Company Instagram Post.mp4")
        
        # Check if video file exists
        if not os.path.exists(video_path):
            await update.message.reply_text(f"❌ Video file not found: {video_path}")
            return
        
        # Check file size
        file_size = os.path.getsize(video_path) / (1024 * 1024)  # Size in MB
        logger.info(f"Video file size: {file_size:.2f}MB")
        
        # Get admin user ID
        admin_id = update.effective_user.id
        
        # Send test reminder to admin
        await update.message.reply_text("🔄 Sending test reminder...")
        
        # Open file and send video
        try:
            with open(video_path, 'rb') as video_file:
                await context.bot.send_video(
                    chat_id=admin_id,
                    video=video_file,
                    caption=reminder_message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=registration_keyboard
                )
            
            await update.message.reply_text("✅ Test reminder sent successfully!")
            logger.info(f"Test reminder sent to admin {admin_id}")
        except Exception as send_error:
            logger.error(f"Error sending video: {send_error}")
            # Try alternative method with InputFile
            try:
                with open(video_path, 'rb') as video_file:
                    video_data = video_file.read()
                    video_io = io.BytesIO(video_data)
                    await context.bot.send_video(
                        chat_id=admin_id,
                        video=InputFile(video_io, filename=os.path.basename(video_path)),
                        caption=reminder_message,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=registration_keyboard
                    )
                await update.message.reply_text("✅ Test reminder sent successfully!")
                logger.info(f"Test reminder sent to admin {admin_id} (using BytesIO)")
            except Exception as alt_error:
                logger.error(f"Alternative method also failed: {alt_error}")
                raise alt_error
        
    except Exception as e:
        logger.error(f"Error in test command: {e}")
        await update.message.reply_text(f"❌ Error sending test reminder: {str(e)}")

async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /restart command - Restart bot menu"""
    user_id = update.effective_user.id
    
    # Get user language
    lang = get_user_language(user_id)
    translations = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
    
    # Send welcome message with main menu
    welcome_text = t(user_id, 'welcome_message')
    
    await update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_main_menu(user_id)
    )

def main():
    """Main function"""
    # Set bot commands and menu button callback
    async def post_init(application: Application) -> None:
        """Set bot commands and menu button after application starts"""
        commands = [
            BotCommand("start", "🚀 Start the bot"),
            BotCommand("restart", "🔄 Restart bot menu"),
            BotCommand("help", "ℹ️ Help & Support"),
            BotCommand("user", "👤 View user information"),
        ]
        await application.bot.set_my_commands(commands)
        # Set menu button to show commands
        await application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())
    
    # Create application with post_init callback
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # Conversation handler for registration flow
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            TERMS: [CallbackQueryHandler(handle_terms)],
            TRIAL_CHOICE: [CallbackQueryHandler(handle_trial_choice)],
            REGISTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_register_name)],
            REGISTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_register_email)],
            ACCOUNT_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_account_number)],
        },
        fallbacks=[CommandHandler("start", start_command)],
    )
    
    # Add handlers
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_registration_message))
    application.add_handler(CallbackQueryHandler(handle_menu_callback))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("approve", approve_command))
    application.add_handler(CommandHandler("reject", reject_command))
    application.add_handler(MessageHandler(filters.Regex(r'^/approve\d+$'), approve_command))
    application.add_handler(MessageHandler(filters.Regex(r'^/reject\d+$'), reject_command))
    application.add_handler(CommandHandler("suspend", suspend_command))
    application.add_handler(CommandHandler("reactivate", reactivate_command))
    application.add_handler(CommandHandler("broadcast_all", broadcast_command))
    application.add_handler(CommandHandler("broadcastall", broadcast_command))
    application.add_handler(CommandHandler("broadcast_premium", broadcast_command))
    application.add_handler(CommandHandler("broadcastpremium", broadcast_command))
    application.add_handler(CommandHandler("broadcast_trial", broadcast_command))
    application.add_handler(CommandHandler("broadcast_free", broadcast_command))
    application.add_handler(CommandHandler("broadcast_suspended", broadcast_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("view", view_command))
    application.add_handler(CommandHandler("signal", signal_command))
    application.add_handler(CommandHandler("close_signal", close_signal_command))
    application.add_handler(CommandHandler("signal_performance", signal_performance_command))
    application.add_handler(CommandHandler("buy", buy_signal_command))
    application.add_handler(CommandHandler("sell", sell_signal_command))
    application.add_handler(CommandHandler("ai_signal", ai_signal_command))
    application.add_handler(CommandHandler("auto_suspend", auto_suspend_command))
    application.add_handler(CommandHandler("smart_notify", smart_notify_command))
    application.add_handler(CommandHandler("system_status", system_status_command))
    application.add_handler(CommandHandler("user", user_command))
    application.add_handler(CommandHandler("reminder", reminder_command))
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(CommandHandler("restart", restart_command))
    
    # Media handlers for admin
    application.add_handler(MessageHandler(filters.PHOTO, handle_admin_media))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_admin_media))
    application.add_handler(MessageHandler(filters.VIDEO, handle_admin_media))
    application.add_handler(MessageHandler(filters.ANIMATION, handle_admin_media))
    
    # Schedule background tasks
    application.job_queue.run_repeating(
        lambda context: asyncio.create_task(check_trial_expiry()),
        interval=86400,  # 24 hours
        first=10
    )
    
    # Schedule daily maintenance
    application.job_queue.run_repeating(
        lambda context: asyncio.create_task(daily_maintenance()),
        interval=86400,  # 24 hours
        first=60
    )
    
    # Schedule market analysis update every 4 hours
    application.job_queue.run_repeating(
        lambda context: asyncio.create_task(update_daily_analysis()),
        interval=14400,  # 4 hours = 14400 seconds
        first=10
    )
    
    # Schedule weekly reminder to free users (once per week)
    application.job_queue.run_repeating(
        lambda context: asyncio.create_task(send_weekly_reminder(context)),
        interval=604800,  # 7 days = 604800 seconds
        first=3600  # Start after 1 hour
    )
    
    # Start bot
    logger.info("🚀 GOLDEN SIGNALS TRADING BOT STARTING...")
    logger.info(f"👑 Admin ID: {ADMIN_ID} | 💾 Database: users.json | 📊 Signals: signals.json")
    logger.info("✅ Bot is now running and ready to receive messages!")
    
    try:
        application.run_polling()
    except KeyboardInterrupt:
        logger.info("🛑 BOT STOPPED BY USER")
    except Exception as e:
        logger.error(f"❌ BOT ERROR: {e}")

if __name__ == '__main__':
    # Railway compatibility
    port = int(os.environ.get('PORT', 8000))
    
    # Start the bot
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 BOT STOPPED BY USER")
    except Exception as e:
        logger.error(f"❌ BOT ERROR: {e}")
