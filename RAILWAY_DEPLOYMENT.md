# Railway Deployment Guide

## আপনার Telegram Trading Bot Railway এ হোস্ট করার গাইড

### ১. Railway এ প্রজেক্ট তৈরি করুন

1. Railway.com এ যান এবং "Empty Project" সিলেক্ট করুন
2. GitHub repository connect করুন অথবা manual upload করুন

### ২. Environment Variables সেট করুন

Railway dashboard এ গিয়ে Variables ট্যাবে যান এবং নিচের variables গুলো add করুন:

```
BOT_TOKEN=your_actual_telegram_bot_token
ADMIN_ID=your_telegram_user_id
BROKER_LINK=https://your-broker-website.com
```

### ৩. Deployment Settings

- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python main.py`
- **Port**: Railway automatically assigns port

### ৪. Database Files

আপনার `users.json` এবং `backups` folder Railway এ automatically create হবে।

### ৫. Important Notes

- Railway free tier এ 500 hours/month limit আছে
- Bot 24/7 চালাতে হলে paid plan নিতে হবে
- Environment variables সবসময় secure রাখুন
- Bot token কখনো public repository এ commit করবেন না

### ৬. Monitoring

Railway dashboard এ logs দেখতে পারবেন এবং bot এর status monitor করতে পারবেন।

### ৭. Troubleshooting

যদি bot start না হয়:
1. Environment variables check করুন
2. Logs দেখুন Railway dashboard এ
3. Requirements.txt এ সব dependencies আছে কিনা check করুন

### ৮. Backup

নিয়মিত backup নিন `users.json` file এর জন্য।
