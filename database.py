#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database management for Telegram Trading Bot
"""

import json
import os
import shutil
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
    
    def save_users(self):
        """Save users to JSON file with backup"""
        try:
            # Create backup before saving
            self.create_backup()
            
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"Error saving users: {e}")
    
    def create_backup(self):
        """Create backup of current database"""
        try:
            if os.path.exists(self.filename):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_filename = f"users_backup_{timestamp}.json"
                backup_path = os.path.join(self.backup_dir, backup_filename)
                shutil.copy2(self.filename, backup_path)
                
                # Keep only last 10 backups
                self.cleanup_old_backups()
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
    
    def update_user(self, user_id: int, **kwargs):
        """Update user data"""
        if user_id not in self.users:
            self.users[user_id] = self.get_user(user_id)
        
        # Update last activity
        kwargs['last_activity'] = datetime.now().isoformat()
        
        # Handle status changes
        if 'status' in kwargs:
            if kwargs['status'] == 'premium' and self.users[user_id].get('status') != 'premium':
                kwargs['premium_since'] = datetime.now().isoformat()
        
        self.users[user_id].update(kwargs)
        self.save_users()
    
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
                        status='suspended')
    
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
                        status=new_status)
    
    def approve_user(self, user_id: int):
        """Approve user for premium access"""
        self.update_user(user_id, 
                        verified=True, 
                        status='premium',
                        last_verification=datetime.now().isoformat())
    
    def reject_user(self, user_id: int):
        """Reject user verification request"""
        self.update_user(user_id, 
                        verified=False, 
                        status='free',
                        verification_requests=self.get_user(user_id).get('verification_requests', 0) + 1)
    
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
                        self.update_user(user_id, status='free')
                        expired_count += 1
                except Exception as e:
                    logger.error(f"Error processing trial expiry for user {user_id}: {e}")
        
        if expired_count > 0:
            logger.info(f"Cleaned up {expired_count} expired trials")
        
        return expired_count
    
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