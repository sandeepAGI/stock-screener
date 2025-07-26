"""
Quality Metrics Calculators - 25% Weight Component

Implements financial quality assessment metrics:
- Return on Equity (ROE) - Shareholder return efficiency
- Return on Invested Capital (ROIC) - Capital allocation efficiency  
- Debt-to-Equity Ratio - Financial leverage assessment
- Current Ratio - Short-term liquidity strength

Each metric is scored 0-100 with sector adjustments, then combined into composite quality score.
Quality metrics help identify financially sound companies vs. those with structural weaknesses.
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
class QualityMetrics:
    """Container for quality analysis results"""
    symbol: str
    calculation_date: date
    
    # Raw metrics
    roe: Optional[float]
    roic: Optional[float]  # Will need to calculate this
    debt_to_equity: Optional[float]
    current_ratio: Optional[float]
    
    # Scored metrics (0-100)
    roe_score: float
    roic_score: float
    debt_to_equity_score: float
    current_ratio_score: float
    
    # Composite score
    quality_score: float
    data_quality_score: float
    
    # Metadata
    sector: Optional[str]
    data_quality: float

class QualityCalculator:
    """
    Calculates and scores financial quality metrics
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = load_config(config_path)
        self.sector_engine = SectorAdjustmentEngine()
        
        # Quality component weights (sum to 100%)
        self.base_component_weights = {
            'roe': 0.35,              # 35% - Most important profitability metric
            'roic': 0.30,             # 30% - Capital allocation efficiency
            'debt_to_equity': 0.20,   # 20% - Financial leverage risk
            'current_ratio': 0.15     # 15% - Liquidity strength
        }
        
        # Base scoring thresholds for quality metrics
        self.scoring_thresholds = {
            'roe': {
                'excellent': 0.20,     # ROE > 20% = 90-100 points
                'good': 0.15,          # ROE > 15% = 70-89 points
                'average': 0.10,       # ROE > 10% = 50-69 points
                'poor': 0.05,          # ROE > 5% = 30-49 points
                'very_poor': 0.0       # ROE <= 0% = 0-29 points
            },
            'roic': {
                'excellent': 0.15,     # ROIC > 15% = 90-100 points
                'good': 0.12,          # ROIC > 12% = 70-89 points
                'average': 0.08,       # ROIC > 8% = 50-69 points
                'poor': 0.04,          # ROIC > 4% = 30-49 points
                'very_poor': 0.0       # ROIC <= 0% = 0-29 points
            },
            'debt_to_equity': {
                'excellent': 0.3,      # D/E < 0.3 = 90-100 points (lower is better)
                'good': 0.5,           # D/E < 0.5 = 70-89 points
                'average': 1.0,        # D/E < 1.0 = 50-69 points
                'poor': 2.0,           # D/E < 2.0 = 30-49 points
                'very_poor': 4.0       # D/E >= 4.0 = 0-29 points
            },
            'current_ratio': {
                'excellent': 2.5,      # Current Ratio > 2.5 = 90-100 points  
                'good': 2.0,           # Current Ratio > 2.0 = 70-89 points
                'average': 1.5,        # Current Ratio > 1.5 = 50-69 points
                'poor': 1.0,           # Current Ratio > 1.0 = 30-49 points
                'very_poor': 0.8       # Current Ratio <= 0.8 = 0-29 points
            }
        }
    
    def get_sector_adjusted_weights(self, sector: Optional[str]) -> Dict[str, float]:
        """
        Get sector-adjusted component weights for quality metrics
        
        Args:
            sector: Sector name
            
        Returns:
            Adjusted component weights dictionary
        """
        weights = self.base_component_weights.copy()
        
        # Sector-specific weight adjustments
        if sector == 'Financials':
            # Banks: ROE more important, debt ratios less relevant
            weights['roe'] = 0.50      # +15% (banking profitability key)
            weights['roic'] = 0.25     # -5% (less relevant for banks)
            weights['debt_to_equity'] = 0.10  # -10% (leverage is operational)
            weights['current_ratio'] = 0.15   # Same (liquidity still matters)
            
        elif sector == 'Real Estate':
            # REITs: Different capital structure, focus on operational efficiency
            weights['roe'] = 0.25      # -10% (asset-heavy model)
            weights['roic'] = 0.40     # +10% (asset utilization critical)
            weights['debt_to_equity'] = 0.25  # +5% (leverage common but monitored)
            weights['current_ratio'] = 0.10   # -5% (different liquidity needs)
            
        elif sector == 'Energy':
            # Energy: Capital intensive, cyclical, debt management crucial
            weights['roe'] = 0.30      # -5% (cyclical earnings)
            weights['roic'] = 0.35     # +5% (capital allocation critical)
            weights['debt_to_equity'] = 0.25  # +5% (debt risk in downturns)
            weights['current_ratio'] = 0.10   # -5% (working capital varies)
            
        elif sector == 'Utilities':
            # Utilities: Regulated returns, high debt normal, steady operations
            weights['roe'] = 0.25      # -10% (regulated returns)
            weights['roic'] = 0.25     # -5% (regulated asset base)
            weights['debt_to_equity'] = 0.35  # +15% (debt management crucial)
            weights['current_ratio'] = 0.15   # Same (steady cash flows)
            
        elif sector == 'Technology':
            # Tech: High ROE/ROIC potential, typically low debt, strong liquidity
            weights['roe'] = 0.40      # +5% (scalability drives ROE)
            weights['roic'] = 0.35     # +5% (R&D capital allocation key)
            weights['debt_to_equity'] = 0.15  # -5% (typically low debt)
            weights['current_ratio'] = 0.10   # -5% (strong cash generation)
        
        return weights
    
    def calculate_roe(self, fundamentals: Dict[str, Any], sector: Optional[str] = None) -> Tuple[Optional[float], float]:
        """
        Calculate and score Return on Equity
        
        Returns:
            (roe, roe_score): Raw ROE and normalized score (0-100)
        """
        try:
            roe = fundamentals.get('return_on_equity')
            
            if roe is None:
                # Try to calculate from net income and shareholders equity
                net_income = fundamentals.get('net_income')
                shareholders_equity = fundamentals.get('shareholders_equity')
                
                if net_income and shareholders_equity and shareholders_equity > 0:
                    roe = net_income / shareholders_equity
                    logger.info("Calculated ROE from net income and shareholders equity")
                else:
                    logger.warning("Insufficient data for ROE calculation")
                    return None, 0.0
            
            # Handle negative equity (bankruptcy risk)
            if roe <= -0.5:  # ROE < -50% indicates severe problems
                return roe, 0.0
            
            # Score ROE (higher is better)
            thresholds = self.scoring_thresholds['roe']
            
            # Apply sector adjustments to thresholds
            if sector == 'Utilities':
                # Lower ROE expectations for regulated utilities
                thresholds = {k: v * 0.8 for k, v in thresholds.items()}
            elif sector == 'Technology':
                # Higher ROE expectations for scalable tech businesses
                thresholds = {k: v * 1.2 for k, v in thresholds.items()}
            elif sector == 'Financials':
                # Higher ROE expectations for banks (leverage amplifies returns)
                thresholds = {k: v * 1.3 for k, v in thresholds.items()}
            
            if roe > thresholds['excellent']:
                score = 90 + min(10, (roe - thresholds['excellent']) / thresholds['excellent'] * 20)
            elif roe > thresholds['good']:
                score = 70 + (roe - thresholds['good']) / (thresholds['excellent'] - thresholds['good']) * 20
            elif roe > thresholds['average']:
                score = 50 + (roe - thresholds['average']) / (thresholds['good'] - thresholds['average']) * 20
            elif roe > thresholds['poor']:
                score = 30 + (roe - thresholds['poor']) / (thresholds['average'] - thresholds['poor']) * 20
            elif roe > thresholds['very_poor']:
                score = 10 + (roe - thresholds['very_poor']) / (thresholds['poor'] - thresholds['very_poor']) * 20
            else:
                score = max(0, 10 + roe * 20)  # Negative ROE gets very low score
            
            return roe, max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating ROE: {str(e)}")
            return None, 0.0
    
    def calculate_roic(self, fundamentals: Dict[str, Any], sector: Optional[str] = None) -> Tuple[Optional[float], float]:
        """
        Calculate and score Return on Invested Capital
        
        ROIC = Operating Income / Invested Capital
        Where Invested Capital = Total Assets - Current Liabilities
        
        Returns:
            (roic, roic_score): Raw ROIC and normalized score (0-100)
        """
        try:
            # ROIC not directly available, need to calculate
            net_income = fundamentals.get('net_income')
            total_assets = fundamentals.get('total_assets')
            # Current liabilities not directly available, use total debt as approximation
            total_debt = fundamentals.get('total_debt')
            
            if not all([net_income, total_assets]):
                logger.warning("Insufficient data for ROIC calculation")
                return None, 0.0
            
            # Approximate ROIC calculation
            # ROIC ≈ Net Income / (Total Assets - Total Debt)
            invested_capital = total_assets - (total_debt or 0)
            
            if invested_capital <= 0:
                logger.warning("Invalid invested capital for ROIC calculation")
                return None, 0.0
            
            roic = net_income / invested_capital
            
            # Handle extreme negative ROIC
            if roic <= -0.3:  # ROIC < -30% indicates severe capital destruction
                return roic, 0.0
            
            # Score ROIC (higher is better)
            thresholds = self.scoring_thresholds['roic']
            
            # Apply sector adjustments
            if sector == 'Real Estate':
                # Lower ROIC expectations for asset-heavy REITs
                thresholds = {k: v * 0.7 for k, v in thresholds.items()}
            elif sector == 'Technology':
                # Higher ROIC expectations for asset-light tech
                thresholds = {k: v * 1.3 for k, v in thresholds.items()}
            elif sector == 'Utilities':
                # Lower ROIC for regulated utilities with mandated asset investments
                thresholds = {k: v * 0.6 for k, v in thresholds.items()}
            
            if roic > thresholds['excellent']:
                score = 90 + min(10, (roic - thresholds['excellent']) / thresholds['excellent'] * 20)
            elif roic > thresholds['good']:
                score = 70 + (roic - thresholds['good']) / (thresholds['excellent'] - thresholds['good']) * 20
            elif roic > thresholds['average']:
                score = 50 + (roic - thresholds['average']) / (thresholds['good'] - thresholds['average']) * 20
            elif roic > thresholds['poor']:
                score = 30 + (roic - thresholds['poor']) / (thresholds['average'] - thresholds['poor']) * 20
            elif roic > thresholds['very_poor']:
                score = 10 + (roic - thresholds['very_poor']) / (thresholds['poor'] - thresholds['very_poor']) * 20
            else:
                score = max(0, 10 + roic * 30)  # Negative ROIC gets very low score
            
            return roic, max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating ROIC: {str(e)}")
            return None, 0.0
    
    def calculate_debt_to_equity(self, fundamentals: Dict[str, Any], sector: Optional[str] = None) -> Tuple[Optional[float], float]:
        """
        Calculate and score Debt-to-Equity ratio
        
        Returns:
            (debt_to_equity, debt_score): Raw D/E ratio and normalized score (0-100)
        """
        try:
            debt_to_equity = fundamentals.get('debt_to_equity')
            
            if debt_to_equity is None:
                # Calculate from total debt and shareholders equity
                total_debt = fundamentals.get('total_debt')
                shareholders_equity = fundamentals.get('shareholders_equity')
                
                if total_debt is not None and shareholders_equity and shareholders_equity > 0:
                    debt_to_equity = total_debt / shareholders_equity
                    logger.info("Calculated debt-to-equity from balance sheet components")
                else:
                    logger.warning("Insufficient data for debt-to-equity calculation")
                    return None, 0.0
            
            # Handle negative equity (distressed situation)
            if debt_to_equity < 0:
                return debt_to_equity, 0.0
            
            # Score debt-to-equity (lower is better for most sectors)
            thresholds = self.scoring_thresholds['debt_to_equity']
            
            # Apply sector adjustments
            if sector == 'Utilities':
                # Higher debt tolerance for regulated utilities
                thresholds = {k: v * 2.0 for k, v in thresholds.items()}
            elif sector == 'Real Estate':
                # Higher debt tolerance for REITs (leverage is common)
                thresholds = {k: v * 1.8 for k, v in thresholds.items()}
            elif sector == 'Financials':
                # Banks have different capital structure, less relevant
                thresholds = {k: v * 3.0 for k, v in thresholds.items()}
            elif sector == 'Technology':
                # Lower debt tolerance for tech (should be self-funding)
                thresholds = {k: v * 0.8 for k, v in thresholds.items()}
            
            if debt_to_equity < thresholds['excellent']:
                score = 90 + min(10, (thresholds['excellent'] - debt_to_equity) / thresholds['excellent'] * 20)
            elif debt_to_equity < thresholds['good']:
                score = 70 + (thresholds['good'] - debt_to_equity) / (thresholds['good'] - thresholds['excellent']) * 20
            elif debt_to_equity < thresholds['average']:
                score = 50 + (thresholds['average'] - debt_to_equity) / (thresholds['average'] - thresholds['good']) * 20
            elif debt_to_equity < thresholds['poor']:
                score = 30 + (thresholds['poor'] - debt_to_equity) / (thresholds['poor'] - thresholds['average']) * 20
            elif debt_to_equity < thresholds['very_poor']:
                score = 10 + (thresholds['very_poor'] - debt_to_equity) / (thresholds['very_poor'] - thresholds['poor']) * 20
            else:
                score = max(0, 10 - (debt_to_equity - thresholds['very_poor']) / 2)
            
            return debt_to_equity, max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating debt-to-equity: {str(e)}")
            return None, 0.0
    
    def calculate_current_ratio(self, fundamentals: Dict[str, Any], sector: Optional[str] = None) -> Tuple[Optional[float], float]:
        """
        Calculate and score Current Ratio
        
        Returns:
            (current_ratio, current_score): Raw current ratio and normalized score (0-100)
        """
        try:
            current_ratio = fundamentals.get('current_ratio')
            
            if current_ratio is None:
                logger.warning("Current ratio not available in fundamental data")
                return None, 0.0
            
            # Score current ratio (higher is generally better, but too high may indicate inefficiency)
            thresholds = self.scoring_thresholds['current_ratio']
            
            # Apply sector adjustments
            if sector == 'Utilities':
                # Lower current ratio expectations (predictable cash flows)
                thresholds = {k: v * 0.8 for k, v in thresholds.items()}
            elif sector == 'Technology':
                # Higher current ratio expectations (should have strong liquidity)
                thresholds = {k: v * 1.1 for k, v in thresholds.items()}
            elif sector == 'Energy':
                # Variable current ratio due to cyclical working capital needs
                thresholds = {k: v * 0.9 for k, v in thresholds.items()}
            
            if current_ratio > thresholds['excellent']:
                # Very high current ratios might indicate cash hoarding
                if current_ratio > thresholds['excellent'] * 2:
                    score = 85  # Cap score for extremely high ratios
                else:
                    score = 90 + min(10, (current_ratio - thresholds['excellent']) / thresholds['excellent'] * 10)
            elif current_ratio > thresholds['good']:
                score = 70 + (current_ratio - thresholds['good']) / (thresholds['excellent'] - thresholds['good']) * 20
            elif current_ratio > thresholds['average']:
                score = 50 + (current_ratio - thresholds['average']) / (thresholds['good'] - thresholds['average']) * 20
            elif current_ratio > thresholds['poor']:
                score = 30 + (current_ratio - thresholds['poor']) / (thresholds['average'] - thresholds['poor']) * 20
            elif current_ratio > thresholds['very_poor']:
                score = 10 + (current_ratio - thresholds['very_poor']) / (thresholds['poor'] - thresholds['very_poor']) * 20
            else:
                score = max(0, current_ratio / thresholds['very_poor'] * 10)
            
            return current_ratio, max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating current ratio: {str(e)}")
            return None, 0.0
    
    def calculate_quality_metrics(self, symbol: str, db: DatabaseManager) -> Optional[QualityMetrics]:
        """
        Calculate all quality metrics for a stock
        
        Args:
            symbol: Stock symbol
            db: Database manager instance
            
        Returns:
            QualityMetrics object or None if insufficient data
        """
        try:
            # Get latest fundamental data from database
            fundamentals = db.get_latest_fundamentals(symbol)
            stock_info = db.get_stock_info(symbol)
            
            if not fundamentals:
                logger.warning(f"No fundamental data found for {symbol}")
                return None
            
            sector = stock_info.get('sector') if stock_info else None
            logger.info(f"Calculating quality metrics for {symbol} (Sector: {sector})")
            
            # Calculate individual metrics with sector adjustments
            roe, roe_score = self.calculate_roe(fundamentals, sector)
            roic, roic_score = self.calculate_roic(fundamentals, sector)
            debt_to_equity, debt_score = self.calculate_debt_to_equity(fundamentals, sector)
            current_ratio, current_score = self.calculate_current_ratio(fundamentals, sector)
            
            # Get sector-adjusted weights
            component_weights = self.get_sector_adjusted_weights(sector)
            
            # Calculate weighted composite score
            scores = [roe_score, roic_score, debt_score, current_score]
            weights = list(component_weights.values())
            
            # Only include valid scores (non-zero) in composite
            valid_scores = [(score, weight) for score, weight in zip(scores, weights) if score > 0]
            
            if not valid_scores:
                logger.warning(f"No valid quality metrics for {symbol}")
                return None
            
            # Recalculate weights for available metrics
            total_weight = sum(weight for _, weight in valid_scores)
            normalized_scores = [(score * weight / total_weight) for score, weight in valid_scores]
            
            quality_score = sum(normalized_scores)
            data_quality_score = len(valid_scores) / len(scores)  # Data quality based on completeness
            
            # Data quality assessment
            data_quality = fundamentals.get('quality_score', 1.0)
            
            return QualityMetrics(
                symbol=symbol,
                calculation_date=date.today(),
                roe=roe,
                roic=roic,
                debt_to_equity=debt_to_equity,
                current_ratio=current_ratio,
                roe_score=roe_score,
                roic_score=roic_score,
                debt_to_equity_score=debt_score,
                current_ratio_score=current_score,
                quality_score=quality_score,
                data_quality_score=data_quality_score,
                sector=sector,
                data_quality=data_quality
            )
            
        except Exception as e:
            logger.error(f"Error calculating quality metrics for {symbol}: {str(e)}")
            return None
    
    def calculate_batch_quality(self, symbols: List[str], db: DatabaseManager) -> Dict[str, QualityMetrics]:
        """
        Calculate quality metrics for multiple stocks
        
        Args:
            symbols: List of stock symbols
            db: Database manager instance
            
        Returns:
            Dictionary mapping symbols to QualityMetrics
        """
        results = {}
        
        for symbol in symbols:
            try:
                metrics = self.calculate_quality_metrics(symbol, db)
                if metrics:
                    results[symbol] = metrics
                    logger.info(f"✅ Calculated quality metrics for {symbol}: {metrics.quality_score:.1f}")
                else:
                    logger.warning(f"❌ Failed to calculate quality metrics for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")
                continue
        
        logger.info(f"Completed quality analysis for {len(results)}/{len(symbols)} stocks")
        return results
    
    def save_quality_metrics(self, metrics: QualityMetrics, db: DatabaseManager):
        """
        Save quality metrics to calculated_metrics table
        
        Args:
            metrics: QualityMetrics object
            db: Database manager instance
        """
        try:
            cursor = db.connection.cursor()
            
            sql = '''
                INSERT OR REPLACE INTO calculated_metrics
                (symbol, calculation_date, quality_score, methodology_version)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(symbol, calculation_date) DO UPDATE SET
                    quality_score = excluded.quality_score,
                    methodology_version = excluded.methodology_version
            '''
            
            cursor.execute(sql, (
                metrics.symbol,
                metrics.calculation_date,
                metrics.quality_score,
                'v1.0'
            ))
            
            db.connection.commit()
            cursor.close()
            
            logger.info(f"Saved quality metrics for {metrics.symbol}")
            
        except Exception as e:
            logger.error(f"Error saving quality metrics for {metrics.symbol}: {str(e)}")

# Convenience functions
def calculate_single_quality(symbol: str, config_path: Optional[str] = None) -> Optional[QualityMetrics]:
    """Calculate quality metrics for a single stock"""
    calculator = QualityCalculator(config_path)
    
    from src.data.database import get_database_connection
    db = get_database_connection(config_path)
    
    try:
        return calculator.calculate_quality_metrics(symbol, db)
    finally:
        db.close()

def calculate_all_quality(config_path: Optional[str] = None) -> Dict[str, QualityMetrics]:
    """Calculate quality metrics for all stocks in database"""
    calculator = QualityCalculator(config_path)
    
    from src.data.database import get_database_connection
    db = get_database_connection(config_path)
    
    try:
        symbols = db.get_all_stocks()
        return calculator.calculate_batch_quality(symbols, db)
    finally:
        db.close()