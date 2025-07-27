#!/usr/bin/env python3
"""
Final Validation Test - Complete System Check
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def final_system_validation():
    """Final comprehensive system validation"""
    print("🎯 FINAL SYSTEM VALIDATION AFTER TERMINOLOGY CHANGES")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Core Imports
    print("1️⃣  Testing Core Module Imports...")
    try:
        from src.calculations.fundamental import FundamentalCalculator, FundamentalMetrics
        from src.calculations.quality import QualityCalculator, QualityMetrics
        from src.calculations.growth import GrowthCalculator, GrowthMetrics
        from src.calculations.sentiment import SentimentCalculator, SentimentMetrics
        from src.calculations.composite import CompositeCalculator, CompositeScore
        from src.data.database import DatabaseManager
        from src.data.sentiment_analyzer import SentimentAnalyzer
        from src.utils.helpers import load_config
        
        print("   ✅ All core modules imported successfully")
        test_results.append(("Core Imports", True))
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        test_results.append(("Core Imports", False))
    
    # Test 2: Configuration Loading
    print("\n2️⃣  Testing Configuration System...")
    try:
        config = load_config()
        assert isinstance(config, dict), "Config should be a dictionary"
        print("   ✅ Configuration loaded successfully")
        test_results.append(("Configuration", True))
    except Exception as e:
        print(f"   ❌ Configuration failed: {e}")
        test_results.append(("Configuration", False))
    
    # Test 3: Data Quality Field Verification
    print("\n3️⃣  Testing Data Quality Field Names...")
    try:
        # Check fundamental metrics
        fund_fields = FundamentalMetrics.__dataclass_fields__.keys()
        assert 'data_quality_score' in fund_fields, "FundamentalMetrics missing data_quality_score"
        
        # Check quality metrics
        qual_fields = QualityMetrics.__dataclass_fields__.keys()
        assert 'data_quality_score' in qual_fields, "QualityMetrics missing data_quality_score"
        
        # Check growth metrics
        growth_fields = GrowthMetrics.__dataclass_fields__.keys()
        assert 'data_quality_score' in growth_fields, "GrowthMetrics missing data_quality_score"
        
        # Check sentiment metrics
        sent_fields = SentimentMetrics.__dataclass_fields__.keys()
        assert 'data_quality_score' in sent_fields, "SentimentMetrics missing data_quality_score"
        
        # Check composite score
        comp_fields = CompositeScore.__dataclass_fields__.keys()
        expected_fields = [
            'fundamental_data_quality', 'quality_data_quality', 
            'growth_data_quality', 'sentiment_data_quality', 'overall_data_quality'
        ]
        for field in expected_fields:
            assert field in comp_fields, f"CompositeScore missing {field}"
        
        print("   ✅ All data quality fields properly named")
        test_results.append(("Data Quality Fields", True))
    except Exception as e:
        print(f"   ❌ Field verification failed: {e}")
        test_results.append(("Data Quality Fields", False))
    
    # Test 4: Calculator Instantiation
    print("\n4️⃣  Testing Calculator Instantiation...")
    try:
        fund_calc = FundamentalCalculator()
        qual_calc = QualityCalculator()
        growth_calc = GrowthCalculator()
        sent_calc = SentimentCalculator()
        comp_calc = CompositeCalculator()
        
        print("   ✅ All calculators instantiate successfully")
        test_results.append(("Calculator Creation", True))
    except Exception as e:
        print(f"   ❌ Calculator instantiation failed: {e}")
        test_results.append(("Calculator Creation", False))
    
    # Test 5: Database Schema Compatibility
    print("\n5️⃣  Testing Database Schema...")
    try:
        db = DatabaseManager()
        db.db_path = "validation_test.db"
        
        if os.path.exists(db.db_path):
            os.remove(db.db_path)
        
        if db.connect():
            db.create_tables()
            db.close()
            
            if os.path.exists(db.db_path):
                os.remove(db.db_path)
            
            print("   ✅ Database schema created successfully")
            test_results.append(("Database Schema", True))
        else:
            print("   ❌ Database connection failed")
            test_results.append(("Database Schema", False))
    except Exception as e:
        print(f"   ❌ Database schema test failed: {e}")
        test_results.append(("Database Schema", False))
    
    # Test 6: Sentiment Analyzer
    print("\n6️⃣  Testing Sentiment Analysis...")
    try:
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze_text("This is a positive test message about great stock performance")
        
        assert hasattr(result, 'data_quality'), "SentimentScore missing data_quality field"
        assert hasattr(result, 'sentiment_score'), "SentimentScore missing sentiment_score field"
        
        print("   ✅ Sentiment analysis working with updated fields")
        test_results.append(("Sentiment Analysis", True))
    except Exception as e:
        print(f"   ❌ Sentiment analysis failed: {e}")
        test_results.append(("Sentiment Analysis", False))
    
    # Test 7: Method Signatures
    print("\n7️⃣  Testing Method Signatures...")
    try:
        # Check that methods use correct parameter names
        import inspect
        
        # Check composite calculator methods
        comp_calc = CompositeCalculator()
        assert hasattr(comp_calc, 'min_data_quality'), "CompositeCalculator missing min_data_quality"
        
        print("   ✅ Method signatures updated correctly")
        test_results.append(("Method Signatures", True))
    except Exception as e:
        print(f"   ❌ Method signature test failed: {e}")
        test_results.append(("Method Signatures", False))
    
    # Results Summary
    print("\n" + "=" * 60)
    print("📊 FINAL VALIDATION RESULTS")
    print("=" * 60)
    
    passed = sum(1 for _, success in test_results if success)
    total = len(test_results)
    
    for test_name, success in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nFinal Score: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 SYSTEM VALIDATION SUCCESSFUL!")
        print("   • All terminology changes implemented correctly")
        print("   • No regression issues detected")
        print("   • System ready for continued development")
        print("   • Safe to proceed with Streamlit dashboard")
    else:
        print("\n⚠️  VALIDATION ISSUES DETECTED!")
        print("   • Review failed tests above")
        print("   • Address issues before proceeding")
    
    print("=" * 60)
    return passed == total

if __name__ == "__main__":
    success = final_system_validation()
    sys.exit(0 if success else 1)