#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Admin Panel for Telegram Trading Bot
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database import UserDatabase
from config import ADMIN_ID, ADMIN_IDS, ERROR_MESSAGES, SUCCESS_MESSAGES

logger = logging.getLogger(__name__)

class AdminPanel:
    """Admin panel management class"""
    
    def __init__(self, db: UserDatabase):
        self.db = db
        self.admin_id = ADMIN_ID
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in ADMIN_IDS
    
    async def send_admin_notification(self, context: ContextTypes.DEFAULT_TYPE, message: str):
        """Send notification to admin"""
        try:
            await context.bot.send_message(
                chat_id=self.admin_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Failed to send admin notification: {e}")
    
    async def handle_user_approval(self, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Handle user approval"""
        user_data = self.db.get_user(user_id)
        
        if not user_data.get('account_number'):
            return False, "User hasn't submitted account details."
        
        # Approve user
        self.db.approve_user(user_id)
        
        # Notify user
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="🎉 **Congratulations!**\n\n"
                     "Your Premium access has been approved & activated ✅\n"
                     "You now have full access to AI-generated Premium market observations.\n\n"
                     "📌 **Remember:**\n\n"
                     "Keep your broker account funded & active to maintain Premium status.\n\n"
                     "All insights are for educational purposes only (DYOR & TAYOR).\n\n"
                     "Enjoy your Premium journey 🚀",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Failed to notify approved user {user_id}: {e}")
        
        return True, f"User {user_id} approved for Premium access."
    
    async def handle_user_rejection(self, context: ContextTypes.DEFAULT_TYPE, user_id: int, reason: str = None):
        """Handle user rejection"""
        self.db.reject_user(user_id)
        
        # Notify user
        try:
            message = "❌ Premium Request Rejected\n\n"
            message += "Unfortunately, we could not verify your details with the broker.\n"
            message += "This means your Premium subscription request has been denied.\n\n"
            message += "👉 What you can do next:\n"
            message += "1️⃣ Double-check that you registered using our official broker link.\n"
            message += "2️⃣ Ensure you provided the correct name and email (same as broker account).\n"
            message += "3️⃣ If you already have an account but not under our IB, please contact admin for instructions.\n\n"
            message += "📬 Contact Admin\n\n"
            message += "⚠️ Reminder: All signals are AI-generated for educational purposes only. DYOR & TAYOR."
            
            await context.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Failed to notify rejected user {user_id}: {e}")
        
        return f"User {user_id} rejected."
    
    async def suspend_user(self, context: ContextTypes.DEFAULT_TYPE, user_id: int, reason: str = "Manual suspension"):
        """Suspend a user"""
        user_data = self.db.get_user(user_id)
        
        if not user_data:
            return False, "User not found."
        
        self.db.suspend_user(user_id, reason)
        
        # Notify user
        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            message = "⏸️ Premium Subscription Suspended\n\n"
            message += "Your Premium access has been temporarily suspended because:\n"
            message += "⚠️ We detected low or inactive balance in your broker account.\n\n"
            message += "👉 To reactivate Premium:\n"
            message += "1️⃣ Fund your broker account.\n"
            message += "2️⃣ Tap \"I've Funded My Account\" below to notify us.\n"
            message += "3️⃣ Our admin will verify and restore your Premium access.\n\n"
            message += "⚠️ Note: You will continue receiving occasional updates from the admin, but full Premium signals remain locked until reactivation"
            
            keyboard = [
                [InlineKeyboardButton("🔘 I've Funded My Account", callback_data="reactivate_request")],
                [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await context.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Failed to notify suspended user {user_id}: {e}")
        
        return True, f"User {user_id} suspended."
    
    async def reactivate_user(self, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Reactivate a suspended user"""
        user_data = self.db.get_user(user_id)
        
        if not user_data:
            return False, "User not found."
        
        if not user_data.get('suspended', False):
            return False, "User is not suspended."
        
        self.db.reactivate_user(user_id)
        
        # Notify user
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="✅ **Account Reactivated**\n\n"
                     "Your account has been reactivated!\n"
                     "You can now access all features again.",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Failed to notify reactivated user {user_id}: {e}")
        
        return True, f"User {user_id} reactivated."
    
    async def send_broadcast(self, context: ContextTypes.DEFAULT_TYPE, message: str, target: str = "all") -> Dict[str, int]:
        """Send broadcast message to users"""
        results = {"sent": 0, "failed": 0}
        
        if target == "all":
            target_users = self.db.get_all_users()
        elif target == "premium":
            target_users = self.db.get_users_by_status('premium')
        elif target == "trial":
            target_users = self.db.get_users_by_status('trial')
        elif target == "free":
            target_users = self.db.get_users_by_status('free')
        elif target == "suspended":
            target_users = self.db.get_suspended_users()
        else:
            return results
        
        for user_id in target_users.keys():
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"📢 **Broadcast Message**\n\n{message}",
                    parse_mode=ParseMode.MARKDOWN
                )
                results["sent"] += 1
                
                # Update signal count for premium users
                if target in ["all", "premium", "trial"]:
                    user_data = self.db.get_user(user_id)
                    current_count = user_data.get('total_signals_received', 0)
                    self.db.update_user(user_id, total_signals_received=current_count + 1)
                
            except Exception as e:
                logger.error(f"Failed to send broadcast to {user_id}: {e}")
                results["failed"] += 1
        
        return results
    
    def get_analytics_report(self) -> str:
        """Generate analytics report"""
        analytics = self.db.get_analytics()
        
        report = f"""📊 **Analytics Report** (as of {date.today()})

👥 **Total Users:** {analytics['total_users']}
🆓 **Free Users:** {analytics['free_users']}
🎁 **Trial Users:** {analytics['trial_users']}
💎 **Premium Users:** {analytics['premium_users']}
🚫 **Suspended Users:** {analytics['suspended_users']}
⏳ **Pending Verifications:** {analytics['pending_verifications']}

📈 **Conversion Rates:**
• Overall: {analytics['conversion_rate']}%
• Trial to Premium: {analytics['trial_conversion_rate']}%

📅 **Recent Activity:**
• New Users (7 days): {analytics['recent_users_7d']}

🔄 **Reactivation Requests (Last 7 days):** {len(self.get_recent_reactivation_requests())}

**Buttons:**
📈 Export CSV / 🔄 Refresh / 📆 Select Date Range
"""
        return report
    
    def get_system_logs(self, days: int = 7) -> str:
        """Get system logs for specified days"""
        logs = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for user_id, user_data in self.db.get_all_users().items():
            # Check for recent activities
            if user_data.get('last_activity'):
                try:
                    last_activity = datetime.fromisoformat(user_data['last_activity'])
                    if last_activity > cutoff_date:
                        status = user_data.get('status', 'free')
                        name = user_data.get('full_name', f'User {user_id}')
                        
                        if status == 'suspended':
                            reason = user_data.get('suspension_reason', 'Unknown')
                            logs.append(f"[{last_activity.strftime('%d-%b')}] @{name} → Suspended ({reason})")
                        elif status == 'premium' and user_data.get('verified'):
                            logs.append(f"[{last_activity.strftime('%d-%b')}] @{name} → Premium Activated")
                        elif status == 'trial':
                            logs.append(f"[{last_activity.strftime('%d-%b')}] @{name} → Trial Started")
                except:
                    pass
        
        # Sort logs by date (most recent first)
        logs.sort(reverse=True)
        
        if logs:
            logs_text = "\n".join(logs[:20])  # Show last 20 activities
            if len(logs) > 20:
                logs_text += f"\n\n... and {len(logs) - 20} more activities"
        else:
            logs_text = "No recent activities found."
        
        return f"""📋 **System Logs** (Last {days} days)

{logs_text}

**Commands:**
📤 /export_logs - Export logs to CSV
🔄 /refresh_logs - Refresh logs
📆 /logs_30d - View 30 days logs
📆 /logs_7d - View 7 days logs"""
    
    def get_recent_reactivation_requests(self) -> List[Dict[str, Any]]:
        """Get recent reactivation requests"""
        week_ago = datetime.now() - timedelta(days=7)
        recent_requests = []
        
        for user_id, user_data in self.db.get_all_users().items():
            if (user_data.get('suspended', False) and 
                user_data.get('last_activity')):
                try:
                    last_activity = datetime.fromisoformat(user_data['last_activity'])
                    if last_activity > week_ago:
                        recent_requests.append({
                            'user_id': user_id,
                            'name': user_data.get('full_name', 'Unknown'),
                            'reason': user_data.get('suspension_reason', 'Unknown'),
                            'last_activity': last_activity
                        })
                except:
                    pass
        
        return recent_requests
    
    def get_user_details(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed user information"""
        user_data = self.db.get_user(user_id)
        if not user_data:
            return None
        
        stats = self.db.get_user_stats(user_id)
        
        return {
            'user_id': user_id,
            'telegram_username': f"@{user_data.get('username', 'N/A')}",
            'full_name': user_data.get('full_name', 'Not provided'),
            'email': user_data.get('email', 'Not provided'),
            'country': user_data.get('country', 'Not set'),
            'status': user_data.get('status', 'free'),
            'verified': user_data.get('verified', False),
            'suspended': user_data.get('suspended', False),
            'account_number': user_data.get('account_number', 'Not provided'),
            'created_at': user_data.get('created_at'),
            'last_activity': user_data.get('last_activity'),
            'trial_days_left': stats['trial_days_left'],
            'verification_requests': stats['verification_requests'],
            'total_signals_received': stats['total_signals_received'],
            'premium_since': user_data.get('premium_since')
        }
    
    def search_users(self, query: str) -> List[Dict[str, Any]]:
        """Search users by name, email, or account number"""
        results = []
        query_lower = query.lower()
        
        for user_id, user_data in self.db.get_all_users().items():
            # Search in name, email, account number
            if (query_lower in (user_data.get('full_name', '').lower()) or
                query_lower in (user_data.get('email', '').lower()) or
                query_lower in (user_data.get('account_number', '').lower()) or
                query_lower in str(user_id)):
                
                results.append({
                    'user_id': user_id,
                    'name': user_data.get('full_name', 'Unknown'),
                    'email': user_data.get('email', 'Not provided'),
                    'status': user_data.get('status', 'free'),
                    'verified': user_data.get('verified', False)
                })
        
        return results[:20]  # Limit to 20 results
    
    def export_user_data(self, filename: str = None) -> str:
        """Export user data to CSV"""
        return self.db.export_csv(filename)
    
    def cleanup_expired_data(self) -> Dict[str, int]:
        """Clean up expired trials and old data"""
        results = {
            'expired_trials': 0,
            'inactive_users': 0
        }
        
        # Clean up expired trials
        results['expired_trials'] = self.db.cleanup_expired_trials()
        
        # Clean up inactive users (optional - users inactive for 90+ days)
        cutoff_date = datetime.now() - timedelta(days=90)
        inactive_count = 0
        
        for user_id, user_data in self.db.get_all_users().items():
            if (user_data.get('last_activity') and 
                user_data.get('status') == 'free' and
                not user_data.get('verified')):
                try:
                    last_activity = datetime.fromisoformat(user_data['last_activity'])
                    if last_activity < cutoff_date:
                        # Mark as inactive (don't delete, just flag)
                        self.db.update_user(user_id, inactive=True)
                        inactive_count += 1
                except:
                    pass
        
        results['inactive_users'] = inactive_count
        return results

def create_admin_keyboard() -> InlineKeyboardMarkup:
    """Create admin menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("👥 Manage Users", callback_data="admin_users")],
        [InlineKeyboardButton("📢 Send Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🚀 Signal Management", callback_data="admin_signals")],
        [InlineKeyboardButton("🚫 Suspended Users", callback_data="admin_suspended")],
        [InlineKeyboardButton("✅ Verify Requests", callback_data="admin_verify")],
        [InlineKeyboardButton("📊 Analytics & Logs", callback_data="admin_analytics")],
        [InlineKeyboardButton("🔍 Search Users", callback_data="admin_search")],
        [InlineKeyboardButton("📤 Export Data", callback_data="admin_export")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_user_management_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Create user management keyboard for specific user"""
    keyboard = [
        [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}")],
        [InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")],
        [InlineKeyboardButton("⛔ Suspend", callback_data=f"suspend_{user_id}")],
        [InlineKeyboardButton("🔄 Reactivate", callback_data=f"reactivate_{user_id}")],
        [InlineKeyboardButton("📊 User Stats", callback_data=f"stats_{user_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_users")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_broadcast_keyboard() -> InlineKeyboardMarkup:
    """Create broadcast options keyboard"""
    keyboard = [
        [InlineKeyboardButton("📢 All Users", callback_data="broadcast_all")],
        [InlineKeyboardButton("💎 Premium Only", callback_data="broadcast_premium")],
        [InlineKeyboardButton("🎁 Trial Only", callback_data="broadcast_trial")],
        [InlineKeyboardButton("🆓 Free Only", callback_data="broadcast_free")],
        [InlineKeyboardButton("🚫 Suspended Only", callback_data="broadcast_suspended")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_signal_management_keyboard() -> InlineKeyboardMarkup:
    """Create signal management keyboard"""
    keyboard = [
        [InlineKeyboardButton("📊 Signal Performance", callback_data="signal_performance")],
        [InlineKeyboardButton("📈 Recent Signals", callback_data="recent_signals")],
        [InlineKeyboardButton("🎯 Send FOMO Signal", callback_data="send_fomo")],
        [InlineKeyboardButton("📤 Export Signals", callback_data="export_signals")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)
