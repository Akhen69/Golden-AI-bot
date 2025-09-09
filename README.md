# 🤖 Telegram Trading Bot - Premium Signal System

একটি সম্পূর্ণ টেলিগ্রাম ট্রেডিং বট যা প্রিমিয়াম সিগন্যাল সিস্টেম, ট্রায়াল সিস্টেম এবং অ্যাডমিন প্যানেল সহ আসে।

## ✨ Features

### 👤 User Features
- **14-day Free Trial** - নতুন ইউজারদের জন্য ১৪ দিনের ফ্রি প্রিমিয়াম ট্রায়াল
- **Premium Signals** - রিয়েল-টাইম ট্রেডিং সিগন্যাল
- **Free Market Analysis** - বিনামূল্যে মার্কেট অ্যানালাইসিস
- **Broker Registration** - ব্রোকারের মাধ্যমে প্রিমিয়াম অ্যাক্সেস
- **Account Management** - ইউজার অ্যাকাউন্ট ম্যানেজমেন্ট

### 🔧 Admin Features
- **User Management** - ইউজার সাসপেন্ড/রিঅ্যাক্টিভেট
- **Broadcast System** - বিভিন্ন গ্রুপে মেসেজ পাঠানো
- **Analytics Dashboard** - বিস্তারিত অ্যানালিটিক্স
- **Verification System** - ইউজার ভেরিফিকেশন
- **Export Data** - CSV ফরম্যাটে ডেটা এক্সপোর্ট

### 🔔 Notification System
- **Trial Reminders** - ট্রায়াল শেষ হওয়ার আগে রিমাইন্ডার
- **Suspension Notifications** - অ্যাকাউন্ট সাসপেনশন নোটিফিকেশন
- **Daily Reminders** - সাসপেন্ড ইউজারদের জন্য দৈনিক রিমাইন্ডার
- **Signal Results** - সিগন্যাল রেজাল্ট (FOMO ইফেক্ট)

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.8+
- Telegram Bot Token (BotFather থেকে)
- Telegram User ID (আপনার অ্যাডমিন ID)

### 2. Installation

```bash
# Repository clone করুন
git clone <your-repo-url>
cd telegram-trading-bot

# Virtual environment তৈরি করুন
python -m venv venv

# Virtual environment activate করুন
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Dependencies install করুন
pip install -r requirements.txt
```

### 3. Configuration

#### Environment Variables সেটআপ করুন:

```bash
# .env ফাইল তৈরি করুন
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_ID=your_telegram_user_id_here
BROKER_LINK=https://your-broker-link.com
```

#### Bot Token পাওয়ার জন্য:
1. Telegram এ @BotFather এর সাথে চ্যাট করুন
2. `/newbot` কমান্ড দিন
3. বটের নাম এবং username দিন
4. Bot Token কপি করুন

#### Admin ID পাওয়ার জন্য:
1. Telegram এ @userinfobot এর সাথে চ্যাট করুন
2. আপনার User ID কপি করুন

### 4. Run the Bot

```bash
python main.py
```

## 📁 Project Structure

```
telegram-trading-bot/
├── main.py                 # Main bot file
├── database.py            # Database management
├── admin_panel.py         # Admin panel functionality
├── notifications.py       # Notification system
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── users.json           # User database (auto-created)
└── backups/            # Database backups (auto-created)
```

## 🎯 User Flow

### 1. User Onboarding
```
/start → Country Selection → Terms Acceptance → Trial Choice
```

### 2. Trial System
- 14-day free Premium trial
- Automatic reminders at 7, 3, 1 days left
- Auto-expiry and downgrade to free

### 3. Premium Registration
- Broker registration required
- Email and account number verification
- Admin approval process

### 4. Premium Features
- Real-time trading signals
- Advanced market analysis
- Educational content

## 🔧 Admin Commands

### User Management
```bash
/approve <user_id>     # Approve user for premium
/reject <user_id>      # Reject user verification
/suspend <user_id>     # Suspend user account
/reactivate <user_id>  # Reactivate suspended user
```

### Broadcasting
```bash
/broadcast_all <message>      # Send to all users
/broadcast_premium <message>  # Send to premium users only
/broadcast_trial <message>    # Send to trial users only
/broadcast_free <message>     # Send to free users only
/broadcast_suspended <message> # Send to suspended users only
```

### Analytics
```bash
/admin              # Open admin panel
/export_csv         # Export user data to CSV
/analytics          # View detailed analytics
```

## 📊 Database Schema

### User Data Structure
```json
{
  "user_id": 123456789,
  "status": "premium",
  "country": "Bangladesh",
  "terms_accepted": true,
  "trial_end": "2025-01-15T00:00:00",
  "subscription_end": null,
  "full_name": "John Doe",
  "email": "john@example.com",
  "account_number": "1234567",
  "verified": true,
  "suspended": false,
  "suspension_reason": null,
  "created_at": "2025-01-01T00:00:00",
  "last_activity": "2025-01-15T12:00:00",
  "last_verification": "2025-01-15T12:00:00",
  "verification_requests": 1,
  "total_signals_received": 25,
  "premium_since": "2025-01-15T12:00:00"
}
```

## 🔔 Notification System

### Automated Notifications
- **Trial Reminders**: 7, 3, 1 days before expiry
- **Trial Expired**: Automatic downgrade notification
- **Suspension**: Account suspension with reactivation option
- **Daily Reminders**: For suspended users
- **Signal Results**: FOMO effect for suspended users

### Manual Notifications
- **Broadcast Messages**: Admin-triggered broadcasts
- **Verification Requests**: Admin notifications for new requests
- **Reactivation Requests**: Admin notifications for reactivation

## 🛡️ Security Features

- **Admin Verification**: Only admin can access admin commands
- **User Data Protection**: Encrypted user data storage
- **Backup System**: Automatic database backups
- **Input Validation**: All user inputs are validated

## 📈 Analytics & Reporting

### User Statistics
- Total users count
- Free/Trial/Premium/Suspended breakdown
- Conversion rates
- Recent activity (7 days)

### Export Options
- CSV export of all user data
- Filtered exports by status
- Analytics reports

## 🔧 Customization

### Message Templates
Edit `config.py` to customize:
- Welcome messages
- Terms and conditions
- Trial activation messages
- Error messages
- Success messages

### Bot Settings
Modify in `config.py`:
- Trial duration (default: 14 days)
- Broker link
- Admin ID
- Database settings

## 🚨 Troubleshooting

### Common Issues

1. **Bot not responding**
   - Check BOT_TOKEN is correct
   - Verify bot is not blocked by users
   - Check internet connection

2. **Admin commands not working**
   - Verify ADMIN_ID is correct
   - Check if user is admin in database

3. **Database errors**
   - Check file permissions
   - Verify JSON format
   - Check backup directory exists

### Logs
Check console output for detailed error logs. All errors are logged with timestamps.

## 📞 Support

For support and questions:
- Create an issue in the repository
- Contact the admin via Telegram
- Check the documentation

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 🔄 Updates

### Version 1.0.0
- Initial release
- Complete user flow
- Admin panel
- Notification system
- Database management
- Analytics dashboard

---

**⚠️ Disclaimer**: This bot is for educational purposes only. Trading involves risk. Always do your own research before making trading decisions.
