"""
Growth Analysis Calculators - 20% Weight Component

Implements growth metrics for stock analysis:
- Revenue Growth Rate - Top-line growth assessment
- Earnings Per Share (EPS) Growth - Bottom-line profitability growth
- Revenue Growth Stability - Consistency of growth over time
- Forward Growth Expectations - Analyst estimates integration

Each metric is scored 0-100 with sector adjustments, then combined into composite growth score.
Growth metrics help identify companies with sustainable business expansion.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, date

from src.data.database import DatabaseManager
from src.utils.helpers import load_config
from src.calculations.sector_adjustments import SectorAdjustmentEngine

logger = logging.getLogger(__name__)

@dataclass
class GrowthMetrics:
    """Container for growth analysis results"""
    symbol: str
    calculation_date: date
    
    # Raw metrics
    revenue_growth: Optional[float]
    eps_growth: Optional[float]
    revenue_stability: Optional[float]
    forward_growth: Optional[float]
    
    # Scored metrics (0-100)
    revenue_growth_score: float
    eps_growth_score: float
    revenue_stability_score: float
    forward_growth_score: float
    
    # Composite score
    growth_score: float
    data_quality_score: float
    
    # Metadata
    sector: Optional[str]
    data_quality: float

class GrowthCalculator:
    """
    Calculates and scores growth analysis metrics
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = load_config(config_path)
        self.sector_engine = SectorAdjustmentEngine()
        
        # Growth component weights (sum to 100%)
        self.base_component_weights = {
            'revenue_growth': 0.40,      # 40% - Top-line growth most important
            'eps_growth': 0.35,          # 35% - Bottom-line profitability growth
            'revenue_stability': 0.15,   # 15% - Consistency of growth
            'forward_growth': 0.10       # 10% - Future expectations (if available)
        }
        
        # Base scoring thresholds for growth metrics
        self.scoring_thresholds = {
            'revenue_growth': {
                'excellent': 0.20,       # Revenue growth > 20% = 90-100 points
                'good': 0.15,            # Revenue growth > 15% = 70-89 points
                'average': 0.10,         # Revenue growth > 10% = 50-69 points
                'poor': 0.05,            # Revenue growth > 5% = 30-49 points
                'very_poor': 0.0         # Revenue growth <= 0% = 0-29 points
            },
            'eps_growth': {
                'excellent': 0.25,       # EPS growth > 25% = 90-100 points
                'good': 0.15,            # EPS growth > 15% = 70-89 points
                'average': 0.10,         # EPS growth > 10% = 50-69 points
                'poor': 0.05,            # EPS growth > 5% = 30-49 points
                'very_poor': 0.0         # EPS growth <= 0% = 0-29 points
            },
            'revenue_stability': {
                'excellent': 0.85,       # Low coefficient of variation = high stability
                'good': 0.70,            # Good = 70-89 points
                'average': 0.50,         # Average = 50-69 points
                'poor': 0.30,            # Poor = 30-49 points
                'very_poor': 0.0         # Very poor = 0-29 points
            },
            'forward_growth': {
                'excellent': 0.20,       # Forward growth > 20% = 90-100 points
                'good': 0.15,            # Forward growth > 15% = 70-89 points
                'average': 0.10,         # Forward growth > 10% = 50-69 points
                'poor': 0.05,            # Forward growth > 5% = 30-49 points
                'very_poor': 0.0         # Forward growth <= 0% = 0-29 points
            }
        }
    
    def get_sector_adjusted_weights(self, sector: Optional[str]) -> Dict[str, float]:
        """
        Get sector-adjusted component weights for growth metrics
        
        Args:
            sector: Sector name
            
        Returns:
            Adjusted component weights dictionary
        """
        weights = self.base_component_weights.copy()
        
        # Sector-specific weight adjustments
        if sector == 'Technology':
            # Tech: Higher growth expectations, forward-looking important
            weights['revenue_growth'] = 0.35      # -5% (still important but tempered)
            weights['eps_growth'] = 0.40          # +5% (profitability scaling key)
            weights['revenue_stability'] = 0.10   # -5% (volatility accepted)
            weights['forward_growth'] = 0.15      # +5% (innovation pipeline critical)
            
        elif sector == 'Healthcare':
            # Healthcare: Steady growth expected, R&D makes forward growth important
            weights['revenue_growth'] = 0.35      # -5% (steady growth expected)
            weights['eps_growth'] = 0.30          # -5% (R&D affects EPS)
            weights['revenue_stability'] = 0.20   # +5% (consistency valued)
            weights['forward_growth'] = 0.15      # +5% (pipeline important)
            
        elif sector == 'Consumer Discretionary':
            # Consumer Discretionary: Revenue growth critical, cyclical nature
            weights['revenue_growth'] = 0.45      # +5% (market share key)
            weights['eps_growth'] = 0.30          # -5% (margins can vary)
            weights['revenue_stability'] = 0.15   # Same (some cyclicality expected)
            weights['forward_growth'] = 0.10      # Same
            
        elif sector == 'Utilities':
            # Utilities: Low growth expectations, stability most important
            weights['revenue_growth'] = 0.25      # -15% (regulated, low growth)
            weights['eps_growth'] = 0.25          # -10% (regulated returns)
            weights['revenue_stability'] = 0.35   # +20% (consistency critical)
            weights['forward_growth'] = 0.15      # +5% (capex planning)
            
        elif sector == 'Energy':
            # Energy: Cyclical, stability less meaningful, focus on current growth
            weights['revenue_growth'] = 0.45      # +5% (commodity cycle timing)
            weights['eps_growth'] = 0.40          # +5% (leverage amplifies)
            weights['revenue_stability'] = 0.05   # -10% (inherently cyclical)
            weights['forward_growth'] = 0.10      # Same
            
        elif sector == 'Financials':
            # Financials: Different growth model, focus on consistency
            weights['revenue_growth'] = 0.30      # -10% (net interest income model)
            weights['eps_growth'] = 0.40          # +5% (ROE expansion key)
            weights['revenue_stability'] = 0.25   # +10% (consistency important)
            weights['forward_growth'] = 0.05      # -5% (harder to predict)
        
        return weights
    
    def calculate_revenue_growth(self, fundamentals: Dict[str, Any], sector: Optional[str] = None) -> Tuple[Optional[float], float]:
        """
        Calculate and score revenue growth rate
        
        Returns:
            (revenue_growth, revenue_growth_score): Raw growth rate and normalized score (0-100)
        """
        try:
            # Try to get revenue growth directly
            revenue_growth = fundamentals.get('revenue_growth')
            
            if revenue_growth is None:
                # Try to calculate from current and previous revenue
                total_revenue = fundamentals.get('total_revenue')
                # Note: Historical revenue data would need to be stored separately
                # For now, we'll rely on the revenue_growth field from yfinance
                logger.warning("Revenue growth not available in fundamental data")
                return None, 0.0
            
            # Handle extreme negative growth (bankruptcy indicator)
            if revenue_growth <= -0.5:  # -50% or worse
                return revenue_growth, 0.0
            
            # Score revenue growth (higher is better)
            thresholds = self.scoring_thresholds['revenue_growth']
            
            # Apply sector adjustments to thresholds
            if sector == 'Technology':
                # Higher growth expectations for tech
                thresholds = {k: v * 1.3 for k, v in thresholds.items()}
            elif sector == 'Utilities':
                # Lower growth expectations for regulated utilities
                thresholds = {k: v * 0.4 for k, v in thresholds.items()}
            elif sector == 'Consumer Staples':
                # Lower growth expectations for mature markets
                thresholds = {k: v * 0.6 for k, v in thresholds.items()}
            elif sector == 'Healthcare':
                # Moderate adjustment for healthcare growth
                thresholds = {k: v * 1.1 for k, v in thresholds.items()}
            elif sector == 'Energy':
                # Variable growth expectations due to cycles
                thresholds = {k: v * 0.8 for k, v in thresholds.items()}
            
            if revenue_growth > thresholds['excellent']:
                score = 90 + min(10, (revenue_growth - thresholds['excellent']) / thresholds['excellent'] * 20)
            elif revenue_growth > thresholds['good']:
                score = 70 + (revenue_growth - thresholds['good']) / (thresholds['excellent'] - thresholds['good']) * 20
            elif revenue_growth > thresholds['average']:
                score = 50 + (revenue_growth - thresholds['average']) / (thresholds['good'] - thresholds['average']) * 20
            elif revenue_growth > thresholds['poor']:
                score = 30 + (revenue_growth - thresholds['poor']) / (thresholds['average'] - thresholds['poor']) * 20
            elif revenue_growth > thresholds['very_poor']:
                score = 10 + (revenue_growth - thresholds['very_poor']) / (thresholds['poor'] - thresholds['very_poor']) * 20
            else:
                score = max(0, 10 + revenue_growth * 20)  # Negative growth gets very low score
            
            return revenue_growth, max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating revenue growth: {str(e)}")
            return None, 0.0
    
    def calculate_eps_growth(self, fundamentals: Dict[str, Any], sector: Optional[str] = None) -> Tuple[Optional[float], float]:
        """
        Calculate and score EPS growth rate
        
        Returns:
            (eps_growth, eps_growth_score): Raw EPS growth and normalized score (0-100)
        """
        try:
            eps_growth = fundamentals.get('earnings_growth')
            
            if eps_growth is None:
                logger.warning("EPS growth not available in fundamental data")
                return None, 0.0
            
            # Handle extreme negative growth
            if eps_growth <= -0.8:  # -80% or worse indicates severe problems
                return eps_growth, 0.0
            
            # Score EPS growth (higher is better)
            thresholds = self.scoring_thresholds['eps_growth']
            
            # Apply sector adjustments
            if sector == 'Technology':
                # Higher EPS growth expectations for scalable tech
                thresholds = {k: v * 1.4 for k, v in thresholds.items()}
            elif sector == 'Financials':
                # Moderate EPS growth expectations for banks
                thresholds = {k: v * 0.8 for k, v in thresholds.items()}
            elif sector == 'Utilities':
                # Lower EPS growth for regulated utilities
                thresholds = {k: v * 0.5 for k, v in thresholds.items()}
            elif sector == 'Energy':
                # Variable EPS due to commodity cycles
                thresholds = {k: v * 1.2 for k, v in thresholds.items()}
            elif sector == 'Healthcare':
                # Good EPS growth expected from healthcare
                thresholds = {k: v * 1.1 for k, v in thresholds.items()}
            
            if eps_growth > thresholds['excellent']:
                score = 90 + min(10, (eps_growth - thresholds['excellent']) / thresholds['excellent'] * 15)
            elif eps_growth > thresholds['good']:
                score = 70 + (eps_growth - thresholds['good']) / (thresholds['excellent'] - thresholds['good']) * 20
            elif eps_growth > thresholds['average']:
                score = 50 + (eps_growth - thresholds['average']) / (thresholds['good'] - thresholds['average']) * 20
            elif eps_growth > thresholds['poor']:
                score = 30 + (eps_growth - thresholds['poor']) / (thresholds['average'] - thresholds['poor']) * 20
            elif eps_growth > thresholds['very_poor']:
                score = 10 + (eps_growth - thresholds['very_poor']) / (thresholds['poor'] - thresholds['very_poor']) * 20
            else:
                score = max(0, 10 + eps_growth * 15)  # Negative EPS growth gets low score
            
            return eps_growth, max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating EPS growth: {str(e)}")
            return None, 0.0
    
    def calculate_revenue_stability(self, fundamentals: Dict[str, Any], sector: Optional[str] = None) -> Tuple[Optional[float], float]:
        """
        Calculate and score revenue growth stability (consistency)
        
        Note: This is a simplified implementation. Full implementation would require
        historical quarterly revenue data to calculate coefficient of variation.
        
        Returns:
            (stability_score, stability_rating): Stability metric and normalized score (0-100)
        """
        try:
            # For POC, we'll use a simplified approach based on available metrics
            # In production, this would analyze quarterly revenue variance over time
            
            revenue_growth = fundamentals.get('revenue_growth')
            
            if revenue_growth is None:
                logger.warning("Cannot calculate revenue stability without growth data")
                return None, 0.0
            
            # Simplified stability assessment based on growth magnitude
            # Assumption: Very high growth rates are often less stable
            # Real implementation would use historical variance
            
            abs_growth = abs(revenue_growth)
            
            if abs_growth < 0.05:  # Very low growth - potentially stable but poor
                stability_score = 0.6
            elif abs_growth < 0.15:  # Moderate growth - likely stable
                stability_score = 0.8
            elif abs_growth < 0.30:  # High growth - moderately stable
                stability_score = 0.7
            elif abs_growth < 0.50:  # Very high growth - less stable
                stability_score = 0.5
            else:  # Extreme growth - likely unstable
                stability_score = 0.3
            
            # Negative growth reduces stability score
            if revenue_growth < 0:
                stability_score *= 0.7
            
            # Score stability (higher stability = higher score)
            thresholds = self.scoring_thresholds['revenue_stability']
            
            # Apply sector adjustments
            if sector == 'Energy':
                # Energy is inherently cyclical, lower stability expectations
                thresholds = {k: v * 0.7 for k, v in thresholds.items()}
            elif sector == 'Utilities':
                # Utilities should be very stable
                thresholds = {k: v * 1.1 for k, v in thresholds.items()}
            elif sector == 'Consumer Staples':
                # Consumer staples should be stable
                thresholds = {k: v * 1.05 for k, v in thresholds.items()}
            elif sector == 'Technology':
                # Tech can be more volatile, adjust expectations
                thresholds = {k: v * 0.9 for k, v in thresholds.items()}
            
            if stability_score > thresholds['excellent']:
                score = 90 + min(10, (stability_score - thresholds['excellent']) / (1.0 - thresholds['excellent']) * 10)
            elif stability_score > thresholds['good']:
                score = 70 + (stability_score - thresholds['good']) / (thresholds['excellent'] - thresholds['good']) * 20
            elif stability_score > thresholds['average']:
                score = 50 + (stability_score - thresholds['average']) / (thresholds['good'] - thresholds['average']) * 20
            elif stability_score > thresholds['poor']:
                score = 30 + (stability_score - thresholds['poor']) / (thresholds['average'] - thresholds['poor']) * 20
            elif stability_score > thresholds['very_poor']:
                score = 10 + (stability_score - thresholds['very_poor']) / (thresholds['poor'] - thresholds['very_poor']) * 20
            else:
                score = stability_score / thresholds['poor'] * 10
            
            return stability_score, max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating revenue stability: {str(e)}")
            return None, 0.0
    
    def calculate_forward_growth(self, fundamentals: Dict[str, Any], sector: Optional[str] = None) -> Tuple[Optional[float], float]:
        """
        Calculate and score forward growth expectations
        
        Note: This relies on analyst estimates if available in the data.
        For POC, we'll use a simplified approach.
        
        Returns:
            (forward_growth, forward_growth_score): Forward growth estimate and score (0-100)
        """
        try:
            # Look for forward-looking growth metrics
            # This would typically come from analyst estimates
            forward_pe = fundamentals.get('forward_pe')
            trailing_pe = fundamentals.get('pe_ratio')
            current_eps_growth = fundamentals.get('earnings_growth')
            
            # Simplified forward growth estimation
            forward_growth = None
            
            if forward_pe and trailing_pe and forward_pe > 0 and trailing_pe > 0:
                # If forward P/E is lower than trailing P/E, implies growth
                pe_ratio_change = (trailing_pe - forward_pe) / trailing_pe
                # This is a rough approximation of expected growth
                forward_growth = pe_ratio_change
                logger.info("Estimated forward growth from P/E ratio comparison")
            elif current_eps_growth is not None:
                # Use current EPS growth as proxy for forward growth (simplified)
                forward_growth = current_eps_growth * 0.8  # Assume some moderation
                logger.info("Used current EPS growth as forward growth proxy")
            else:
                logger.warning("No forward growth data available")
                return None, 0.0
            
            # Handle negative forward growth
            if forward_growth <= -0.3:  # -30% or worse
                return forward_growth, 0.0
            
            # Score forward growth
            thresholds = self.scoring_thresholds['forward_growth']
            
            # Apply sector adjustments
            if sector == 'Technology':
                # Higher forward growth expectations for tech
                thresholds = {k: v * 1.3 for k, v in thresholds.items()}
            elif sector == 'Healthcare':
                # Good forward growth expected from healthcare pipeline
                thresholds = {k: v * 1.1 for k, v in thresholds.items()}
            elif sector == 'Utilities':
                # Lower forward growth for utilities
                thresholds = {k: v * 0.4 for k, v in thresholds.items()}
            elif sector == 'Consumer Staples':
                # Lower forward growth for mature markets
                thresholds = {k: v * 0.6 for k, v in thresholds.items()}
            
            if forward_growth > thresholds['excellent']:
                score = 90 + min(10, (forward_growth - thresholds['excellent']) / thresholds['excellent'] * 15)
            elif forward_growth > thresholds['good']:
                score = 70 + (forward_growth - thresholds['good']) / (thresholds['excellent'] - thresholds['good']) * 20
            elif forward_growth > thresholds['average']:
                score = 50 + (forward_growth - thresholds['average']) / (thresholds['good'] - thresholds['average']) * 20
            elif forward_growth > thresholds['poor']:
                score = 30 + (forward_growth - thresholds['poor']) / (thresholds['average'] - thresholds['poor']) * 20
            elif forward_growth > thresholds['very_poor']:
                score = 10 + (forward_growth - thresholds['very_poor']) / (thresholds['poor'] - thresholds['very_poor']) * 20
            else:
                score = max(0, 10 + forward_growth * 30)
            
            return forward_growth, max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating forward growth: {str(e)}")
            return None, 0.0
    
    def calculate_growth_metrics(self, symbol: str, db: DatabaseManager) -> Optional[GrowthMetrics]:
        """
        Calculate all growth metrics for a stock
        
        Args:
            symbol: Stock symbol
            db: Database manager instance
            
        Returns:
            GrowthMetrics object or None if insufficient data
        """
        try:
            # Get latest fundamental data from database
            fundamentals = db.get_latest_fundamentals(symbol)
            stock_info = db.get_stock_info(symbol)
            
            if not fundamentals:
                logger.warning(f"No fundamental data found for {symbol}")
                return None
            
            sector = stock_info.get('sector') if stock_info else None
            logger.info(f"Calculating growth metrics for {symbol} (Sector: {sector})")
            
            # Calculate individual metrics with sector adjustments
            revenue_growth, revenue_growth_score = self.calculate_revenue_growth(fundamentals, sector)
            eps_growth, eps_growth_score = self.calculate_eps_growth(fundamentals, sector)
            revenue_stability, revenue_stability_score = self.calculate_revenue_stability(fundamentals, sector)
            forward_growth, forward_growth_score = self.calculate_forward_growth(fundamentals, sector)
            
            # Get sector-adjusted weights
            component_weights = self.get_sector_adjusted_weights(sector)
            
            # Calculate weighted composite score
            scores = [revenue_growth_score, eps_growth_score, revenue_stability_score, forward_growth_score]
            weights = list(component_weights.values())
            
            # Only include valid scores (non-zero) in composite
            valid_scores = [(score, weight) for score, weight in zip(scores, weights) if score > 0]
            
            if not valid_scores:
                logger.warning(f"No valid growth metrics for {symbol}")
                return None
            
            # Recalculate weights for available metrics
            total_weight = sum(weight for _, weight in valid_scores)
            normalized_scores = [(score * weight / total_weight) for score, weight in valid_scores]
            
            growth_score = sum(normalized_scores)
            data_quality_score = len(valid_scores) / len(scores)  # Data quality based on completeness
            
            # Data quality assessment
            data_quality = fundamentals.get('quality_score', 1.0)
            
            return GrowthMetrics(
                symbol=symbol,
                calculation_date=date.today(),
                revenue_growth=revenue_growth,
                eps_growth=eps_growth,
                revenue_stability=revenue_stability,
                forward_growth=forward_growth,
                revenue_growth_score=revenue_growth_score,
                eps_growth_score=eps_growth_score,
                revenue_stability_score=revenue_stability_score,
                forward_growth_score=forward_growth_score,
                growth_score=growth_score,
                data_quality_score=data_quality_score,
                sector=sector,
                data_quality=data_quality
            )
            
        except Exception as e:
            logger.error(f"Error calculating growth metrics for {symbol}: {str(e)}")
            return None
    
    def calculate_batch_growth(self, symbols: List[str], db: DatabaseManager) -> Dict[str, GrowthMetrics]:
        """
        Calculate growth metrics for multiple stocks
        
        Args:
            symbols: List of stock symbols
            db: Database manager instance
            
        Returns:
            Dictionary mapping symbols to GrowthMetrics
        """
        results = {}
        
        for symbol in symbols:
            try:
                metrics = self.calculate_growth_metrics(symbol, db)
                if metrics:
                    results[symbol] = metrics
                    logger.info(f"✅ Calculated growth metrics for {symbol}: {metrics.growth_score:.1f}")
                else:
                    logger.warning(f"❌ Failed to calculate growth metrics for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")
                continue
        
        logger.info(f"Completed growth analysis for {len(results)}/{len(symbols)} stocks")
        return results
    
    def save_growth_metrics(self, metrics: GrowthMetrics, db: DatabaseManager):
        """
        Save growth metrics to calculated_metrics table
        
        Args:
            metrics: GrowthMetrics object
            db: Database manager instance
        """
        try:
            cursor = db.connection.cursor()
            
            sql = '''
                INSERT OR REPLACE INTO calculated_metrics
                (symbol, calculation_date, growth_score, methodology_version)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(symbol, calculation_date) DO UPDATE SET
                    growth_score = excluded.growth_score,
                    methodology_version = excluded.methodology_version
            '''
            
            cursor.execute(sql, (
                metrics.symbol,
                metrics.calculation_date,
                metrics.growth_score,
                'v1.0'
            ))
            
            db.connection.commit()
            cursor.close()
            
            logger.info(f"Saved growth metrics for {metrics.symbol}")
            
        except Exception as e:
            logger.error(f"Error saving growth metrics for {metrics.symbol}: {str(e)}")

# Convenience functions
def calculate_single_growth(symbol: str, config_path: Optional[str] = None) -> Optional[GrowthMetrics]:
    """Calculate growth metrics for a single stock"""
    calculator = GrowthCalculator(config_path)
    
    from src.data.database import get_database_connection
    db = get_database_connection(config_path)
    
    try:
        return calculator.calculate_growth_metrics(symbol, db)
    finally:
        db.close()

def calculate_all_growth(config_path: Optional[str] = None) -> Dict[str, GrowthMetrics]:
    """Calculate growth metrics for all stocks in database"""
    calculator = GrowthCalculator(config_path)
    
    from src.data.database import get_database_connection
    db = get_database_connection(config_path)
    
    try:
        symbols = db.get_all_stocks()
        return calculator.calculate_batch_growth(symbols, db)
    finally:
        db.close()