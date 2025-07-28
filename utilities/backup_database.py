#!/usr/bin/env python3
"""
Database Backup Utility - StockAnalyzer Pro
Create timestamped backups of the SQLite database with verification

Usage:
    python utilities/backup_database.py                    # Create backup with timestamp
    python utilities/backup_database.py --name demo_ready  # Create backup with custom name
    python utilities/backup_database.py --list             # List existing backups
    python utilities/backup_database.py --restore latest   # Restore from latest backup
"""

import sys
import os
import argparse
import shutil
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_logging():
    """Setup logging for backup operations"""
    log_dir = Path("data/logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def get_database_stats(db_path: str) -> dict:
    """Get basic statistics about the database"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Get table counts
        tables = ['stocks', 'fundamental_data', 'price_data', 'news_articles', 'calculated_metrics']
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f'{table}_count'] = cursor.fetchone()[0]
            except sqlite3.Error:
                stats[f'{table}_count'] = 0
        
        # Get database file size
        stats['file_size_mb'] = os.path.getsize(db_path) / (1024 * 1024)
        
        # Get last modification time
        stats['last_modified'] = datetime.fromtimestamp(os.path.getmtime(db_path))
        
        conn.close()
        return stats
        
    except Exception as e:
        return {'error': str(e)}

def verify_backup(original_path: str, backup_path: str, logger: logging.Logger) -> bool:
    """Verify that backup was created successfully and matches original"""
    try:
        # Check file exists
        if not os.path.exists(backup_path):
            logger.error(f"❌ Backup file not found: {backup_path}")
            return False
        
        # Check file sizes match
        original_size = os.path.getsize(original_path)
        backup_size = os.path.getsize(backup_path)
        
        if original_size != backup_size:
            logger.error(f"❌ File size mismatch: original={original_size}, backup={backup_size}")
            return False
        
        # Verify database integrity
        try:
            conn = sqlite3.connect(backup_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            conn.close()
            
            if result != "ok":
                logger.error(f"❌ Backup database integrity check failed: {result}")
                return False
        except Exception as e:
            logger.error(f"❌ Backup database verification failed: {str(e)}")
            return False
        
        # Compare table counts
        original_stats = get_database_stats(original_path)
        backup_stats = get_database_stats(backup_path)
        
        tables_to_check = ['stocks_count', 'news_articles_count', 'calculated_metrics_count']
        for table_stat in tables_to_check:
            if original_stats.get(table_stat, 0) != backup_stats.get(table_stat, 0):
                logger.warning(f"⚠️  Table count mismatch for {table_stat}: "
                             f"original={original_stats.get(table_stat, 0)}, "
                             f"backup={backup_stats.get(table_stat, 0)}")
        
        logger.info("✅ Backup verification passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Backup verification failed: {str(e)}")
        return False

def create_backup(db_path: str = "data/stock_data.db", backup_name: Optional[str] = None, 
                 logger: logging.Logger = None) -> Tuple[bool, str]:
    """
    Create a backup of the database
    
    Args:
        db_path: Path to original database
        backup_name: Custom name for backup (None = timestamp)
        logger: Logger instance
        
    Returns:
        Tuple of (success, backup_path)
    """
    try:
        # Check if original database exists
        if not os.path.exists(db_path):
            logger.error(f"❌ Original database not found: {db_path}")
            return False, ""
        
        # Create backups directory
        backup_dir = Path("data/backups")
        backup_dir.mkdir(exist_ok=True)
        
        # Generate backup filename
        if backup_name:
            backup_filename = f"stock_data_backup_{backup_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        else:
            backup_filename = f"stock_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        backup_path = backup_dir / backup_filename
        
        logger.info(f"🔄 Creating backup: {backup_filename}")
        
        # Get original database stats
        original_stats = get_database_stats(db_path)
        logger.info(f"📊 Original database: {original_stats['file_size_mb']:.1f} MB")
        
        for key, value in original_stats.items():
            if key.endswith('_count'):
                table_name = key.replace('_count', '')
                logger.info(f"   {table_name}: {value:,} records")
        
        # Create backup using SQLite backup method (more reliable than file copy)
        try:
            # Connect to both databases
            source_conn = sqlite3.connect(db_path)
            backup_conn = sqlite3.connect(str(backup_path))
            
            # Perform backup
            source_conn.backup(backup_conn)
            
            # Close connections
            backup_conn.close()
            source_conn.close()
            
            logger.info("✅ Database backup completed using SQLite backup method")
            
        except Exception as e:
            logger.warning(f"⚠️  SQLite backup method failed: {str(e)}")
            logger.info("🔄 Falling back to file copy method...")
            
            # Fallback to file copy
            shutil.copy2(db_path, backup_path)
            logger.info("✅ Database backup completed using file copy method")
        
        # Verify backup
        if verify_backup(db_path, str(backup_path), logger):
            backup_stats = get_database_stats(str(backup_path))
            logger.info(f"✅ Backup created successfully: {backup_path}")
            logger.info(f"📊 Backup size: {backup_stats['file_size_mb']:.1f} MB")
            return True, str(backup_path)
        else:
            # Remove failed backup
            if backup_path.exists():
                backup_path.unlink()
            logger.error("❌ Backup verification failed - backup removed")
            return False, ""
        
    except Exception as e:
        logger.error(f"❌ Backup creation failed: {str(e)}")
        return False, ""

def list_backups(logger: logging.Logger = None) -> List[dict]:
    """List all available backups with details"""
    backup_dir = Path("data/backups")
    
    if not backup_dir.exists():
        logger.info("📁 No backups directory found")
        return []
    
    backups = []
    backup_files = list(backup_dir.glob("stock_data_backup_*.db"))
    
    if not backup_files:
        logger.info("📁 No backups found")
        return []
    
    logger.info(f"📁 Found {len(backup_files)} backup(s):")
    
    for backup_file in sorted(backup_files, key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            stats = backup_file.stat()
            backup_info = {
                'filename': backup_file.name,
                'path': str(backup_file),
                'size_mb': stats.st_size / (1024 * 1024),
                'created': datetime.fromtimestamp(stats.st_mtime),
                'age_hours': (datetime.now() - datetime.fromtimestamp(stats.st_mtime)).total_seconds() / 3600
            }
            
            # Try to get database stats
            db_stats = get_database_stats(str(backup_file))
            if 'error' not in db_stats:
                backup_info.update(db_stats)
            
            backups.append(backup_info)
            
            # Display info
            age_str = f"{backup_info['age_hours']:.1f} hours ago" if backup_info['age_hours'] < 48 else f"{backup_info['age_hours']/24:.1f} days ago"
            logger.info(f"   📦 {backup_file.name}")
            logger.info(f"      Created: {backup_info['created'].strftime('%Y-%m-%d %H:%M:%S')} ({age_str})")
            logger.info(f"      Size: {backup_info['size_mb']:.1f} MB")
            
            if 'stocks_count' in backup_info:
                logger.info(f"      Contents: {backup_info['stocks_count']} stocks, {backup_info.get('news_articles_count', 0)} news articles")
            
        except Exception as e:
            logger.warning(f"⚠️  Could not read backup {backup_file.name}: {str(e)}")
    
    return backups

def restore_backup(backup_identifier: str, target_path: str = "data/stock_data.db", 
                  logger: logging.Logger = None) -> bool:
    """
    Restore database from backup
    
    Args:
        backup_identifier: 'latest', full filename, or partial name match
        target_path: Where to restore the database
        logger: Logger instance
        
    Returns:
        bool: Success status
    """
    try:
        backup_dir = Path("data/backups")
        backup_files = list(backup_dir.glob("stock_data_backup_*.db"))
        
        if not backup_files:
            logger.error("❌ No backups found to restore")
            return False
        
        # Find the backup to restore
        selected_backup = None
        
        if backup_identifier == "latest":
            # Use most recent backup
            selected_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
            logger.info(f"🔄 Selected latest backup: {selected_backup.name}")
            
        else:
            # Look for exact filename match first
            for backup_file in backup_files:
                if backup_file.name == backup_identifier:
                    selected_backup = backup_file
                    break
            
            # If no exact match, look for partial match
            if not selected_backup:
                matches = [f for f in backup_files if backup_identifier in f.name]
                if len(matches) == 1:
                    selected_backup = matches[0]
                    logger.info(f"🔄 Found matching backup: {selected_backup.name}")
                elif len(matches) > 1:
                    logger.error(f"❌ Multiple backups match '{backup_identifier}': {[f.name for f in matches]}")
                    return False
                else:
                    logger.error(f"❌ No backup found matching '{backup_identifier}'")
                    return False
        
        if not selected_backup:
            logger.error("❌ Could not identify backup to restore")
            return False
        
        # Verify backup before restoring
        if not verify_backup(str(selected_backup), str(selected_backup), logger):
            logger.error("❌ Backup verification failed - cannot restore corrupted backup")
            return False
        
        # Create backup of current database before overwriting
        if os.path.exists(target_path):
            logger.info("🛡️  Creating safety backup of current database...")
            safety_backup_path = f"{target_path}.pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(target_path, safety_backup_path)
            logger.info(f"✅ Safety backup created: {safety_backup_path}")
        
        # Restore the backup
        logger.info(f"🔄 Restoring backup: {selected_backup.name} → {target_path}")
        shutil.copy2(selected_backup, target_path)
        
        # Verify restored database
        if verify_backup(str(selected_backup), target_path, logger):
            restored_stats = get_database_stats(target_path)
            logger.info("✅ Database restored successfully!")
            logger.info(f"📊 Restored database: {restored_stats['file_size_mb']:.1f} MB")
            
            for key, value in restored_stats.items():
                if key.endswith('_count'):
                    table_name = key.replace('_count', '')
                    logger.info(f"   {table_name}: {value:,} records")
            
            return True
        else:
            logger.error("❌ Restored database verification failed")
            return False
        
    except Exception as e:
        logger.error(f"❌ Database restore failed: {str(e)}")
        return False

def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Backup and restore database for StockAnalyzer Pro",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python utilities/backup_database.py                    # Create timestamped backup
  python utilities/backup_database.py --name demo_ready  # Create named backup
  python utilities/backup_database.py --list             # List all backups
  python utilities/backup_database.py --restore latest   # Restore latest backup
  python utilities/backup_database.py --restore stock_data_backup_demo_ready_20250728_120000.db
        """
    )
    
    parser.add_argument(
        '--name',
        type=str,
        help='Custom name for the backup (e.g., "demo_ready", "before_testing")'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available backups with details'
    )
    
    parser.add_argument(
        '--restore',
        type=str,
        help='Restore from backup: "latest" or specific backup filename'
    )
    
    parser.add_argument(
        '--db-path',
        type=str,
        default='data/stock_data.db',
        help='Path to database file (default: data/stock_data.db)'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress interactive prompts'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    
    print("💾 StockAnalyzer Pro - Database Backup Utility")
    print("=" * 50)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # List backups
    if args.list:
        list_backups(logger)
        return
    
    # Restore backup
    if args.restore:
        if not args.quiet:
            response = input(f"⚠️  This will overwrite the current database. Continue? (y/N): ")
            if response.lower() != 'y':
                print("❌ Restore cancelled by user")
                return
        
        success = restore_backup(args.restore, args.db_path, logger)
        if success:
            print("\n✅ Database restore completed successfully!")
            print("💡 Restart any running applications to use the restored database")
        else:
            print("\n❌ Database restore failed - check logs for details")
            sys.exit(1)
        return
    
    # Create backup (default action)
    if not args.quiet and not args.name:
        print("🔄 Creating backup of current database...")
        response = input("Enter custom name (optional, press Enter for timestamp): ")
        if response.strip():
            args.name = response.strip()
    
    success, backup_path = create_backup(args.db_path, args.name, logger)
    
    if success:
        print(f"\n✅ Backup created successfully!")
        print(f"📁 Location: {backup_path}")
        print(f"💡 To restore: python utilities/backup_database.py --restore latest")
    else:
        print("\n❌ Backup creation failed - check logs for details")
        sys.exit(1)

if __name__ == "__main__":
    main()