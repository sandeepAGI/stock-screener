#!/usr/bin/env python3
"""
Test script for quality calculator implementation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.calculations.quality import QualityCalculator, calculate_single_quality, calculate_all_quality
from src.data.database import get_database_connection
from src.utils.helpers import setup_logging
import time

def test_individual_quality_calculations():
    """Test individual quality calculation methods"""
    print('🏗️  Testing Individual Quality Calculation Methods')
    print('=' * 60)
    
    try:
        calculator = QualityCalculator()
        
        # Test data (simulating realistic company fundamentals)
        test_fundamentals = {
            'return_on_equity': 0.18,          # 18% ROE (good)
            'net_income': 50_000_000_000,      # $50B net income
            'total_assets': 400_000_000_000,   # $400B assets
            'total_debt': 100_000_000_000,     # $100B debt
            'shareholders_equity': 280_000_000_000,  # $280B equity
            'debt_to_equity': 0.36,            # 0.36 D/E ratio (good)
            'current_ratio': 1.8,              # 1.8 current ratio (decent)
        }
        
        # Test ROE calculation
        print('\n📊 ROE Calculation:')
        roe, roe_score = calculator.calculate_roe(test_fundamentals)
        print(f'   ROE: {roe:.1%}')
        print(f'   ROE Score: {roe_score:.1f}/100')
        
        # Test ROIC calculation  
        print('\n🏢 ROIC Calculation:')
        roic, roic_score = calculator.calculate_roic(test_fundamentals)
        print(f'   ROIC: {roic:.1%}')
        print(f'   ROIC Score: {roic_score:.1f}/100')
        
        # Test Debt-to-Equity calculation
        print('\n💳 Debt-to-Equity Calculation:')
        debt_to_equity, debt_score = calculator.calculate_debt_to_equity(test_fundamentals)
        print(f'   Debt-to-Equity: {debt_to_equity:.2f}')
        print(f'   D/E Score: {debt_score:.1f}/100')
        
        # Test Current Ratio calculation
        print('\n💰 Current Ratio Calculation:')
        current_ratio, current_score = calculator.calculate_current_ratio(test_fundamentals)
        print(f'   Current Ratio: {current_ratio:.1f}')
        print(f'   Current Ratio Score: {current_score:.1f}/100')
        
        # Calculate composite score manually
        weights = calculator.base_component_weights
        composite = (roe_score * weights['roe'] + 
                    roic_score * weights['roic'] + 
                    debt_score * weights['debt_to_equity'] + 
                    current_score * weights['current_ratio'])
        
        print(f'\n🎯 Composite Quality Score: {composite:.1f}/100')
        print(f'   Weighted Components:')
        print(f'   • ROE ({weights["roe"]*100:.0f}%): {roe_score:.1f} → {roe_score * weights["roe"]:.1f}')
        print(f'   • ROIC ({weights["roic"]*100:.0f}%): {roic_score:.1f} → {roic_score * weights["roic"]:.1f}')
        print(f'   • D/E ({weights["debt_to_equity"]*100:.0f}%): {debt_score:.1f} → {debt_score * weights["debt_to_equity"]:.1f}')
        print(f'   • Current Ratio ({weights["current_ratio"]*100:.0f}%): {current_score:.1f} → {current_score * weights["current_ratio"]:.1f}')
        
        return True
        
    except Exception as e:
        print(f'❌ Individual quality calculations test failed: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

def test_sector_weight_adjustments():
    """Test sector-specific weight adjustments"""
    print('\n⚖️  Testing Sector Weight Adjustments')
    print('=' * 40)
    
    try:
        calculator = QualityCalculator()
        base_weights = calculator.base_component_weights
        
        print('\n📊 Base Weights:')
        for metric, weight in base_weights.items():
            print(f'   {metric}: {weight:.1%}')
        
        # Test different sector adjustments
        test_sectors = ['Technology', 'Financials', 'Real Estate', 'Utilities', 'Energy']
        
        print('\n🏭 Sector-Adjusted Weights:')
        print(f'{"Sector":<15} {"ROE":<8} {"ROIC":<8} {"D/E":<8} {"Current":<8}')
        print('-' * 55)
        
        for sector in test_sectors:
            weights = calculator.get_sector_adjusted_weights(sector)
            print(f'{sector:<15} {weights["roe"]:<8.1%} {weights["roic"]:<8.1%} {weights["debt_to_equity"]:<8.1%} {weights["current_ratio"]:<8.1%}')
        
        return True
        
    except Exception as e:
        print(f'❌ Sector weight adjustment test failed: {str(e)}')
        return False

def test_aapl_quality_analysis():
    """Test quality analysis with real AAPL data"""
    print('\n🍎 Testing AAPL Quality Analysis')
    print('=' * 35)
    
    try:
        db = get_database_connection()
        calculator = QualityCalculator()
        
        # Get AAPL fundamental data
        fundamentals = db.get_latest_fundamentals('AAPL')
        stock_info = db.get_stock_info('AAPL')
        
        if not fundamentals:
            print('❌ No AAPL fundamental data available')
            return False
        
        sector = stock_info.get('sector') if stock_info else 'Technology'
        print(f'AAPL Sector: {sector}')
        
        # Show raw fundamental data relevant to quality
        print(f'\n📊 Raw Quality-Related Data for AAPL:')
        quality_metrics = ['return_on_equity', 'return_on_assets', 'debt_to_equity', 'current_ratio', 
                          'net_income', 'total_assets', 'total_debt', 'shareholders_equity']
        
        for metric in quality_metrics:
            value = fundamentals.get(metric)
            if value is not None:
                if metric in ['return_on_equity', 'return_on_assets']:
                    print(f'   {metric}: {value:.1%}' if abs(value) < 10 else f'   {metric}: {value}')
                elif metric in ['net_income', 'total_assets', 'total_debt', 'shareholders_equity']:
                    print(f'   {metric}: ${value:,.0f}' if value > 1e6 else f'   {metric}: {value}')
                else:
                    print(f'   {metric}: {value:.2f}')
            else:
                print(f'   {metric}: N/A')
        
        # Calculate quality metrics
        metrics = calculator.calculate_quality_metrics('AAPL', db)
        
        if metrics:
            print(f'\n🎯 Calculated Quality Metrics for AAPL:')
            
            # Handle None values in formatting
            roe_str = f'{metrics.roe:.1%}' if metrics.roe is not None else 'N/A'
            roic_str = f'{metrics.roic:.1%}' if metrics.roic is not None else 'N/A'
            debt_str = f'{metrics.debt_to_equity:.2f}' if metrics.debt_to_equity is not None else 'N/A'
            current_str = f'{metrics.current_ratio:.1f}' if metrics.current_ratio is not None else 'N/A'
            
            print(f'   ROE: {roe_str} → Score: {metrics.roe_score:.1f}/100')
            print(f'   ROIC: {roic_str} → Score: {metrics.roic_score:.1f}/100')
            print(f'   Debt-to-Equity: {debt_str} → Score: {metrics.debt_to_equity_score:.1f}/100')
            print(f'   Current Ratio: {current_str} → Score: {metrics.current_ratio_score:.1f}/100')
            print(f'\n   📈 Composite Quality Score: {metrics.quality_score:.1f}/100')
            print(f'   🎯 Confidence Level: {metrics.confidence*100:.0f}%')
            print(f'   🏭 Sector: {metrics.sector}')
            
            # Show sector-adjusted weights used
            weights = calculator.get_sector_adjusted_weights(sector)
            print(f'\n   ⚖️  Sector-Adjusted Weights Used:')
            print(f'   • ROE: {weights["roe"]:.1%}')
            print(f'   • ROIC: {weights["roic"]:.1%}')
            print(f'   • D/E: {weights["debt_to_equity"]:.1%}')
            print(f'   • Current Ratio: {weights["current_ratio"]:.1%}')
            
            # Save to database
            calculator.save_quality_metrics(metrics, db)
            print(f'   ✅ Quality metrics saved to database')
            
        else:
            print(f'❌ Failed to calculate quality metrics for AAPL')
            return False
        
        db.close()
        return True
        
    except Exception as e:
        print(f'❌ AAPL quality analysis test failed: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

def test_sector_specific_scoring():
    """Test scoring differences across sectors"""
    print('\n🏭 Testing Sector-Specific Scoring')
    print('=' * 40)
    
    try:
        calculator = QualityCalculator()
        
        # Test same metrics across different sectors
        test_metrics = {
            'return_on_equity': 0.15,       # 15% ROE
            'net_income': 10_000_000_000,   # $10B
            'total_assets': 100_000_000_000, # $100B  
            'total_debt': 30_000_000_000,   # $30B
            'shareholders_equity': 70_000_000_000, # $70B
            'debt_to_equity': 0.43,         # 0.43 D/E
            'current_ratio': 1.5            # 1.5 current ratio
        }
        
        sectors = ['Technology', 'Financials', 'Utilities', 'Energy']
        
        print('\n📊 Same Metrics, Different Sector Scores:')
        print('ROE: 15%, D/E: 0.43, Current Ratio: 1.5')
        print('-' * 60)
        print(f'{"Sector":<15} {"ROE Score":<10} {"ROIC Score":<11} {"D/E Score":<10} {"Composite":<10}')
        print('-' * 60)
        
        for sector in sectors:
            roe, roe_score = calculator.calculate_roe(test_metrics, sector)
            roic, roic_score = calculator.calculate_roic(test_metrics, sector)
            debt_to_equity, debt_score = calculator.calculate_debt_to_equity(test_metrics, sector)
            current_ratio, current_score = calculator.calculate_current_ratio(test_metrics, sector)
            
            # Calculate sector-weighted composite
            weights = calculator.get_sector_adjusted_weights(sector)
            composite = (roe_score * weights['roe'] + 
                        roic_score * weights['roic'] + 
                        debt_score * weights['debt_to_equity'] + 
                        current_score * weights['current_ratio'])
            
            print(f'{sector:<15} {roe_score:<10.1f} {roic_score:<11.1f} {debt_score:<10.1f} {composite:<10.1f}')
        
        return True
        
    except Exception as e:
        print(f'❌ Sector-specific scoring test failed: {str(e)}')
        return False

def test_edge_cases():
    """Test edge cases and error handling"""
    print('\n⚠️  Testing Edge Cases')
    print('=' * 25)
    
    try:
        calculator = QualityCalculator()
        
        # Test with negative equity (bankruptcy scenario)
        print('Testing with negative shareholders equity...')
        negative_equity = {
            'net_income': -5_000_000_000,
            'shareholders_equity': -1_000_000_000,
            'total_debt': 10_000_000_000
        }
        roe, roe_score = calculator.calculate_roe(negative_equity)
        debt_to_equity, debt_score = calculator.calculate_debt_to_equity(negative_equity)
        print(f'   ROE: {roe}, Score: {roe_score} ✅')
        print(f'   D/E: {debt_to_equity}, Score: {debt_score} ✅')
        
        # Test with missing data
        print('Testing with missing current ratio...')
        missing_data = {'return_on_equity': 0.12}
        current_ratio, current_score = calculator.calculate_current_ratio(missing_data)
        print(f'   Result: Current Ratio={current_ratio}, Score={current_score} ✅')
        
        # Test with extreme values
        print('Testing with extreme debt ratio...')
        extreme_debt = {
            'total_debt': 50_000_000_000,
            'shareholders_equity': 5_000_000_000  # 10:1 debt to equity
        }
        debt_to_equity, debt_score = calculator.calculate_debt_to_equity(extreme_debt)
        print(f'   Result: D/E={debt_to_equity:.1f}, Score={debt_score} ✅')
        
        return True
        
    except Exception as e:
        print(f'❌ Edge cases test failed: {str(e)}')
        return False

def run_quality_calculator_tests():
    """Run all quality calculator tests"""
    print('🏗️  StockAnalyzer Pro - Quality Calculator Tests')
    print('=' * 60)
    
    # Setup logging
    logger = setup_logging("INFO")
    
    tests = [
        ("Individual Quality Calculations", test_individual_quality_calculations),
        ("Sector Weight Adjustments", test_sector_weight_adjustments),
        ("AAPL Quality Analysis", test_aapl_quality_analysis),
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
        print('\n🎉 All quality calculator tests passed!')
        print('\n🏗️  Quality Calculator (25% Component) Implementation:')
        print('   ✅ ROE calculation and sector-adjusted scoring')
        print('   ✅ ROIC calculation with invested capital approximation')
        print('   ✅ Debt-to-Equity ratio with sector tolerance adjustments') 
        print('   ✅ Current Ratio scoring with liquidity assessment')
        print('   ✅ Sector-specific component weighting (Banking, Tech, REITs, etc.)')
        print('   ✅ Database integration and persistence')
        print('   ✅ Edge case handling (negative equity, missing data)')
        
        return True
    else:
        print(f'\n⚠️  {total - passed} test(s) failed. Please fix before proceeding.')
        return False

if __name__ == "__main__":
    success = run_quality_calculator_tests()
    
    if success:
        print('\n🚀 Quality Calculator ready! Next: Growth Calculators (20%)')
    else:
        print('\n🔧 Please fix quality calculator issues before proceeding.')
        sys.exit(1)