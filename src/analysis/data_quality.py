#!/usr/bin/env python3
"""
Data Quality Analytics Engine
Comprehensive analysis and monitoring of data quality across all components
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging
from collections import defaultdict

from ..data.database import DatabaseManager
from ..utils.helpers import load_config

logger = logging.getLogger(__name__)

@dataclass
class QualityMetric:
    """Individual quality metric result"""
    name: str
    value: float
    threshold: float
    status: str  # 'excellent', 'good', 'fair', 'poor'
    description: str
    improvement_suggestion: Optional[str] = None

@dataclass
class ComponentQuality:
    """Quality analysis for a specific component"""
    component_name: str
    overall_score: float
    coverage_percentage: float
    freshness_score: float
    completeness_score: float
    reliability_score: float
    metrics: List[QualityMetric]
    sample_issues: List[Dict[str, Any]]

@dataclass
class QualityReport:
    """Comprehensive data quality report"""
    report_date: datetime
    overall_quality_score: float
    component_scores: Dict[str, ComponentQuality]
    trends: Dict[str, List[float]]
    recommendations: List[str]
    quality_distribution: Dict[str, int]

class QualityAnalyticsEngine:
    """Comprehensive data quality analytics and monitoring"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = load_config(config_path)
        self.db = DatabaseManager()
        self.logger = logging.getLogger(__name__)
        
        # Quality thresholds
        self.thresholds = {
            'excellent': 0.90,
            'good': 0.75,
            'fair': 0.60,
            'poor': 0.0
        }
        
        # Component weights for overall score
        self.component_weights = {
            'fundamental': 0.30,
            'price': 0.25,
            'news': 0.20,
            'sentiment': 0.15,
            'completeness': 0.10
        }
    
    def generate_comprehensive_quality_report(self) -> QualityReport:
        """Generate comprehensive data quality report"""
        self.logger.info("Generating comprehensive data quality report")
        
        if not self.db.connect():
            raise RuntimeError("Cannot connect to database for quality analysis")
        
        try:
            # Analyze each component
            component_scores = {}
            component_scores['fundamental'] = self._analyze_fundamental_quality()
            component_scores['price'] = self._analyze_price_quality()
            component_scores['news'] = self._analyze_news_quality()
            component_scores['sentiment'] = self._analyze_sentiment_quality()
            component_scores['completeness'] = self._analyze_completeness_quality()
            
            # Calculate overall quality score
            overall_score = self._calculate_overall_quality_score(component_scores)
            
            # Generate trends (placeholder - would use historical data)
            trends = self._generate_quality_trends()
            
            # Generate recommendations
            recommendations = self._generate_recommendations(component_scores)
            
            # Quality distribution
            quality_distribution = self._calculate_quality_distribution(component_scores)
            
            report = QualityReport(
                report_date=datetime.now(),
                overall_quality_score=overall_score,
                component_scores=component_scores,
                trends=trends,
                recommendations=recommendations,
                quality_distribution=quality_distribution
            )
            
            self.logger.info(f"Quality report generated: Overall score {overall_score:.2f}")
            return report
            
        finally:
            self.db.close()
    
    def _analyze_fundamental_quality(self) -> ComponentQuality:
        """Analyze fundamental data quality"""
        cursor = self.db.connection.cursor()
        
        # Get fundamental data statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT symbol) as unique_symbols,
                AVG(CASE WHEN pe_ratio IS NOT NULL THEN 1 ELSE 0 END) as pe_completeness,
                AVG(CASE WHEN market_cap IS NOT NULL THEN 1 ELSE 0 END) as mcap_completeness,
                AVG(CASE WHEN debt_to_equity IS NOT NULL THEN 1 ELSE 0 END) as de_completeness,
                AVG(CASE WHEN return_on_equity IS NOT NULL THEN 1 ELSE 0 END) as roe_completeness,
                COUNT(CASE WHEN reporting_date >= date('now', '-90 days') THEN 1 END) as recent_records
            FROM fundamental_data
        """)
        
        stats = cursor.fetchone()
        total_records, unique_symbols, pe_comp, mcap_comp, de_comp, roe_comp, recent_records = stats
        
        # Get total stock count for coverage calculation
        cursor.execute("SELECT COUNT(*) FROM stocks")
        total_stocks = cursor.fetchone()[0]
        
        # Calculate metrics
        coverage_percentage = (unique_symbols / total_stocks * 100) if total_stocks > 0 else 0
        freshness_score = (recent_records / total_records) if total_records > 0 else 0
        completeness_score = (pe_comp + mcap_comp + de_comp + roe_comp) / 4
        
        # Sample data quality issues
        cursor.execute("""
            SELECT symbol, pe_ratio, market_cap, debt_to_equity
            FROM fundamental_data
            WHERE pe_ratio IS NULL OR pe_ratio < 0 OR pe_ratio > 1000
               OR market_cap IS NULL OR market_cap <= 0
               OR debt_to_equity IS NULL OR debt_to_equity < 0
            LIMIT 5
        """)
        
        sample_issues = [
            {"symbol": row[0], "pe_ratio": row[1], "market_cap": row[2], "debt_to_equity": row[3]}
            for row in cursor.fetchall()
        ]
        
        # Reliability score based on data consistency
        cursor.execute("""
            SELECT 
                AVG(CASE WHEN pe_ratio BETWEEN 0 AND 100 THEN 1 ELSE 0 END) as pe_validity,
                AVG(CASE WHEN market_cap > 1000000 THEN 1 ELSE 0 END) as mcap_validity,
                AVG(CASE WHEN debt_to_equity BETWEEN 0 AND 5 THEN 1 ELSE 0 END) as de_validity
            FROM fundamental_data
            WHERE pe_ratio IS NOT NULL AND market_cap IS NOT NULL AND debt_to_equity IS NOT NULL
        """)
        
        validity_stats = cursor.fetchone()
        reliability_score = sum(validity_stats) / 3 if validity_stats else 0
        
        # Create quality metrics
        metrics = [
            QualityMetric(
                name="Coverage",
                value=coverage_percentage / 100,
                threshold=0.8,
                status=self._get_quality_status(coverage_percentage / 100),
                description=f"{coverage_percentage:.1f}% of stocks have fundamental data"
            ),
            QualityMetric(
                name="Freshness",
                value=freshness_score,
                threshold=0.7,
                status=self._get_quality_status(freshness_score),
                description=f"{freshness_score*100:.1f}% of records are recent (90 days)"
            ),
            QualityMetric(
                name="Completeness",
                value=completeness_score,
                threshold=0.85,
                status=self._get_quality_status(completeness_score),
                description=f"{completeness_score*100:.1f}% of required fields are populated"
            ),
            QualityMetric(
                name="Reliability",
                value=reliability_score,
                threshold=0.9,
                status=self._get_quality_status(reliability_score),
                description=f"{reliability_score*100:.1f}% of values are within expected ranges"
            )
        ]
        
        overall_score = (coverage_percentage/100 * 0.3 + freshness_score * 0.2 + 
                        completeness_score * 0.3 + reliability_score * 0.2)
        
        return ComponentQuality(
            component_name="Fundamental Data",
            overall_score=overall_score,
            coverage_percentage=coverage_percentage,
            freshness_score=freshness_score,
            completeness_score=completeness_score,
            reliability_score=reliability_score,
            metrics=metrics,
            sample_issues=sample_issues
        )
    
    def _analyze_price_quality(self) -> ComponentQuality:
        """Analyze price data quality"""
        cursor = self.db.connection.cursor()
        
        # Get price data statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT symbol) as unique_symbols,
                COUNT(CASE WHEN date >= date('now', '-7 days') THEN 1 END) as recent_records,
                AVG(CASE WHEN volume > 0 THEN 1 ELSE 0 END) as volume_completeness
            FROM price_data
        """)
        
        stats = cursor.fetchone()
        total_records, unique_symbols, recent_records, volume_comp = stats
        
        # Get total stock count
        cursor.execute("SELECT COUNT(*) FROM stocks")
        total_stocks = cursor.fetchone()[0]
        
        # Calculate metrics
        coverage_percentage = (unique_symbols / total_stocks * 100) if total_stocks > 0 else 0
        freshness_score = (recent_records / total_records) if total_records > 0 else 0
        completeness_score = volume_comp if volume_comp else 0
        
        # Check for data gaps and invalid values
        cursor.execute("""
            SELECT COUNT(*) FROM price_data
            WHERE open <= 0 OR high <= 0 OR low <= 0 OR close <= 0
               OR high < low OR high < open OR high < close
        """)
        
        invalid_records = cursor.fetchone()[0]
        reliability_score = 1 - (invalid_records / total_records) if total_records > 0 else 0
        
        # Sample issues
        cursor.execute("""
            SELECT symbol, date, open, high, low, close, volume
            FROM price_data
            WHERE open <= 0 OR high <= 0 OR low <= 0 OR close <= 0
               OR high < low OR volume <= 0
            LIMIT 5
        """)
        
        sample_issues = [
            {"symbol": row[0], "date": row[1], "ohlc": f"{row[2]}/{row[3]}/{row[4]}/{row[5]}", "volume": row[6]}
            for row in cursor.fetchall()
        ]
        
        metrics = [
            QualityMetric(
                name="Coverage",
                value=coverage_percentage / 100,
                threshold=0.95,
                status=self._get_quality_status(coverage_percentage / 100),
                description=f"{coverage_percentage:.1f}% of stocks have price data"
            ),
            QualityMetric(
                name="Freshness",
                value=freshness_score,
                threshold=0.8,
                status=self._get_quality_status(freshness_score),
                description=f"{freshness_score*100:.1f}% of records are recent (7 days)"
            ),
            QualityMetric(
                name="Completeness",
                value=completeness_score,
                threshold=0.95,
                status=self._get_quality_status(completeness_score),
                description=f"{completeness_score*100:.1f}% of records have valid volume"
            ),
            QualityMetric(
                name="Reliability",
                value=reliability_score,
                threshold=0.99,
                status=self._get_quality_status(reliability_score),
                description=f"{reliability_score*100:.1f}% of prices are valid"
            )
        ]
        
        overall_score = (coverage_percentage/100 * 0.2 + freshness_score * 0.4 + 
                        completeness_score * 0.2 + reliability_score * 0.2)
        
        return ComponentQuality(
            component_name="Price Data",
            overall_score=overall_score,
            coverage_percentage=coverage_percentage,
            freshness_score=freshness_score,
            completeness_score=completeness_score,
            reliability_score=reliability_score,
            metrics=metrics,
            sample_issues=sample_issues
        )
    
    def _analyze_news_quality(self) -> ComponentQuality:
        """Analyze news data quality"""
        cursor = self.db.connection.cursor()
        
        # Get news data statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT symbol) as unique_symbols,
                COUNT(CASE WHEN publish_date >= datetime('now', '-30 days') THEN 1 END) as recent_records,
                AVG(CASE WHEN title IS NOT NULL AND title != '' THEN 1 ELSE 0 END) as title_completeness,
                AVG(CASE WHEN content IS NOT NULL AND content != '' THEN 1 ELSE 0 END) as content_completeness,
                AVG(CASE WHEN sentiment_score IS NOT NULL THEN 1 ELSE 0 END) as sentiment_completeness
            FROM news_articles
        """)
        
        stats = cursor.fetchone()
        if stats[0] is None:  # No news data
            return self._create_empty_component_quality("News Data")
        
        total_records, unique_symbols, recent_records, title_comp, content_comp, sentiment_comp = stats
        
        # Get total stock count
        cursor.execute("SELECT COUNT(*) FROM stocks")
        total_stocks = cursor.fetchone()[0]
        
        # Calculate metrics
        coverage_percentage = (unique_symbols / total_stocks * 100) if total_stocks > 0 else 0
        freshness_score = (recent_records / total_records) if total_records > 0 else 0
        completeness_score = (title_comp + content_comp + sentiment_comp) / 3
        
        # Check for duplicate articles
        cursor.execute("""
            SELECT COUNT(*) - COUNT(DISTINCT url) as duplicates
            FROM news_articles
            WHERE url IS NOT NULL AND url != ''
        """)
        
        duplicates = cursor.fetchone()[0] or 0
        reliability_score = 1 - (duplicates / total_records) if total_records > 0 else 1
        
        # Sample issues
        cursor.execute("""
            SELECT symbol, title, publish_date, sentiment_score
            FROM news_articles
            WHERE title IS NULL OR title = ''
               OR content IS NULL OR content = ''
               OR sentiment_score IS NULL
            LIMIT 5
        """)
        
        sample_issues = [
            {"symbol": row[0], "title": row[1] or "Missing", "date": row[2], "sentiment": row[3]}
            for row in cursor.fetchall()
        ]
        
        metrics = [
            QualityMetric(
                name="Coverage",
                value=coverage_percentage / 100,
                threshold=0.7,
                status=self._get_quality_status(coverage_percentage / 100),
                description=f"{coverage_percentage:.1f}% of stocks have news articles"
            ),
            QualityMetric(
                name="Freshness",
                value=freshness_score,
                threshold=0.5,
                status=self._get_quality_status(freshness_score),
                description=f"{freshness_score*100:.1f}% of articles are recent (30 days)"
            ),
            QualityMetric(
                name="Completeness",
                value=completeness_score,
                threshold=0.8,
                status=self._get_quality_status(completeness_score),
                description=f"{completeness_score*100:.1f}% of articles have complete content"
            ),
            QualityMetric(
                name="Reliability",
                value=reliability_score,
                threshold=0.95,
                status=self._get_quality_status(reliability_score),
                description=f"{reliability_score*100:.1f}% uniqueness (no duplicates)"
            )
        ]
        
        overall_score = (coverage_percentage/100 * 0.3 + freshness_score * 0.3 + 
                        completeness_score * 0.2 + reliability_score * 0.2)
        
        return ComponentQuality(
            component_name="News Data",
            overall_score=overall_score,
            coverage_percentage=coverage_percentage,
            freshness_score=freshness_score,
            completeness_score=completeness_score,
            reliability_score=reliability_score,
            metrics=metrics,
            sample_issues=sample_issues
        )
    
    def _analyze_sentiment_quality(self) -> ComponentQuality:
        """Analyze sentiment data quality"""
        cursor = self.db.connection.cursor()
        
        # Get sentiment data statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT symbol) as unique_symbols,
                COUNT(CASE WHEN date >= date('now', '-7 days') THEN 1 END) as recent_records,
                AVG(CASE WHEN news_sentiment IS NOT NULL THEN 1 ELSE 0 END) as news_completeness,
                AVG(CASE WHEN reddit_sentiment IS NOT NULL THEN 1 ELSE 0 END) as reddit_completeness,
                AVG(CASE WHEN combined_sentiment IS NOT NULL THEN 1 ELSE 0 END) as combined_completeness
            FROM daily_sentiment
        """)
        
        stats = cursor.fetchone()
        if stats[0] is None or stats[0] == 0:  # No sentiment data
            return self._create_empty_component_quality("Sentiment Data")
        
        total_records, unique_symbols, recent_records, news_comp, reddit_comp, combined_comp = stats
        
        # Get total stock count
        cursor.execute("SELECT COUNT(*) FROM stocks")
        total_stocks = cursor.fetchone()[0]
        
        # Calculate metrics
        coverage_percentage = (unique_symbols / total_stocks * 100) if total_stocks > 0 else 0
        freshness_score = (recent_records / total_records) if total_records > 0 else 0
        completeness_score = (news_comp + reddit_comp + combined_comp) / 3
        
        # Check for sentiment scores in valid range
        cursor.execute("""
            SELECT COUNT(*) FROM daily_sentiment
            WHERE (news_sentiment < -1 OR news_sentiment > 1)
               OR (reddit_sentiment < -1 OR reddit_sentiment > 1)
               OR (combined_sentiment < -1 OR combined_sentiment > 1)
        """)
        
        invalid_sentiments = cursor.fetchone()[0] or 0
        reliability_score = 1 - (invalid_sentiments / total_records) if total_records > 0 else 1
        
        # Sample issues
        cursor.execute("""
            SELECT symbol, date, news_sentiment, reddit_sentiment, combined_sentiment
            FROM daily_sentiment
            WHERE news_sentiment IS NULL OR reddit_sentiment IS NULL
               OR news_sentiment < -1 OR news_sentiment > 1
               OR reddit_sentiment < -1 OR reddit_sentiment > 1
            LIMIT 5
        """)
        
        sample_issues = [
            {"symbol": row[0], "date": row[1], "news": row[2], "reddit": row[3], "combined": row[4]}
            for row in cursor.fetchall()
        ]
        
        metrics = [
            QualityMetric(
                name="Coverage",
                value=coverage_percentage / 100,
                threshold=0.6,
                status=self._get_quality_status(coverage_percentage / 100),
                description=f"{coverage_percentage:.1f}% of stocks have sentiment data"
            ),
            QualityMetric(
                name="Freshness",
                value=freshness_score,
                threshold=0.7,
                status=self._get_quality_status(freshness_score),
                description=f"{freshness_score*100:.1f}% of sentiment is recent (7 days)"
            ),
            QualityMetric(
                name="Completeness",
                value=completeness_score,
                threshold=0.8,
                status=self._get_quality_status(completeness_score),
                description=f"{completeness_score*100:.1f}% of sentiment fields are populated"
            ),
            QualityMetric(
                name="Reliability",
                value=reliability_score,
                threshold=0.95,
                status=self._get_quality_status(reliability_score),
                description=f"{reliability_score*100:.1f}% of sentiment scores are valid"
            )
        ]
        
        overall_score = (coverage_percentage/100 * 0.25 + freshness_score * 0.35 + 
                        completeness_score * 0.2 + reliability_score * 0.2)
        
        return ComponentQuality(
            component_name="Sentiment Data",
            overall_score=overall_score,
            coverage_percentage=coverage_percentage,
            freshness_score=freshness_score,
            completeness_score=completeness_score,
            reliability_score=reliability_score,
            metrics=metrics,
            sample_issues=sample_issues
        )
    
    def _analyze_completeness_quality(self) -> ComponentQuality:
        """Analyze overall data completeness across all tables"""
        cursor = self.db.connection.cursor()
        
        # Get total stock count
        cursor.execute("SELECT COUNT(*) FROM stocks")
        total_stocks = cursor.fetchone()[0]
        
        if total_stocks == 0:
            return self._create_empty_component_quality("Data Completeness")
        
        # Check completeness across all data types
        cursor.execute("""
            SELECT 
                s.symbol,
                CASE WHEN pd.symbol IS NOT NULL THEN 1 ELSE 0 END as has_price,
                CASE WHEN fd.symbol IS NOT NULL THEN 1 ELSE 0 END as has_fundamental,
                CASE WHEN na.symbol IS NOT NULL THEN 1 ELSE 0 END as has_news,
                CASE WHEN ds.symbol IS NOT NULL THEN 1 ELSE 0 END as has_sentiment
            FROM stocks s
            LEFT JOIN (SELECT DISTINCT symbol FROM price_data WHERE date >= date('now', '-30 days')) pd ON s.symbol = pd.symbol
            LEFT JOIN (SELECT DISTINCT symbol FROM fundamental_data WHERE reporting_date >= date('now', '-365 days')) fd ON s.symbol = fd.symbol
            LEFT JOIN (SELECT DISTINCT symbol FROM news_articles WHERE publish_date >= datetime('now', '-90 days')) na ON s.symbol = na.symbol
            LEFT JOIN (SELECT DISTINCT symbol FROM daily_sentiment WHERE date >= date('now', '-30 days')) ds ON s.symbol = ds.symbol
        """)
        
        completeness_data = cursor.fetchall()
        
        # Calculate metrics
        total_data_points = len(completeness_data) * 4  # 4 data types per stock
        complete_data_points = sum([row[1] + row[2] + row[3] + row[4] for row in completeness_data])
        
        overall_completeness = complete_data_points / total_data_points if total_data_points > 0 else 0
        
        # Individual component completeness
        price_completeness = sum([row[1] for row in completeness_data]) / total_stocks
        fundamental_completeness = sum([row[2] for row in completeness_data]) / total_stocks
        news_completeness = sum([row[3] for row in completeness_data]) / total_stocks
        sentiment_completeness = sum([row[4] for row in completeness_data]) / total_stocks
        
        # Find stocks with missing data
        incomplete_stocks = [
            {"symbol": row[0], "missing": 4 - (row[1] + row[2] + row[3] + row[4])}
            for row in completeness_data
            if (row[1] + row[2] + row[3] + row[4]) < 4
        ][:5]  # Limit to 5 examples
        
        metrics = [
            QualityMetric(
                name="Price Data Coverage",
                value=price_completeness,
                threshold=0.95,
                status=self._get_quality_status(price_completeness),
                description=f"{price_completeness*100:.1f}% of stocks have recent price data"
            ),
            QualityMetric(
                name="Fundamental Data Coverage",
                value=fundamental_completeness,
                threshold=0.8,
                status=self._get_quality_status(fundamental_completeness),
                description=f"{fundamental_completeness*100:.1f}% of stocks have fundamental data"
            ),
            QualityMetric(
                name="News Data Coverage",
                value=news_completeness,
                threshold=0.6,
                status=self._get_quality_status(news_completeness),
                description=f"{news_completeness*100:.1f}% of stocks have news data"
            ),
            QualityMetric(
                name="Sentiment Data Coverage",
                value=sentiment_completeness,
                threshold=0.5,
                status=self._get_quality_status(sentiment_completeness),
                description=f"{sentiment_completeness*100:.1f}% of stocks have sentiment data"
            )
        ]
        
        return ComponentQuality(
            component_name="Data Completeness",
            overall_score=overall_completeness,
            coverage_percentage=overall_completeness * 100,
            freshness_score=overall_completeness,  # Using same value
            completeness_score=overall_completeness,
            reliability_score=1.0,  # Completeness is binary
            metrics=metrics,
            sample_issues=incomplete_stocks
        )
    
    def _create_empty_component_quality(self, component_name: str) -> ComponentQuality:
        """Create empty component quality for components with no data"""
        return ComponentQuality(
            component_name=component_name,
            overall_score=0.0,
            coverage_percentage=0.0,
            freshness_score=0.0,
            completeness_score=0.0,
            reliability_score=0.0,
            metrics=[],
            sample_issues=[]
        )
    
    def _get_quality_status(self, score: float) -> str:
        """Get quality status based on score"""
        if score >= self.thresholds['excellent']:
            return 'excellent'
        elif score >= self.thresholds['good']:
            return 'good'
        elif score >= self.thresholds['fair']:
            return 'fair'
        else:
            return 'poor'
    
    def _calculate_overall_quality_score(self, component_scores: Dict[str, ComponentQuality]) -> float:
        """Calculate weighted overall quality score"""
        total_weight = 0
        weighted_sum = 0
        
        for component_name, quality in component_scores.items():
            if component_name in self.component_weights:
                weight = self.component_weights[component_name]
                weighted_sum += quality.overall_score * weight
                total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0
    
    def _generate_quality_trends(self) -> Dict[str, List[float]]:
        """Generate quality trends (placeholder for historical analysis)"""
        # In a real implementation, this would analyze historical quality data
        return {
            'overall_quality': [0.75, 0.78, 0.80, 0.82, 0.85],
            'fundamental_quality': [0.80, 0.82, 0.85, 0.87, 0.88],
            'price_quality': [0.95, 0.94, 0.96, 0.95, 0.97],
            'news_quality': [0.60, 0.65, 0.68, 0.70, 0.72],
            'sentiment_quality': [0.55, 0.58, 0.60, 0.62, 0.65]
        }
    
    def _generate_recommendations(self, component_scores: Dict[str, ComponentQuality]) -> List[str]:
        """Generate quality improvement recommendations"""
        recommendations = []
        
        for component_name, quality in component_scores.items():
            if quality.overall_score < self.thresholds['fair']:
                recommendations.append(f"CRITICAL: {quality.component_name} quality is poor ({quality.overall_score:.1%}) - immediate attention required")
            elif quality.overall_score < self.thresholds['good']:
                recommendations.append(f"IMPROVEMENT: {quality.component_name} quality is fair ({quality.overall_score:.1%}) - consider data collection improvements")
            
            # Specific recommendations based on metrics
            for metric in quality.metrics:
                if metric.status == 'poor' and metric.improvement_suggestion:
                    recommendations.append(f"{component_name}: {metric.improvement_suggestion}")
        
        # Generic recommendations if overall quality is good
        if not recommendations:
            recommendations.append("Overall data quality is good - maintain current collection standards")
            recommendations.append("Consider implementing automated quality monitoring alerts")
            recommendations.append("Schedule regular quality reviews to maintain standards")
        
        return recommendations[:10]  # Limit to top 10
    
    def _calculate_quality_distribution(self, component_scores: Dict[str, ComponentQuality]) -> Dict[str, int]:
        """Calculate distribution of quality statuses"""
        distribution = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0}
        
        for quality in component_scores.values():
            status = self._get_quality_status(quality.overall_score)
            distribution[status] += 1
        
        return distribution
    
    def get_quality_summary(self) -> Dict[str, Any]:
        """Get quick quality summary for dashboard display"""
        report = self.generate_comprehensive_quality_report()
        
        return {
            'overall_score': report.overall_quality_score,
            'overall_grade': self._get_quality_status(report.overall_quality_score),
            'component_scores': {
                name: {
                    'score': comp.overall_score,
                    'grade': self._get_quality_status(comp.overall_score),
                    'coverage': comp.coverage_percentage
                }
                for name, comp in report.component_scores.items()
            },
            'top_issues': [rec for rec in report.recommendations if 'CRITICAL' in rec or 'IMPROVEMENT' in rec][:3],
            'last_updated': report.report_date.isoformat()
        }