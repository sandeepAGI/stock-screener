"""
Fundamental Analysis Calculators - 40% Weight Component

Implements core fundamental metrics for stock valuation:
- P/E Ratio analysis with sector normalization
- EV/EBITDA calculation for enterprise value assessment
- PEG Ratio for growth-adjusted valuation
- Free Cash Flow Yield for cash generation analysis

Each metric is scored 0-100 and combined into composite fundamental score.
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
from src.data.data_versioning import DataVersionManager

logger = logging.getLogger(__name__)

@dataclass
class FundamentalMetrics:
    """Container for fundamental analysis results"""
    symbol: str
    calculation_date: date
    
    # Raw metrics
    pe_ratio: Optional[float]
    ev_ebitda: Optional[float]
    peg_ratio: Optional[float]
    fcf_yield: Optional[float]
    
    # Scored metrics (0-100)
    pe_score: float
    ev_ebitda_score: float
    peg_score: float
    fcf_yield_score: float
    
    # Composite score
    fundamental_score: float
    data_quality_score: float
    
    # Metadata
    sector: Optional[str]
    data_quality: float
    
    # Data versioning and staleness indicators
    data_age_days: Optional[float]
    data_freshness_level: Optional[str]
    staleness_impact: float
    staleness_warnings: List[str]
    data_version_id: Optional[str]

class FundamentalCalculator:
    """
    Calculates and scores fundamental analysis metrics
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = load_config(config_path)
        self.weights = self.config.get('methodology', {}).get('weights', {})
        self.sector_engine = SectorAdjustmentEngine()
        
        # Fundamental component weights (sum to 100%)
        self.base_component_weights = {
            'pe_ratio': 0.30,      # 30% - Most important valuation metric
            'ev_ebitda': 0.25,     # 25% - Enterprise value assessment
            'peg_ratio': 0.25,     # 25% - Growth-adjusted valuation
            'fcf_yield': 0.20      # 20% - Cash generation quality
        }
        
        # Scoring thresholds for normalization
        self.scoring_thresholds = {
            'pe_ratio': {
                'excellent': 15,    # P/E < 15 = 90-100 points
                'good': 20,         # P/E < 20 = 70-89 points
                'average': 25,      # P/E < 25 = 50-69 points
                'poor': 35,         # P/E < 35 = 30-49 points
                'very_poor': 50     # P/E >= 50 = 0-29 points
            },
            'ev_ebitda': {
                'excellent': 10,    # EV/EBITDA < 10 = 90-100 points
                'good': 15,         # EV/EBITDA < 15 = 70-89 points
                'average': 20,      # EV/EBITDA < 20 = 50-69 points
                'poor': 30,         # EV/EBITDA < 30 = 30-49 points
                'very_poor': 40     # EV/EBITDA >= 40 = 0-29 points
            },
            'peg_ratio': {
                'excellent': 0.5,   # PEG < 0.5 = 90-100 points
                'good': 1.0,        # PEG < 1.0 = 70-89 points
                'average': 1.5,     # PEG < 1.5 = 50-69 points
                'poor': 2.0,        # PEG < 2.0 = 30-49 points
                'very_poor': 3.0    # PEG >= 3.0 = 0-29 points
            },
            'fcf_yield': {
                'excellent': 0.08,  # FCF Yield > 8% = 90-100 points
                'good': 0.05,       # FCF Yield > 5% = 70-89 points
                'average': 0.03,    # FCF Yield > 3% = 50-69 points
                'poor': 0.01,       # FCF Yield > 1% = 30-49 points
                'very_poor': 0.0    # FCF Yield <= 0% = 0-29 points
            }
        }
    
    def get_sector_adjusted_weights(self, sector: Optional[str]) -> Dict[str, float]:
        """
        Get sector-adjusted component weights
        
        Args:
            sector: Sector name
            
        Returns:
            Adjusted component weights dictionary
        """
        weights = self.base_component_weights.copy()
        
        # Apply FCF focus adjustment
        fcf_adjustment = self.sector_engine.get_fcf_weight_adjustment(sector)
        
        if fcf_adjustment != 1.0:
            # Adjust FCF weight and rebalance others proportionally
            old_fcf_weight = weights['fcf_yield']
            new_fcf_weight = old_fcf_weight * fcf_adjustment
            
            # Ensure weights don't exceed reasonable bounds
            new_fcf_weight = max(0.10, min(0.40, new_fcf_weight))
            
            # Calculate adjustment factor for other weights
            remaining_weight = 1.0 - new_fcf_weight
            other_weight_sum = sum(w for k, w in weights.items() if k != 'fcf_yield')
            adjustment_factor = remaining_weight / other_weight_sum
            
            # Apply adjustments
            for key in weights:
                if key == 'fcf_yield':
                    weights[key] = new_fcf_weight
                else:
                    weights[key] *= adjustment_factor
        
        return weights
        
    def calculate_pe_ratio(self, fundamentals: Dict[str, Any], sector: Optional[str] = None) -> Tuple[Optional[float], float]:
        """
        Calculate and score P/E ratio with sector adjustments
        
        Returns:
            (pe_ratio, pe_score): Raw P/E ratio and normalized score (0-100)
        """
        try:
            pe_ratio = fundamentals.get('pe_ratio')
            
            if pe_ratio is None or pe_ratio <= 0:
                logger.warning("Invalid P/E ratio data")
                return None, 0.0
            
            # Get sector-adjusted thresholds
            adjusted_thresholds = self.sector_engine.adjust_thresholds(self.scoring_thresholds, sector)
            thresholds = adjusted_thresholds['pe_ratio']
            
            if pe_ratio < thresholds['excellent']:
                score = 90 + (thresholds['excellent'] - pe_ratio) / thresholds['excellent'] * 10
                score = min(100, max(90, score))
            elif pe_ratio < thresholds['good']:
                score = 70 + (thresholds['good'] - pe_ratio) / (thresholds['good'] - thresholds['excellent']) * 20
            elif pe_ratio < thresholds['average']:
                score = 50 + (thresholds['average'] - pe_ratio) / (thresholds['average'] - thresholds['good']) * 20
            elif pe_ratio < thresholds['poor']:
                score = 30 + (thresholds['poor'] - pe_ratio) / (thresholds['poor'] - thresholds['average']) * 20
            elif pe_ratio < thresholds['very_poor']:
                score = 10 + (thresholds['very_poor'] - pe_ratio) / (thresholds['very_poor'] - thresholds['poor']) * 20
            else:
                # Very high P/E ratios get very low scores
                score = max(0, 10 - (pe_ratio - thresholds['very_poor']) / 10)
            
            return pe_ratio, max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating P/E ratio: {str(e)}")
            return None, 0.0
    
    def calculate_ev_ebitda(self, fundamentals: Dict[str, Any], sector: Optional[str] = None) -> Tuple[Optional[float], float]:
        """
        Calculate and score EV/EBITDA ratio with sector adjustments
        
        Returns:
            (ev_ebitda, ev_ebitda_score): Raw EV/EBITDA and normalized score (0-100)
        """
        try:
            ev_ebitda = fundamentals.get('ev_to_ebitda')
            
            if ev_ebitda is None or ev_ebitda <= 0:
                # Try to calculate from components if available
                enterprise_value = fundamentals.get('enterprise_value')
                # Note: EBITDA not directly available from yfinance, using approximation
                operating_cash_flow = fundamentals.get('operating_cash_flow')
                
                if enterprise_value and operating_cash_flow and operating_cash_flow > 0:
                    # Approximate EV/EBITDA using EV/Operating Cash Flow as proxy
                    ev_ebitda = enterprise_value / operating_cash_flow
                    logger.info("Calculated EV/EBITDA using operating cash flow approximation")
                else:
                    logger.warning("Insufficient data for EV/EBITDA calculation")
                    return None, 0.0
            
            # Get sector-adjusted thresholds
            adjusted_thresholds = self.sector_engine.adjust_thresholds(self.scoring_thresholds, sector)
            thresholds = adjusted_thresholds['ev_ebitda']
            
            if ev_ebitda < thresholds['excellent']:
                score = 90 + (thresholds['excellent'] - ev_ebitda) / thresholds['excellent'] * 10
                score = min(100, max(90, score))
            elif ev_ebitda < thresholds['good']:
                score = 70 + (thresholds['good'] - ev_ebitda) / (thresholds['good'] - thresholds['excellent']) * 20
            elif ev_ebitda < thresholds['average']:
                score = 50 + (thresholds['average'] - ev_ebitda) / (thresholds['average'] - thresholds['good']) * 20
            elif ev_ebitda < thresholds['poor']:
                score = 30 + (thresholds['poor'] - ev_ebitda) / (thresholds['poor'] - thresholds['average']) * 20
            elif ev_ebitda < thresholds['very_poor']:
                score = 10 + (thresholds['very_poor'] - ev_ebitda) / (thresholds['very_poor'] - thresholds['poor']) * 20
            else:
                score = max(0, 10 - (ev_ebitda - thresholds['very_poor']) / 20)
            
            return ev_ebitda, max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating EV/EBITDA: {str(e)}")
            return None, 0.0
    
    def calculate_peg_ratio(self, fundamentals: Dict[str, Any], sector: Optional[str] = None) -> Tuple[Optional[float], float]:
        """
        Calculate and score PEG ratio (P/E to Growth) with sector adjustments
        
        Returns:
            (peg_ratio, peg_score): Raw PEG ratio and normalized score (0-100)
        """
        try:
            peg_ratio = fundamentals.get('peg_ratio')
            
            if peg_ratio is None:
                # Try to calculate from P/E and growth rate
                pe_ratio = fundamentals.get('pe_ratio')
                earnings_growth = fundamentals.get('earnings_growth')
                
                if pe_ratio and earnings_growth and earnings_growth > 0:
                    # Convert growth rate to percentage if needed
                    growth_rate_pct = earnings_growth * 100 if earnings_growth < 1 else earnings_growth
                    if growth_rate_pct > 0:
                        peg_ratio = pe_ratio / growth_rate_pct
                        logger.info("Calculated PEG ratio from P/E and earnings growth")
                    else:
                        logger.warning("Invalid earnings growth rate for PEG calculation")
                        return None, 0.0
                else:
                    logger.warning("Insufficient data for PEG ratio calculation")
                    return None, 0.0
            
            if peg_ratio <= 0:
                return None, 0.0
            
            # Get sector-adjusted thresholds
            adjusted_thresholds = self.sector_engine.adjust_thresholds(self.scoring_thresholds, sector)
            thresholds = adjusted_thresholds['peg_ratio']
            
            if peg_ratio < thresholds['excellent']:
                # Very low PEG could be suspicious, cap the score boost
                score = 90 + min(10, (thresholds['excellent'] - peg_ratio) / thresholds['excellent'] * 15)
            elif peg_ratio < thresholds['good']:
                score = 70 + (thresholds['good'] - peg_ratio) / (thresholds['good'] - thresholds['excellent']) * 20
            elif peg_ratio < thresholds['average']:
                score = 50 + (thresholds['average'] - peg_ratio) / (thresholds['average'] - thresholds['good']) * 20
            elif peg_ratio < thresholds['poor']:
                score = 30 + (thresholds['poor'] - peg_ratio) / (thresholds['poor'] - thresholds['average']) * 20
            elif peg_ratio < thresholds['very_poor']:
                score = 10 + (thresholds['very_poor'] - peg_ratio) / (thresholds['very_poor'] - thresholds['poor']) * 20
            else:
                score = max(0, 10 - (peg_ratio - thresholds['very_poor']) / 2)
            
            return peg_ratio, max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating PEG ratio: {str(e)}")
            return None, 0.0
    
    def calculate_fcf_yield(self, fundamentals: Dict[str, Any], sector: Optional[str] = None) -> Tuple[Optional[float], float]:
        """
        Calculate and score Free Cash Flow Yield (no sector threshold adjustment - uses weighting instead)
        
        Returns:
            (fcf_yield, fcf_yield_score): Raw FCF yield and normalized score (0-100)
        """
        try:
            free_cash_flow = fundamentals.get('free_cash_flow')
            market_cap = fundamentals.get('market_cap')
            
            if not free_cash_flow or not market_cap or market_cap <= 0:
                logger.warning("Insufficient data for FCF yield calculation")
                return None, 0.0
            
            # Calculate FCF yield as percentage
            fcf_yield = free_cash_flow / market_cap
            
            # Handle negative FCF
            if fcf_yield <= 0:
                return fcf_yield, 0.0
            
            # Score FCF yield (higher is better)
            thresholds = self.scoring_thresholds['fcf_yield']
            
            if fcf_yield > thresholds['excellent']:
                score = 90 + min(10, (fcf_yield - thresholds['excellent']) / thresholds['excellent'] * 20)
            elif fcf_yield > thresholds['good']:
                score = 70 + (fcf_yield - thresholds['good']) / (thresholds['excellent'] - thresholds['good']) * 20
            elif fcf_yield > thresholds['average']:
                score = 50 + (fcf_yield - thresholds['average']) / (thresholds['good'] - thresholds['average']) * 20
            elif fcf_yield > thresholds['poor']:
                score = 30 + (fcf_yield - thresholds['poor']) / (thresholds['average'] - thresholds['poor']) * 20
            elif fcf_yield > thresholds['very_poor']:
                score = 10 + (fcf_yield - thresholds['very_poor']) / (thresholds['poor'] - thresholds['very_poor']) * 20
            else:
                score = max(0, fcf_yield / thresholds['poor'] * 10)
            
            return fcf_yield, max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating FCF yield: {str(e)}")
            return None, 0.0
    
    def calculate_fundamental_metrics(self, symbol: str, db: DatabaseManager, max_age_days: Optional[int] = None) -> Optional[FundamentalMetrics]:
        """
        Calculate all fundamental metrics for a stock with data versioning and staleness indicators
        
        Args:
            symbol: Stock symbol
            db: Database manager instance
            max_age_days: Maximum allowed age of data in days (None = no limit)
            
        Returns:
            FundamentalMetrics object or None if insufficient data
        """
        try:
            # Initialize data version manager
            version_manager = DataVersionManager(db)
            
            # Get versioned fundamental data
            versioned_data = version_manager.get_versioned_fundamentals(symbol, max_age_days)
            
            if not versioned_data or not versioned_data.data:
                logger.warning(f"No fundamental data found for {symbol}")
                return None
            
            fundamentals = versioned_data.data
            version_info = versioned_data.version_info
            staleness_impact = versioned_data.staleness_impact
            
            # Get stock info for sector
            stock_info = db.get_stock_info(symbol)
            sector = stock_info.get('sector') if stock_info else None
            
            logger.info(f"Calculating fundamental metrics for {symbol} (Sector: {sector}, Data age: {version_info.age_days:.1f} days)")
            
            # Log staleness warnings
            for warning in version_info.staleness_warnings:
                logger.warning(f"{symbol}: {warning}")
            
            # Calculate individual metrics with sector adjustments
            pe_ratio, pe_score = self.calculate_pe_ratio(fundamentals, sector)
            ev_ebitda, ev_ebitda_score = self.calculate_ev_ebitda(fundamentals, sector)
            peg_ratio, peg_score = self.calculate_peg_ratio(fundamentals, sector)
            fcf_yield, fcf_yield_score = self.calculate_fcf_yield(fundamentals, sector)
            
            # Apply staleness impact to scores
            pe_score *= staleness_impact
            ev_ebitda_score *= staleness_impact
            peg_score *= staleness_impact
            fcf_yield_score *= staleness_impact
            
            # Get sector-adjusted weights
            component_weights = self.get_sector_adjusted_weights(sector)
            
            # Calculate weighted composite score
            scores = [pe_score, ev_ebitda_score, peg_score, fcf_yield_score]
            weights = list(component_weights.values())
            
            # Only include valid scores (non-zero) in composite
            valid_scores = [(score, weight) for score, weight in zip(scores, weights) if score > 0]
            
            if not valid_scores:
                logger.warning(f"No valid fundamental metrics for {symbol}")
                return None
            
            # Recalculate weights for available metrics
            total_weight = sum(weight for _, weight in valid_scores)
            normalized_scores = [(score * weight / total_weight) for score, weight in valid_scores]
            
            fundamental_score = sum(normalized_scores)
            
            # Adjust data quality score based on completeness and staleness
            completeness_score = len(valid_scores) / len(scores)
            data_quality_score = completeness_score * version_info.quality_score
            
            # Traditional data quality assessment
            data_quality = fundamentals.get('quality_score', 1.0) * staleness_impact
            
            return FundamentalMetrics(
                symbol=symbol,
                calculation_date=date.today(),
                pe_ratio=pe_ratio,
                ev_ebitda=ev_ebitda,
                peg_ratio=peg_ratio,
                fcf_yield=fcf_yield,
                pe_score=pe_score,
                ev_ebitda_score=ev_ebitda_score,
                peg_score=peg_score,
                fcf_yield_score=fcf_yield_score,
                fundamental_score=fundamental_score,
                data_quality_score=data_quality_score,
                sector=sector,
                data_quality=data_quality,
                # Data versioning information
                data_age_days=version_info.age_days,
                data_freshness_level=version_info.freshness_level.value,
                staleness_impact=staleness_impact,
                staleness_warnings=version_info.staleness_warnings,
                data_version_id=version_info.version_id
            )
            
        except Exception as e:
            logger.error(f"Error calculating fundamental metrics for {symbol}: {str(e)}")
            return None
    
    def calculate_batch_fundamentals(self, symbols: List[str], db: DatabaseManager) -> Dict[str, FundamentalMetrics]:
        """
        Calculate fundamental metrics for multiple stocks
        
        Args:
            symbols: List of stock symbols
            db: Database manager instance
            
        Returns:
            Dictionary mapping symbols to FundamentalMetrics
        """
        results = {}
        
        for symbol in symbols:
            try:
                metrics = self.calculate_fundamental_metrics(symbol, db)
                if metrics:
                    results[symbol] = metrics
                    logger.info(f"✅ Calculated fundamental metrics for {symbol}: {metrics.fundamental_score:.1f}")
                else:
                    logger.warning(f"❌ Failed to calculate metrics for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")
                continue
        
        logger.info(f"Completed fundamental analysis for {len(results)}/{len(symbols)} stocks")
        return results
    
    def save_fundamental_metrics(self, metrics: FundamentalMetrics, db: DatabaseManager):
        """
        Save fundamental metrics to calculated_metrics table
        
        Args:
            metrics: FundamentalMetrics object
            db: Database manager instance
        """
        try:
            cursor = db.connection.cursor()
            
            sql = '''
                INSERT OR REPLACE INTO calculated_metrics
                (symbol, calculation_date, fundamental_score, methodology_version)
                VALUES (?, ?, ?, ?)
            '''
            
            cursor.execute(sql, (
                metrics.symbol,
                metrics.calculation_date,
                metrics.fundamental_score,
                'v1.0'
            ))
            
            db.connection.commit()
            cursor.close()
            
            logger.info(f"Saved fundamental metrics for {metrics.symbol}")
            
        except Exception as e:
            logger.error(f"Error saving fundamental metrics for {metrics.symbol}: {str(e)}")

# Convenience functions
def calculate_single_fundamental(symbol: str, config_path: Optional[str] = None) -> Optional[FundamentalMetrics]:
    """Calculate fundamental metrics for a single stock"""
    calculator = FundamentalCalculator(config_path)
    
    from src.data.database import get_database_connection
    db = get_database_connection(config_path)
    
    try:
        return calculator.calculate_fundamental_metrics(symbol, db)
    finally:
        db.close()

def calculate_all_fundamentals(config_path: Optional[str] = None) -> Dict[str, FundamentalMetrics]:
    """Calculate fundamental metrics for all stocks in database"""
    calculator = FundamentalCalculator(config_path)
    
    from src.data.database import get_database_connection
    db = get_database_connection(config_path)
    
    try:
        symbols = db.get_all_stocks()
        return calculator.calculate_batch_fundamentals(symbols, db)
    finally:
        db.close()