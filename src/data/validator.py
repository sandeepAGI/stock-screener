#!/usr/bin/env python3
"""
Data Validation and Integrity Checking Module
Validates data quality, detects inconsistencies, and provides repair capabilities
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging
import numpy as np

from .database import DatabaseManager
from ..utils.helpers import load_config

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of a data validation check"""
    check_name: str
    table_name: str
    status: str  # 'pass', 'warning', 'fail'
    affected_records: int
    description: str
    details: List[Dict[str, Any]]
    suggested_fix: Optional[str] = None

@dataclass
class DataIntegrityReport:
    """Comprehensive data integrity report"""
    report_date: datetime
    total_checks: int
    passed_checks: int
    warning_checks: int
    failed_checks: int
    overall_score: float
    validation_results: List[ValidationResult]
    recommendations: List[str]

class DataValidator:
    """Comprehensive data validation and integrity checking"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = load_config(config_path)
        self.db = DatabaseManager()
        self.logger = logging.getLogger(__name__)
        
        # Validation thresholds
        self.thresholds = {
            'min_fundamentals_completeness': 0.8,  # 80% of fields should be present
            'max_price_gap_days': 7,               # No more than 7 days without price data
            'min_news_articles_per_month': 1,      # At least 1 news article per month
            'max_sentiment_score': 1.0,            # Sentiment scores should be <= 1.0
            'min_sentiment_score': -1.0,           # Sentiment scores should be >= -1.0
            'max_pe_ratio': 1000,                  # PE ratios above 1000 are suspicious
            'min_market_cap': 1000000,             # Market cap should be at least $1M
            'max_debt_to_equity': 10,              # Debt/equity ratio above 10 is suspicious
        }
    
    def run_complete_validation(self) -> DataIntegrityReport:
        """Run comprehensive validation across all data"""
        self.logger.info("Starting comprehensive data validation")
        
        if not self.db.connect():
            raise RuntimeError("Cannot connect to database for validation")
        
        validation_results = []
        
        try:
            # Stock table validations
            validation_results.extend(self._validate_stocks_table())
            
            # Price data validations
            validation_results.extend(self._validate_price_data())
            
            # Fundamental data validations
            validation_results.extend(self._validate_fundamental_data())
            
            # News data validations
            validation_results.extend(self._validate_news_data())
            
            # Sentiment data validations
            validation_results.extend(self._validate_sentiment_data())
            
            # Cross-table relationship validations
            validation_results.extend(self._validate_data_relationships())
            
            # Generate report
            report = self._generate_integrity_report(validation_results)
            
            self.logger.info(f"Validation complete: {report.passed_checks}/{report.total_checks} checks passed")
            return report
            
        finally:
            self.db.close()
    
    def _validate_stocks_table(self) -> List[ValidationResult]:
        """Validate the stocks table"""
        results = []
        cursor = self.db.connection.cursor()
        
        # Check for duplicate symbols
        cursor.execute("""
            SELECT symbol, COUNT(*) as count
            FROM stocks
            GROUP BY symbol
            HAVING COUNT(*) > 1
        """)
        
        duplicates = cursor.fetchall()
        if duplicates:
            results.append(ValidationResult(
                check_name="Duplicate Symbols",
                table_name="stocks",
                status="fail",
                affected_records=len(duplicates),
                description=f"Found {len(duplicates)} duplicate symbols in stocks table",
                details=[{"symbol": dup[0], "count": dup[1]} for dup in duplicates],
                suggested_fix="Remove duplicate entries, keeping the most recent"
            ))
        else:
            results.append(ValidationResult(
                check_name="Duplicate Symbols",
                table_name="stocks",
                status="pass",
                affected_records=0,
                description="No duplicate symbols found",
                details=[]
            ))
        
        # Check for missing required fields
        cursor.execute("""
            SELECT symbol, company_name, sector
            FROM stocks
            WHERE company_name IS NULL OR company_name = '' 
               OR sector IS NULL OR sector = ''
        """)
        
        missing_fields = cursor.fetchall()
        if missing_fields:
            results.append(ValidationResult(
                check_name="Missing Required Fields",
                table_name="stocks",
                status="warning",
                affected_records=len(missing_fields),
                description=f"Found {len(missing_fields)} stocks with missing company name or sector",
                details=[{"symbol": row[0], "company_name": row[1], "sector": row[2]} for row in missing_fields],
                suggested_fix="Update missing company names and sectors from external data sources"
            ))
        else:
            results.append(ValidationResult(
                check_name="Missing Required Fields",
                table_name="stocks",
                status="pass",
                affected_records=0,
                description="All stocks have required fields",
                details=[]
            ))
        
        return results
    
    def _validate_price_data(self) -> List[ValidationResult]:
        """Validate price data table"""
        results = []
        cursor = self.db.connection.cursor()
        
        # Check for data gaps (missing price data for extended periods)
        cursor.execute("""
            WITH price_gaps AS (
                SELECT 
                    symbol,
                    date,
                    LAG(date) OVER (PARTITION BY symbol ORDER BY date) as prev_date,
                    julianday(date) - julianday(LAG(date) OVER (PARTITION BY symbol ORDER BY date)) as gap_days
                FROM price_data
                ORDER BY symbol, date
            )
            SELECT symbol, date, prev_date, gap_days
            FROM price_gaps
            WHERE gap_days > ?
        """, (self.thresholds['max_price_gap_days'],))
        
        gaps = cursor.fetchall()
        if gaps:
            results.append(ValidationResult(
                check_name="Price Data Gaps",
                table_name="price_data",
                status="warning",
                affected_records=len(gaps),
                description=f"Found {len(gaps)} price data gaps exceeding {self.thresholds['max_price_gap_days']} days",
                details=[{"symbol": row[0], "gap_start": row[2], "gap_end": row[1], "gap_days": row[3]} for row in gaps],
                suggested_fix="Fill gaps by collecting missing price data"
            ))
        else:
            results.append(ValidationResult(
                check_name="Price Data Gaps",
                table_name="price_data",
                status="pass",
                affected_records=0,
                description="No significant price data gaps found",
                details=[]
            ))
        
        # Check for invalid price values
        cursor.execute("""
            SELECT symbol, date, open, high, low, close, volume
            FROM price_data
            WHERE open <= 0 OR high <= 0 OR low <= 0 OR close <= 0
               OR high < low OR high < open OR high < close
               OR volume < 0
        """)
        
        invalid_prices = cursor.fetchall()
        if invalid_prices:
            results.append(ValidationResult(
                check_name="Invalid Price Values",
                table_name="price_data",
                status="fail",
                affected_records=len(invalid_prices),
                description=f"Found {len(invalid_prices)} records with invalid price values",
                details=[{"symbol": row[0], "date": row[1], "issue": "Invalid OHLC or volume"} for row in invalid_prices],
                suggested_fix="Remove or correct invalid price records"
            ))
        else:
            results.append(ValidationResult(
                check_name="Invalid Price Values",
                table_name="price_data",
                status="pass",
                affected_records=0,
                description="All price values are valid",
                details=[]
            ))
        
        return results
    
    def _validate_fundamental_data(self) -> List[ValidationResult]:
        """Validate fundamental data table"""
        results = []
        cursor = self.db.connection.cursor()
        
        # Check for extreme PE ratios
        cursor.execute("""
            SELECT symbol, pe_ratio, reporting_date
            FROM fundamental_data
            WHERE pe_ratio > ? OR pe_ratio < 0
        """, (self.thresholds['max_pe_ratio'],))
        
        extreme_pe = cursor.fetchall()
        if extreme_pe:
            results.append(ValidationResult(
                check_name="Extreme PE Ratios",
                table_name="fundamental_data",
                status="warning",
                affected_records=len(extreme_pe),
                description=f"Found {len(extreme_pe)} stocks with extreme PE ratios",
                details=[{"symbol": row[0], "pe_ratio": row[1], "date": row[2]} for row in extreme_pe],
                suggested_fix="Review and validate extreme PE ratios"
            ))
        else:
            results.append(ValidationResult(
                check_name="Extreme PE Ratios",
                table_name="fundamental_data",
                status="pass",
                affected_records=0,
                description="All PE ratios are within reasonable bounds",
                details=[]
            ))
        
        # Check for very low market caps
        cursor.execute("""
            SELECT symbol, market_cap, reporting_date
            FROM fundamental_data
            WHERE market_cap < ? AND market_cap > 0
        """, (self.thresholds['min_market_cap'],))
        
        low_mcap = cursor.fetchall()
        if low_mcap:
            results.append(ValidationResult(
                check_name="Low Market Cap",
                table_name="fundamental_data",
                status="warning",
                affected_records=len(low_mcap),
                description=f"Found {len(low_mcap)} stocks with very low market cap",
                details=[{"symbol": row[0], "market_cap": row[1], "date": row[2]} for row in low_mcap],
                suggested_fix="Verify market cap calculations and consider removing micro-cap stocks"
            ))
        else:
            results.append(ValidationResult(
                check_name="Low Market Cap",
                table_name="fundamental_data",
                status="pass",
                affected_records=0,
                description="All market caps are above minimum threshold",
                details=[]
            ))
        
        # Check for extreme debt-to-equity ratios
        cursor.execute("""
            SELECT symbol, debt_to_equity, reporting_date
            FROM fundamental_data
            WHERE debt_to_equity > ? OR debt_to_equity < 0
        """, (self.thresholds['max_debt_to_equity'],))
        
        extreme_de = cursor.fetchall()
        if extreme_de:
            results.append(ValidationResult(
                check_name="Extreme Debt-to-Equity",
                table_name="fundamental_data",
                status="warning",
                affected_records=len(extreme_de),
                description=f"Found {len(extreme_de)} stocks with extreme debt-to-equity ratios",
                details=[{"symbol": row[0], "debt_to_equity": row[1], "date": row[2]} for row in extreme_de],
                suggested_fix="Review high debt-to-equity ratios for accuracy"
            ))
        else:
            results.append(ValidationResult(
                check_name="Extreme Debt-to-Equity",
                table_name="fundamental_data",
                status="pass",
                affected_records=0,
                description="All debt-to-equity ratios are reasonable",
                details=[]
            ))
        
        return results
    
    def _validate_news_data(self) -> List[ValidationResult]:
        """Validate news data table"""
        results = []
        cursor = self.db.connection.cursor()
        
        # Check for duplicate news articles
        cursor.execute("""
            SELECT url, COUNT(*) as count
            FROM news_articles
            WHERE url IS NOT NULL AND url != ''
            GROUP BY url
            HAVING COUNT(*) > 1
        """)
        
        duplicate_news = cursor.fetchall()
        if duplicate_news:
            results.append(ValidationResult(
                check_name="Duplicate News Articles",
                table_name="news_articles",
                status="warning",
                affected_records=len(duplicate_news),
                description=f"Found {len(duplicate_news)} duplicate news articles",
                details=[{"url": row[0], "count": row[1]} for row in duplicate_news],
                suggested_fix="Remove duplicate news articles"
            ))
        else:
            results.append(ValidationResult(
                check_name="Duplicate News Articles",
                table_name="news_articles",
                status="pass",
                affected_records=0,
                description="No duplicate news articles found",
                details=[]
            ))
        
        # Check for missing content
        cursor.execute("""
            SELECT symbol, title, publish_date
            FROM news_articles
            WHERE (title IS NULL OR title = '') 
               OR (content IS NULL OR content = '')
               OR (summary IS NULL OR summary = '')
        """)
        
        missing_content = cursor.fetchall()
        if missing_content:
            results.append(ValidationResult(
                check_name="Missing News Content",
                table_name="news_articles",
                status="warning",
                affected_records=len(missing_content),
                description=f"Found {len(missing_content)} news articles with missing content",
                details=[{"symbol": row[0], "title": row[1], "date": row[2]} for row in missing_content],
                suggested_fix="Re-fetch or remove articles with missing content"
            ))
        else:
            results.append(ValidationResult(
                check_name="Missing News Content",
                table_name="news_articles",
                status="pass",
                affected_records=0,
                description="All news articles have complete content",
                details=[]
            ))
        
        return results
    
    def _validate_sentiment_data(self) -> List[ValidationResult]:
        """Validate sentiment data"""
        results = []
        cursor = self.db.connection.cursor()
        
        # Check for sentiment scores outside valid range
        cursor.execute("""
            SELECT symbol, date, news_sentiment, reddit_sentiment, combined_sentiment
            FROM daily_sentiment
            WHERE news_sentiment < ? OR news_sentiment > ?
               OR reddit_sentiment < ? OR reddit_sentiment > ?
               OR combined_sentiment < ? OR combined_sentiment > ?
        """, (
            self.thresholds['min_sentiment_score'], self.thresholds['max_sentiment_score'],
            self.thresholds['min_sentiment_score'], self.thresholds['max_sentiment_score'],
            self.thresholds['min_sentiment_score'], self.thresholds['max_sentiment_score']
        ))
        
        invalid_sentiment = cursor.fetchall()
        if invalid_sentiment:
            results.append(ValidationResult(
                check_name="Invalid Sentiment Scores",
                table_name="daily_sentiment",
                status="fail",
                affected_records=len(invalid_sentiment),
                description=f"Found {len(invalid_sentiment)} sentiment scores outside valid range",
                details=[{"symbol": row[0], "date": row[1], "news": row[2], "reddit": row[3], "combined": row[4]} for row in invalid_sentiment],
                suggested_fix="Recalculate sentiment scores to ensure they're in [-1, 1] range"
            ))
        else:
            results.append(ValidationResult(
                check_name="Invalid Sentiment Scores",
                table_name="daily_sentiment",
                status="pass",
                affected_records=0,
                description="All sentiment scores are within valid range",
                details=[]
            ))
        
        return results
    
    def _validate_data_relationships(self) -> List[ValidationResult]:
        """Validate relationships between tables"""
        results = []
        cursor = self.db.connection.cursor()
        
        # Check for orphaned price data (price data without corresponding stock)
        cursor.execute("""
            SELECT DISTINCT pd.symbol
            FROM price_data pd
            LEFT JOIN stocks s ON pd.symbol = s.symbol
            WHERE s.symbol IS NULL
        """)
        
        orphaned_prices = cursor.fetchall()
        if orphaned_prices:
            results.append(ValidationResult(
                check_name="Orphaned Price Data",
                table_name="price_data",
                status="warning",
                affected_records=len(orphaned_prices),
                description=f"Found price data for {len(orphaned_prices)} symbols not in stocks table",
                details=[{"symbol": row[0]} for row in orphaned_prices],
                suggested_fix="Add missing stocks to stocks table or remove orphaned data"
            ))
        else:
            results.append(ValidationResult(
                check_name="Orphaned Price Data",
                table_name="price_data",
                status="pass",
                affected_records=0,
                description="All price data has corresponding stock entries",
                details=[]
            ))
        
        # Check for stocks without any data
        cursor.execute("""
            SELECT s.symbol
            FROM stocks s
            LEFT JOIN price_data pd ON s.symbol = pd.symbol
            LEFT JOIN fundamental_data fd ON s.symbol = fd.symbol
            WHERE pd.symbol IS NULL AND fd.symbol IS NULL
        """)
        
        empty_stocks = cursor.fetchall()
        if empty_stocks:
            results.append(ValidationResult(
                check_name="Stocks Without Data",
                table_name="stocks",
                status="warning",
                affected_records=len(empty_stocks),
                description=f"Found {len(empty_stocks)} stocks with no price or fundamental data",
                details=[{"symbol": row[0]} for row in empty_stocks],
                suggested_fix="Collect data for these stocks or remove them from tracking"
            ))
        else:
            results.append(ValidationResult(
                check_name="Stocks Without Data",
                table_name="stocks",
                status="pass",
                affected_records=0,
                description="All stocks have associated data",
                details=[]
            ))
        
        return results
    
    def _generate_integrity_report(self, validation_results: List[ValidationResult]) -> DataIntegrityReport:
        """Generate comprehensive integrity report"""
        total_checks = len(validation_results)
        passed_checks = sum(1 for r in validation_results if r.status == 'pass')
        warning_checks = sum(1 for r in validation_results if r.status == 'warning')
        failed_checks = sum(1 for r in validation_results if r.status == 'fail')
        
        overall_score = passed_checks / total_checks if total_checks > 0 else 0
        
        # Generate recommendations
        recommendations = []
        
        if failed_checks > 0:
            recommendations.append(f"Address {failed_checks} critical data issues immediately")
        
        if warning_checks > 0:
            recommendations.append(f"Review {warning_checks} data quality warnings")
        
        if overall_score < 0.8:
            recommendations.append("Overall data quality is below 80% - comprehensive data cleanup recommended")
        elif overall_score < 0.9:
            recommendations.append("Data quality is good but could be improved")
        else:
            recommendations.append("Excellent data quality - maintain current standards")
        
        # Add specific recommendations based on results
        for result in validation_results:
            if result.status in ['warning', 'fail'] and result.suggested_fix:
                recommendations.append(f"{result.check_name}: {result.suggested_fix}")
        
        return DataIntegrityReport(
            report_date=datetime.now(),
            total_checks=total_checks,
            passed_checks=passed_checks,
            warning_checks=warning_checks,
            failed_checks=failed_checks,
            overall_score=overall_score,
            validation_results=validation_results,
            recommendations=recommendations[:10]  # Limit to top 10 recommendations
        )
    
    def repair_duplicate_stocks(self) -> Dict[str, int]:
        """Remove duplicate stock entries, keeping the most recent"""
        if not self.db.connect():
            return {"error": "Cannot connect to database"}
        
        try:
            cursor = self.db.connection.cursor()
            
            # Find and remove duplicates
            cursor.execute("""
                DELETE FROM stocks
                WHERE rowid NOT IN (
                    SELECT MIN(rowid)
                    FROM stocks
                    GROUP BY symbol
                )
            """)
            
            removed_count = cursor.rowcount
            self.db.connection.commit()
            
            self.logger.info(f"Removed {removed_count} duplicate stock entries")
            return {"removed_duplicates": removed_count}
            
        except Exception as e:
            self.logger.error(f"Error removing duplicate stocks: {e}")
            return {"error": str(e)}
        finally:
            self.db.close()
    
    def repair_invalid_prices(self) -> Dict[str, int]:
        """Remove price records with invalid values"""
        if not self.db.connect():
            return {"error": "Cannot connect to database"}
        
        try:
            cursor = self.db.connection.cursor()
            
            # Remove invalid price records
            cursor.execute("""
                DELETE FROM price_data
                WHERE open <= 0 OR high <= 0 OR low <= 0 OR close <= 0
                   OR high < low OR high < open OR high < close
                   OR volume < 0
            """)
            
            removed_count = cursor.rowcount
            self.db.connection.commit()
            
            self.logger.info(f"Removed {removed_count} invalid price records")
            return {"removed_invalid_prices": removed_count}
            
        except Exception as e:
            self.logger.error(f"Error removing invalid prices: {e}")
            return {"error": str(e)}
        finally:
            self.db.close()
    
    def get_data_completeness_report(self) -> Dict[str, Any]:
        """Generate data completeness report across all tables"""
        if not self.db.connect():
            return {"error": "Cannot connect to database"}
        
        try:
            cursor = self.db.connection.cursor()
            
            # Get stock count
            cursor.execute("SELECT COUNT(*) FROM stocks")
            total_stocks = cursor.fetchone()[0]
            
            if total_stocks == 0:
                return {"error": "No stocks in database"}
            
            report = {
                "total_stocks": total_stocks,
                "completeness": {}
            }
            
            # Price data completeness
            cursor.execute("""
                SELECT COUNT(DISTINCT symbol) FROM price_data
                WHERE date >= date('now', '-30 days')
            """)
            recent_price_stocks = cursor.fetchone()[0]
            report["completeness"]["recent_price_data"] = recent_price_stocks / total_stocks
            
            # Fundamental data completeness
            cursor.execute("""
                SELECT COUNT(DISTINCT symbol) FROM fundamental_data
                WHERE reporting_date >= date('now', '-365 days')
            """)
            recent_fundamental_stocks = cursor.fetchone()[0]
            report["completeness"]["recent_fundamental_data"] = recent_fundamental_stocks / total_stocks
            
            # News data completeness
            cursor.execute("""
                SELECT COUNT(DISTINCT symbol) FROM news_articles
                WHERE publish_date >= datetime('now', '-30 days')
            """)
            recent_news_stocks = cursor.fetchone()[0]
            report["completeness"]["recent_news_data"] = recent_news_stocks / total_stocks
            
            # Sentiment data completeness
            cursor.execute("""
                SELECT COUNT(DISTINCT symbol) FROM daily_sentiment
                WHERE date >= date('now', '-7 days')
            """)
            recent_sentiment_stocks = cursor.fetchone()[0]
            report["completeness"]["recent_sentiment_data"] = recent_sentiment_stocks / total_stocks
            
            # Overall completeness score
            completeness_scores = [
                report["completeness"]["recent_price_data"],
                report["completeness"]["recent_fundamental_data"],
                report["completeness"]["recent_news_data"],
                report["completeness"]["recent_sentiment_data"]
            ]
            report["overall_completeness"] = sum(completeness_scores) / len(completeness_scores)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating completeness report: {e}")
            return {"error": str(e)}
        finally:
            self.db.close()