#!/usr/bin/env python3
"""
Data Source Monitoring Module
Real-time monitoring of API connections, rate limits, and data freshness
"""

import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import yfinance as yf
import praw
import logging

from ..utils.helpers import load_config
from .database import DatabaseManager

@dataclass
class APIStatus:
    """Status information for an API source"""
    name: str
    status: str  # 'active', 'limited', 'down', 'unknown'
    last_check: datetime
    response_time_ms: Optional[float]
    rate_limit_remaining: Optional[int]
    rate_limit_total: Optional[int]
    rate_limit_reset: Optional[datetime]
    error_message: Optional[str]
    success_rate: float  # Last 24h success rate

@dataclass
class DataFreshness:
    """Data freshness information"""
    data_type: str
    table_name: str
    last_update: Optional[datetime]
    record_count: int
    staleness_hours: float
    is_stale: bool
    threshold_hours: int

class DataSourceMonitor:
    """Monitor data sources, API connections, and data freshness"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = load_config(config_path)
        self.db = DatabaseManager()
        self.logger = logging.getLogger(__name__)
        
        # API status cache
        self._api_status_cache: Dict[str, APIStatus] = {}
        self._cache_ttl = 300  # 5 minutes
        
        # Freshness thresholds (hours)
        self.freshness_thresholds = {
            'price_data': 24,      # Daily price updates
            'fundamental_data': 72,  # 3 days for fundamentals
            'news_articles': 6,     # 6 hours for news
            'reddit_posts': 12,     # 12 hours for social data
            'daily_sentiment': 24   # Daily sentiment aggregation
        }
    
    def get_all_api_status(self) -> Dict[str, APIStatus]:
        """Get status for all configured APIs"""
        statuses = {}
        
        # Check Yahoo Finance API
        statuses['yahoo_finance'] = self._check_yahoo_finance_status()
        
        # Check Reddit API (if configured)
        if self._is_reddit_configured():
            statuses['reddit'] = self._check_reddit_status()
        else:
            statuses['reddit'] = APIStatus(
                name='Reddit API',
                status='not_configured',
                last_check=datetime.now(),
                response_time_ms=None,
                rate_limit_remaining=None,
                rate_limit_total=None,
                rate_limit_reset=None,
                error_message='API credentials not configured',
                success_rate=0.0
            )
        
        # Check database connection
        statuses['database'] = self._check_database_status()
        
        return statuses
    
    def _check_yahoo_finance_status(self) -> APIStatus:
        """Check Yahoo Finance API status"""
        try:
            start_time = time.time()
            
            # Test with a simple ticker query
            ticker = yf.Ticker("AAPL")
            info = ticker.info
            
            response_time = (time.time() - start_time) * 1000
            
            if info and 'symbol' in info:
                status = 'active'
                error_msg = None
            else:
                status = 'limited'
                error_msg = 'Limited data returned'
            
            return APIStatus(
                name='Yahoo Finance',
                status=status,
                last_check=datetime.now(),
                response_time_ms=response_time,
                rate_limit_remaining=None,  # Yahoo Finance doesn't expose limits
                rate_limit_total=None,
                rate_limit_reset=None,
                error_message=error_msg,
                success_rate=self._calculate_success_rate('yahoo_finance')
            )
            
        except Exception as e:
            return APIStatus(
                name='Yahoo Finance',
                status='down',
                last_check=datetime.now(),
                response_time_ms=None,
                rate_limit_remaining=None,
                rate_limit_total=None,
                rate_limit_reset=None,
                error_message=str(e),
                success_rate=self._calculate_success_rate('yahoo_finance')
            )
    
    def _check_reddit_status(self) -> APIStatus:
        """Check Reddit API status"""
        try:
            config = self.config.get('reddit', {})
            
            if not all(key in config for key in ['client_id', 'client_secret']):
                raise ValueError("Reddit API credentials not configured")
            
            start_time = time.time()
            
            reddit = praw.Reddit(
                client_id=config['client_id'],
                client_secret=config['client_secret'],
                user_agent=config.get('user_agent', 'StockAnalyzer/1.0')
            )
            
            # Test API connection
            subreddit = reddit.subreddit('test')
            _ = subreddit.display_name
            
            response_time = (time.time() - start_time) * 1000
            
            # Get rate limit info if available
            rate_limit_remaining = getattr(reddit.auth, 'limits', {}).get('remaining')
            rate_limit_total = getattr(reddit.auth, 'limits', {}).get('used')
            
            return APIStatus(
                name='Reddit API',
                status='active',
                last_check=datetime.now(),
                response_time_ms=response_time,
                rate_limit_remaining=rate_limit_remaining,
                rate_limit_total=rate_limit_total,
                rate_limit_reset=None,
                error_message=None,
                success_rate=self._calculate_success_rate('reddit')
            )
            
        except Exception as e:
            return APIStatus(
                name='Reddit API',
                status='down',
                last_check=datetime.now(),
                response_time_ms=None,
                rate_limit_remaining=None,
                rate_limit_total=None,
                rate_limit_reset=None,
                error_message=str(e),
                success_rate=self._calculate_success_rate('reddit')
            )
    
    def _check_database_status(self) -> APIStatus:
        """Check database connection status"""
        try:
            start_time = time.time()
            
            if not self.db.connect():
                raise Exception("Database connection failed")
            
            # Test with a simple query
            cursor = self.db.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM stocks")
            count = cursor.fetchone()[0]
            
            response_time = (time.time() - start_time) * 1000
            
            return APIStatus(
                name='Database',
                status='active',
                last_check=datetime.now(),
                response_time_ms=response_time,
                rate_limit_remaining=None,
                rate_limit_total=None,
                rate_limit_reset=None,
                error_message=None,
                success_rate=self._calculate_success_rate('database')
            )
            
        except Exception as e:
            return APIStatus(
                name='Database',
                status='down',
                last_check=datetime.now(),
                response_time_ms=None,
                rate_limit_remaining=None,
                rate_limit_total=None,
                rate_limit_reset=None,
                error_message=str(e),
                success_rate=self._calculate_success_rate('database')
            )
        finally:
            if hasattr(self.db, 'connection') and self.db.connection:
                self.db.close()
    
    def get_data_freshness_report(self) -> List[DataFreshness]:
        """Get comprehensive data freshness report"""
        freshness_report = []
        
        if not self.db.connect():
            self.logger.error("Cannot connect to database for freshness report")
            return freshness_report
        
        try:
            cursor = self.db.connection.cursor()
            
            # Check each data type
            for data_type, threshold_hours in self.freshness_thresholds.items():
                table_name = data_type
                
                # Get last update time and record count
                cursor.execute(f"""
                    SELECT 
                        MAX(updated_at) as last_update,
                        COUNT(*) as record_count
                    FROM {table_name}
                """)
                
                result = cursor.fetchone()
                last_update_str = result[0] if result[0] else None
                record_count = result[1] if result[1] else 0
                
                # Parse last update time
                last_update = None
                staleness_hours = float('inf')
                
                if last_update_str:
                    try:
                        last_update = datetime.fromisoformat(last_update_str)
                        staleness_hours = (datetime.now() - last_update).total_seconds() / 3600
                    except ValueError:
                        self.logger.warning(f"Invalid timestamp in {table_name}: {last_update_str}")
                
                is_stale = staleness_hours > threshold_hours
                
                freshness_report.append(DataFreshness(
                    data_type=data_type.replace('_', ' ').title(),
                    table_name=table_name,
                    last_update=last_update,
                    record_count=record_count,
                    staleness_hours=staleness_hours,
                    is_stale=is_stale,
                    threshold_hours=threshold_hours
                ))
        
        except Exception as e:
            self.logger.error(f"Error generating freshness report: {e}")
        
        finally:
            self.db.close()
        
        return freshness_report
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        stats = {
            'total_size_mb': 0,
            'table_stats': [],
            'connection_count': 0,
            'query_performance': {}
        }
        
        if not self.db.connect():
            return stats
        
        try:
            cursor = self.db.connection.cursor()
            
            # Get database file size
            import os
            if os.path.exists(self.db.db_path):
                stats['total_size_mb'] = os.path.getsize(self.db.db_path) / (1024 * 1024)
            
            # Get table statistics
            tables = [
                'stocks', 'price_data', 'fundamental_data', 
                'news_articles', 'reddit_posts', 'daily_sentiment'
            ]
            
            for table in tables:
                try:
                    # Get row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    row_count = cursor.fetchone()[0]
                    
                    # Get last modified (approximate)
                    cursor.execute(f"""
                        SELECT MAX(updated_at) FROM {table}
                        WHERE updated_at IS NOT NULL
                    """)
                    last_modified = cursor.fetchone()[0]
                    
                    stats['table_stats'].append({
                        'table_name': table,
                        'row_count': row_count,
                        'last_modified': last_modified
                    })
                    
                except Exception as e:
                    self.logger.warning(f"Error getting stats for table {table}: {e}")
                    stats['table_stats'].append({
                        'table_name': table,
                        'row_count': 0,
                        'last_modified': None
                    })
        
        except Exception as e:
            self.logger.error(f"Error getting database statistics: {e}")
        
        finally:
            self.db.close()
        
        return stats
    
    def _is_reddit_configured(self) -> bool:
        """Check if Reddit API is properly configured"""
        config = self.config.get('reddit', {})
        return all(key in config for key in ['client_id', 'client_secret'])
    
    def _calculate_success_rate(self, api_name: str) -> float:
        """Calculate 24-hour success rate for an API"""
        # For now, return a placeholder. In production, this would
        # query a monitoring log table for historical success/failure rates
        return 0.95  # 95% success rate placeholder
    
    def log_api_call(self, api_name: str, success: bool, response_time_ms: float, error_msg: Optional[str] = None):
        """Log API call for monitoring and success rate calculation"""
        # This would insert into a monitoring log table for tracking
        # For now, just log to application logger
        status = "SUCCESS" if success else "FAILED"
        log_msg = f"API Call - {api_name}: {status} ({response_time_ms:.1f}ms)"
        
        if error_msg:
            log_msg += f" - Error: {error_msg}"
        
        if success:
            self.logger.info(log_msg)
        else:
            self.logger.error(log_msg)
    
    def get_api_health_summary(self) -> Dict[str, str]:
        """Get simplified health summary for dashboard display"""
        statuses = self.get_all_api_status()
        
        summary = {}
        for api_name, status in statuses.items():
            if status.status == 'active':
                summary[api_name] = '🟢 Active'
            elif status.status == 'limited':
                summary[api_name] = '🟡 Limited'
            elif status.status == 'down':
                summary[api_name] = '🔴 Down'
            elif status.status == 'not_configured':
                summary[api_name] = '⚪ Not Configured'
            else:
                summary[api_name] = '❓ Unknown'
        
        return summary