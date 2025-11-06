#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database management for Telegram Trading Bot
"""

import json
import os
import shutil
import threading
import time
from datetime import datetime, date
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class UserDatabase:
    """Enhanced JSON-based user database with backup and analytics"""
    
    def __init__(self, filename: str = 'users.json', backup_dir: str = 'backups'):
        self.filename = filename
        self.backup_dir = backup_dir
        self.users = self.load_users()
        self.ensure_backup_dir()
        
        # Debounced save mechanism
        self._save_pending = False
        self._save_lock = threading.Lock()
        self._last_backup = None
        self._save_thread = None
        self._save_interval = 5  # Save every 5 seconds
        self._shutdown = False
    
    def ensure_backup_dir(self):
        """Create backup directory if it doesn't exist"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def load_users(self) -> Dict[int, Dict[str, Any]]:
        """Load users from JSON file"""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert string keys back to integers
                    return {int(k): v for k, v in data.items()}
        except Exception as e:
            logger.error(f"Error loading users: {e}")
        return {}
    
    def save_users(self, immediate: bool = False):
        """Save users to JSON file with backup (debounced unless immediate=True)"""
        with self._save_lock:
            self._save_pending = True
        
        if immediate:
            self._perform_save()
        else:
            # Start background save thread if not running
            if self._save_thread is None or not self._save_thread.is_alive():
                self._save_thread = threading.Thread(target=self._background_save, daemon=True)
                self._save_thread.start()
    
    def _background_save(self):
        """Background thread for debounced saves"""
        while not self._shutdown:
            time.sleep(self._save_interval)
            
            with self._save_lock:
                if self._save_pending:
                    self._perform_save()
                    self._save_pending = False
    
    def _perform_save(self):
        """Perform the actual save operation"""
        try:
            # Only create backup once per minute (not every save)
            should_backup = False
            now = time.time()
            if self._last_backup is None or (now - self._last_backup) > 60:
                should_backup = True
                self._last_backup = now
            
            if should_backup:
                self.create_backup()
            
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False, default=str)
            
            logger.debug(f"Users database saved ({len(self.users)} users)")
        except Exception as e:
            logger.error(f"Error saving users: {e}")
    
    def create_backup(self):
        """Create backup of current database (optimized - only when needed)"""
        try:
            if os.path.exists(self.filename):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_filename = f"users_backup_{timestamp}.json"
                backup_path = os.path.join(self.backup_dir, backup_filename)
                shutil.copy2(self.filename, backup_path)
                
                # Cleanup old backups in background (don't block)
                threading.Thread(target=self.cleanup_old_backups, daemon=True).start()
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
    
    def cleanup_old_backups(self):
        """Keep only the last 10 backup files"""
        try:
            backup_files = [f for f in os.listdir(self.backup_dir) if f.startswith('users_backup_')]
            backup_files.sort(reverse=True)
            
            for old_backup in backup_files[10:]:
                os.remove(os.path.join(self.backup_dir, old_backup))
        except Exception as e:
            logger.error(f"Error cleaning up backups: {e}")
    
    def get_user(self, user_id: int) -> Dict[str, Any]:
        """Get user data with default values"""
        return self.users.get(user_id, {
            'user_id': user_id,
            'status': 'free',
            'country': None,
            'terms_accepted': False,
            'trial_end': None,
            'subscription_end': None,
            'full_name': None,
            'email': None,
            'account_number': None,
            'verified': False,
            'suspended': False,
            'suspension_reason': None,
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'last_verification': None,
            'verification_requests': 0,
            'total_signals_received': 0,
            'premium_since': None
        })
    
    def update_user(self, user_id: int, immediate: bool = False, **kwargs):
        """Update user data
        
        Args:
            user_id: User ID to update
            immediate: If True, save immediately. Otherwise, use debounced save.
            **kwargs: User data fields to update
        """
        if user_id not in self.users:
            self.users[user_id] = self.get_user(user_id)
        
        # Update last activity
        kwargs['last_activity'] = datetime.now().isoformat()
        
        # Handle status changes
        if 'status' in kwargs:
            if kwargs['status'] == 'premium' and self.users[user_id].get('status') != 'premium':
                kwargs['premium_since'] = datetime.now().isoformat()
        
        self.users[user_id].update(kwargs)
        self.save_users(immediate=immediate)
    
    def get_all_users(self) -> Dict[int, Dict[str, Any]]:
        """Get all users"""
        return self.users
    
    def get_users_by_status(self, status: str) -> Dict[int, Dict[str, Any]]:
        """Get users by status"""
        return {uid: user for uid, user in self.users.items() 
                if user.get('status') == status}
    
    def get_suspended_users(self) -> Dict[int, Dict[str, Any]]:
        """Get suspended users"""
        return {uid: user for uid, user in self.users.items() 
                if user.get('suspended', False)}
    
    def get_pending_verifications(self) -> List[Dict[str, Any]]:
        """Get users pending verification"""
        pending = []
        for uid, user in self.users.items():
            if (user.get('account_number') and 
                not user.get('verified') and 
                user.get('status') != 'premium' and
                not user.get('suspended', False)):
                pending.append({
                    'user_id': uid,
                    'full_name': user.get('full_name'),
                    'email': user.get('email'),
                    'account_number': user.get('account_number'),
                    'created_at': user.get('created_at')
                })
        return pending
    
    def suspend_user(self, user_id: int, reason: str = "Manual suspension"):
        """Suspend a user"""
        self.update_user(user_id, 
                        suspended=True, 
                        suspension_reason=reason,
                        status='suspended',
                        immediate=True)
    
    def reactivate_user(self, user_id: int):
        """Reactivate a suspended user"""
        user = self.get_user(user_id)
        if user.get('verified'):
            new_status = 'premium'
        else:
            new_status = 'free'
        
        self.update_user(user_id, 
                        suspended=False, 
                        suspension_reason=None,
                        status=new_status,
                        immediate=True)
    
    def approve_user(self, user_id: int):
        """Approve user for premium access"""
        user = self.get_user(user_id)
        
        # Check if user is on trial
        if user.get('status') == 'trial' and user.get('trial_end'):
            # User is on trial - keep trial status until it expires
            # Just mark as verified, don't change status yet
            self.update_user(user_id, 
                            verified=True,
                            last_verification=datetime.now().isoformat(),
                            immediate=True)
        else:
            # User is not on trial - approve normally
            self.update_user(user_id, 
                            verified=True, 
                            status='premium',
                            last_verification=datetime.now().isoformat(),
                            immediate=True)
    
    def reject_user(self, user_id: int):
        """Reject user verification request"""
        self.update_user(user_id, 
                        verified=False, 
                        status='free',
                        verification_requests=self.get_user(user_id).get('verification_requests', 0) + 1,
                        immediate=True)
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get comprehensive analytics"""
        users = self.users
        total = len(users)
        
        if total == 0:
            return {
                'total_users': 0,
                'free_users': 0,
                'trial_users': 0,
                'premium_users': 0,
                'suspended_users': 0,
                'pending_verifications': 0,
                'conversion_rate': 0,
                'trial_conversion_rate': 0
            }
        
        # Count by status
        free = len([u for u in users.values() if u.get('status') == 'free'])
        trial = len([u for u in users.values() if u.get('status') == 'trial'])
        premium = len([u for u in users.values() if u.get('status') == 'premium'])
        suspended = len([u for u in users.values() if u.get('suspended', False)])
        pending = len(self.get_pending_verifications())
        
        # Calculate conversion rates
        conversion_rate = (premium / total) * 100 if total > 0 else 0
        trial_conversion_rate = (premium / (trial + premium)) * 100 if (trial + premium) > 0 else 0
        
        # Recent activity (last 7 days)
        week_ago = datetime.now().timestamp() - (7 * 24 * 60 * 60)
        recent_users = len([u for u in users.values() 
                           if u.get('created_at') and 
                           datetime.fromisoformat(u['created_at']).timestamp() > week_ago])
        
        return {
            'total_users': total,
            'free_users': free,
            'trial_users': trial,
            'premium_users': premium,
            'suspended_users': suspended,
            'pending_verifications': pending,
            'conversion_rate': round(conversion_rate, 2),
            'trial_conversion_rate': round(trial_conversion_rate, 2),
            'recent_users_7d': recent_users,
            'last_updated': datetime.now().isoformat()
        }
    
    def export_csv(self, filename: str = None) -> str:
        """Export user data to CSV"""
        import csv
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"users_export_{timestamp}.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                if not self.users:
                    return filename
                
                # Get all possible fields
                all_fields = set()
                for user in self.users.values():
                    all_fields.update(user.keys())
                
                fieldnames = ['user_id'] + sorted([f for f in all_fields if f != 'user_id'])
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for user_id, user_data in self.users.items():
                    row = {'user_id': user_id}
                    row.update(user_data)
                    writer.writerow(row)
            
            return filename
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            return None
    
    def cleanup_expired_trials(self):
        """Clean up expired trials"""
        today = date.today()
        expired_count = 0
        
        for user_id, user_data in self.users.items():
            if (user_data.get('status') == 'trial' and 
                user_data.get('trial_end')):
                try:
                    trial_end = datetime.fromisoformat(user_data['trial_end']).date()
                    if trial_end < today:
                        self.update_user(user_id, status='free', immediate=True)
                        expired_count += 1
                except Exception as e:
                    logger.error(f"Error processing trial expiry for user {user_id}: {e}")
        
        if expired_count > 0:
            logger.info(f"Cleaned up {expired_count} expired trials")
        
        return expired_count
    
    def shutdown(self):
        """Shutdown database and save pending changes"""
        self._shutdown = True
        if self._save_pending:
            self._perform_save()
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get detailed stats for a specific user"""
        user = self.get_user(user_id)
        
        # Calculate days since creation
        days_since_creation = 0
        if user.get('created_at'):
            try:
                created = datetime.fromisoformat(user['created_at'])
                days_since_creation = (datetime.now() - created).days
            except:
                pass
        
        # Calculate trial days left
        trial_days_left = 0
        if user.get('status') == 'trial' and user.get('trial_end'):
            try:
                trial_end = datetime.fromisoformat(user['trial_end']).date()
                trial_days_left = max(0, (trial_end - date.today()).days)
            except:
                pass
        
        return {
            'user_id': user_id,
            'status': user.get('status'),
            'country': user.get('country'),
            'verified': user.get('verified', False),
            'suspended': user.get('suspended', False),
            'days_since_creation': days_since_creation,
            'trial_days_left': trial_days_left,
            'verification_requests': user.get('verification_requests', 0),
            'total_signals_received': user.get('total_signals_received', 0),
            'last_activity': user.get('last_activity'),
            'premium_since': user.get('premium_since')
        }