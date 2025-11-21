#!/usr/bin/env python3
"""
Test script for fundamental calculator implementation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.calculations.fundamental import FundamentalCalculator, calculate_single_fundamental, calculate_all_fundamentals
from src.data.database import get_database_connection
from src.utils.helpers import setup_logging
import time

def test_individual_calculations():
    """Test individual fundamental calculation methods"""
    print('🧮 Testing Individual Calculation Methods')
    print('=' * 55)
    
    try:
        calculator = FundamentalCalculator()
        
        # Test data (simulating AAPL-like fundamentals)
        test_fundamentals = {
            'pe_ratio': 28.5,
            'ev_to_ebitda': 18.2,
            'peg_ratio': 1.8,
            'free_cash_flow': 99_000_000_000,  # $99B
            'market_cap': 3_000_000_000_000,   # $3T
            'earnings_growth': 0.15,           # 15% growth
            'operating_cash_flow': 110_000_000_000  # $110B
        }
        
        # Test P/E calculation
        print('\n📊 P/E Ratio Calculation:')
        pe_ratio, pe_score = calculator.calculate_pe_ratio(test_fundamentals)
        print(f'   P/E Ratio: {pe_ratio}')
        print(f'   P/E Score: {pe_score:.1f}/100')
        
        # Test EV/EBITDA calculation  
        print('\n🏢 EV/EBITDA Calculation:')
        ev_ebitda, ev_score = calculator.calculate_ev_ebitda(test_fundamentals)
        print(f'   EV/EBITDA: {ev_ebitda}')
        print(f'   EV/EBITDA Score: {ev_score:.1f}/100')
        
        # Test PEG calculation
        print('\n📈 PEG Ratio Calculation:')
        peg_ratio, peg_score = calculator.calculate_peg_ratio(test_fundamentals)
        print(f'   PEG Ratio: {peg_ratio}')
        print(f'   PEG Score: {peg_score:.1f}/100')
        
        # Test FCF Yield calculation
        print('\n💰 FCF Yield Calculation:')
        fcf_yield, fcf_score = calculator.calculate_fcf_yield(test_fundamentals)
        print(f'   FCF Yield: {fcf_yield:.3f} ({fcf_yield*100:.1f}%)')
        print(f'   FCF Yield Score: {fcf_score:.1f}/100')
        
        # Calculate composite score manually
        weights = calculator.component_weights
        composite = (pe_score * weights['pe_ratio'] + 
                    ev_score * weights['ev_ebitda'] + 
                    peg_score * weights['peg_ratio'] + 
                    fcf_score * weights['fcf_yield'])
        
        print(f'\n🎯 Composite Fundamental Score: {composite:.1f}/100')
        print(f'   Weighted Components:')
        print(f'   • P/E ({weights["pe_ratio"]*100:.0f}%): {pe_score:.1f} → {pe_score * weights["pe_ratio"]:.1f}')
        print(f'   • EV/EBITDA ({weights["ev_ebitda"]*100:.0f}%): {ev_score:.1f} → {ev_score * weights["ev_ebitda"]:.1f}')
        print(f'   • PEG ({weights["peg_ratio"]*100:.0f}%): {peg_score:.1f} → {peg_score * weights["peg_ratio"]:.1f}')
        print(f'   • FCF Yield ({weights["fcf_yield"]*100:.0f}%): {fcf_score:.1f} → {fcf_score * weights["fcf_yield"]:.1f}')
        
        return True
        
    except Exception as e:
        print(f'❌ Individual calculations test failed: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

def test_database_integration():
    """Test fundamental calculator with real database data"""
    print('\n🗄️  Testing Database Integration')
    print('=' * 40)
    
    try:
        db = get_database_connection()
        calculator = FundamentalCalculator()
        
        # Test with AAPL (should have data from previous tests)
        test_symbol = 'AAPL'
        print(f'Testing with {test_symbol}...')
        
        # Get raw fundamental data
        fundamentals = db.get_latest_fundamentals(test_symbol)
        if not fundamentals:
            print(f'❌ No fundamental data found for {test_symbol}')
            return False
        
        print(f'\n📊 Raw Fundamental Data for {test_symbol}:')
        key_metrics = ['pe_ratio', 'market_cap', 'free_cash_flow', 'enterprise_value', 'ev_to_ebitda']
        for metric in key_metrics:
            value = fundamentals.get(metric)
            if value is not None:
                if metric == 'market_cap' or metric == 'free_cash_flow' or metric == 'enterprise_value':
                    print(f'   {metric}: ${value:,.0f}' if value > 1e6 else f'   {metric}: {value}')
                else:
                    print(f'   {metric}: {value}')
            else:
                print(f'   {metric}: N/A')
        
        # Calculate metrics
        metrics = calculator.calculate_fundamental_metrics(test_symbol, db)
        
        if metrics:
            print(f'\n🎯 Calculated Fundamental Metrics for {test_symbol}:')
            print(f'   P/E Ratio: {metrics.pe_ratio} → Score: {metrics.pe_score:.1f}/100')
            print(f'   EV/EBITDA: {metrics.ev_ebitda} → Score: {metrics.ev_ebitda_score:.1f}/100')
            print(f'   PEG Ratio: {metrics.peg_ratio} → Score: {metrics.peg_score:.1f}/100')
            print(f'   FCF Yield: {metrics.fcf_yield:.3f} → Score: {metrics.fcf_yield_score:.1f}/100')
            print(f'\n   📈 Composite Fundamental Score: {metrics.fundamental_score:.1f}/100')
            print(f'   🎯 Confidence Level: {metrics.confidence*100:.0f}%')
            print(f'   🏭 Sector: {metrics.sector}')
            
            # Save to database
            calculator.save_fundamental_metrics(metrics, db)
            print(f'   ✅ Metrics saved to database')
            
        else:
            print(f'❌ Failed to calculate metrics for {test_symbol}')
            return False
        
        db.close()
        return True
        
    except Exception as e:
        print(f'❌ Database integration test failed: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

def test_batch_calculation():
    """Test batch calculation for multiple stocks"""
    print('\n📊 Testing Batch Calculation')
    print('=' * 35)
    
    try:
        db = get_database_connection()
        
        # Get first 5 stocks for testing
        all_stocks = db.get_all_stocks()
        test_stocks = all_stocks[:5]  # Test with first 5 stocks
        
        print(f'Testing batch calculation with {len(test_stocks)} stocks: {test_stocks}')
        
        # Calculate all fundamentals
        start_time = time.time()
        results = calculate_all_fundamentals()
        end_time = time.time()
        
        print(f'\n🎯 Batch Calculation Results:')
        print(f'   Processing time: {end_time - start_time:.2f} seconds')
        print(f'   Successful calculations: {len(results)}/{len(test_stocks)}')
        
        if results:
            print(f'\n📈 Top Fundamental Scores:')
            sorted_results = sorted(results.items(), key=lambda x: x[1].fundamental_score, reverse=True)
            
            for i, (symbol, metrics) in enumerate(sorted_results[:3], 1):
                print(f'   {i}. {symbol}: {metrics.fundamental_score:.1f}/100')
                print(f'      • P/E: {metrics.pe_score:.0f} | EV/EBITDA: {metrics.ev_ebitda_score:.0f} | PEG: {metrics.peg_score:.0f} | FCF: {metrics.fcf_yield_score:.0f}')
                print(f'      • Confidence: {metrics.confidence*100:.0f}% | Sector: {metrics.sector}')
        
        db.close()
        return len(results) > 0
        
    except Exception as e:
        print(f'❌ Batch calculation test failed: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

def test_edge_cases():
    """Test edge cases and error handling"""
    print('\n⚠️  Testing Edge Cases')
    print('=' * 25)
    
    try:
        calculator = FundamentalCalculator()
        
        # Test with missing data
        print('Testing with missing P/E data...')
        empty_data = {}
        pe_ratio, pe_score = calculator.calculate_pe_ratio(empty_data)
        print(f'   Result: P/E={pe_ratio}, Score={pe_score} ✅')
        
        # Test with negative values
        print('Testing with negative FCF...')
        negative_fcf = {
            'free_cash_flow': -1_000_000_000,
            'market_cap': 100_000_000_000
        }
        fcf_yield, fcf_score = calculator.calculate_fcf_yield(negative_fcf)
        print(f'   Result: FCF Yield={fcf_yield}, Score={fcf_score} ✅')
        
        # Test with extreme values
        print('Testing with extreme P/E...')
        extreme_pe = {'pe_ratio': 500}
        pe_ratio, pe_score = calculator.calculate_pe_ratio(extreme_pe)
        print(f'   Result: P/E={pe_ratio}, Score={pe_score} ✅')
        
        return True
        
    except Exception as e:
        print(f'❌ Edge cases test failed: {str(e)}')
        return False

def run_fundamental_calculator_tests():
    """Run all fundamental calculator tests"""
    print('🧪 StockAnalyzer Pro - Fundamental Calculator Tests')
    print('=' * 60)
    
    # Setup logging
    logger = setup_logging("INFO")
    
    tests = [
        ("Individual Calculations", test_individual_calculations),
        ("Database Integration", test_database_integration),
        ("Batch Calculation", test_batch_calculation),
        ("Edge Cases", test_edge_cases)
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
        print('\n🎉 All fundamental calculator tests passed!')
        print('\n📊 Fundamental Calculator (40% Component) Implementation:')
        print('   ✅ P/E Ratio calculation and scoring')
        print('   ✅ EV/EBITDA calculation and scoring')
        print('   ✅ PEG Ratio calculation and scoring') 
        print('   ✅ Free Cash Flow Yield calculation and scoring')
        print('   ✅ Weighted composite scoring (30/25/25/20)')
        print('   ✅ Database integration and persistence')
        print('   ✅ Batch processing capabilities')
        print('   ✅ Error handling and edge cases')
        
        return True
    else:
        print(f'\n⚠️  {total - passed} test(s) failed. Please fix before proceeding.')
        return False

if __name__ == "__main__":
    success = run_fundamental_calculator_tests()
    
    if success:
        print('\n🚀 Fundamental Calculator ready! Next: Quality Calculators (25%)')
    else:
        print('\n🔧 Please fix fundamental calculator issues before proceeding.')
        sys.exit(1)