#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notification System for Telegram Trading Bot
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database import UserDatabase
from config import ADMIN_ID, BROKER_LINK

logger = logging.getLogger(__name__)

class NotificationSystem:
    """Automated notification system for the trading bot"""
    
    def __init__(self, db: UserDatabase):
        self.db = db
        self.admin_id = ADMIN_ID
        self.broker_link = BROKER_LINK
    
    async def send_trial_reminder(self, context: ContextTypes.DEFAULT_TYPE, user_id: int, days_left: int):
        """Send trial reminder to user"""
        try:
            if days_left == 7:
                message = """⏳ **Trial Reminder - 7 Days Left**

You have 7 days remaining in your Premium trial.

🎁 **What you'll lose after trial:**
• Premium trading signals
• Daily market analysis
• Trading education materials

📝 **To keep Premium access:**
Register with our broker and get verified.

🔗 [Register Now]({})""".format(self.broker_link)
            
            elif days_left == 3:
                message = """⚠️ **Trial Ending Soon - 3 Days Left**

Your Premium trial expires in 3 days!

💎 **Don't miss out on:**
• Real-time trading signals
• Professional market analysis
• Risk management tips

📝 **Register now to continue:**
🔗 [Register with Broker]({})""".format(self.broker_link)
            
            elif days_left == 1:
                message = """🚨 **Last Day of Trial!**

Your Premium trial ends tomorrow!

⚡ **Act now to keep:**
• Premium signals
• Market analysis
• Trading insights

📝 **Register immediately:**
🔗 [Register Now]({})""".format(self.broker_link)
            
            else:
                return  # Don't send for other days
            
            await context.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📝 Register for Premium", callback_data="register")]
                ])
            )
            
            logger.info(f"Sent trial reminder to user {user_id} ({days_left} days left)")
            
        except Exception as e:
            logger.error(f"Failed to send trial reminder to {user_id}: {e}")
    
    async def send_trial_expired_notification(self, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Send trial expired notification"""
        try:
            message = """⏳ **Trial Expired**

Your 14-day Premium trial has ended.

🔒 **Premium features are now locked:**
• Trading signals
• Advanced analysis
• Educational content

📝 **To unlock Premium again:**
Register with our broker and get verified.

🔗 [Register Now]({})""".format(self.broker_link)
            
            await context.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📝 Register for Premium", callback_data="register")],
                    [InlineKeyboardButton("📊 Free Analysis", callback_data="analysis")]
                ])
            )
            
            logger.info(f"Sent trial expired notification to user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send trial expired notification to {user_id}: {e}")
    
    async def send_suspension_notification(self, context: ContextTypes.DEFAULT_TYPE, user_id: int, reason: str):
        """Send account suspension notification"""
        try:
            message = f"""⚠️ **Account Suspended**

Your Premium account has been suspended.

📋 **Reason:** {reason}

🔄 **To reactivate:**
1. Fund your broker account
2. Contact admin for verification
3. Get reactivated

💡 **You can still access:**
• Free market analysis
• Basic educational content

📬 **Need help?** Contact admin for assistance."""
            
            await context.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 I've Funded My Account", callback_data="reactivate_request")],
                    [InlineKeyboardButton("📊 Free Analysis", callback_data="analysis")],
                    [InlineKeyboardButton("👤 Contact Admin", callback_data="contact_admin")]
                ])
            )
            
            logger.info(f"Sent suspension notification to user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send suspension notification to {user_id}: {e}")
    
    async def send_reactivation_notification(self, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Send account reactivation notification"""
        try:
            message = """✅ **Account Reactivated!**

Welcome back! Your Premium account has been reactivated.

💎 **You now have access to:**
• Premium trading signals
• Advanced market analysis
• Educational materials
• Risk management tips

🎯 **Keep your account active to maintain Premium status.**

Happy trading! 📈"""
            
            await context.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.info(f"Sent reactivation notification to user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send reactivation notification to {user_id}: {e}")
    
    async def send_daily_reminder_to_suspended(self, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Send daily reminder to suspended users"""
        try:
            message = """🚫 **Daily Reminder - Premium Suspended**

Your Premium subscription is currently suspended.

📉 **Today's signals are locked.**
Don't let opportunities pass by while you're on the sidelines.

💡 **Fund your broker account today and reactivate instantly.**

🔗 [Register/Reactivate]({})""".format(self.broker_link)
            
            await context.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Reactivate Now", callback_data="reactivate_request")]
                ])
            )
            
            logger.info(f"Sent daily reminder to suspended user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send daily reminder to suspended user {user_id}: {e}")
    
    async def send_signal_result_to_suspended(self, context: ContextTypes.DEFAULT_TYPE, user_id: int, signal_result: str):
        """Send signal result to suspended users (FOMO effect)"""
        try:
            message = f"""📊 **Premium Signal Result**

{signal_result}

⚠️ **Your subscription is suspended.**
You missed the full entry details and targets.

👉 **Reactivate to unlock ALL entries, SL & TP setups.**

🔗 [Unlock Premium]({self.broker_link})"""
            
            await context.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Unlock Premium", callback_data="reactivate_request")]
                ])
            )
            
            logger.info(f"Sent signal result to suspended user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send signal result to suspended user {user_id}: {e}")
    
    async def send_verification_request_notification(self, context: ContextTypes.DEFAULT_TYPE, user_id: int, user_data: Dict[str, Any]):
        """Send verification request notification to admin"""
        try:
            message = f"""🔔 **New Premium Request**

👤 **User:** @{user_data.get('username', 'Unknown')}
🆔 **ID:** {user_id}
📝 **Name:** {user_data.get('full_name', 'Not provided')}
📧 **Email:** {user_data.get('email', 'Not provided')}
🔢 **Account:** {user_data.get('account_number', 'Not provided')}
🌍 **Country:** {user_data.get('country', 'Not set')}

**Actions:**
✅ /approve_{user_id}
❌ /reject_{user_id}
👁️ /view_{user_id}"""
            
            await context.bot.send_message(
                chat_id=self.admin_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.info(f"Sent verification request notification for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send verification request notification: {e}")
    
    async def send_reactivation_request_notification(self, context: ContextTypes.DEFAULT_TYPE, user_id: int, user_data: Dict[str, Any]):
        """Send reactivation request notification to admin"""
        try:
            message = f"""🔄 **Reactivation Request**

👤 **User:** @{user_data.get('username', 'Unknown')}
🆔 **ID:** {user_id}
📝 **Name:** {user_data.get('full_name', 'Not provided')}
📧 **Email:** {user_data.get('email', 'Not provided')}
🔢 **Account:** {user_data.get('account_number', 'Not provided')}
🚫 **Suspended Reason:** {user_data.get('suspension_reason', 'Unknown')}

**Actions:**
✅ /reactivate_{user_id}
👁️ /view_{user_id}"""
            
            await context.bot.send_message(
                chat_id=self.admin_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.info(f"Sent reactivation request notification for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send reactivation request notification: {e}")
    
    async def check_and_send_trial_reminders(self, context: ContextTypes.DEFAULT_TYPE):
        """Check all users and send trial reminders"""
        today = date.today()
        reminders_sent = 0
        
        for user_id, user_data in self.db.get_all_users().items():
            if user_data.get('status') == 'trial' and user_data.get('trial_end'):
                try:
                    trial_end = datetime.fromisoformat(user_data['trial_end']).date()
                    days_left = (trial_end - today).days
                    
                    if days_left in [7, 3, 1]:
                        await self.send_trial_reminder(context, user_id, days_left)
                        reminders_sent += 1
                    
                except Exception as e:
                    logger.error(f"Error processing trial reminder for user {user_id}: {e}")
        
        logger.info(f"Sent {reminders_sent} trial reminders")
        return reminders_sent
    
    async def check_and_handle_expired_trials(self, context: ContextTypes.DEFAULT_TYPE):
        """Check and handle expired trials"""
        today = date.today()
        expired_count = 0
        
        for user_id, user_data in self.db.get_all_users().items():
            if user_data.get('status') == 'trial' and user_data.get('trial_end'):
                try:
                    trial_end = datetime.fromisoformat(user_data['trial_end']).date()
                    if trial_end < today:
                        # Update user status
                        self.db.update_user(user_id, status='free')
                        
                        # Send notification
                        await self.send_trial_expired_notification(context, user_id)
                        expired_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing expired trial for user {user_id}: {e}")
        
        logger.info(f"Processed {expired_count} expired trials")
        return expired_count
    
    async def send_daily_suspended_reminders(self, context: ContextTypes.DEFAULT_TYPE):
        """Send daily reminders to suspended users"""
        suspended_users = self.db.get_suspended_users()
        reminders_sent = 0
        
        for user_id in suspended_users.keys():
            try:
                await self.send_daily_reminder_to_suspended(context, user_id)
                reminders_sent += 1
            except Exception as e:
                logger.error(f"Failed to send daily reminder to suspended user {user_id}: {e}")
        
        logger.info(f"Sent {reminders_sent} daily reminders to suspended users")
        return reminders_sent
    
    async def send_weekly_analytics_to_admin(self, context: ContextTypes.DEFAULT_TYPE):
        """Send weekly analytics report to admin"""
        try:
            analytics = self.db.get_analytics()
            
            message = f"""📊 **Weekly Analytics Report**

📅 **Period:** {date.today() - timedelta(days=7)} to {date.today()}

👥 **User Statistics:**
• Total Users: {analytics['total_users']}
• Free Users: {analytics['free_users']}
• Trial Users: {analytics['trial_users']}
• Premium Users: {analytics['premium_users']}
• Suspended Users: {analytics['suspended_users']}

📈 **Conversion Rates:**
• Overall: {analytics['conversion_rate']}%
• Trial to Premium: {analytics['trial_conversion_rate']}%

🆕 **New Users (7 days):** {analytics['recent_users_7d']}
⏳ **Pending Verifications:** {analytics['pending_verifications']}

**Commands:**
📤 /export_csv - Export user data
🔍 /search_users - Search users
📊 /analytics - Detailed analytics"""
            
            await context.bot.send_message(
                chat_id=self.admin_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.info("Sent weekly analytics report to admin")
            
        except Exception as e:
            logger.error(f"Failed to send weekly analytics to admin: {e}")
    
    async def send_monthly_premium_review_reminder(self, context: ContextTypes.DEFAULT_TYPE):
        """Send monthly premium review reminder to admin"""
        try:
            premium_users = self.db.get_users_by_status('premium')
            premium_count = len(premium_users)
            
            message = f"""📅 **Premium Review Time**

Please verify all Premium users in your broker portal.

👥 **Premium Users to Review:** {premium_count}

**Review Process:**
1. Check broker portal for active trading
2. Verify account balances
3. Suspend inactive users
4. Keep active users as Premium

**Commands:**
👥 /admin - Open admin panel
📊 /analytics - View user statistics
🚫 /suspend <user_id> - Suspend user
🔄 /reactivate <user_id> - Reactivate user

⚠️ **Important:** Users inactive / low balance should be suspended."""
            
            await context.bot.send_message(
                chat_id=self.admin_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.info("Sent monthly premium review reminder to admin")
            
        except Exception as e:
            logger.error(f"Failed to send monthly premium review reminder: {e}")
    
    async def send_premium_warning_before_suspension(self, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Send warning to premium users before suspension"""
        try:
            message = """⏳ **Premium Review Reminder**

Our system will review your trading account in 7 days.

If your balance is inactive or too low, your Premium subscription may be suspended.

💡 **To maintain Premium access:**
• Keep your broker account active
• Maintain minimum balance
• Continue trading regularly

📬 **Questions?** Contact admin for assistance."""
            
            await context.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.info(f"Sent premium warning to user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send premium warning to user {user_id}: {e}")
    
    async def send_signal_broadcast(self, context: ContextTypes.DEFAULT_TYPE, signal_message: str, target: str = "premium"):
        """Send signal broadcast to users"""
        if target == "premium":
            target_users = self.db.get_users_by_status('premium')
        elif target == "trial":
            target_users = self.db.get_users_by_status('trial')
        elif target == "all_premium":
            premium_users = self.db.get_users_by_status('premium')
            trial_users = self.db.get_users_by_status('trial')
            target_users = {**premium_users, **trial_users}
        else:
            return {"sent": 0, "failed": 0}
        
        sent = 0
        failed = 0
        
        for user_id in target_users.keys():
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"📢 **New Signal Alert**\n\n{signal_message}",
                    parse_mode=ParseMode.MARKDOWN
                )
                sent += 1
                
                # Update signal count
                user_data = self.db.get_user(user_id)
                current_count = user_data.get('total_signals_received', 0)
                self.db.update_user(user_id, total_signals_received=current_count + 1)
                
            except Exception as e:
                logger.error(f"Failed to send signal to user {user_id}: {e}")
                failed += 1
        
        logger.info(f"Signal broadcast sent to {sent} users, {failed} failed")
        return {"sent": sent, "failed": failed}