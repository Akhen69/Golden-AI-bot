"""
Signal Management System for Trading Bot
Handles signal creation, distribution, and tracking
"""

import json
import os
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import logging

logger = logging.getLogger(__name__)

class SignalManager:
    def __init__(self, db, notification_system):
        self.db = db
        self.notification_system = notification_system
        self.signals_file = "signals.json"
        self.load_signals()
    
    def load_signals(self):
        """Load signals from JSON file"""
        if os.path.exists(self.signals_file):
            try:
                with open(self.signals_file, 'r', encoding='utf-8') as f:
                    self.signals = json.load(f)
            except Exception as e:
                logger.error(f"Error loading signals: {e}")
                self.signals = {}
        else:
            self.signals = {}
    
    def save_signals(self):
        """Save signals to JSON file"""
        try:
            with open(self.signals_file, 'w', encoding='utf-8') as f:
                json.dump(self.signals, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"Error saving signals: {e}")
    
    def create_signal(self, signal_type: str, symbol: str, action: str, 
                     entry_price: float, stop_loss: float, take_profit: float,
                     description: str = "") -> str:
        """Create a new trading signal"""
        signal_id = f"SIG_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        signal_data = {
            "signal_id": signal_id,
            "type": signal_type,  # "entry" or "exit"
            "symbol": symbol,
            "action": action,  # "BUY" or "SELL"
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "status": "active",  # "active", "closed", "cancelled"
            "results": {
                "hit_sl": False,
                "hit_tp": False,
                "manual_close": False,
                "close_price": None,
                "close_time": None,
                "profit_loss": 0.0
            }
        }
        
        self.signals[signal_id] = signal_data
        self.save_signals()
        
        logger.info(f"Created signal: {signal_id}")
        return signal_id
    
    def get_signal(self, signal_id: str) -> Optional[Dict]:
        """Get signal by ID"""
        return self.signals.get(signal_id)
    
    def get_active_signals(self) -> List[Dict]:
        """Get all active signals"""
        return [signal for signal in self.signals.values() if signal["status"] == "active"]
    
    def close_signal(self, signal_id: str, close_price: float, 
                    close_reason: str = "manual") -> bool:
        """Close a signal with result"""
        if signal_id not in self.signals:
            return False
        
        signal = self.signals[signal_id]
        signal["status"] = "closed"
        signal["results"]["close_price"] = close_price
        signal["results"]["close_time"] = datetime.now().isoformat()
        
        # Calculate profit/loss
        entry_price = signal["entry_price"]
        if signal["action"] == "BUY":
            signal["results"]["profit_loss"] = close_price - entry_price
        else:  # SELL
            signal["results"]["profit_loss"] = entry_price - close_price
        
        # Determine if hit SL or TP
        if close_reason == "sl":
            signal["results"]["hit_sl"] = True
        elif close_reason == "tp":
            signal["results"]["hit_tp"] = True
        else:
            signal["results"]["manual_close"] = True
        
        self.save_signals()
        logger.info(f"Closed signal {signal_id}: {close_reason}")
        return True
    
    def format_signal_message(self, signal: Dict, user_status: str = "premium") -> str:
        """Format signal message based on user status"""
        if user_status == "premium":
            # Calculate risk/reward ratio
            if signal['action'] == "BUY":
                risk = signal['entry_price'] - signal['stop_loss']
                reward = signal['take_profit'] - signal['entry_price']
            else:  # SELL
                risk = signal['stop_loss'] - signal['entry_price']
                reward = signal['entry_price'] - signal['take_profit']
            
            risk_reward_ratio = reward / risk if risk > 0 else 0
            
            # Full signal details for premium users
            message = f"""🚀 **{signal['action']} SIGNAL** 🚀

📊 **Symbol:** {signal['symbol']}
💰 **Entry:** {signal['entry_price']}
🛑 **Stop Loss:** {signal['stop_loss']}
🎯 **Take Profit:** {signal['take_profit']}
📊 **Risk/Reward:** 1:{risk_reward_ratio:.1f}
📝 **Analysis:** {signal['description'] or 'Technical analysis suggests strong momentum'}

⏰ **Time:** {datetime.fromisoformat(signal['created_at']).strftime('%H:%M:%S')}
🆔 **ID:** {signal['signal_id']}

⚠️ **Risk Management:**
• Risk: Max 2% per trade
• Position sizing: Calculate based on account balance
• Follow SL/TP levels exactly
• Never move stop loss against you

💡 **Good Luck Trading!**"""
        
        elif user_status == "trial":
            # Limited details for trial users
            message = f"""🎁 **TRIAL SIGNAL** 🎁

📊 **Symbol:** {signal['symbol']}
💰 **Entry Price:** {signal['entry_price']}
🛑 **Stop Loss:** {signal['stop_loss']}
🎯 **Take Profit:** {signal['take_profit']}

⏰ **Time:** {datetime.fromisoformat(signal['created_at']).strftime('%H:%M:%S')}

⚠️ **Trial Access:** Limited to 3 signals per day
💎 **Upgrade to Premium** for unlimited signals + detailed analysis

💡 **Good Luck!**"""
        
        else:  # suspended or free users - FOMO effect
            message = f"""📊 **PREMIUM SIGNAL RESULT** 📊

🎯 **Symbol:** {signal['symbol']}
💰 **Entry:** {signal['entry_price']}
📈 **Action:** {signal['action']}

⏰ **Time:** {datetime.fromisoformat(signal['created_at']).strftime('%H:%M:%S')}

🚫 **Your subscription is suspended.**
You missed the full entry details and targets.

👉 **Reactivate to unlock ALL entries, SL & TP setups.**
🔗 [Unlock Premium Access](https://t.me/your_bot)"""
        
        return message
    
    async def send_signal_to_users(self, context: ContextTypes.DEFAULT_TYPE, 
                                 signal_id: str, target_status: str = "premium") -> Dict:
        """Send signal to users based on their status"""
        signal = self.get_signal(signal_id)
        if not signal:
            return {"sent": 0, "failed": 0}
        
        users = self.db.get_all_users()
        sent = 0
        failed = 0
        
        for user_id, user_data in users.items():
            try:
                # Skip suspended users for premium signals
                if target_status == "premium" and user_data.get("suspended", False):
                    continue
                
                # Skip non-premium users for premium signals
                if target_status == "premium" and user_data.get("status") != "premium":
                    continue
                
                # Send to trial users
                if target_status == "trial" and user_data.get("status") == "trial":
                    message = self.format_signal_message(signal, "trial")
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode=ParseMode.MARKDOWN
                    )
                    sent += 1
                
                # Send to premium users
                elif target_status == "premium" and user_data.get("status") == "premium":
                    message = self.format_signal_message(signal, "premium")
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode=ParseMode.MARKDOWN
                    )
                    sent += 1
                
                # Send FOMO to suspended users
                elif target_status == "fomo" and user_data.get("suspended", False):
                    message = self.format_signal_message(signal, "suspended")
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode=ParseMode.MARKDOWN
                    )
                    sent += 1
                
            except Exception as e:
                logger.error(f"Failed to send signal to user {user_id}: {e}")
                failed += 1
        
        return {"sent": sent, "failed": failed}
    
    def get_signal_performance(self, days: int = 30) -> Dict:
        """Get signal performance statistics"""
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        total_signals = 0
        closed_signals = 0
        profitable_signals = 0
        total_profit = 0.0
        hit_sl_count = 0
        hit_tp_count = 0
        
        for signal in self.signals.values():
            signal_time = datetime.fromisoformat(signal["created_at"]).timestamp()
            if signal_time < cutoff_date:
                continue
            
            total_signals += 1
            
            if signal["status"] == "closed":
                closed_signals += 1
                profit = signal["results"]["profit_loss"]
                total_profit += profit
                
                if profit > 0:
                    profitable_signals += 1
                
                if signal["results"]["hit_sl"]:
                    hit_sl_count += 1
                elif signal["results"]["hit_tp"]:
                    hit_tp_count += 1
        
        win_rate = (profitable_signals / closed_signals * 100) if closed_signals > 0 else 0
        
        return {
            "total_signals": total_signals,
            "closed_signals": closed_signals,
            "profitable_signals": profitable_signals,
            "win_rate": win_rate,
            "total_profit": total_profit,
            "hit_sl_count": hit_sl_count,
            "hit_tp_count": hit_tp_count,
            "avg_profit": total_profit / closed_signals if closed_signals > 0 else 0
        }
    
    def get_recent_signals(self, limit: int = 10) -> List[Dict]:
        """Get recent signals"""
        sorted_signals = sorted(
            self.signals.values(),
            key=lambda x: x["created_at"],
            reverse=True
        )
        return sorted_signals[:limit]
