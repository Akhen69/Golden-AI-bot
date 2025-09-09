#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration file for Telegram Trading Bot
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
# Support multiple admin IDs (comma separated)
ADMIN_IDS_STR = os.getenv('ADMIN_ID', '123456789')
ADMIN_IDS = [int(id.strip()) for id in ADMIN_IDS_STR.split(',') if id.strip().isdigit()]
ADMIN_ID = ADMIN_IDS[0] if ADMIN_IDS else 123456789  # First admin as primary
BROKER_LINK = os.getenv('BROKER_LINK', 'https://your-broker-link.com')

# Database Configuration
DB_FILE = 'users.json'
BACKUP_DIR = 'backups'

# Trial Configuration
TRIAL_DAYS = 14

# Message Templates
WELCOME_MESSAGE = """
👋 Welcome to Golden Signals Trading Bot!

Before we continue, I need to ask you two quick things:

🌍 **Step 1 - Country**
Which country are you trading from?
(Please type your country name)
"""

TERMS_MESSAGE = """
📜 **Terms of Use**
• This bot provides market analysis & trading signals for educational purposes only
• We do not provide financial advice and are not responsible for profits or losses
• By continuing, you confirm that you understand trading risks and agree to use this bot responsibly

👉 Do you accept the Terms & Conditions?
"""

TRIAL_ACTIVATED_MESSAGE = """
🚀 Your 14-day Premium trial has started, {name}!

You now have full access to:
💎 Premium buy/sell signal calls
📊 Daily analysis & updates
🎓 Trading tips & strategies

📅 Trial Expiry Date: {expiry_date}

👉 What would you like to do now?
"""

# Admin Messages
ADMIN_NOTIFICATION_TEMPLATE = """
🔔 **New Premium Request**

👤 User: @{username}
🆔 ID: {user_id}
📝 Name: {full_name}
📧 Email: {email}
🔢 Account: {account_number}

✅ /approve_{user_id}
❌ /reject_{user_id}
"""

# Signal Templates
SIGNAL_TEMPLATE = """
📈 **Premium Trading Signal**

🟡 **GOLD (XAU/USD)**
• Type: BUY
• Entry: 1935.00
• Stop Loss: 1928.00
• Take Profit: 1950.00
• Risk: 0.5% per trade

🔵 **EUR/USD**
• Type: SELL
• Entry: 1.0850
• Stop Loss: 1.0880
• Take Profit: 1.0800
• Risk: 0.5% per trade

⚡ Manage your risk wisely!
"""

# Error Messages
ERROR_MESSAGES = {
    'access_denied': '❌ Access denied.',
    'invalid_user_id': '❌ Invalid user ID.',
    'user_not_found': '❌ User not found.',
    'no_account_details': '❌ User hasn\'t submitted account details.',
    'trial_expired': '⏳ Your 14-day Premium trial has ended.',
    'premium_locked': '⛔ Premium Signals Locked',
    'terms_required': '❌ You must accept the Terms & Conditions to use this bot.'
}

# Success Messages
SUCCESS_MESSAGES = {
    'trial_started': '🚀 Your 14-day Premium trial has started!',
    'premium_approved': '🎉 Your Premium request has been approved!',
    'registration_complete': '✅ Registration Complete!',
    'broadcast_sent': '✅ Broadcast sent to {count} users.',
    'user_approved': '✅ User {user_id} approved for Premium access.',
    'user_rejected': '❌ User {user_id} rejected.'
}
