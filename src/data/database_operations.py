#!/usr/bin/env python3
"""
Database Operations Manager
Production-critical module for backup, export, and performance operations
"""

import os
import json
import csv
import sqlite3
import shutil
import gzip
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import pandas as pd

from .database import DatabaseManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseOperationsManager:
    """
    Production-critical database operations manager
    
    Features:
    - Backup and restore operations with integrity verification
    - Data export in multiple formats (CSV, JSON, Excel)
    - Performance monitoring and optimization
    - Database cleanup and archival
    - Error recovery and repair operations
    """
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """Initialize Database Operations Manager"""
        self.db_manager = db_manager or DatabaseManager()
        self.backup_dir = Path("backups")
        self.export_dir = Path("exports")
        self.backup_dir.mkdir(exist_ok=True)
        self.export_dir.mkdir(exist_ok=True)
        
        logger.info("Database Operations Manager initialized")
    
    # ==================== BACKUP OPERATIONS ====================
    
    def create_backup(self, backup_name: Optional[str] = None, compress: bool = True) -> Dict[str, Any]:
        """
        Create comprehensive database backup with integrity verification
        
        Args:
            backup_name: Custom backup name (defaults to timestamp)
            compress: Whether to compress backup file
            
        Returns:
            Dict with backup metadata and verification results
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = backup_name or f"backup_{timestamp}"
            
            logger.info(f"Creating backup: {backup_name}")
            
            # Ensure database connection
            if not self.db_manager.connect():
                raise Exception("Failed to connect to database")
            
            # Create backup metadata
            metadata = {
                "backup_name": backup_name,
                "timestamp": timestamp,
                "created_at": datetime.now().isoformat(),
                "compressed": compress,
                "integrity_verified": False,
                "file_size_bytes": 0,
                "record_counts": {},
                "checksum": None
            }
            
            # Get record counts before backup
            tables = ["stocks", "price_data", "fundamental_data", "news_articles", "reddit_posts", "daily_sentiment"]
            for table in tables:
                try:
                    cursor = self.db_manager.connection.cursor()
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    metadata["record_counts"][table] = count
                except sqlite3.OperationalError:
                    metadata["record_counts"][table] = 0
            
            # Create backup file path
            backup_file = self.backup_dir / f"{backup_name}.db"
            if compress:
                backup_file = self.backup_dir / f"{backup_name}.db.gz"
            
            # Perform backup
            if compress:
                # Compressed backup
                with open(self.db_manager.db_path, 'rb') as src:
                    with gzip.open(backup_file, 'wb') as dst:
                        shutil.copyfileobj(src, dst)
            else:
                # Uncompressed backup
                shutil.copy2(self.db_manager.db_path, backup_file)
            
            # Calculate file size and checksum
            metadata["file_size_bytes"] = backup_file.stat().st_size
            metadata["checksum"] = self._calculate_file_checksum(backup_file)
            
            # Verify backup integrity
            verification_result = self._verify_backup_integrity(backup_file, metadata)
            metadata["integrity_verified"] = verification_result["verified"]
            metadata["verification_details"] = verification_result
            
            # Save metadata
            metadata_file = self.backup_dir / f"{backup_name}_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Backup created successfully: {backup_file}")
            logger.info(f"Backup size: {metadata['file_size_bytes']:,} bytes")
            logger.info(f"Integrity verified: {metadata['integrity_verified']}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Backup creation failed: {str(e)}")
            raise
        finally:
            self.db_manager.close()
    
    def restore_backup(self, backup_name: str, verify_before_restore: bool = True) -> Dict[str, Any]:
        """
        Restore database from backup with verification
        
        Args:
            backup_name: Name of backup to restore
            verify_before_restore: Whether to verify backup before restoring
            
        Returns:
            Dict with restoration results
        """
        try:
            logger.info(f"Starting restore from backup: {backup_name}")
            
            # Find backup files
            backup_file = None
            for ext in [".db.gz", ".db"]:
                candidate = self.backup_dir / f"{backup_name}{ext}"
                if candidate.exists():
                    backup_file = candidate
                    break
            
            if not backup_file:
                raise FileNotFoundError(f"Backup not found: {backup_name}")
            
            # Load metadata
            metadata_file = self.backup_dir / f"{backup_name}_metadata.json"
            metadata = {}
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
            
            # Verify backup before restore
            if verify_before_restore:
                logger.info("Verifying backup integrity before restore...")
                verification = self._verify_backup_integrity(backup_file, metadata)
                if not verification["verified"]:
                    raise Exception(f"Backup verification failed: {verification['errors']}")
            
            # Create backup of current database
            current_backup = f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            logger.info(f"Creating safety backup: {current_backup}")
            self.create_backup(current_backup, compress=True)
            
            # Close current database connection
            self.db_manager.close()
            
            # Restore database
            if backup_file.suffix == '.gz':
                # Decompress and restore
                with gzip.open(backup_file, 'rb') as src:
                    with open(self.db_manager.db_path, 'wb') as dst:
                        shutil.copyfileobj(src, dst)
            else:
                # Direct copy
                shutil.copy2(backup_file, self.db_manager.db_path)
            
            # Verify restored database
            if not self.db_manager.connect():
                raise Exception("Failed to connect to restored database")
            
            # Verify record counts
            restored_counts = {}
            tables = ["stocks", "price_data", "fundamental_data", "news_articles", "reddit_posts", "daily_sentiment"]
            for table in tables:
                try:
                    cursor = self.db_manager.connection.cursor()
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    restored_counts[table] = count
                except sqlite3.OperationalError:
                    restored_counts[table] = 0
            
            # Compare with original counts if available
            count_verification = True
            if "record_counts" in metadata:
                for table, original_count in metadata["record_counts"].items():
                    if restored_counts.get(table, 0) != original_count:
                        count_verification = False
                        logger.warning(f"Record count mismatch in {table}: expected {original_count}, got {restored_counts.get(table, 0)}")
            
            result = {
                "backup_name": backup_name,
                "restored_at": datetime.now().isoformat(),
                "backup_file": str(backup_file),
                "backup_size_bytes": backup_file.stat().st_size,
                "count_verification": count_verification,
                "restored_counts": restored_counts,
                "metadata_available": bool(metadata),
                "safety_backup": current_backup
            }
            
            logger.info("Database restore completed successfully")
            logger.info(f"Restored counts: {restored_counts}")
            
            return result
            
        except Exception as e:
            logger.error(f"Database restore failed: {str(e)}")
            raise
    
    # ==================== EXPORT OPERATIONS ====================
    
    def export_data(self, format_type: str = "csv", tables: Optional[List[str]] = None, 
                   filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Export database data in various formats
        
        Args:
            format_type: Export format ('csv', 'json', 'excel')
            tables: List of tables to export (None = all tables)
            filters: Optional filters for data export
            
        Returns:
            Dict with export results
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_name = f"export_{timestamp}"
            
            logger.info(f"Starting data export: {format_type}")
            
            if not self.db_manager.connect():
                raise Exception("Failed to connect to database")
            
            # Get list of tables to export
            if tables is None:
                tables = ["stocks", "price_data", "fundamental_data", "news_articles", "reddit_posts", "daily_sentiment"]
            
            exported_files = []
            total_records = 0
            
            if format_type.lower() == "csv":
                # CSV Export
                for table in tables:
                    csv_file = self.export_dir / f"{export_name}_{table}.csv"
                    records = self._export_table_to_csv(table, csv_file, filters)
                    if records > 0:
                        exported_files.append(str(csv_file))
                        total_records += records
            
            elif format_type.lower() == "json":
                # JSON Export
                json_file = self.export_dir / f"{export_name}.json"
                data = {}
                for table in tables:
                    table_data = self._export_table_to_dict(table, filters)
                    if table_data:
                        data[table] = table_data
                        total_records += len(table_data)
                
                with open(json_file, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
                exported_files.append(str(json_file))
            
            elif format_type.lower() == "excel":
                # Excel Export
                excel_file = self.export_dir / f"{export_name}.xlsx"
                with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                    for table in tables:
                        df = self._export_table_to_dataframe(table, filters)
                        if not df.empty:
                            df.to_excel(writer, sheet_name=table, index=False)
                            total_records += len(df)
                exported_files.append(str(excel_file))
            
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
            
            result = {
                "export_name": export_name,
                "format": format_type,
                "exported_at": datetime.now().isoformat(),
                "tables_exported": tables,
                "total_records": total_records,
                "files": exported_files,
                "filters_applied": filters or {}
            }
            
            logger.info(f"Data export completed: {total_records:,} records exported")
            
            return result
            
        except Exception as e:
            logger.error(f"Data export failed: {str(e)}")
            raise
        finally:
            self.db_manager.close()
    
    # ==================== PERFORMANCE OPERATIONS ====================
    
    def analyze_performance(self) -> Dict[str, Any]:
        """
        Comprehensive database performance analysis
        
        Returns:
            Dict with performance metrics and recommendations
        """
        try:
            logger.info("Starting database performance analysis")
            
            if not self.db_manager.connect():
                raise Exception("Failed to connect to database")
            
            cursor = self.db_manager.connection.cursor()
            
            # Database file size
            db_size = Path(self.db_manager.db_path).stat().st_size
            
            # Table sizes and record counts
            table_stats = {}
            total_records = 0
            
            tables = ["stocks", "price_data", "fundamental_data", "news_articles", "reddit_posts", "daily_sentiment"]
            for table in tables:
                try:
                    # Record count
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    
                    # Table size (approximate)
                    cursor.execute(f"SELECT SUM(LENGTH(sql)) FROM sqlite_master WHERE type='table' AND name='{table}'")
                    schema_size = cursor.fetchone()[0] or 0
                    
                    table_stats[table] = {
                        "record_count": count,
                        "schema_size": schema_size
                    }
                    total_records += count
                    
                except sqlite3.OperationalError:
                    table_stats[table] = {"record_count": 0, "schema_size": 0}
            
            # Index analysis
            cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
            indexes = cursor.fetchall()
            
            # Query performance test
            query_performance = self._test_query_performance()
            
            # Database integrity check
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            
            # Database statistics
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            
            # Vacuum recommendation
            cursor.execute("PRAGMA freelist_count")
            free_pages = cursor.fetchone()[0]
            vacuum_recommended = free_pages > (page_count * 0.1)  # >10% free pages
            
            result = {
                "analysis_timestamp": datetime.now().isoformat(),
                "database_size_bytes": db_size,
                "database_size_mb": round(db_size / (1024 * 1024), 2),
                "total_records": total_records,
                "table_statistics": table_stats,
                "indexes": [{"name": idx[0], "definition": idx[1]} for idx in indexes],
                "query_performance": query_performance,
                "integrity_check": integrity_result,
                "page_statistics": {
                    "page_count": page_count,
                    "page_size": page_size,
                    "free_pages": free_pages,
                    "vacuum_recommended": vacuum_recommended
                },
                "recommendations": self._generate_performance_recommendations(
                    db_size, total_records, vacuum_recommended, query_performance
                )
            }
            
            logger.info(f"Performance analysis completed - DB Size: {result['database_size_mb']} MB, Records: {total_records:,}")
            
            return result
            
        except Exception as e:
            logger.error(f"Performance analysis failed: {str(e)}")
            raise
        finally:
            self.db_manager.close()
    
    def optimize_database(self, vacuum: bool = True, reindex: bool = True) -> Dict[str, Any]:
        """
        Optimize database performance
        
        Args:
            vacuum: Whether to run VACUUM operation
            reindex: Whether to rebuild indexes
            
        Returns:
            Dict with optimization results
        """
        try:
            logger.info("Starting database optimization")
            
            if not self.db_manager.connect():
                raise Exception("Failed to connect to database")
            
            cursor = self.db_manager.connection.cursor()
            
            # Pre-optimization metrics
            cursor.execute("PRAGMA page_count")
            pages_before = cursor.fetchone()[0]
            cursor.execute("PRAGMA freelist_count")
            free_pages_before = cursor.fetchone()[0]
            
            optimization_steps = []
            
            if reindex:
                logger.info("Rebuilding indexes...")
                cursor.execute("REINDEX")
                optimization_steps.append("REINDEX completed")
            
            if vacuum:
                logger.info("Running VACUUM operation...")
                cursor.execute("VACUUM")
                optimization_steps.append("VACUUM completed")
            
            # Post-optimization metrics
            cursor.execute("PRAGMA page_count")
            pages_after = cursor.fetchone()[0]
            cursor.execute("PRAGMA freelist_count")
            free_pages_after = cursor.fetchone()[0]
            
            # Calculate space saved
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            space_saved = (pages_before - pages_after) * page_size
            
            result = {
                "optimization_timestamp": datetime.now().isoformat(),
                "steps_performed": optimization_steps,
                "pages_before": pages_before,
                "pages_after": pages_after,
                "free_pages_before": free_pages_before,
                "free_pages_after": free_pages_after,
                "space_saved_bytes": space_saved,
                "space_saved_mb": round(space_saved / (1024 * 1024), 2),
                "vacuum_performed": vacuum,
                "reindex_performed": reindex
            }
            
            logger.info(f"Database optimization completed - Space saved: {result['space_saved_mb']} MB")
            
            return result
            
        except Exception as e:
            logger.error(f"Database optimization failed: {str(e)}")
            raise
        finally:
            self.db_manager.close()
    
    # ==================== CLEANUP OPERATIONS ====================
    
    def cleanup_old_data(self, retention_days: int = 30) -> Dict[str, Any]:
        """
        Clean up old data based on retention policy
        
        Args:
            retention_days: Number of days to retain data
            
        Returns:
            Dict with cleanup results
        """
        try:
            logger.info(f"Starting data cleanup - retention: {retention_days} days")
            
            if not self.db_manager.connect():
                raise Exception("Failed to connect to database")
            
            cursor = self.db_manager.connection.cursor()
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            cleanup_results = {}
            
            # Clean up old news articles
            cursor.execute("SELECT COUNT(*) FROM news_articles WHERE publish_date < ?", (cutoff_date,))
            old_news_count = cursor.fetchone()[0]
            
            cursor.execute("DELETE FROM news_articles WHERE publish_date < ?", (cutoff_date,))
            cleanup_results["news_articles_deleted"] = old_news_count
            
            # Clean up old Reddit posts
            cursor.execute("SELECT COUNT(*) FROM reddit_posts WHERE created_utc < ?", (cutoff_date.timestamp(),))
            old_reddit_count = cursor.fetchone()[0]
            
            cursor.execute("DELETE FROM reddit_posts WHERE created_utc < ?", (cutoff_date.timestamp(),))
            cleanup_results["reddit_posts_deleted"] = old_reddit_count
            
            # Clean up old sentiment data
            cursor.execute("SELECT COUNT(*) FROM daily_sentiment WHERE date < ?", (cutoff_date.date(),))
            old_sentiment_count = cursor.fetchone()[0]
            
            cursor.execute("DELETE FROM daily_sentiment WHERE date < ?", (cutoff_date.date(),))
            cleanup_results["sentiment_records_deleted"] = old_sentiment_count
            
            self.db_manager.connection.commit()
            
            total_deleted = sum(cleanup_results.values())
            
            result = {
                "cleanup_timestamp": datetime.now().isoformat(),
                "retention_days": retention_days,
                "cutoff_date": cutoff_date.isoformat(),
                "cleanup_results": cleanup_results,
                "total_records_deleted": total_deleted
            }
            
            logger.info(f"Data cleanup completed - {total_deleted:,} records deleted")
            
            return result
            
        except Exception as e:
            logger.error(f"Data cleanup failed: {str(e)}")
            raise
        finally:
            self.db_manager.close()
    
    # ==================== HELPER METHODS ====================
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _verify_backup_integrity(self, backup_file: Path, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Verify backup file integrity"""
        try:
            # Check file exists and has size
            if not backup_file.exists():
                return {"verified": False, "errors": ["Backup file does not exist"]}
            
            file_size = backup_file.stat().st_size
            if file_size == 0:
                return {"verified": False, "errors": ["Backup file is empty"]}
            
            # Verify checksum if available
            errors = []
            if "checksum" in metadata:
                current_checksum = self._calculate_file_checksum(backup_file)
                if current_checksum != metadata["checksum"]:
                    errors.append("Checksum mismatch - file may be corrupted")
            
            # Test database connectivity (for uncompressed backups)
            if backup_file.suffix != '.gz':
                try:
                    test_conn = sqlite3.connect(backup_file)
                    test_conn.execute("SELECT COUNT(*) FROM sqlite_master")
                    test_conn.close()
                except sqlite3.Error as e:
                    errors.append(f"Database connectivity test failed: {str(e)}")
            
            return {
                "verified": len(errors) == 0,
                "errors": errors,
                "file_size": file_size,
                "checksum_verified": "checksum" in metadata and len(errors) == 0
            }
            
        except Exception as e:
            return {"verified": False, "errors": [f"Verification failed: {str(e)}"]}
    
    def _export_table_to_csv(self, table: str, csv_file: Path, filters: Optional[Dict[str, Any]]) -> int:
        """Export table to CSV file"""
        cursor = self.db_manager.connection.cursor()
        
        # Build query with filters
        query = f"SELECT * FROM {table}"
        params = []
        
        if filters and table in filters:
            where_clauses = []
            for column, value in filters[table].items():
                where_clauses.append(f"{column} = ?")
                params.append(value)
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
        
        cursor.execute(query, params)
        
        # Get column names
        columns = [description[0] for description in cursor.description]
        
        # Write CSV
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            
            count = 0
            for row in cursor:
                writer.writerow(row)
                count += 1
        
        return count
    
    def _export_table_to_dict(self, table: str, filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Export table to list of dictionaries"""
        cursor = self.db_manager.connection.cursor()
        
        # Build query with filters
        query = f"SELECT * FROM {table}"
        params = []
        
        if filters and table in filters:
            where_clauses = []
            for column, value in filters[table].items():
                where_clauses.append(f"{column} = ?")
                params.append(value)
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
        
        cursor.execute(query, params)
        
        # Get column names
        columns = [description[0] for description in cursor.description]
        
        # Convert to list of dicts
        result = []
        for row in cursor:
            result.append(dict(zip(columns, row)))
        
        return result
    
    def _export_table_to_dataframe(self, table: str, filters: Optional[Dict[str, Any]]) -> pd.DataFrame:
        """Export table to pandas DataFrame"""
        # Build query with filters
        query = f"SELECT * FROM {table}"
        params = []
        
        if filters and table in filters:
            where_clauses = []
            for column, value in filters[table].items():
                where_clauses.append(f"{column} = ?")
                params.append(value)
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
        
        return pd.read_sql_query(query, self.db_manager.connection, params=params)
    
    def _test_query_performance(self) -> Dict[str, float]:
        """Test common query performance"""
        cursor = self.db_manager.connection.cursor()
        performance_tests = {}
        
        # Test queries
        test_queries = {
            "stock_count": "SELECT COUNT(*) FROM stocks",
            "recent_fundamentals": "SELECT * FROM fundamental_data ORDER BY reporting_date DESC LIMIT 100",
            "sector_grouping": "SELECT sector, COUNT(*) FROM stocks GROUP BY sector",
            "composite_scores": "SELECT symbol, composite_score FROM stocks WHERE composite_score IS NOT NULL LIMIT 100"
        }
        
        for test_name, query in test_queries.items():
            try:
                start_time = datetime.now()
                cursor.execute(query)
                cursor.fetchall()
                end_time = datetime.now()
                
                duration = (end_time - start_time).total_seconds()
                performance_tests[test_name] = duration
                
            except sqlite3.Error:
                performance_tests[test_name] = -1.0  # Error indicator
        
        return performance_tests
    
    def _generate_performance_recommendations(self, db_size: int, total_records: int, 
                                            vacuum_recommended: bool, query_performance: Dict[str, float]) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        # Size-based recommendations
        if db_size > 100 * 1024 * 1024:  # >100MB
            recommendations.append("Consider archiving old data - database size is large")
        
        # Vacuum recommendation
        if vacuum_recommended:
            recommendations.append("Run VACUUM to reclaim free space and optimize storage")
        
        # Query performance recommendations
        slow_queries = [name for name, duration in query_performance.items() if duration > 1.0]
        if slow_queries:
            recommendations.append(f"Consider adding indexes for slow queries: {', '.join(slow_queries)}")
        
        # Record count recommendations
        if total_records > 100000:
            recommendations.append("Consider implementing data partitioning for large datasets")
        
        if not recommendations:
            recommendations.append("Database performance is optimal")
        
        return recommendations
    
    # ==================== UTILITY METHODS ====================
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups with metadata"""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.db*"):
            if backup_file.suffix in ['.db', '.gz']:
                backup_name = backup_file.stem
                if backup_name.endswith('.db'):
                    backup_name = backup_name[:-3]  # Remove .db extension
                
                # Load metadata if available
                metadata_file = self.backup_dir / f"{backup_name}_metadata.json"
                metadata = {"backup_name": backup_name}
                
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata.update(json.load(f))
                    except:
                        pass
                
                # Add file stats
                metadata["file_size_bytes"] = backup_file.stat().st_size
                metadata["file_path"] = str(backup_file)
                metadata["compressed"] = backup_file.suffix == '.gz'
                
                backups.append(metadata)
        
        return sorted(backups, key=lambda x: x.get("created_at", ""), reverse=True)
    
    def get_storage_usage(self) -> Dict[str, Any]:
        """Get storage usage statistics"""
        def get_dir_size(path: Path) -> int:
            return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        
        database_size = Path(self.db_manager.db_path).stat().st_size if Path(self.db_manager.db_path).exists() else 0
        backup_size = get_dir_size(self.backup_dir)
        export_size = get_dir_size(self.export_dir)
        
        return {
            "database_size_bytes": database_size,
            "backup_size_bytes": backup_size,
            "export_size_bytes": export_size,
            "total_size_bytes": database_size + backup_size + export_size,
            "database_size_mb": round(database_size / (1024 * 1024), 2),
            "backup_size_mb": round(backup_size / (1024 * 1024), 2),
            "export_size_mb": round(export_size / (1024 * 1024), 2),
            "total_size_mb": round((database_size + backup_size + export_size) / (1024 * 1024), 2)
        }