"""
Composite Score Calculator - Final Integration

Combines all four methodology components into final stock scores:
- Fundamental Valuation (40% weight)  
- Quality Metrics (25% weight)
- Growth Analysis (20% weight)
- Sentiment Analysis (15% weight)

Generates composite scores for outlier detection and ranking with sector-aware adjustments.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, date

from src.data.database import DatabaseManager
from src.utils.helpers import load_config
from src.calculations.fundamental import FundamentalCalculator
from src.calculations.quality import QualityCalculator
from src.calculations.growth import GrowthCalculator
from src.calculations.sentiment import SentimentCalculator

logger = logging.getLogger(__name__)

@dataclass
class CompositeScore:
    """Container for complete stock analysis results"""
    symbol: str
    calculation_date: date
    
    # Component scores (0-100)
    fundamental_score: float
    quality_score: float
    growth_score: float
    sentiment_score: float
    
    # Component data quality levels (0-1)
    fundamental_data_quality: float
    quality_data_quality: float
    growth_data_quality: float
    sentiment_data_quality: float
    
    # Composite results
    composite_score: float
    overall_data_quality: float
    
    # Metadata
    sector: Optional[str]
    methodology_version: str
    data_sources_count: int
    
    # Outlier metrics
    sector_percentile: Optional[float]
    market_percentile: Optional[float]
    outlier_category: Optional[str]

class CompositeCalculator:
    """
    Calculates composite scores by combining all four methodology components
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = load_config(config_path)
        
        # Initialize component calculators
        self.fundamental_calc = FundamentalCalculator(config_path)
        self.quality_calc = QualityCalculator(config_path)
        self.growth_calc = GrowthCalculator(config_path)
        self.sentiment_calc = SentimentCalculator(config_path)
        
        # Base methodology weights (sum to 100%)
        self.base_methodology_weights = {
            'fundamental': 0.40,    # 40% - Core valuation metrics
            'quality': 0.25,       # 25% - Financial health metrics  
            'growth': 0.20,        # 20% - Growth trajectory metrics
            'sentiment': 0.15      # 15% - Market perception metrics
        }
        
        # Outlier detection thresholds
        self.outlier_thresholds = {
            'strong_undervalued': 20,    # Bottom 20th percentile
            'undervalued': 35,           # Bottom 35th percentile  
            'fairly_valued': 65,         # 35th-65th percentile
            'overvalued': 80,            # 65th-80th percentile
            'strong_overvalued': 100     # Top 80th+ percentile
        }
        
        # Minimum data quality requirements (relaxed for post-refresh compatibility)
        self.min_data_quality = {
            'fundamental': 0.3,    # Need 1+ fundamental metrics (relaxed from 0.5)
            'quality': 0.3,        # Need 1+ quality metrics (relaxed from 0.5)
            'growth': 0.3,         # Need 1+ growth metrics (relaxed from 0.5)
            'sentiment': 0.2,      # Need 1+ sentiment metrics (optional, relaxed from 0.3)
            'overall': 0.4         # Need 40%+ overall data quality (relaxed from 0.6)
        }
    
    def get_sector_methodology_weights(self, sector: Optional[str]) -> Dict[str, float]:
        """
        Get sector-adjusted methodology weights
        
        Args:
            sector: Sector name
            
        Returns:
            Adjusted methodology weights dictionary
        """
        weights = self.base_methodology_weights.copy()
        
        # Sector-specific methodology adjustments
        if sector == 'Technology':
            # Tech: Emphasize growth and sentiment, reduce quality focus
            weights['fundamental'] = 0.35    # -5% (growth premiums accepted)
            weights['quality'] = 0.20        # -5% (asset-light businesses)
            weights['growth'] = 0.25         # +5% (growth is key driver)
            weights['sentiment'] = 0.20      # +5% (momentum and narrative important)
            
        elif sector == 'Utilities':
            # Utilities: Emphasize quality and fundamentals, reduce growth/sentiment
            weights['fundamental'] = 0.45    # +5% (yield and valuation key)
            weights['quality'] = 0.35        # +10% (financial stability critical)
            weights['growth'] = 0.10         # -10% (low growth expectations)
            weights['sentiment'] = 0.10      # -5% (less sentiment-driven)
            
        elif sector == 'Financials':
            # Financials: Balance quality and fundamentals, reduce sentiment
            weights['fundamental'] = 0.35    # -5% (unique valuation metrics)
            weights['quality'] = 0.35        # +10% (balance sheet strength key)
            weights['growth'] = 0.20         # Same (moderate growth expected)
            weights['sentiment'] = 0.10      # -5% (institutional focus)
            
        elif sector == 'Healthcare':
            # Healthcare: Emphasize fundamentals and growth, sentiment important for biotech
            weights['fundamental'] = 0.40    # Same (valuation important)
            weights['quality'] = 0.20        # -5% (R&D spending affects metrics)
            weights['growth'] = 0.25         # +5% (pipeline and innovation key)
            weights['sentiment'] = 0.15      # Same (regulatory news matters)
            
        elif sector == 'Energy':
            # Energy: Emphasize fundamentals and quality, reduce growth reliability
            weights['fundamental'] = 0.45    # +5% (commodity cycle valuation)
            weights['quality'] = 0.30        # +5% (balance sheet strength in cycles)
            weights['growth'] = 0.15         # -5% (cyclical growth less meaningful)
            weights['sentiment'] = 0.10      # -5% (commodity fundamentals drive more)
            
        elif sector == 'Consumer Discretionary':
            # Consumer Discretionary: Balance all components, slight sentiment boost
            weights['fundamental'] = 0.35    # -5% (brand premiums accepted)
            weights['quality'] = 0.25        # Same
            weights['growth'] = 0.20         # Same (market share expansion)
            weights['sentiment'] = 0.20      # +5% (consumer sentiment matters)
        
        return weights
    
    def calculate_composite_score(self, symbol: str, db: DatabaseManager) -> Optional[CompositeScore]:
        """
        Calculate complete composite score for a stock
        
        Args:
            symbol: Stock symbol
            db: Database manager instance
            
        Returns:
            CompositeScore object or None if insufficient data
        """
        try:
            logger.info(f"Calculating composite score for {symbol}")
            
            # Get stock info for sector
            stock_info = db.get_stock_info(symbol)
            sector = stock_info.get('sector') if stock_info else None
            
            # Calculate all component scores
            fundamental_metrics = self.fundamental_calc.calculate_fundamental_metrics(symbol, db)
            quality_metrics = self.quality_calc.calculate_quality_metrics(symbol, db)
            growth_metrics = self.growth_calc.calculate_growth_metrics(symbol, db)  
            sentiment_metrics = self.sentiment_calc.calculate_sentiment_metrics(symbol, db)
            
            # Extract scores and data quality ratings
            scores = {}
            data_qualities = {}
            data_sources = 0
            
            if fundamental_metrics:
                scores['fundamental'] = fundamental_metrics.fundamental_score
                data_qualities['fundamental'] = fundamental_metrics.data_quality_score
                data_sources += 1
            else:
                scores['fundamental'] = 0.0
                data_qualities['fundamental'] = 0.0
                
            if quality_metrics:
                scores['quality'] = quality_metrics.quality_score
                data_qualities['quality'] = quality_metrics.data_quality_score
                data_sources += 1
            else:
                scores['quality'] = 0.0
                data_qualities['quality'] = 0.0
                
            if growth_metrics:
                scores['growth'] = growth_metrics.growth_score
                data_qualities['growth'] = growth_metrics.data_quality_score
                data_sources += 1
            else:
                scores['growth'] = 0.0
                data_qualities['growth'] = 0.0
                
            if sentiment_metrics:
                scores['sentiment'] = sentiment_metrics.sentiment_score
                data_qualities['sentiment'] = sentiment_metrics.data_quality_score
                data_sources += 1
            else:
                scores['sentiment'] = 0.0
                data_qualities['sentiment'] = 0.0
            
            # Check minimum data quality requirements
            if (data_qualities['fundamental'] < self.min_data_quality['fundamental'] or
                data_qualities['quality'] < self.min_data_quality['quality'] or  
                data_qualities['growth'] < self.min_data_quality['growth']):
                logger.warning(f"Insufficient data quality for {symbol} composite calculation")
                return None
            
            # Get sector-adjusted methodology weights
            methodology_weights = self.get_sector_methodology_weights(sector)
            
            # Calculate data quality-weighted composite score
            component_contributions = []
            total_quality_weight = 0
            
            for component in ['fundamental', 'quality', 'growth', 'sentiment']:
                if scores[component] > 0 and data_qualities[component] > 0:
                    # Weight by both methodology weight and data quality
                    quality_weight = methodology_weights[component] * data_qualities[component]
                    component_contributions.append(scores[component] * quality_weight)
                    total_quality_weight += quality_weight
            
            if total_quality_weight == 0:
                logger.warning(f"No valid component scores for {symbol}")
                return None
            
            # Calculate final composite score
            composite_score = sum(component_contributions) / total_quality_weight
            
            # Calculate overall data quality
            component_data_qualities = [data_qualities[c] for c in ['fundamental', 'quality', 'growth', 'sentiment']]
            available_components = sum(1 for c in component_data_qualities if c > 0)
            
            # Overall data quality considers both completeness and individual quality scores
            completeness_factor = available_components / 4
            quality_factor = np.mean([c for c in component_data_qualities if c > 0])
            overall_data_quality = completeness_factor * quality_factor
            
            # Check minimum overall data quality
            if overall_data_quality < self.min_data_quality['overall']:
                logger.warning(f"Overall data quality too low for {symbol}: {overall_data_quality:.2f}")
                return None
            
            return CompositeScore(
                symbol=symbol,
                calculation_date=date.today(),
                fundamental_score=scores['fundamental'],
                quality_score=scores['quality'],
                growth_score=scores['growth'],
                sentiment_score=scores['sentiment'],
                fundamental_data_quality=data_qualities['fundamental'],
                quality_data_quality=data_qualities['quality'],
                growth_data_quality=data_qualities['growth'],
                sentiment_data_quality=data_qualities['sentiment'],
                composite_score=composite_score,
                overall_data_quality=overall_data_quality,
                sector=sector,
                methodology_version='v1.0',
                data_sources_count=data_sources,
                sector_percentile=None,  # Calculated separately
                market_percentile=None,  # Calculated separately
                outlier_category=None    # Calculated separately
            )
            
        except Exception as e:
            logger.error(f"Error calculating composite score for {symbol}: {str(e)}")
            return None
    
    def calculate_batch_composite(self, symbols: List[str], db: DatabaseManager) -> Dict[str, CompositeScore]:
        """
        Calculate composite scores for multiple stocks
        
        Args:
            symbols: List of stock symbols
            db: Database manager instance
            
        Returns:
            Dictionary mapping symbols to CompositeScore objects
        """
        results = {}
        
        for symbol in symbols:
            try:
                composite = self.calculate_composite_score(symbol, db)
                if composite:
                    results[symbol] = composite
                    logger.info(f"✅ Calculated composite score for {symbol}: {composite.composite_score:.1f}")
                else:
                    logger.warning(f"❌ Failed to calculate composite score for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")
                continue
        
        logger.info(f"Completed composite analysis for {len(results)}/{len(symbols)} stocks")
        return results
    
    def calculate_percentiles(self, composite_scores: Dict[str, CompositeScore]) -> Dict[str, CompositeScore]:
        """
        Calculate market and sector percentiles for outlier detection
        
        Args:
            composite_scores: Dictionary of CompositeScore objects
            
        Returns:
            Updated dictionary with percentiles calculated
        """
        try:
            # Convert to DataFrame for easier analysis
            scores_data = []
            for symbol, score_obj in composite_scores.items():
                scores_data.append({
                    'symbol': symbol,
                    'composite_score': score_obj.composite_score,
                    'sector': score_obj.sector or 'Unknown'
                })
            
            df = pd.DataFrame(scores_data)
            
            # Calculate market percentiles
            df['market_percentile'] = df['composite_score'].rank(pct=True) * 100
            
            # Calculate sector percentiles
            df['sector_percentile'] = df.groupby('sector')['composite_score'].rank(pct=True) * 100
            
            # Update CompositeScore objects with percentiles
            updated_scores = {}
            for _, row in df.iterrows():
                symbol = row['symbol']
                original_score = composite_scores[symbol]
                
                # Determine outlier category based on market percentile
                market_pct = row['market_percentile']
                if market_pct <= self.outlier_thresholds['strong_undervalued']:
                    outlier_category = 'strong_undervalued'
                elif market_pct <= self.outlier_thresholds['undervalued']:
                    outlier_category = 'undervalued'
                elif market_pct <= self.outlier_thresholds['fairly_valued']:
                    outlier_category = 'fairly_valued'
                elif market_pct <= self.outlier_thresholds['overvalued']:
                    outlier_category = 'overvalued'
                else:
                    outlier_category = 'strong_overvalued'
                
                # Create updated CompositeScore
                updated_scores[symbol] = CompositeScore(
                    symbol=original_score.symbol,
                    calculation_date=original_score.calculation_date,
                    fundamental_score=original_score.fundamental_score,
                    quality_score=original_score.quality_score,
                    growth_score=original_score.growth_score,
                    sentiment_score=original_score.sentiment_score,
                    fundamental_data_quality=original_score.fundamental_data_quality,
                    quality_data_quality=original_score.quality_data_quality,
                    growth_data_quality=original_score.growth_data_quality,
                    sentiment_data_quality=original_score.sentiment_data_quality,
                    composite_score=original_score.composite_score,
                    overall_data_quality=original_score.overall_data_quality,
                    sector=original_score.sector,
                    methodology_version=original_score.methodology_version,
                    data_sources_count=original_score.data_sources_count,
                    sector_percentile=row['sector_percentile'],
                    market_percentile=row['market_percentile'],
                    outlier_category=outlier_category
                )
            
            return updated_scores
            
        except Exception as e:
            logger.error(f"Error calculating percentiles: {str(e)}")
            return composite_scores
    
    def get_outliers(self, composite_scores: Dict[str, CompositeScore], 
                    category: str = 'undervalued', min_data_quality: float = 0.7) -> List[CompositeScore]:
        """
        Get stocks in specific outlier category
        
        Args:
            composite_scores: Dictionary of CompositeScore objects
            category: Outlier category ('strong_undervalued', 'undervalued', etc.)
            min_data_quality: Minimum data quality threshold
            
        Returns:
            List of CompositeScore objects matching criteria
        """
        outliers = []
        
        for score_obj in composite_scores.values():
            if (score_obj.outlier_category == category and 
                score_obj.overall_data_quality >= min_data_quality):
                outliers.append(score_obj)
        
        # Sort by composite score (ascending for undervalued, descending for overvalued)
        if category in ['strong_undervalued', 'undervalued']:
            outliers.sort(key=lambda x: x.composite_score)
        else:
            outliers.sort(key=lambda x: x.composite_score, reverse=True)
        
        return outliers
    
    def save_composite_scores(self, composite_scores: Dict[str, CompositeScore], db: DatabaseManager):
        """
        Save composite scores to database
        
        Args:
            composite_scores: Dictionary of CompositeScore objects
            db: Database manager instance
        """
        try:
            cursor = db.connection.cursor()
            
            for score_obj in composite_scores.values():
                sql = '''
                    INSERT OR REPLACE INTO calculated_metrics
                    (symbol, calculation_date, fundamental_score, quality_score, 
                     growth_score, sentiment_score, composite_score, methodology_version,
                     sector_percentile, market_percentile, outlier_category)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                '''
                
                cursor.execute(sql, (
                    score_obj.symbol,
                    score_obj.calculation_date,
                    score_obj.fundamental_score,
                    score_obj.quality_score,
                    score_obj.growth_score,
                    score_obj.sentiment_score,
                    score_obj.composite_score,
                    score_obj.methodology_version,
                    score_obj.sector_percentile,
                    score_obj.market_percentile,
                    score_obj.outlier_category
                ))
            
            db.connection.commit()
            cursor.close()
            
            logger.info(f"Saved composite scores for {len(composite_scores)} stocks")
            
        except Exception as e:
            logger.error(f"Error saving composite scores: {str(e)}")

# Convenience functions
def calculate_all_composite_scores(config_path: Optional[str] = None) -> Dict[str, CompositeScore]:
    """Calculate composite scores for all stocks in database"""
    calculator = CompositeCalculator(config_path)
    
    from src.data.database import get_database_connection
    db = get_database_connection(config_path)
    
    try:
        symbols = db.get_all_stocks()
        composite_scores = calculator.calculate_batch_composite(symbols, db)
        
        # Calculate percentiles for outlier detection
        composite_scores = calculator.calculate_percentiles(composite_scores)
        
        # Save to database
        calculator.save_composite_scores(composite_scores, db)
        
        return composite_scores
    finally:
        db.close()

def get_stock_outliers(category: str = 'undervalued', limit: int = 20, 
                      config_path: Optional[str] = None) -> List[CompositeScore]:
    """Get top stock outliers in specific category"""
    composite_scores = calculate_all_composite_scores(config_path)
    
    calculator = CompositeCalculator(config_path)
    outliers = calculator.get_outliers(composite_scores, category)
    
    return outliers[:limit]