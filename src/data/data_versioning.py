#!/usr/bin/env python3
"""
Data Versioning and Staleness Management System
Provides data freshness indicators and version selection for analysis components
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DataFreshnessLevel(Enum):
    """Data freshness classification"""
    FRESH = "fresh"           # < 1 day
    RECENT = "recent"         # 1-7 days  
    STALE = "stale"          # 7-30 days
    VERY_STALE = "very_stale" # 30+ days
    MISSING = "missing"       # No data


@dataclass
class DataVersionInfo:
    """Information about data version and freshness"""
    data_type: str              # 'fundamentals', 'price', 'news', 'sentiment'
    symbol: str
    data_date: Optional[datetime]
    collection_date: Optional[datetime]
    freshness_level: DataFreshnessLevel
    age_days: Optional[float]
    version_id: Optional[str]
    quality_score: float
    is_approved: bool
    staleness_warnings: List[str]


@dataclass
class VersionedData:
    """Container for data with version and freshness metadata"""
    data: Dict[str, Any]
    version_info: DataVersionInfo
    staleness_impact: float  # 0.0-1.0 multiplier for scoring


class DataVersionManager:
    """Manages data versions and staleness indicators for analysis components"""
    
    def __init__(self, db_manager, config_manager=None):
        self.db_manager = db_manager
        self.config_manager = config_manager
        
        # Load freshness thresholds from config or use defaults
        if config_manager and hasattr(config_manager, 'system_config') and config_manager.system_config:
            staleness_limits = getattr(config_manager.methodology_config, 'staleness_limits', {}) if config_manager.methodology_config else {}
            self.freshness_thresholds = self._build_freshness_thresholds(staleness_limits)
        else:
            self.freshness_thresholds = self._get_default_freshness_thresholds()
        
        # Staleness impact on scoring (multiplier)
        self.staleness_multipliers = {
            DataFreshnessLevel.FRESH: 1.0,
            DataFreshnessLevel.RECENT: 0.95,
            DataFreshnessLevel.STALE: 0.85,
            DataFreshnessLevel.VERY_STALE: 0.70,
            DataFreshnessLevel.MISSING: 0.0
        }
    
    def get_versioned_fundamentals(self, symbol: str, max_age_days: Optional[int] = None) -> Optional[VersionedData]:
        """Get fundamental data with version and staleness information"""
        try:
            if not self.db_manager.connect():
                return None
                
            cursor = self.db_manager.connection.cursor()
            
            # Get latest fundamental data with dates
            cursor.execute('''
                SELECT *
                FROM fundamental_data 
                WHERE symbol = ? 
                ORDER BY reporting_date DESC 
                LIMIT 1
            ''', (symbol,))
            
            row = cursor.fetchone()
            if not row:
                return self._create_missing_data_version(symbol, 'fundamentals')
            
            data = dict(row)
            
            # FIXED: Use actual schema columns - reporting_date and created_at
            reporting_date = None
            collection_date = None
            
            # Parse reporting_date (when the data is FOR)
            if data.get('reporting_date'):
                reporting_date = self._parse_date_safely(data['reporting_date'])
            
            # Parse created_at as collection_date (when the data was COLLECTED)
            if data.get('created_at'):
                collection_date = self._parse_date_safely(data['created_at'])
            elif reporting_date:
                collection_date = reporting_date  # Fallback to reporting date
            
            version_info = self._calculate_data_freshness(
                data_type='fundamentals',
                symbol=symbol,
                data_date=reporting_date,
                collection_date=collection_date
            )
            
            # Check if data meets age requirements
            if max_age_days and version_info.age_days and version_info.age_days > max_age_days:
                logger.warning(f"Fundamental data for {symbol} is {version_info.age_days:.1f} days old (limit: {max_age_days})")
                return None
            
            # Calculate staleness impact
            staleness_impact = self.staleness_multipliers[version_info.freshness_level]
            
            return VersionedData(
                data=data,
                version_info=version_info,
                staleness_impact=staleness_impact
            )
            
        except Exception as e:
            logger.error(f"Error getting versioned fundamentals for {symbol}: {e}")
            return None
        # Note: Don't close the connection here as it may be reused by caller
    
    def get_versioned_price_data(self, symbol: str, max_age_days: Optional[int] = None) -> Optional[VersionedData]:
        """Get latest price data with version information"""
        try:
            if not self.db_manager.connect():
                return None
                
            cursor = self.db_manager.connection.cursor()
            
            # Get latest price data
            cursor.execute('''
                SELECT *, date as data_date
                FROM price_data 
                WHERE symbol = ? 
                ORDER BY date DESC 
                LIMIT 1
            ''', (symbol,))
            
            row = cursor.fetchone()
            if not row:
                return self._create_missing_data_version(symbol, 'price')
            
            data = dict(row)
            
            # Price data uses the trading date as both data and collection date
            data_date = self._parse_date_safely(data.get('data_date'))
            
            version_info = self._calculate_data_freshness(
                data_type='price',
                symbol=symbol,
                data_date=data_date,
                collection_date=data_date  # Assuming collected same day
            )
            
            # Check age requirements
            if max_age_days and version_info.age_days and version_info.age_days > max_age_days:
                logger.warning(f"Price data for {symbol} is {version_info.age_days:.1f} days old (limit: {max_age_days})")
                return None
            
            staleness_impact = self.staleness_multipliers[version_info.freshness_level]
            
            return VersionedData(
                data=data,
                version_info=version_info,
                staleness_impact=staleness_impact
            )
            
        except Exception as e:
            logger.error(f"Error getting versioned price data for {symbol}: {e}")
            return None
        # Note: Don't close the connection here as it may be reused by caller
    
    def get_versioned_news_data(self, symbol: str, days_back: int = 30, max_age_days: Optional[int] = None) -> Optional[VersionedData]:
        """Get recent news data with version information"""
        try:
            if not self.db_manager.connect():
                return None
                
            cursor = self.db_manager.connection.cursor()
            
            # Get recent news articles
            cutoff_date = datetime.now() - timedelta(days=days_back)
            cursor.execute('''
                SELECT *, publish_date as data_date
                FROM news_articles 
                WHERE symbol = ? AND publish_date >= ?
                ORDER BY publish_date DESC
            ''', (symbol, cutoff_date.isoformat()))
            
            rows = cursor.fetchall()
            if not rows:
                return self._create_missing_data_version(symbol, 'news')
            
            # Convert to list of dicts and find latest
            articles = [dict(row) for row in rows]
            latest_article = articles[0]
            
            data_date = self._parse_date_safely(latest_article.get('data_date'))
            
            version_info = self._calculate_data_freshness(
                data_type='news',
                symbol=symbol,
                data_date=data_date,
                collection_date=data_date  # Assuming collected when published
            )
            
            # Check age requirements
            if max_age_days and version_info.age_days and version_info.age_days > max_age_days:
                logger.warning(f"News data for {symbol} is {version_info.age_days:.1f} days old (limit: {max_age_days})")
                return None
            
            staleness_impact = self.staleness_multipliers[version_info.freshness_level]
            
            # Return aggregated news data
            data = {
                'article_count': len(articles),
                'latest_date': latest_article['data_date'],
                'articles': articles,
                'avg_sentiment': sum(a.get('sentiment_score', 0) for a in articles) / len(articles) if articles else 0
            }
            
            return VersionedData(
                data=data,
                version_info=version_info,
                staleness_impact=staleness_impact
            )
            
        except Exception as e:
            logger.error(f"Error getting versioned news data for {symbol}: {e}")
            return None
        # Note: Don't close the connection here as it may be reused by caller
    
    def get_versioned_sentiment_data(self, symbol: str, max_age_days: Optional[int] = None) -> Optional[VersionedData]:
        """Get latest sentiment data with version information"""
        try:
            if not self.db_manager.connect():
                return None
                
            cursor = self.db_manager.connection.cursor()
            
            # Get latest sentiment data
            cursor.execute('''
                SELECT *, date as data_date
                FROM daily_sentiment 
                WHERE symbol = ? 
                ORDER BY date DESC 
                LIMIT 1
            ''', (symbol,))
            
            row = cursor.fetchone()
            if not row:
                return self._create_missing_data_version(symbol, 'sentiment')
            
            data = dict(row)
            
            data_date = self._parse_date_safely(data.get('data_date'))
            
            version_info = self._calculate_data_freshness(
                data_type='sentiment',
                symbol=symbol,
                data_date=data_date,
                collection_date=data_date
            )
            
            # Check age requirements
            if max_age_days and version_info.age_days and version_info.age_days > max_age_days:
                logger.warning(f"Sentiment data for {symbol} is {version_info.age_days:.1f} days old (limit: {max_age_days})")
                return None
            
            staleness_impact = self.staleness_multipliers[version_info.freshness_level]
            
            return VersionedData(
                data=data,
                version_info=version_info,
                staleness_impact=staleness_impact
            )
            
        except Exception as e:
            logger.error(f"Error getting versioned sentiment data for {symbol}: {e}")
            return None
        # Note: Don't close the connection here as it may be reused by caller
    
    def _calculate_data_freshness(self, data_type: str, symbol: str, 
                                 data_date: Optional[datetime], 
                                 collection_date: Optional[datetime]) -> DataVersionInfo:
        """Calculate data freshness level and generate warnings"""
        
        now = datetime.now()
        staleness_warnings = []
        
        # Use the more recent of data_date or collection_date for age calculation
        reference_date = max(filter(None, [data_date, collection_date]), default=None)
        
        if not reference_date:
            return DataVersionInfo(
                data_type=data_type,
                symbol=symbol,
                data_date=data_date,
                collection_date=collection_date,
                freshness_level=DataFreshnessLevel.MISSING,
                age_days=None,
                version_id=None,
                quality_score=0.0,
                is_approved=False,
                staleness_warnings=["No valid dates found for data"]
            )
        
        # Calculate age
        age_timedelta = now - reference_date
        age_days = age_timedelta.total_seconds() / 86400  # Convert to days
        
        # Determine freshness level
        thresholds = self.freshness_thresholds.get(data_type, self.freshness_thresholds['fundamentals'])
        
        if age_days <= thresholds['fresh']:
            freshness_level = DataFreshnessLevel.FRESH
        elif age_days <= thresholds['recent']:
            freshness_level = DataFreshnessLevel.RECENT
        elif age_days <= thresholds['stale']:
            freshness_level = DataFreshnessLevel.STALE
            staleness_warnings.append(f"{data_type.title()} data is {age_days:.1f} days old")
        else:
            freshness_level = DataFreshnessLevel.VERY_STALE
            staleness_warnings.append(f"{data_type.title()} data is very stale ({age_days:.1f} days old)")
        
        # Generate quality score based on freshness
        if freshness_level == DataFreshnessLevel.FRESH:
            quality_score = 1.0
        elif freshness_level == DataFreshnessLevel.RECENT:
            quality_score = 0.95
        elif freshness_level == DataFreshnessLevel.STALE:
            quality_score = 0.80
        else:
            quality_score = 0.60
        
        # Create version ID
        version_id = f"{symbol}_{data_type}_{reference_date.strftime('%Y%m%d_%H%M%S')}"
        
        return DataVersionInfo(
            data_type=data_type,
            symbol=symbol,
            data_date=data_date,
            collection_date=collection_date,
            freshness_level=freshness_level,
            age_days=age_days,
            version_id=version_id,
            quality_score=quality_score,
            is_approved=True,  # For now, assume all retrieved data is approved
            staleness_warnings=staleness_warnings
        )
    
    def _create_missing_data_version(self, symbol: str, data_type: str) -> VersionedData:
        """Create a version info object for missing data"""
        version_info = DataVersionInfo(
            data_type=data_type,
            symbol=symbol,
            data_date=None,
            collection_date=None,
            freshness_level=DataFreshnessLevel.MISSING,
            age_days=None,
            version_id=None,
            quality_score=0.0,
            is_approved=False,
            staleness_warnings=[f"No {data_type} data available for {symbol}"]
        )
        
        return VersionedData(
            data={},
            version_info=version_info,
            staleness_impact=0.0
        )
    
    def get_data_freshness_summary(self, symbol: str) -> Dict[str, DataVersionInfo]:
        """Get freshness summary for all data types for a symbol"""
        summary = {}
        
        # Check each data type
        for data_type in ['fundamentals', 'price', 'news', 'sentiment']:
            try:
                if data_type == 'fundamentals':
                    versioned_data = self.get_versioned_fundamentals(symbol)
                elif data_type == 'price':
                    versioned_data = self.get_versioned_price_data(symbol)
                elif data_type == 'news':
                    versioned_data = self.get_versioned_news_data(symbol)
                elif data_type == 'sentiment':
                    versioned_data = self.get_versioned_sentiment_data(symbol)
                
                if versioned_data:
                    summary[data_type] = versioned_data.version_info
                else:
                    summary[data_type] = self._create_missing_data_version(symbol, data_type).version_info
                    
            except Exception as e:
                logger.error(f"Error getting {data_type} freshness for {symbol}: {e}")
                summary[data_type] = self._create_missing_data_version(symbol, data_type).version_info
        
        return summary
    
    def generate_staleness_report(self, symbols: List[str]) -> Dict[str, Any]:
        """Generate comprehensive staleness report for multiple symbols"""
        report = {
            'report_date': datetime.now().isoformat(),
            'symbols_analyzed': len(symbols),
            'freshness_summary': {},
            'stale_data_warnings': [],
            'recommendations': []
        }
        
        freshness_counts = {level.value: 0 for level in DataFreshnessLevel}
        
        for symbol in symbols:
            summary = self.get_data_freshness_summary(symbol)
            report['freshness_summary'][symbol] = summary
            
            # Count freshness levels
            for data_type, version_info in summary.items():
                freshness_counts[version_info.freshness_level.value] += 1
                
                # Collect warnings
                if version_info.staleness_warnings:
                    report['stale_data_warnings'].extend([
                        f"{symbol}: {warning}" for warning in version_info.staleness_warnings
                    ])
        
        # Generate recommendations
        total_data_points = len(symbols) * 4  # 4 data types per symbol
        stale_ratio = (freshness_counts['stale'] + freshness_counts['very_stale']) / total_data_points
        
        if stale_ratio > 0.3:
            report['recommendations'].append("High proportion of stale data detected - consider refreshing data collection")
        
        missing_ratio = freshness_counts['missing'] / total_data_points
        if missing_ratio > 0.2:
            report['recommendations'].append("Significant missing data detected - review data collection coverage")
        
        report['freshness_distribution'] = freshness_counts
        
        return report
    
    def _get_default_freshness_thresholds(self) -> Dict[str, Dict[str, int]]:
        """Get default freshness thresholds"""
        return {
            'fundamentals': {
                'fresh': 1,
                'recent': 30,     # Quarterly reports
                'stale': 120,     # ~4 months
            },
            'price': {
                'fresh': 1,
                'recent': 3,      # Weekend gap
                'stale': 7,       # Week old
            },
            'news': {
                'fresh': 1,
                'recent': 7,      # Week old news
                'stale': 30,      # Month old
            },
            'sentiment': {
                'fresh': 1,
                'recent': 7,
                'stale': 14,      # Two weeks
            }
        }
    
    def _build_freshness_thresholds(self, staleness_limits: Dict[str, int]) -> Dict[str, Dict[str, int]]:
        """Build freshness thresholds from configuration staleness limits"""
        defaults = self._get_default_freshness_thresholds()
        
        # Map config keys to data types
        config_mapping = {
            'fundamentals_days': 'fundamentals',
            'price_days': 'price',
            'news_days': 'news',
            'sentiment_days': 'sentiment'
        }
        
        for config_key, data_type in config_mapping.items():
            if config_key in staleness_limits:
                max_days = staleness_limits[config_key]
                # Set thresholds as fractions of max days
                defaults[data_type] = {
                    'fresh': max(1, max_days // 10),      # 10% of max
                    'recent': max(2, max_days // 3),       # 33% of max  
                    'stale': max_days                      # Max configured days
                }
        
        return defaults
    
    def _parse_date_safely(self, date_input) -> Optional[datetime]:
        """
        Centralized date parsing to handle inconsistent date formats
        
        Args:
            date_input: String, datetime, or date object
            
        Returns:
            datetime object or None if parsing fails
        """
        if date_input is None:
            return None
        
        # If already a datetime, return it
        if isinstance(date_input, datetime):
            return date_input
        
        # If it's a date object, convert to datetime
        if hasattr(date_input, 'year') and hasattr(date_input, 'month'):
            try:
                return datetime.combine(date_input, datetime.min.time())
            except:
                pass
        
        # If it's a string, try multiple formats
        if isinstance(date_input, str):
            date_formats = [
                '%Y-%m-%d %H:%M:%S',      # Full datetime
                '%Y-%m-%dT%H:%M:%S',      # ISO format without timezone
                '%Y-%m-%dT%H:%M:%SZ',     # ISO format with Z
                '%Y-%m-%d',               # Date only
                '%Y/%m/%d',               # Alternative date format
                '%m/%d/%Y',               # US date format
                '%d/%m/%Y',               # European date format
            ]
            
            # Try ISO format first (most reliable)
            try:
                # Handle timezone info
                if 'T' in date_input:
                    clean_date = date_input.replace('Z', '+00:00') if date_input.endswith('Z') else date_input
                    return datetime.fromisoformat(clean_date.split('+')[0].split('Z')[0])
            except:
                pass
            
            # Try other formats
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_input, fmt)
                except:
                    continue
        
        # If all parsing fails, log warning and return None
        logger.warning(f"Could not parse date: {date_input} (type: {type(date_input)})")
        return None