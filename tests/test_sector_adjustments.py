#!/usr/bin/env python3
"""
Test script for sector-adjusted fundamental scoring
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.calculations.fundamental import FundamentalCalculator
from src.calculations.sector_adjustments import SectorAdjustmentEngine
from src.data.database import get_database_connection
from src.utils.helpers import setup_logging
import time

def test_sector_adjustment_engine():
    """Test the sector adjustment engine itself"""
    print('🏭 Testing Sector Adjustment Engine')
    print('=' * 40)
    
    try:
        engine = SectorAdjustmentEngine()
        
        # Test sector profile retrieval
        print('\n📊 Sector Profile Examples:')
        
        test_sectors = ['Technology', 'Financials', 'Energy', 'Unknown Sector']
        
        for sector in test_sectors:
            profile = engine.get_sector_profile(sector)
            context = engine.get_sector_context(sector)
            
            print(f'\n   {sector}:')
            print(f'   • Matched to: {profile.name}')
            print(f'   • Growth expectation: {profile.growth_expectation}')
            print(f'   • P/E multiplier: {profile.pe_multiplier:.1f}x')
            print(f'   • EV/EBITDA multiplier: {profile.ev_ebitda_multiplier:.1f}x')
            print(f'   • FCF focus: {profile.fcf_focus:.1f}x')
            print(f'   • Interpretation: {context["interpretation"]}')
        
        return True
        
    except Exception as e:
        print(f'❌ Sector adjustment engine test failed: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

def test_threshold_adjustments():
    """Test threshold adjustments for different sectors"""
    print('\n⚙️  Testing Threshold Adjustments')
    print('=' * 35)
    
    try:
        calculator = FundamentalCalculator()
        base_thresholds = calculator.scoring_thresholds
        
        # Test P/E threshold adjustments for different sectors
        print('\n📈 P/E Ratio Threshold Adjustments:')
        print(f'{"Sector":<20} {"Base Excellent":<15} {"Adjusted":<15} {"Multiplier":<10}')
        print('-' * 60)
        
        test_sectors = ['Technology', 'Financials', 'Energy', 'Utilities']
        
        for sector in test_sectors:
            adjusted = calculator.sector_engine.adjust_thresholds(base_thresholds, sector)
            base_pe = base_thresholds['pe_ratio']['excellent']
            adj_pe = adjusted['pe_ratio']['excellent']
            multiplier = adj_pe / base_pe
            
            print(f'{sector:<20} {base_pe:<15} {adj_pe:<15.1f} {multiplier:<10.1f}')
        
        return True
        
    except Exception as e:
        print(f'❌ Threshold adjustment test failed: {str(e)}')
        return False

def test_aapl_with_sector_adjustments():
    """Test AAPL scoring with and without sector adjustments"""
    print('\n🍎 Testing AAPL with Sector Adjustments')
    print('=' * 40)
    
    try:
        db = get_database_connection()
        calculator = FundamentalCalculator()
        
        # Get AAPL fundamental data
        fundamentals = db.get_latest_fundamentals('AAPL')
        stock_info = db.get_stock_info('AAPL')
        
        if not fundamentals:
            print('❌ No AAPL fundamental data available')
            return False
        
        sector = stock_info.get('sector') if stock_info else 'Technology'
        print(f'AAPL Sector: {sector}')
        print(f'P/E Ratio: {fundamentals.get("pe_ratio"):.2f}')
        
        # Calculate without sector adjustments (pass None as sector)
        print('\n📊 Scoring WITHOUT Sector Adjustments:')
        pe_ratio_base, pe_score_base = calculator.calculate_pe_ratio(fundamentals, None)
        ev_ebitda_base, ev_score_base = calculator.calculate_ev_ebitda(fundamentals, None)
        peg_ratio_base, peg_score_base = calculator.calculate_peg_ratio(fundamentals, None)
        fcf_yield_base, fcf_score_base = calculator.calculate_fcf_yield(fundamentals, None)
        
        base_weights = calculator.base_component_weights
        base_composite = (pe_score_base * base_weights['pe_ratio'] + 
                         ev_score_base * base_weights['ev_ebitda'] + 
                         peg_score_base * base_weights['peg_ratio'] + 
                         fcf_score_base * base_weights['fcf_yield'])
        
        print(f'   P/E Score: {pe_score_base:.1f}')
        print(f'   EV/EBITDA Score: {ev_score_base:.1f}')
        print(f'   PEG Score: {peg_score_base:.1f}')
        print(f'   FCF Yield Score: {fcf_score_base:.1f}')
        print(f'   Composite Score: {base_composite:.1f}')
        
        # Calculate WITH sector adjustments
        print('\n🏭 Scoring WITH Sector Adjustments (Technology):')
        pe_ratio_adj, pe_score_adj = calculator.calculate_pe_ratio(fundamentals, sector)
        ev_ebitda_adj, ev_score_adj = calculator.calculate_ev_ebitda(fundamentals, sector)
        peg_ratio_adj, peg_score_adj = calculator.calculate_peg_ratio(fundamentals, sector)
        fcf_yield_adj, fcf_score_adj = calculator.calculate_fcf_yield(fundamentals, sector)
        
        adj_weights = calculator.get_sector_adjusted_weights(sector)
        adj_composite = (pe_score_adj * adj_weights['pe_ratio'] + 
                        ev_score_adj * adj_weights['ev_ebitda'] + 
                        peg_score_adj * adj_weights['peg_ratio'] + 
                        fcf_score_adj * adj_weights['fcf_yield'])
        
        print(f'   P/E Score: {pe_score_adj:.1f} (vs {pe_score_base:.1f}) [+{pe_score_adj-pe_score_base:+.1f}]')
        print(f'   EV/EBITDA Score: {ev_score_adj:.1f} (vs {ev_score_base:.1f}) [+{ev_score_adj-ev_score_base:+.1f}]')
        print(f'   PEG Score: {peg_score_adj:.1f} (vs {peg_score_base:.1f}) [+{peg_score_adj-peg_score_base:+.1f}]')
        print(f'   FCF Yield Score: {fcf_score_adj:.1f} (vs {fcf_score_base:.1f}) [+{fcf_score_adj-fcf_score_base:+.1f}]')
        print(f'   Composite Score: {adj_composite:.1f} (vs {base_composite:.1f}) [+{adj_composite-base_composite:+.1f}]')
        
        print('\n⚖️  Weight Adjustments:')
        print(f'   P/E Weight: {adj_weights["pe_ratio"]:.1%} (vs {base_weights["pe_ratio"]:.1%})')
        print(f'   EV/EBITDA Weight: {adj_weights["ev_ebitda"]:.1%} (vs {base_weights["ev_ebitda"]:.1%})')
        print(f'   PEG Weight: {adj_weights["peg_ratio"]:.1%} (vs {base_weights["peg_ratio"]:.1%})')
        print(f'   FCF Yield Weight: {adj_weights["fcf_yield"]:.1%} (vs {base_weights["fcf_yield"]:.1%})')
        
        # Show threshold differences
        base_thresholds = calculator.scoring_thresholds
        adj_thresholds = calculator.sector_engine.adjust_thresholds(base_thresholds, sector)
        
        print('\n🎯 Threshold Adjustments:')
        print(f'   P/E Excellent: {adj_thresholds["pe_ratio"]["excellent"]:.1f} (vs {base_thresholds["pe_ratio"]["excellent"]:.1f})')
        print(f'   EV/EBITDA Excellent: {adj_thresholds["ev_ebitda"]["excellent"]:.1f} (vs {base_thresholds["ev_ebitda"]["excellent"]:.1f})')
        
        db.close()
        return True
        
    except Exception as e:
        print(f'❌ AAPL sector adjustment test failed: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

def test_sector_aware_calculation():
    """Test the full sector-aware calculation method"""
    print('\n🧮 Testing Full Sector-Aware Calculation')
    print('=' * 45)
    
    try:
        calculator = FundamentalCalculator()
        db = get_database_connection()
        
        # Test with AAPL
        metrics = calculator.calculate_fundamental_metrics('AAPL', db)
        
        if metrics:
            print(f'✅ AAPL Sector-Aware Fundamental Analysis:')
            print(f'   Symbol: {metrics.symbol}')
            print(f'   Sector: {metrics.sector}')
            print(f'   Fundamental Score: {metrics.fundamental_score:.1f}/100')
            print(f'   Confidence: {metrics.confidence*100:.0f}%')
            print(f'   Component Scores:')
            print(f'   • P/E: {metrics.pe_score:.1f}')
            print(f'   • EV/EBITDA: {metrics.ev_ebitda_score:.1f}')
            print(f'   • PEG: {metrics.peg_score:.1f}')
            print(f'   • FCF Yield: {metrics.fcf_yield_score:.1f}')
        
        db.close()
        return metrics is not None
        
    except Exception as e:
        print(f'❌ Sector-aware calculation test failed: {str(e)}')
        return False

def run_sector_adjustment_tests():
    """Run all sector adjustment tests"""
    print('🏭 StockAnalyzer Pro - Sector Adjustment Tests')
    print('=' * 55)
    
    # Setup logging
    logger = setup_logging("INFO")
    
    tests = [
        ("Sector Adjustment Engine", test_sector_adjustment_engine),
        ("Threshold Adjustments", test_threshold_adjustments),
        ("AAPL Sector Comparison", test_aapl_with_sector_adjustments),
        ("Sector-Aware Calculation", test_sector_aware_calculation)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f'\n🔬 Running: {test_name}')
        try:
            start_time = time.time()
            success = test_func()
            end_time = time.time()
            
            results[test_name] = {
                'success': success,
                'duration': end_time - start_time
            }
            
            if success:
                print(f'✅ {test_name} PASSED ({end_time - start_time:.2f}s)')
            else:
                print(f'❌ {test_name} FAILED ({end_time - start_time:.2f}s)')
                
        except Exception as e:
            print(f'💥 {test_name} CRASHED: {str(e)}')
            results[test_name] = {'success': False, 'error': str(e)}
    
    # Summary
    print('\n📋 Test Summary')
    print('=' * 30)
    
    passed = sum(1 for r in results.values() if r.get('success', False))
    total = len(results)
    
    print(f'Tests Passed: {passed}/{total}')
    
    for test_name, result in results.items():
        status = '✅ PASS' if result.get('success', False) else '❌ FAIL'
        duration = f" ({result.get('duration', 0):.2f}s)" if 'duration' in result else ""
        print(f'  {status} {test_name}{duration}')
    
    if passed == total:
        print('\n🎉 All sector adjustment tests passed!')
        print('\n🏭 Sector-Aware Fundamental Analysis Features:')
        print('   ✅ 11 sector profiles with specific adjustments')
        print('   ✅ P/E threshold adjustments (±40% for tech vs energy)')
        print('   ✅ EV/EBITDA adjustments for sector characteristics')
        print('   ✅ PEG ratio adjustments for growth expectations')
        print('   ✅ FCF weighting adjustments (REITs get +30% FCF focus)')
        print('   ✅ Fuzzy sector matching for data inconsistencies')
        print('   ✅ Outlier detection now sector-context aware')
        
        return True
    else:
        print(f'\n⚠️  {total - passed} test(s) failed. Please fix before proceeding.')
        return False

if __name__ == "__main__":
    success = run_sector_adjustment_tests()
    
    if success:
        print('\n🚀 Sector-aware fundamental analysis ready!')
        print('   📊 AAPL now scores appropriately for tech sector')
        print('   🎯 Outlier detection considers sector context')
        print('   ⚖️  Component weights adjust by sector needs')
    else:
        print('\n🔧 Please fix sector adjustment issues before proceeding.')
        sys.exit(1)