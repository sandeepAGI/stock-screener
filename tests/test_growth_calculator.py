#!/usr/bin/env python3
"""
Test script for growth calculator implementation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.calculations.growth import GrowthCalculator, calculate_single_growth, calculate_all_growth
from src.data.database import get_database_connection
from src.utils.helpers import setup_logging
import time

def test_individual_growth_calculations():
    """Test individual growth calculation methods"""
    print('📈 Testing Individual Growth Calculation Methods')
    print('=' * 60)
    
    try:
        calculator = GrowthCalculator()
        
        # Test data (simulating realistic company fundamentals)
        test_fundamentals = {
            'revenue_growth': 0.12,          # 12% revenue growth (good)
            'earnings_growth': 0.18,         # 18% EPS growth (good)
            'forward_pe': 22.5,              # Forward P/E
            'pe_ratio': 25.0,                # Trailing P/E
            'total_revenue': 50_000_000_000, # $50B revenue
        }
        
        # Test Revenue Growth calculation
        print('\n💰 Revenue Growth Calculation:')
        revenue_growth, revenue_score = calculator.calculate_revenue_growth(test_fundamentals)
        print(f'   Revenue Growth: {revenue_growth:.1%}')
        print(f'   Revenue Growth Score: {revenue_score:.1f}/100')
        
        # Test EPS Growth calculation  
        print('\n📊 EPS Growth Calculation:')
        eps_growth, eps_score = calculator.calculate_eps_growth(test_fundamentals)
        print(f'   EPS Growth: {eps_growth:.1%}')
        print(f'   EPS Growth Score: {eps_score:.1f}/100')
        
        # Test Revenue Stability calculation
        print('\n🎯 Revenue Stability Calculation:')
        stability, stability_score = calculator.calculate_revenue_stability(test_fundamentals)
        print(f'   Revenue Stability: {stability:.2f}')
        print(f'   Stability Score: {stability_score:.1f}/100')
        
        # Test Forward Growth calculation
        print('\n🔮 Forward Growth Calculation:')
        forward_growth, forward_score = calculator.calculate_forward_growth(test_fundamentals)
        print(f'   Forward Growth: {forward_growth:.1%}' if forward_growth else '   Forward Growth: N/A')
        print(f'   Forward Growth Score: {forward_score:.1f}/100')
        
        # Calculate composite score manually
        weights = calculator.base_component_weights
        composite = (revenue_score * weights['revenue_growth'] + 
                    eps_score * weights['eps_growth'] + 
                    stability_score * weights['revenue_stability'] + 
                    forward_score * weights['forward_growth'])
        
        print(f'\n🎯 Composite Growth Score: {composite:.1f}/100')
        print(f'   Weighted Components:')
        print(f'   • Revenue Growth ({weights["revenue_growth"]*100:.0f}%): {revenue_score:.1f} → {revenue_score * weights["revenue_growth"]:.1f}')
        print(f'   • EPS Growth ({weights["eps_growth"]*100:.0f}%): {eps_score:.1f} → {eps_score * weights["eps_growth"]:.1f}')
        print(f'   • Revenue Stability ({weights["revenue_stability"]*100:.0f}%): {stability_score:.1f} → {stability_score * weights["revenue_stability"]:.1f}')
        print(f'   • Forward Growth ({weights["forward_growth"]*100:.0f}%): {forward_score:.1f} → {forward_score * weights["forward_growth"]:.1f}')
        
        return True
        
    except Exception as e:
        print(f'❌ Individual growth calculations test failed: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

def test_sector_weight_adjustments():
    """Test sector-specific weight adjustments"""
    print('\n⚖️  Testing Sector Weight Adjustments')
    print('=' * 40)
    
    try:
        calculator = GrowthCalculator()
        base_weights = calculator.base_component_weights
        
        print('\n📊 Base Weights:')
        for metric, weight in base_weights.items():
            print(f'   {metric}: {weight:.1%}')
        
        # Test different sector adjustments
        test_sectors = ['Technology', 'Healthcare', 'Utilities', 'Energy', 'Financials']
        
        print('\n🏭 Sector-Adjusted Weights:')
        print(f'{"Sector":<15} {"Rev Growth":<12} {"EPS Growth":<12} {"Stability":<12} {"Forward":<10}')
        print('-' * 70)
        
        for sector in test_sectors:
            weights = calculator.get_sector_adjusted_weights(sector)
            print(f'{sector:<15} {weights["revenue_growth"]:<12.1%} {weights["eps_growth"]:<12.1%} {weights["revenue_stability"]:<12.1%} {weights["forward_growth"]:<10.1%}')
        
        return True
        
    except Exception as e:
        print(f'❌ Sector weight adjustment test failed: {str(e)}')
        return False

def test_aapl_growth_analysis():
    """Test growth analysis with real AAPL data"""
    print('\n🍎 Testing AAPL Growth Analysis')
    print('=' * 35)
    
    try:
        db = get_database_connection()
        calculator = GrowthCalculator()
        
        # Get AAPL fundamental data
        fundamentals = db.get_latest_fundamentals('AAPL')
        stock_info = db.get_stock_info('AAPL')
        
        if not fundamentals:
            print('❌ No AAPL fundamental data available')
            return False
        
        sector = stock_info.get('sector') if stock_info else 'Technology'
        print(f'AAPL Sector: {sector}')
        
        # Show raw growth-related data
        print(f'\n📊 Raw Growth-Related Data for AAPL:')
        growth_metrics = ['revenue_growth', 'earnings_growth', 'forward_pe', 'pe_ratio', 'total_revenue']
        
        for metric in growth_metrics:
            value = fundamentals.get(metric)
            if value is not None:
                if metric in ['revenue_growth', 'earnings_growth']:
                    print(f'   {metric}: {value:.1%}' if abs(value) < 10 else f'   {metric}: {value}')
                elif metric in ['total_revenue']:
                    print(f'   {metric}: ${value:,.0f}' if value > 1e6 else f'   {metric}: {value}')
                else:
                    print(f'   {metric}: {value:.2f}')
            else:
                print(f'   {metric}: N/A')
        
        # Calculate growth metrics
        metrics = calculator.calculate_growth_metrics('AAPL', db)
        
        if metrics:
            print(f'\n🎯 Calculated Growth Metrics for AAPL:')
            
            # Handle None values in formatting
            rev_growth_str = f'{metrics.revenue_growth:.1%}' if metrics.revenue_growth is not None else 'N/A'
            eps_growth_str = f'{metrics.eps_growth:.1%}' if metrics.eps_growth is not None else 'N/A'
            stability_str = f'{metrics.revenue_stability:.2f}' if metrics.revenue_stability is not None else 'N/A'
            forward_str = f'{metrics.forward_growth:.1%}' if metrics.forward_growth is not None else 'N/A'
            
            print(f'   Revenue Growth: {rev_growth_str} → Score: {metrics.revenue_growth_score:.1f}/100')
            print(f'   EPS Growth: {eps_growth_str} → Score: {metrics.eps_growth_score:.1f}/100')
            print(f'   Revenue Stability: {stability_str} → Score: {metrics.revenue_stability_score:.1f}/100')
            print(f'   Forward Growth: {forward_str} → Score: {metrics.forward_growth_score:.1f}/100')
            print(f'\n   📈 Composite Growth Score: {metrics.growth_score:.1f}/100')
            print(f'   🎯 Confidence Level: {metrics.confidence*100:.0f}%')
            print(f'   🏭 Sector: {metrics.sector}')
            
            # Show sector-adjusted weights used
            weights = calculator.get_sector_adjusted_weights(sector)
            print(f'\n   ⚖️  Sector-Adjusted Weights Used:')
            print(f'   • Revenue Growth: {weights["revenue_growth"]:.1%}')
            print(f'   • EPS Growth: {weights["eps_growth"]:.1%}')
            print(f'   • Revenue Stability: {weights["revenue_stability"]:.1%}')
            print(f'   • Forward Growth: {weights["forward_growth"]:.1%}')
            
            # Save to database
            calculator.save_growth_metrics(metrics, db)
            print(f'   ✅ Growth metrics saved to database')
            
        else:
            print(f'❌ Failed to calculate growth metrics for AAPL')
            return False
        
        db.close()
        return True
        
    except Exception as e:
        print(f'❌ AAPL growth analysis test failed: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

def test_sector_specific_scoring():
    """Test scoring differences across sectors"""
    print('\n🏭 Testing Sector-Specific Scoring')
    print('=' * 40)
    
    try:
        calculator = GrowthCalculator()
        
        # Test same metrics across different sectors
        test_metrics = {
            'revenue_growth': 0.12,         # 12% revenue growth
            'earnings_growth': 0.15,        # 15% EPS growth
            'forward_pe': 20.0,             # Forward P/E
            'pe_ratio': 22.0,               # Trailing P/E
        }
        
        sectors = ['Technology', 'Healthcare', 'Utilities', 'Energy']
        
        print('\n📊 Same Metrics, Different Sector Scores:')
        print('Revenue Growth: 12%, EPS Growth: 15%')
        print('-' * 75)
        print(f'{"Sector":<15} {"Rev Score":<10} {"EPS Score":<10} {"Stability":<10} {"Composite":<10}')
        print('-' * 75)
        
        for sector in sectors:
            revenue_growth, revenue_score = calculator.calculate_revenue_growth(test_metrics, sector)
            eps_growth, eps_score = calculator.calculate_eps_growth(test_metrics, sector)
            stability, stability_score = calculator.calculate_revenue_stability(test_metrics, sector)
            forward_growth, forward_score = calculator.calculate_forward_growth(test_metrics, sector)
            
            # Calculate sector-weighted composite
            weights = calculator.get_sector_adjusted_weights(sector)
            composite = (revenue_score * weights['revenue_growth'] + 
                        eps_score * weights['eps_growth'] + 
                        stability_score * weights['revenue_stability'] + 
                        forward_score * weights['forward_growth'])
            
            print(f'{sector:<15} {revenue_score:<10.1f} {eps_score:<10.1f} {stability_score:<10.1f} {composite:<10.1f}')
        
        return True
        
    except Exception as e:
        print(f'❌ Sector-specific scoring test failed: {str(e)}')
        return False

def test_edge_cases():
    """Test edge cases and error handling"""
    print('\n⚠️  Testing Edge Cases')
    print('=' * 25)
    
    try:
        calculator = GrowthCalculator()
        
        # Test with negative growth (recession scenario)
        print('Testing with negative revenue growth...')
        negative_growth = {
            'revenue_growth': -0.15,    # -15% revenue decline
            'earnings_growth': -0.25,   # -25% EPS decline
        }
        revenue_growth, revenue_score = calculator.calculate_revenue_growth(negative_growth)
        eps_growth, eps_score = calculator.calculate_eps_growth(negative_growth)
        print(f'   Revenue Growth: {revenue_growth:.1%}, Score: {revenue_score:.1f} ✅')
        print(f'   EPS Growth: {eps_growth:.1%}, Score: {eps_score:.1f} ✅')
        
        # Test with missing growth data
        print('Testing with missing EPS growth...')
        missing_data = {'revenue_growth': 0.08}
        eps_growth, eps_score = calculator.calculate_eps_growth(missing_data)
        print(f'   Result: EPS Growth={eps_growth}, Score={eps_score} ✅')
        
        # Test with extreme growth values
        print('Testing with extreme revenue growth...')
        extreme_growth = {
            'revenue_growth': 2.5,      # 250% growth (possibly acquisition)
            'earnings_growth': 5.0,     # 500% EPS growth
        }
        revenue_growth, revenue_score = calculator.calculate_revenue_growth(extreme_growth)
        eps_growth, eps_score = calculator.calculate_eps_growth(extreme_growth)
        print(f'   Result: Revenue={revenue_growth:.1%}, Score={revenue_score:.1f} ✅')
        print(f'   Result: EPS={eps_growth:.1%}, Score={eps_score:.1f} ✅')
        
        return True
        
    except Exception as e:
        print(f'❌ Edge cases test failed: {str(e)}')
        return False

def run_growth_calculator_tests():
    """Run all growth calculator tests"""
    print('📈 StockAnalyzer Pro - Growth Calculator Tests')
    print('=' * 60)
    
    # Setup logging
    logger = setup_logging("INFO")
    
    tests = [
        ("Individual Growth Calculations", test_individual_growth_calculations),
        ("Sector Weight Adjustments", test_sector_weight_adjustments),
        ("AAPL Growth Analysis", test_aapl_growth_analysis),
        ("Sector-Specific Scoring", test_sector_specific_scoring),
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
        print('\n🎉 All growth calculator tests passed!')
        print('\n📈 Growth Calculator (20% Component) Implementation:')
        print('   ✅ Revenue growth calculation and sector-adjusted scoring')
        print('   ✅ EPS growth calculation with sector-specific thresholds')
        print('   ✅ Revenue stability assessment (simplified for POC)')
        print('   ✅ Forward growth estimation from P/E ratios')
        print('   ✅ Sector-specific component weighting (Tech, Healthcare, Utilities, etc.)')
        print('   ✅ Database integration and persistence')
        print('   ✅ Edge case handling (negative growth, missing data)')
        
        return True
    else:
        print(f'\n⚠️  {total - passed} test(s) failed. Please fix before proceeding.')
        return False

if __name__ == "__main__":
    success = run_growth_calculator_tests()
    
    if success:
        print('\n🚀 Growth Calculator ready! Next: Sentiment Analysis (15%)')
    else:
        print('\n🔧 Please fix growth calculator issues before proceeding.')
        sys.exit(1)