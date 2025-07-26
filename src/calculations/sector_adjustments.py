"""
Sector-Specific Adjustment Factors for Fundamental Scoring

Implements sector-aware scoring adjustments based on industry characteristics:
- Technology: Higher growth expectations, premium valuations accepted
- Banking: Lower P/E norms, focus on book value and ROE
- Utilities: Stable dividends, lower growth, moderate valuations
- Healthcare: Mixed growth profiles, R&D considerations
- Consumer: Cyclical considerations, brand value premiums
- Industrial: Capital intensity, cyclical adjustments
- Energy: Commodity cycle awareness, volatility adjustments

Outlier detection requires sector context to distinguish genuine mispricings
from normal sector-specific valuation patterns.
"""

from typing import Dict, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class SectorProfile:
    """Sector-specific adjustment profile"""
    name: str
    pe_multiplier: float      # Multiply base P/E thresholds
    ev_ebitda_multiplier: float  # Multiply base EV/EBITDA thresholds  
    peg_multiplier: float     # Multiply base PEG thresholds
    fcf_focus: float         # Weight FCF more/less (1.0 = normal)
    growth_expectation: str  # 'high', 'medium', 'low'
    description: str

class SectorAdjustmentEngine:
    """
    Provides sector-specific adjustments for fundamental scoring
    """
    
    def __init__(self):
        self.sector_profiles = self._initialize_sector_profiles()
        
    def _initialize_sector_profiles(self) -> Dict[str, SectorProfile]:
        """Initialize sector-specific adjustment profiles"""
        
        profiles = {
            'Technology': SectorProfile(
                name='Technology',
                pe_multiplier=1.4,        # 40% higher P/E tolerance
                ev_ebitda_multiplier=1.3, # 30% higher EV/EBITDA tolerance
                peg_multiplier=1.2,       # 20% higher PEG tolerance
                fcf_focus=1.1,           # Slightly higher FCF importance
                growth_expectation='high',
                description='High growth, premium valuations, strong FCF generation'
            ),
            
            'Financials': SectorProfile(
                name='Financials',
                pe_multiplier=0.8,        # 20% lower P/E expectations
                ev_ebitda_multiplier=0.7, # EV/EBITDA less relevant for banks
                peg_multiplier=0.9,       # More conservative growth expectations
                fcf_focus=0.8,           # FCF less relevant, focus on ROE instead
                growth_expectation='low',
                description='Regulated, lower P/E norms, book value focus'
            ),
            
            'Healthcare': SectorProfile(
                name='Healthcare',
                pe_multiplier=1.2,        # 20% higher P/E tolerance
                ev_ebitda_multiplier=1.15, # 15% higher EV/EBITDA tolerance
                peg_multiplier=1.1,       # 10% higher PEG tolerance
                fcf_focus=1.0,           # Normal FCF focus
                growth_expectation='medium',
                description='Mixed growth, R&D investments, patent considerations'
            ),
            
            'Consumer Discretionary': SectorProfile(
                name='Consumer Discretionary',
                pe_multiplier=1.1,        # 10% higher P/E tolerance
                ev_ebitda_multiplier=1.1, # 10% higher EV/EBITDA tolerance
                peg_multiplier=1.0,       # Normal PEG expectations
                fcf_focus=1.0,           # Normal FCF focus
                growth_expectation='medium',
                description='Cyclical, brand premiums, consumer spending dependent'
            ),
            
            'Consumer Staples': SectorProfile(
                name='Consumer Staples',
                pe_multiplier=1.0,        # Normal P/E expectations
                ev_ebitda_multiplier=1.0, # Normal EV/EBITDA expectations
                peg_multiplier=0.9,       # Lower growth expectations
                fcf_focus=1.1,           # Higher FCF importance for dividends
                growth_expectation='low',
                description='Stable, dividend-focused, defensive characteristics'
            ),
            
            'Industrials': SectorProfile(
                name='Industrials',
                pe_multiplier=0.95,       # Slightly lower P/E expectations
                ev_ebitda_multiplier=1.0, # Normal EV/EBITDA expectations
                peg_multiplier=0.95,      # Slightly lower growth expectations
                fcf_focus=1.0,           # Normal FCF focus
                growth_expectation='medium',
                description='Capital intensive, cyclical, infrastructure dependent'
            ),
            
            'Energy': SectorProfile(
                name='Energy',
                pe_multiplier=0.7,        # Much lower P/E due to volatility
                ev_ebitda_multiplier=0.8, # Lower EV/EBITDA due to cyclicality
                peg_multiplier=0.6,       # Very low PEG due to cyclical earnings
                fcf_focus=1.2,           # Higher FCF importance
                growth_expectation='low',
                description='Commodity-driven, highly cyclical, FCF focus'
            ),
            
            'Utilities': SectorProfile(
                name='Utilities',
                pe_multiplier=0.9,        # 10% lower P/E expectations
                ev_ebitda_multiplier=0.9, # 10% lower EV/EBITDA expectations
                peg_multiplier=0.8,       # Much lower growth expectations
                fcf_focus=1.15,          # Higher FCF importance for dividends
                growth_expectation='low',
                description='Regulated, stable, dividend-focused, low growth'
            ),
            
            'Materials': SectorProfile(
                name='Materials',
                pe_multiplier=0.85,       # Lower P/E due to cyclicality
                ev_ebitda_multiplier=0.9, # Slightly lower EV/EBITDA expectations
                peg_multiplier=0.8,       # Lower growth expectations
                fcf_focus=1.0,           # Normal FCF focus
                growth_expectation='low',
                description='Commodity-driven, cyclical, capital intensive'
            ),
            
            'Communication Services': SectorProfile(
                name='Communication Services',
                pe_multiplier=1.3,        # 30% higher P/E tolerance
                ev_ebitda_multiplier=1.2, # 20% higher EV/EBITDA tolerance
                peg_multiplier=1.15,      # 15% higher PEG tolerance
                fcf_focus=1.0,           # Normal FCF focus
                growth_expectation='high',
                description='Platform effects, network advantages, high growth'
            ),
            
            'Real Estate': SectorProfile(
                name='Real Estate',
                pe_multiplier=0.8,        # Lower P/E expectations
                ev_ebitda_multiplier=0.7, # EV/EBITDA less relevant for REITs
                peg_multiplier=0.8,       # Lower growth expectations
                fcf_focus=1.3,           # Much higher FCF importance
                growth_expectation='low',
                description='REIT structure, dividend requirements, FCF critical'
            )
        }
        
        return profiles
    
    def get_sector_profile(self, sector: Optional[str]) -> SectorProfile:
        """
        Get sector profile with fallback to default
        
        Args:
            sector: Sector name (can be None or non-standard)
            
        Returns:
            SectorProfile object (defaults to balanced profile if sector unknown)
        """
        if not sector:
            return self._get_default_profile()
        
        # Try exact match first
        if sector in self.sector_profiles:
            return self.sector_profiles[sector]
        
        # Try fuzzy matching for common variations
        sector_lower = sector.lower()
        
        fuzzy_matches = {
            'tech': 'Technology',
            'information technology': 'Technology',
            'software': 'Technology',
            'semiconductor': 'Technology',
            
            'financial': 'Financials',
            'banks': 'Financials',
            'insurance': 'Financials',
            
            'health': 'Healthcare',
            'pharmaceutical': 'Healthcare',
            'biotech': 'Healthcare',
            'medical': 'Healthcare',
            
            'consumer': 'Consumer Discretionary',
            'retail': 'Consumer Discretionary',
            
            'industrial': 'Industrials',
            'manufacturing': 'Industrials',
            
            'oil': 'Energy',
            'gas': 'Energy',
            'petroleum': 'Energy',
            
            'utility': 'Utilities',
            'electric': 'Utilities',
            'power': 'Utilities',
            
            'material': 'Materials',
            'mining': 'Materials',
            'chemical': 'Materials',
            
            'telecom': 'Communication Services',
            'media': 'Communication Services',
            'internet': 'Communication Services',
            
            'reit': 'Real Estate',
            'property': 'Real Estate'
        }
        
        for key, sector_name in fuzzy_matches.items():
            if key in sector_lower:
                logger.info(f"Fuzzy matched '{sector}' to '{sector_name}'")
                return self.sector_profiles[sector_name]
        
        # Default fallback
        logger.warning(f"Unknown sector '{sector}', using default profile")
        return self._get_default_profile()
    
    def _get_default_profile(self) -> SectorProfile:
        """Default balanced profile for unknown sectors"""
        return SectorProfile(
            name='Default',
            pe_multiplier=1.0,
            ev_ebitda_multiplier=1.0,
            peg_multiplier=1.0,
            fcf_focus=1.0,
            growth_expectation='medium',
            description='Balanced profile for unclassified sectors'
        )
    
    def adjust_thresholds(self, base_thresholds: Dict[str, Dict[str, float]], 
                         sector: Optional[str]) -> Dict[str, Dict[str, float]]:
        """
        Apply sector adjustments to base scoring thresholds
        
        Args:
            base_thresholds: Base threshold dictionary from FundamentalCalculator
            sector: Sector name for adjustment
            
        Returns:
            Adjusted thresholds dictionary
        """
        profile = self.get_sector_profile(sector)
        adjusted = {}
        
        # Adjust P/E thresholds
        pe_thresholds = base_thresholds['pe_ratio'].copy()
        for key, value in pe_thresholds.items():
            pe_thresholds[key] = value * profile.pe_multiplier
        adjusted['pe_ratio'] = pe_thresholds
        
        # Adjust EV/EBITDA thresholds
        ev_thresholds = base_thresholds['ev_ebitda'].copy()
        for key, value in ev_thresholds.items():
            ev_thresholds[key] = value * profile.ev_ebitda_multiplier
        adjusted['ev_ebitda'] = ev_thresholds
        
        # Adjust PEG thresholds
        peg_thresholds = base_thresholds['peg_ratio'].copy()
        for key, value in peg_thresholds.items():
            peg_thresholds[key] = value * profile.peg_multiplier
        adjusted['peg_ratio'] = peg_thresholds
        
        # FCF thresholds remain the same (adjustment applied via weighting)
        adjusted['fcf_yield'] = base_thresholds['fcf_yield'].copy()
        
        logger.info(f"Applied {profile.name} sector adjustments: "
                   f"P/E×{profile.pe_multiplier:.1f}, EV/EBITDA×{profile.ev_ebitda_multiplier:.1f}, "
                   f"PEG×{profile.peg_multiplier:.1f}")
        
        return adjusted
    
    def get_fcf_weight_adjustment(self, sector: Optional[str]) -> float:
        """
        Get FCF weighting adjustment for sector
        
        Args:
            sector: Sector name
            
        Returns:
            FCF weight multiplier (1.0 = normal weight)
        """
        profile = self.get_sector_profile(sector)
        return profile.fcf_focus
    
    def get_sector_context(self, sector: Optional[str]) -> Dict[str, Any]:
        """
        Get comprehensive sector context for logging and debugging
        
        Args:
            sector: Sector name
            
        Returns:
            Dictionary with sector analysis context
        """
        profile = self.get_sector_profile(sector)
        
        return {
            'sector_name': profile.name,
            'growth_expectation': profile.growth_expectation,
            'description': profile.description,
            'adjustments': {
                'pe_multiplier': profile.pe_multiplier,
                'ev_ebitda_multiplier': profile.ev_ebitda_multiplier,
                'peg_multiplier': profile.peg_multiplier,
                'fcf_focus': profile.fcf_focus
            },
            'interpretation': self._get_adjustment_interpretation(profile)
        }
    
    def _get_adjustment_interpretation(self, profile: SectorProfile) -> str:
        """Generate human-readable interpretation of adjustments"""
        adjustments = []
        
        if profile.pe_multiplier > 1.1:
            adjustments.append(f"Higher P/E tolerance (+{(profile.pe_multiplier-1)*100:.0f}%)")
        elif profile.pe_multiplier < 0.9:
            adjustments.append(f"Lower P/E expectations ({(1-profile.pe_multiplier)*100:.0f}%)")
            
        if profile.ev_ebitda_multiplier > 1.1:
            adjustments.append(f"Higher EV/EBITDA tolerance (+{(profile.ev_ebitda_multiplier-1)*100:.0f}%)")
        elif profile.ev_ebitda_multiplier < 0.9:
            adjustments.append(f"Lower EV/EBITDA expectations ({(1-profile.ev_ebitda_multiplier)*100:.0f}%)")
            
        if profile.fcf_focus > 1.1:
            adjustments.append(f"Enhanced FCF importance (+{(profile.fcf_focus-1)*100:.0f}%)")
        elif profile.fcf_focus < 0.9:
            adjustments.append(f"Reduced FCF weighting ({(1-profile.fcf_focus)*100:.0f}%)")
        
        return "; ".join(adjustments) if adjustments else "Standard scoring approach"

# Convenience function for easy integration
def get_sector_adjusted_thresholds(base_thresholds: Dict[str, Dict[str, float]], 
                                 sector: Optional[str]) -> Dict[str, Dict[str, float]]:
    """
    Quick function to get sector-adjusted thresholds
    
    Args:
        base_thresholds: Base thresholds from FundamentalCalculator
        sector: Sector name
        
    Returns:
        Sector-adjusted thresholds
    """
    engine = SectorAdjustmentEngine()
    return engine.adjust_thresholds(base_thresholds, sector)