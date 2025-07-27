# StockAnalyzer Pro - Methodology Documentation

## Overview

This document provides detailed documentation of the calculation methodologies, assumptions, and sector adjustments used in StockAnalyzer Pro's automated stock mispricing detection system. The methodology combines four weighted components to generate composite scores for outlier detection.

**Composite Methodology Weights:**
- **Fundamental Valuation**: 40%
- **Quality Metrics**: 25% 
- **Growth Analysis**: 20%
- **Sentiment Analysis**: 15%

---

## 1. Fundamental Valuation (40% Weight)

### 1.1 Overview

The Fundamental Valuation component evaluates stock pricing relative to underlying business fundamentals using four key metrics. Each metric is scored 0-100 using sector-adjusted thresholds, then combined into a weighted composite score.

**Component Weights:**
- P/E Ratio: 30%
- EV/EBITDA: 25%
- PEG Ratio: 25%
- Free Cash Flow Yield: 20%

### 1.2 Individual Metric Calculations

#### 1.2.1 Price-to-Earnings (P/E) Ratio

**Formula:**
```
P/E Ratio = Current Stock Price / Earnings Per Share (Trailing 12 Months)
```

**Data Source:** Yahoo Finance `pe_ratio` field

**Scoring Methodology:**
- Lower P/E ratios receive higher scores (inverse relationship)
- Sector-adjusted thresholds account for industry-specific valuation norms
- Score calculation uses piecewise linear interpolation between threshold bands

**Base Scoring Thresholds:**
| Score Range | P/E Threshold | Interpretation |
|-------------|---------------|----------------|
| 90-100 | < 15 | Excellent value |
| 70-89 | 15-20 | Good value |
| 50-69 | 20-25 | Fair value |
| 30-49 | 25-35 | Expensive |
| 0-29 | ≥ 35 | Very expensive |

**Sector Adjustments:**
- Technology: +40% threshold adjustment (recognizes growth premium)
- Financials: -20% threshold adjustment (lower growth expectations)
- Energy: -30% threshold adjustment (cyclical earnings volatility)
- Utilities: -10% threshold adjustment (regulated, stable earnings)

**Calculation Algorithm:**
```python
def calculate_pe_score(pe_ratio, sector_adjusted_thresholds):
    if pe_ratio < thresholds['excellent']:
        score = 90 + (thresholds['excellent'] - pe_ratio) / thresholds['excellent'] * 10
    elif pe_ratio < thresholds['good']:
        score = 70 + (thresholds['good'] - pe_ratio) / (thresholds['good'] - thresholds['excellent']) * 20
    # ... additional bands
    return max(0, min(100, score))
```

**Key Assumptions:**
- Trailing 12-month EPS provides more stable basis than forward estimates
- P/E ratios above 50 indicate speculative pricing regardless of sector
- Negative earnings result in zero score (P/E ratio undefined)

#### 1.2.2 Enterprise Value to EBITDA (EV/EBITDA)

**Formula:**
```
EV/EBITDA = Enterprise Value / EBITDA (Trailing 12 Months)
Enterprise Value = Market Cap + Total Debt - Cash
```

**Data Source:** Yahoo Finance `ev_to_ebitda` field, with fallback calculation using `enterprise_value` and `operating_cash_flow` as EBITDA proxy

**Scoring Methodology:**
- Lower EV/EBITDA ratios receive higher scores
- Less affected by capital structure differences than P/E
- Particularly relevant for capital-intensive industries

**Base Scoring Thresholds:**
| Score Range | EV/EBITDA Threshold | Interpretation |
|-------------|---------------------|----------------|
| 90-100 | < 10 | Excellent value |
| 70-89 | 10-15 | Good value |
| 50-69 | 15-20 | Fair value |
| 30-49 | 20-30 | Expensive |
| 0-29 | ≥ 30 | Very expensive |

**Sector Adjustments:**
- Technology: +30% threshold adjustment (high margins, growth premium)
- Financials: -30% threshold adjustment (EV/EBITDA less relevant for banks)
- Healthcare: +15% threshold adjustment (R&D investments, patent premiums)
- Energy: -20% threshold adjustment (commodity cycle considerations)

**Fallback Calculation:**
When EV/EBITDA is not available, we approximate using:
```
EV/Operating Cash Flow Ratio = Enterprise Value / Operating Cash Flow
```
This provides a reasonable proxy while maintaining scoring consistency.

**Key Assumptions:**
- EBITDA provides better comparison across companies than net earnings
- Operating cash flow serves as acceptable EBITDA proxy when unavailable
- Enterprise value captures true cost of acquiring the business

#### 1.2.3 PEG Ratio (Price/Earnings to Growth)

**Formula:**
```
PEG Ratio = (P/E Ratio) / (Earnings Growth Rate %)
```

**Data Source:** Yahoo Finance `trailingPegRatio` field (trailing P/E divided by trailing earnings growth rate)

**Scoring Methodology:**
- Lower PEG ratios indicate better value relative to growth
- Peter Lynch's "PEG < 1.0 = fair value" principle adapted for sector context
- Growth rates converted to percentage terms for calculation

**Base Scoring Thresholds:**
| Score Range | PEG Threshold | Interpretation |
|-------------|---------------|----------------|
| 90-100 | < 0.5 | Excellent growth value |
| 70-89 | 0.5-1.0 | Good growth value |
| 50-69 | 1.0-1.5 | Fair growth value |
| 30-49 | 1.5-2.0 | Expensive for growth |
| 0-29 | ≥ 2.0 | Very expensive for growth |

**Sector Adjustments:**
- Technology: +20% threshold adjustment (higher sustainable growth rates)
- Energy: -40% threshold adjustment (cyclical earnings make growth unreliable)
- Utilities: -20% threshold adjustment (low growth expectations)
- Consumer Staples: -10% threshold adjustment (mature, stable growth)

**Growth Rate Handling:**
```python
# Convert growth rate to percentage if needed
growth_rate_pct = earnings_growth * 100 if earnings_growth < 1 else earnings_growth
if growth_rate_pct > 0:
    peg_ratio = pe_ratio / growth_rate_pct
```

**Key Assumptions:**
- Historical earnings growth provides reasonable proxy for future growth
- Negative growth rates result in zero PEG score
- Very low PEG ratios (< 0.3) may indicate data quality issues or unsustainable growth

#### 1.2.4 Free Cash Flow Yield

**Formula:**
```
FCF Yield = Free Cash Flow (TTM) / Market Capitalization
```

**Data Source:** Yahoo Finance `free_cash_flow` and `market_cap` fields

**Scoring Methodology:**
- Higher FCF yields receive higher scores (direct relationship)
- Less susceptible to accounting manipulation than earnings-based metrics
- Critical for dividend sustainability and capital allocation assessment

**Base Scoring Thresholds:**
| Score Range | FCF Yield Threshold | Interpretation |
|-------------|---------------------|----------------|
| 90-100 | > 8% | Excellent cash generation |
| 70-89 | 5-8% | Good cash generation |
| 50-69 | 3-5% | Adequate cash generation |
| 30-49 | 1-3% | Weak cash generation |
| 0-29 | ≤ 0% | Negative cash generation |

**Sector Weight Adjustments:**
Rather than adjusting thresholds, FCF receives sector-specific weighting adjustments:
- Real Estate (REITs): +30% weight (FCF critical for distributions)
- Utilities: +15% weight (FCF important for dividends and infrastructure)
- Energy: +20% weight (FCF crucial in commodity cycles)
- Financials: -20% weight (different capital structure, focus on ROE instead)

**Key Assumptions:**
- Free cash flow represents actual cash available to shareholders
- TTM provides more stable measure than quarterly variations
- Negative FCF may be acceptable for high-growth companies (scored as zero)

### 1.3 Sector-Specific Adjustments

#### 1.3.1 Sector Profiles

The system includes 11 comprehensive sector profiles with specific adjustment factors:

| Sector | P/E Multiplier | EV/EBITDA Multiplier | PEG Multiplier | FCF Weight | Growth Expectation |
|--------|----------------|----------------------|----------------|------------|-------------------|
| Technology | 1.4x | 1.3x | 1.2x | 1.1x | High |
| Financials | 0.8x | 0.7x | 0.9x | 0.8x | Low |
| Healthcare | 1.2x | 1.15x | 1.1x | 1.0x | Medium |
| Consumer Discretionary | 1.1x | 1.1x | 1.0x | 1.0x | Medium |
| Consumer Staples | 1.0x | 1.0x | 0.9x | 1.1x | Low |
| Industrials | 0.95x | 1.0x | 0.95x | 1.0x | Medium |
| Energy | 0.7x | 0.8x | 0.6x | 1.2x | Low |
| Utilities | 0.9x | 0.9x | 0.8x | 1.15x | Low |
| Materials | 0.85x | 0.9x | 0.8x | 1.0x | Low |
| Communication Services | 1.3x | 1.2x | 1.15x | 1.0x | High |
| Real Estate | 0.8x | 0.7x | 0.8x | 1.3x | Low |

#### 1.3.2 Rationale for Sector Adjustments

**Technology Sector (+40% P/E tolerance):**
- Higher sustainable growth rates justify premium valuations
- Network effects and scalability support higher margins
- Innovation-driven competitive advantages

**Energy Sector (-30% P/E expectations):**
- Highly cyclical earnings make P/E ratios unreliable
- Commodity price volatility affects valuation metrics
- Enhanced focus on FCF during commodity cycles

**Financial Sector (-20% P/E expectations):**
- Regulated industry with lower growth potential
- Different capital structure (leverage is operational, not structural)
- Book value and ROE more relevant than EV/EBITDA

**Real Estate (REITs) (+30% FCF focus):**
- Required distributions make FCF critical
- Tax structure differences affect traditional metrics
- Asset-heavy business model with different valuation norms

### 1.4 Component Weighting and Composite Calculation

#### 1.4.1 Base Component Weights
```python
base_weights = {
    'pe_ratio': 0.30,      # Most important valuation metric
    'ev_ebitda': 0.25,     # Enterprise value assessment
    'peg_ratio': 0.25,     # Growth-adjusted valuation
    'fcf_yield': 0.20      # Cash generation quality
}
```

#### 1.4.2 Sector Weight Adjustments

FCF weight is adjusted based on sector characteristics, with other weights rebalanced proportionally:

```python
def get_sector_adjusted_weights(sector):
    fcf_adjustment = get_fcf_weight_adjustment(sector)
    new_fcf_weight = base_fcf_weight * fcf_adjustment
    new_fcf_weight = max(0.10, min(0.40, new_fcf_weight))  # Bounds check
    
    # Rebalance other weights proportionally
    remaining_weight = 1.0 - new_fcf_weight
    other_weight_sum = sum(other_base_weights)
    adjustment_factor = remaining_weight / other_weight_sum
    
    return adjusted_weights
```

#### 1.4.3 Composite Score Calculation

```python
def calculate_fundamental_score(pe_score, ev_score, peg_score, fcf_score, weights):
    # Only include valid scores (non-zero) in composite
    valid_scores = [(score, weight) for score, weight in zip(scores, weights) if score > 0]
    
    if not valid_scores:
        return 0.0, 0.0
    
    # Recalculate weights for available metrics
    total_weight = sum(weight for _, weight in valid_scores)
    normalized_scores = [(score * weight / total_weight) for score, weight in valid_scores]
    
    composite_score = sum(normalized_scores)
    data_quality_score = len(valid_scores) / 4  # Based on data completeness
    
    return composite_score, data_quality_score
```

### 1.5 Data Quality Assessment

#### 1.5.1 Data Sources and Quality
- **Primary Source:** Yahoo Finance API via yfinance library
- **Update Frequency:** Daily for prices, quarterly for fundamentals
- **Quality Score:** Based on data completeness and freshness

#### 1.5.2 Data Quality Calculation
```python
data_quality = (number_of_valid_metrics / 4) * source_quality_score
```

Where:
- `number_of_valid_metrics`: Count of successfully calculated metrics (0-4)
- `source_quality_score`: Source reliability score (0.8-1.0 for Yahoo Finance)

#### 1.5.3 Missing Data Handling
- **P/E Ratio:** Zero score if negative earnings or missing data
- **EV/EBITDA:** Fallback to EV/Operating Cash Flow approximation
- **PEG Ratio:** Uses Yahoo Finance trailingPegRatio directly
- **FCF Yield:** Zero score if negative FCF or missing market cap

### 1.6 Limitations and Assumptions

#### 1.6.1 Data Limitations
- **Trailing 12-month data:** May not reflect current business conditions
- **Yahoo Finance accuracy:** Occasional data quality issues or delays
- **Sector classification:** Reliance on Yahoo Finance sector assignments
- **Currency effects:** No adjustment for international stocks

#### 1.6.2 Methodological Assumptions
- **Linear scoring:** Assumes linear relationship between metric values and investment attractiveness within bands
- **Sector stability:** Assumes sector characteristics remain relatively stable over time
- **Growth predictability:** Historical growth rates proxy for future expectations
- **Market efficiency:** Assumes temporary mispricings exist but markets eventually correct

#### 1.6.3 Calculation Edge Cases
- **Extreme values:** P/E ratios > 200 or negative are capped/zeroed
- **Missing growth:** PEG calculation skipped if growth rate unavailable or negative
- **Micro-cap stocks:** May have lower data quality and higher volatility
- **Recent IPOs:** Limited historical data affects metric reliability

### 1.7 Validation and Calibration

#### 1.7.1 Threshold Calibration
- Base thresholds derived from academic literature and industry best practices
- Sector adjustments based on historical sector median valuations
- Periodic recalibration recommended as market conditions evolve

#### 1.7.2 Example Calculation: AAPL

**Raw Metrics (as of implementation):**
- P/E Ratio: 33.38
- EV/EBITDA: 23.35
- PEG Ratio: 4.28 (calculated)
- FCF Yield: 3.0%
- Sector: Technology

**Sector-Adjusted Scoring:**
- P/E Score: 54.6/100 (vs 33.2 without sector adjustment)
- EV/EBITDA Score: 58.2/100 (vs 43.3 without sector adjustment)
- PEG Score: 9.7/100 (limited improvement due to high PEG)
- FCF Yield Score: 50.4/100 (no threshold adjustment, slight weight increase)

**Composite Calculation:**
```
Fundamental Score = (54.6 × 0.292) + (58.2 × 0.244) + (9.7 × 0.244) + (50.4 × 0.220)
                  = 15.9 + 14.2 + 2.4 + 11.1
                  = 43.6/100
```

**Data Quality:** 100% (all four metrics successfully calculated)

This represents a significant improvement from the non-sector-adjusted score of 33.2, better reflecting AAPL's reasonable valuation within the technology sector context.

---

## 2. Quality Metrics (25% Weight)

### 2.1 Overview

The Quality Metrics component evaluates the financial health and operational efficiency of companies using four key indicators of business quality. Quality metrics help distinguish financially sound companies from those with structural weaknesses or unsustainable business models.

**Component Weights:**
- Return on Equity (ROE): 35%
- Return on Invested Capital (ROIC): 30%
- Debt-to-Equity Ratio: 20%
- Current Ratio: 15%

### 2.2 Individual Metric Calculations

#### 2.2.1 Return on Equity (ROE)

**Formula:**
```
ROE = Net Income / Shareholders' Equity
```

**Data Source:** Yahoo Finance `return_on_equity` field with fallback calculation from `net_income` and `shareholders_equity`

**Scoring Methodology:**
- Higher ROE values receive higher scores
- Sector-adjusted thresholds account for industry capital intensity and regulatory environment
- Negative ROE indicates poor profitability and receives very low scores

**Base Scoring Thresholds:**
| Score Range | ROE Threshold | Interpretation |
|-------------|---------------|----------------|
| 90-100 | > 20% | Excellent profitability |
| 70-89 | 15-20% | Good profitability |
| 50-69 | 10-15% | Average profitability |
| 30-49 | 5-10% | Weak profitability |
| 0-29 | ≤ 0% | Poor/negative profitability |

**Sector Adjustments:**
- Financials: +30% threshold adjustment (leverage amplifies returns, higher expectations)
- Technology: +20% threshold adjustment (scalable business models enable higher ROE)
- Utilities: -20% threshold adjustment (regulated returns, asset-heavy operations)
- Real Estate: Standard thresholds (asset-heavy but leveraged structure)

**Key Assumptions:**
- ROE reflects management's effectiveness in generating profits from shareholders' investments
- Extremely high ROE (>50%) may indicate accounting issues or unsustainable leverage
- Negative ROE below -50% indicates severe financial distress

#### 2.2.2 Return on Invested Capital (ROIC)

**Formula:**
```
ROIC = Net Income / Invested Capital
Where: Invested Capital ≈ Total Assets - Total Debt (approximation)
```

**Data Source:** Calculated from Yahoo Finance `net_income`, `total_assets`, and `total_debt` fields

**Scoring Methodology:**
- Higher ROIC indicates better capital allocation efficiency
- Less affected by capital structure differences than ROE
- Critical metric for evaluating management's investment decisions

**Base Scoring Thresholds:**
| Score Range | ROIC Threshold | Interpretation |
|-------------|----------------|----------------|
| 90-100 | > 15% | Excellent capital efficiency |
| 70-89 | 12-15% | Good capital efficiency |
| 50-69 | 8-12% | Average capital efficiency |
| 30-49 | 4-8% | Weak capital efficiency |
| 0-29 | ≤ 0% | Poor capital allocation |

**Sector Adjustments:**
- Technology: +30% threshold adjustment (asset-light, high-margin business models)
- Utilities: -40% threshold adjustment (regulated asset base, mandated investments)
- Real Estate: -30% threshold adjustment (asset-heavy REITs, different return profiles)
- Energy: Standard thresholds (capital intensive but cyclical)

**Calculation Notes:**
- ROIC approximation uses available balance sheet data
- More sophisticated calculation would use NOPAT and exclude cash from invested capital
- Negative ROIC below -30% indicates severe capital destruction

#### 2.2.3 Debt-to-Equity Ratio

**Formula:**
```
Debt-to-Equity = Total Debt / Shareholders' Equity
```

**Data Source:** Yahoo Finance `debt_to_equity` field with fallback calculation from balance sheet components

**Scoring Methodology:**
- Lower debt ratios generally receive higher scores (conservative approach)
- Sector adjustments reflect different capital structure norms
- Extreme ratios may indicate financial distress or aggressive financing

**Base Scoring Thresholds:**
| Score Range | D/E Threshold | Interpretation |
|-------------|---------------|----------------|
| 90-100 | < 0.3 | Conservative leverage |
| 70-89 | 0.3-0.5 | Moderate leverage |
| 50-69 | 0.5-1.0 | Average leverage |
| 30-49 | 1.0-2.0 | High leverage |
| 0-29 | ≥ 2.0 | Very high leverage risk |

**Sector Adjustments:**
- Utilities: +100% threshold adjustment (infrastructure financing requires debt)
- Real Estate: +80% threshold adjustment (REITs commonly use leverage)
- Financials: +200% threshold adjustment (different capital structure model)
- Technology: -20% threshold adjustment (should be largely self-funding)
- Energy: Standard thresholds (debt risk varies with commodity cycles)

**Key Assumptions:**
- Higher debt increases financial risk, especially during downturns
- Some sectors (utilities, REITs) naturally operate with higher leverage
- Negative debt-to-equity (negative equity) indicates potential bankruptcy risk

#### 2.2.4 Current Ratio

**Formula:**
```
Current Ratio = Current Assets / Current Liabilities
```

**Data Source:** Yahoo Finance `current_ratio` field

**Scoring Methodology:**
- Higher ratios generally indicate better liquidity, but extremely high ratios may suggest inefficient cash management
- Sector adjustments reflect different working capital requirements
- Ratios below 1.0 indicate potential short-term liquidity issues

**Base Scoring Thresholds:**
| Score Range | Current Ratio Threshold | Interpretation |
|-------------|-------------------------|----------------|
| 90-100 | > 2.5 | Excellent liquidity |
| 70-89 | 2.0-2.5 | Good liquidity |
| 50-69 | 1.5-2.0 | Adequate liquidity |
| 30-49 | 1.0-1.5 | Weak liquidity |
| 0-29 | ≤ 1.0 | Liquidity concern |

**Sector Adjustments:**
- Technology: +10% threshold adjustment (should maintain strong liquidity)
- Utilities: -20% threshold adjustment (predictable cash flows reduce liquidity needs)
- Energy: -10% threshold adjustment (variable working capital due to commodity cycles)
- Financials: Standard thresholds (different liquidity management approach)

**Key Assumptions:**
- Current ratio provides snapshot of short-term financial health
- Very high ratios (>4.0) may indicate excess cash that could be deployed more productively
- Seasonal businesses may show significant quarterly variation

### 2.3 Sector-Specific Weight Adjustments

#### 2.3.1 Sector Weight Profiles

| Sector | ROE Weight | ROIC Weight | D/E Weight | Current Ratio Weight | Rationale |
|--------|------------|-------------|------------|---------------------|-----------|
| **Base Weights** | 35% | 30% | 20% | 15% | Balanced approach |
| **Technology** | 40% | 35% | 15% | 10% | High ROE/ROIC potential, low debt |
| **Financials** | 50% | 25% | 10% | 15% | ROE critical, leverage operational |
| **Real Estate** | 25% | 40% | 25% | 10% | Asset utilization key, debt common |
| **Utilities** | 25% | 25% | 35% | 15% | Regulated returns, debt management crucial |
| **Energy** | 30% | 35% | 25% | 10% | Capital allocation critical, debt risk in cycles |

#### 2.3.2 Weight Adjustment Rationale

**Technology Sector (+5% ROE, +5% ROIC, -5% D/E, -5% Current):**
- Scalable business models can achieve exceptional ROE and ROIC
- Typically asset-light with strong cash generation
- Lower debt requirements due to self-funding capability

**Financial Sector (+15% ROE, -5% ROIC, -10% D/E, +0% Current):**
- ROE most critical metric for bank profitability assessment
- Leverage is operational tool, not structural weakness
- ROIC less relevant due to different business model

**Real Estate (+10% ROIC, -10% ROE, +5% D/E, -5% Current):**
- Asset utilization efficiency most important for REITs
- Leverage commonly used to enhance returns
- Different liquidity management due to asset base

### 2.4 Composite Score Calculation

#### 2.4.1 Sector-Adjusted Composite Calculation

```python
def calculate_quality_score(roe_score, roic_score, debt_score, current_score, sector_weights):
    # Only include valid scores (non-zero) in composite
    valid_scores = [(score, weight) for score, weight in zip(scores, weights) if score > 0]
    
    # Recalculate weights for available metrics
    total_weight = sum(weight for _, weight in valid_scores)
    normalized_scores = [(score * weight / total_weight) for score, weight in valid_scores]
    
    composite_score = sum(normalized_scores)
    data_quality_score = len(valid_scores) / 4  # Based on data completeness
    
    return composite_score, data_quality_score
```

#### 2.4.2 Missing Data Handling

- **ROE**: Zero score if negative shareholders' equity or missing income data
- **ROIC**: Zero score if insufficient balance sheet data for calculation
- **Debt-to-Equity**: Calculate from components if direct ratio unavailable
- **Current Ratio**: Zero score if not provided by data source

### 2.5 Data Quality and Validation

#### 2.5.1 Data Anomaly Detection

The system includes checks for unrealistic values:
- **ROE > 100%**: May indicate data quality issues or share buyback effects
- **D/E > 50**: Extreme leverage indicating potential financial distress
- **Current Ratio > 10**: May suggest excessive cash hoarding

#### 2.5.2 Example Calculation: AAPL Quality Assessment

**Raw Metrics (as of implementation):**
- ROE: 138% (potentially inflated due to share buybacks)
- ROIC: N/A (insufficient balance sheet data)
- Debt-to-Equity: 147 (extremely high, data quality concern)
- Current Ratio: 0.82 (below 1.0, liquidity concern)
- Sector: Technology

**Sector-Adjusted Scoring:**
- ROE Score: 100/100 (capped at maximum despite extreme value)
- ROIC Score: 0/100 (missing data)
- D/E Score: 0/100 (extreme value indicates high risk)
- Current Ratio Score: 9.3/100 (below 1.0 threshold)

**Composite Calculation with Technology Weights:**
```
Quality Score = (100 × 0.40) + (0 × 0.35) + (0 × 0.15) + (9.3 × 0.10) / 0.50
              = (40.0 + 0.0 + 0.0 + 0.93) / 0.50  [reweighted for missing data]
              = 81.9/100
```

**Data Quality:** 50% (2 out of 4 metrics successfully calculated)

This example demonstrates the system's ability to handle data quality issues while providing meaningful scores based on available information.

### 2.6 Limitations and Considerations

#### 2.6.1 Data Quality Issues
- **Share buyback effects**: Can artificially inflate ROE by reducing equity base
- **Seasonal variations**: Quarterly metrics may not reflect annual performance
- **Accounting differences**: GAAP vs. IFRS variations in international stocks
- **Missing current assets/liabilities**: Limits current ratio availability

#### 2.6.2 Methodological Limitations  
- **ROIC approximation**: Simplified calculation due to data availability constraints
- **Sector classification**: Reliance on data provider sector assignments
- **Static thresholds**: Don't adjust for market cycle conditions
- **Equal weighting assumption**: Components within sectors treated equally

#### 2.6.3 Interpretation Guidelines
- **High scores (80-100)**: Strong financial quality, low bankruptcy risk
- **Medium scores (50-79)**: Average quality, monitor debt levels and trends
- **Low scores (0-49)**: Quality concerns, higher risk of financial distress
- **Data Quality Levels**: Scores below 75% data quality should be interpreted cautiously

---

## 3. Growth Analysis (20% Weight)

### 3.1 Overview

The Growth Analysis component evaluates the expansion trajectory and future potential of companies using four key growth indicators. Growth metrics help identify companies with sustainable business expansion and distinguish between temporary spikes and genuine long-term growth momentum.

**Component Weights:**
- Revenue Growth Rate: 40%
- Earnings Per Share (EPS) Growth: 35%
- Revenue Growth Stability: 15%
- Forward Growth Expectations: 10%

### 3.2 Individual Metric Calculations

#### 3.2.1 Revenue Growth Rate

**Formula:**
```
Revenue Growth Rate = (Current Revenue - Previous Revenue) / Previous Revenue
```

**Data Source:** Yahoo Finance `revenue_growth` field (trailing 12-month basis)

**Scoring Methodology:**
- Higher growth rates receive higher scores (direct relationship)
- Sector-adjusted thresholds reflect industry-specific growth expectations
- Negative growth indicates business contraction and receives low scores

**Base Scoring Thresholds:**
| Score Range | Revenue Growth Threshold | Interpretation |
|-------------|-------------------------|----------------|
| 90-100 | > 20% | Excellent growth |
| 70-89 | 15-20% | Good growth |
| 50-69 | 10-15% | Average growth |
| 30-49 | 5-10% | Weak growth |
| 0-29 | ≤ 0% | Declining/stagnant |

**Sector Adjustments:**
- Technology: +30% threshold adjustment (higher growth expectations)
- Healthcare: +10% threshold adjustment (innovation-driven growth)
- Consumer Staples: -40% threshold adjustment (mature market, low growth)
- Utilities: -60% threshold adjustment (regulated, infrastructure-limited)
- Energy: -20% threshold adjustment (cyclical commodity dependence)

**Key Assumptions:**
- Trailing 12-month revenue growth provides stable measurement
- Revenue growth above 50% may indicate acquisition activity or one-time events
- Consistent negative growth indicates fundamental business problems

#### 3.2.2 Earnings Per Share (EPS) Growth

**Formula:**
```
EPS Growth Rate = (Current EPS - Previous EPS) / Previous EPS
```

**Data Source:** Yahoo Finance `earnings_growth` field

**Scoring Methodology:**
- Higher EPS growth indicates improving profitability and operational efficiency
- More volatile than revenue growth due to leverage and cost structure effects
- Critical metric for assessing management's ability to convert revenue into profits

**Base Scoring Thresholds:**
| Score Range | EPS Growth Threshold | Interpretation |
|-------------|---------------------|----------------|
| 90-100 | > 25% | Excellent profit growth |
| 70-89 | 15-25% | Good profit growth |
| 50-69 | 10-15% | Average profit growth |
| 30-49 | 5-10% | Weak profit growth |
| 0-29 | ≤ 0% | Declining profitability |

**Sector Adjustments:**
- Technology: +40% threshold adjustment (scalable business models enable high EPS growth)
- Energy: +20% threshold adjustment (operational leverage amplifies commodity price changes)
- Healthcare: +10% threshold adjustment (R&D investments create profit growth potential)
- Financials: -20% threshold adjustment (regulated returns, interest rate sensitivity)
- Utilities: -50% threshold adjustment (regulated profit margins)

**Key Assumptions:**
- EPS growth reflects operational efficiency improvements and margin expansion
- Extremely high EPS growth (>100%) may indicate unsustainable cost-cutting or one-time gains
- Negative EPS growth below -80% indicates severe operational problems

#### 3.2.3 Revenue Growth Stability

**Formula (Simplified for POC):**
```
Stability Score = Function of(Revenue Growth Magnitude, Consistency Assessment)
```

**Methodology:**
- Assesses consistency and predictability of revenue growth over time
- Higher stability indicates more reliable business model and reduced execution risk
- In full implementation, would use coefficient of variation of quarterly revenue growth

**Simplified Scoring Logic:**
```python
if abs(revenue_growth) < 5%:    # Very low growth - potentially stable but poor
    stability_score = 0.6
elif abs(revenue_growth) < 15%: # Moderate growth - likely stable
    stability_score = 0.8
elif abs(revenue_growth) < 30%: # High growth - moderately stable
    stability_score = 0.7
else:                           # Extreme growth - likely unstable
    stability_score = 0.3

# Negative growth reduces stability
if revenue_growth < 0:
    stability_score *= 0.7
```

**Base Scoring Thresholds:**
| Score Range | Stability Score | Interpretation |
|-------------|----------------|----------------|
| 90-100 | > 0.85 | Highly consistent growth |
| 70-89 | 0.70-0.85 | Good consistency |
| 50-69 | 0.50-0.70 | Average consistency |
| 30-49 | 0.30-0.50 | Inconsistent growth |
| 0-29 | ≤ 0.30 | Highly volatile |

**Sector Adjustments:**
- Energy: -30% threshold adjustment (inherently cyclical business)
- Technology: -10% threshold adjustment (innovation cycles create volatility)
- Utilities: +10% threshold adjustment (regulated businesses should be stable)
- Consumer Staples: +5% threshold adjustment (defensive characteristics)

**Key Assumptions:**
- Consistent growth is more valuable than sporadic high growth
- Full implementation would require historical quarterly data analysis
- Some volatility is acceptable for high-growth sectors

#### 3.2.4 Forward Growth Expectations

**Formula (Simplified Estimation):**
```
Forward Growth ≈ (Trailing P/E - Forward P/E) / Trailing P/E
Alternative: Current EPS Growth * 0.8 (moderation factor)
```

**Data Source:** Yahoo Finance `forward_pe` and `pe_ratio` fields, with fallback to `earnings_growth`

**Scoring Methodology:**
- Incorporates market expectations for future growth
- Lower forward P/E relative to trailing P/E implies expected earnings growth
- Provides forward-looking perspective beyond historical performance

**Base Scoring Thresholds:**
| Score Range | Forward Growth Threshold | Interpretation |
|-------------|-------------------------|----------------|
| 90-100 | > 20% | Excellent growth expected |
| 70-89 | 15-20% | Good growth expected |
| 50-69 | 10-15% | Average growth expected |
| 30-49 | 5-10% | Weak growth expected |
| 0-29 | ≤ 0% | Declining expectations |

**Sector Adjustments:**
- Technology: +30% threshold adjustment (innovation pipeline critical)
- Healthcare: +10% threshold adjustment (R&D pipeline important)
- Consumer Staples: -40% threshold adjustment (mature growth expectations)
- Utilities: -60% threshold adjustment (regulated growth limitations)

**Key Assumptions:**
- Market P/E ratios embed forward growth expectations
- Forward estimates are subject to analyst bias and market sentiment
- Simplified calculation provides reasonable approximation for POC

### 3.3 Sector-Specific Weight Adjustments

#### 3.3.1 Sector Weight Profiles

| Sector | Revenue Growth | EPS Growth | Stability | Forward Growth | Rationale |
|--------|----------------|------------|-----------|----------------|-----------|
| **Base Weights** | 40% | 35% | 15% | 10% | Balanced approach |
| **Technology** | 35% | 40% | 10% | 15% | EPS scaling key, forward pipeline critical |
| **Healthcare** | 35% | 30% | 20% | 15% | R&D affects EPS, consistency valued |
| **Consumer Discretionary** | 45% | 30% | 15% | 10% | Market share expansion critical |
| **Utilities** | 25% | 25% | 35% | 15% | Consistency most important |
| **Energy** | 45% | 40% | 5% | 10% | Cyclical timing key, stability less meaningful |
| **Financials** | 30% | 40% | 25% | 5% | ROE expansion key, consistency important |

#### 3.3.2 Weight Adjustment Rationale

**Technology Sector (+5% EPS, +5% Forward, -5% Revenue, -5% Stability):**
- Scalable business models enable exceptional EPS growth through operational leverage
- Innovation pipeline and forward expectations critical for valuation
- Some growth volatility accepted due to innovation cycles

**Healthcare Sector (-5% EPS, +5% Stability, +5% Forward):**
- R&D investments can depress short-term EPS while building future growth
- Drug development pipeline makes forward expectations important
- Regulatory approval processes require consistent business execution

**Utilities Sector (-15% Revenue, -10% EPS, +20% Stability, +5% Forward):**
- Regulated industries have inherently limited growth potential
- Consistency of returns most important for dividend sustainability
- Forward planning critical for infrastructure capital allocation

**Energy Sector (+5% Revenue, +5% EPS, -10% Stability):**
- Commodity cycle timing makes current growth rates more important than stability
- Operational leverage amplifies commodity price movements into EPS
- Inherent cyclicality makes stability metrics less meaningful

### 3.4 Composite Score Calculation

#### 3.4.1 Sector-Adjusted Composite Calculation

```python
def calculate_growth_score(revenue_score, eps_score, stability_score, forward_score, sector_weights):
    # Only include valid scores (non-zero) in composite
    valid_scores = [(score, weight) for score, weight in zip(scores, weights) if score > 0]
    
    # Recalculate weights for available metrics
    total_weight = sum(weight for _, weight in valid_scores)
    normalized_scores = [(score * weight / total_weight) for score, weight in valid_scores]
    
    composite_score = sum(normalized_scores)
    data_quality_score = len(valid_scores) / 4  # Based on data completeness
    
    return composite_score, data_quality_score
```

#### 3.4.2 Missing Data Handling

- **Revenue Growth**: Zero score if not available from data source
- **EPS Growth**: Zero score if missing earnings data
- **Revenue Stability**: Calculated from available revenue growth data
- **Forward Growth**: Estimated from P/E ratios or use current EPS growth as proxy

### 3.5 Example Calculation: AAPL Growth Assessment

**Raw Metrics (as of implementation):**
- Revenue Growth: 5.1%
- EPS Growth: 7.8%
- Forward P/E: 25.75, Trailing P/E: 33.38
- Calculated Forward Growth: 22.9% (from P/E comparison)
- Sector: Technology

**Sector-Adjusted Scoring:**
- Revenue Growth Score: 25.7/100 (below tech sector expectations)
- EPS Growth Score: 32.3/100 (moderate for tech sector)
- Revenue Stability Score: 91.5/100 (consistent moderate growth)
- Forward Growth Score: 80.4/100 (strong forward expectations)

**Composite Calculation with Technology Weights:**
```
Growth Score = (25.7 × 0.35) + (32.3 × 0.40) + (91.5 × 0.10) + (80.4 × 0.15)
             = 9.0 + 12.9 + 9.2 + 12.1
             = 43.1/100
```

**Data Quality:** 100% (all four metrics successfully calculated)

This score reflects AAPL's moderate growth profile within the technology sector context, where higher growth rates are typically expected.

### 3.6 Limitations and Considerations

#### 3.6.1 Data Limitations
- **Historical data depth**: Stability assessment simplified due to limited quarterly history
- **Forward estimates accuracy**: P/E-based forward growth is approximation, not analyst consensus
- **Revenue recognition**: Accounting changes can affect growth rate comparability
- **Acquisition effects**: M&A activity can distort organic growth measurements

#### 3.6.2 Methodological Limitations
- **Growth sustainability**: High growth rates may not be maintainable long-term
- **Cyclical adjustments**: Some sectors require cycle-adjusted growth analysis
- **Currency effects**: International companies affected by exchange rate fluctuations
- **Market condition dependence**: Growth rates influenced by overall economic environment

#### 3.6.3 Interpretation Guidelines
- **High scores (80-100)**: Strong, consistent growth with positive outlook
- **Medium scores (50-79)**: Moderate growth, typical for mature companies
- **Low scores (0-49)**: Weak growth or declining business fundamentals
- **Data Quality Levels**: Scores below 75% data quality should be interpreted cautiously

---

## 4. Sentiment Analysis (15% Weight)

### 4.1 Overview

The Sentiment Analysis component evaluates market perception and momentum through analysis of news articles and social media discussions. Sentiment metrics help identify potential catalysts, market sentiment shifts, and investor perception that may not be reflected in fundamental metrics alone.

**Component Weights:**
- News Sentiment Analysis: 45%
- Social Media Sentiment: 30%
- Sentiment Momentum: 15%
- Sentiment Volume: 10%

### 4.2 Individual Metric Calculations

#### 4.2.1 News Sentiment Analysis

**Methodology:**
- Dual-engine sentiment analysis using TextBlob and VADER algorithms
- Combined scoring approach for improved accuracy
- Data quality weighting based on algorithm agreement
- Focus on financial news headlines and summaries

**Data Sources:**
- Yahoo Finance news articles (title + summary)
- 30-day lookback period for analysis
- Minimum 10-character text requirement for meaningful analysis

**Sentiment Scoring Algorithm:**
```python
def analyze_text_sentiment(text):
    # TextBlob analysis (polarity: -1 to +1)
    textblob_sentiment = TextBlob(text).sentiment.polarity
    
    # VADER analysis (compound: -1 to +1) 
    vader_sentiment = SentimentIntensityAnalyzer().polarity_scores(text)['compound']
    
    # Combined score with equal weighting
    combined_sentiment = (textblob_sentiment + vader_sentiment) / 2
    
    # Data quality based on algorithm agreement
    agreement = 1 - abs(textblob_sentiment - vader_sentiment) / 2
    reliability = max(0.5, agreement)
    
    return combined_sentiment, reliability
```

**Base Scoring Thresholds:**
| Score Range | Sentiment Threshold | Interpretation |
|-------------|-------------------|----------------|
| 90-100 | > +0.3 | Very positive news |
| 70-89 | +0.1 to +0.3 | Positive news |
| 50-69 | -0.1 to +0.1 | Neutral news |
| 30-49 | -0.3 to -0.1 | Negative news |
| 0-29 | < -0.3 | Very negative news |

**Key Assumptions:**
- Financial news sentiment correlates with stock performance
- Combined algorithm approach reduces individual model bias
- Headlines and summaries capture key sentiment drivers
- Recent news (30 days) most relevant for current sentiment

#### 4.2.2 Social Media Sentiment

**Methodology:**
- Analysis of Reddit posts from investing and stock-specific subreddits
- Engagement-weighted sentiment scoring (post score + comments)
- 14-day lookback period for social sentiment analysis
- Focus on retail investor sentiment and community discussions

**Data Sources:**
- Reddit posts (title + content) via PRAW API
- Subreddits: r/investing, r/stocks, r/SecurityAnalysis, r/StockMarket
- Engagement metrics: upvotes, comments, post score

**Engagement-Weighted Scoring:**
```python
def calculate_social_sentiment(posts):
    sentiments = []
    weights = []
    
    for post in posts:
        sentiment, reliability = analyze_text_sentiment(post.text)
        if reliability > 0.5:
            # Weight by engagement (logarithmic scaling)
            engagement = max(1, post.score + post.num_comments)
            post_weight = reliability * log(1 + engagement)
            
            sentiments.append(sentiment)
            weights.append(post_weight)
    
    return weighted_average(sentiments, weights)
```

**Base Scoring Thresholds:**
| Score Range | Sentiment Threshold | Interpretation |
|-------------|-------------------|----------------|
| 90-100 | > +0.2 | Very positive social sentiment |
| 70-89 | +0.05 to +0.2 | Positive social sentiment |
| 50-69 | -0.05 to +0.05 | Neutral social sentiment |
| 30-49 | -0.2 to -0.05 | Negative social sentiment |
| 0-29 | < -0.2 | Very negative social sentiment |

**Key Assumptions:**
- Social media reflects retail investor sentiment
- Higher engagement indicates more influential opinions  
- Recent social sentiment (14 days) captures current mood
- Reddit discussions provide meaningful sentiment signal

#### 4.2.3 Sentiment Momentum

**Methodology:**
- Comparison of recent sentiment (7 days) vs. historical sentiment (14-21 days ago)
- Momentum calculated as difference between time periods
- Identifies improving or deteriorating sentiment trends
- Based on news sentiment due to higher data consistency

**Calculation Formula:**
```
Sentiment Momentum = Recent Sentiment (7 days) - Historical Sentiment (14-21 days ago)
```

**Base Scoring Thresholds:**
| Score Range | Momentum Threshold | Interpretation |
|-------------|-------------------|----------------|
| 90-100 | > +0.15 | Strong positive momentum |
| 70-89 | +0.05 to +0.15 | Positive momentum |
| 50-69 | -0.05 to +0.05 | Neutral momentum |
| 30-49 | -0.15 to -0.05 | Negative momentum |
| 0-29 | < -0.15 | Strong negative momentum |

**Key Assumptions:**
- Sentiment trends persist in the short term
- Recent sentiment changes predict near-term performance
- News sentiment provides more consistent momentum signal than social
- 7-day recent period captures current sentiment shift

#### 4.2.4 Sentiment Volume

**Methodology:**
- Quantitative measure of attention and engagement
- Combined count of news articles and social media posts
- 30-day measurement period for comprehensive coverage
- Higher volume indicates increased market attention

**Volume Sources:**
- News articles from Yahoo Finance
- Reddit posts mentioning the stock symbol
- Combined total across all sources

**Base Scoring Thresholds:**
| Score Range | Volume Threshold | Interpretation |
|-------------|-----------------|----------------|
| 90-100 | ≥ 50 mentions | High attention/engagement |
| 70-89 | 20-49 mentions | Good attention |
| 50-69 | 10-19 mentions | Average attention |
| 30-49 | 5-9 mentions | Low attention |
| 0-29 | 1-4 mentions | Very low attention |

**Key Assumptions:**
- Higher mention volume correlates with investor interest
- Increased attention often precedes price movements
- Combined news and social volume provides comprehensive measure
- 30-day period captures sustained attention vs. temporary spikes

### 4.3 Sector-Specific Weight Adjustments

#### 4.3.1 Sector Weight Profiles

| Sector | News Sentiment | Social Sentiment | Momentum | Volume | Rationale |
|--------|----------------|------------------|-----------|---------|-----------|
| **Base Weights** | 45% | 30% | 15% | 10% | Balanced approach |
| **Technology** | 40% | 35% | 20% | 5% | Community-driven, momentum important |
| **Financials** | 55% | 20% | 15% | 10% | Regulation-sensitive, news critical |
| **Healthcare** | 50% | 25% | 15% | 10% | FDA/regulatory news crucial |
| **Consumer Discretionary** | 35% | 40% | 15% | 10% | Consumer opinion matters |
| **Energy** | 45% | 25% | 20% | 10% | Commodity news and timing |

#### 4.3.2 Weight Adjustment Rationale

**Technology Sector (+5% Social, +5% Momentum, -5% News, -5% Volume):**
- Community-driven investment decisions (Reddit, Twitter influence)
- Momentum important for growth stocks and innovation cycles
- High baseline volume reduces relative importance of volume metric

**Financial Sector (+10% News, -10% Social, +0% Momentum, +0% Volume):**
- Regulatory news and policy changes have immediate impact
- Institutional focus reduces relevance of retail social sentiment
- Interest rate and banking regulation news critical

**Healthcare Sector (+5% News, -5% Social, +0% Momentum, +0% Volume):**
- FDA approvals, clinical trial results drive sentiment
- Technical nature reduces meaningful social media discussion
- Regulatory and scientific news most relevant

**Consumer Discretionary (-10% News, +10% Social, +0% Momentum, +0% Volume):**
- Brand perception and consumer sentiment directly relevant
- Social media discussions influence purchasing decisions
- Consumer opinions translate to business performance

### 4.4 Composite Score Calculation

#### 4.4.1 Sector-Adjusted Composite Calculation

```python
def calculate_sentiment_score(news_score, social_score, momentum_score, volume_score, sector_weights):
    # Only include valid scores (non-zero) in composite
    valid_scores = [(score, weight) for score, weight in zip(scores, weights) if score > 0]
    
    # Recalculate weights for available metrics
    total_weight = sum(weight for _, weight in valid_scores)
    normalized_scores = [(score * weight / total_weight) for score, weight in valid_scores]
    
    composite_score = sum(normalized_scores)
    data_quality_score = len(valid_scores) / 4  # Based on data completeness
    
    # Adjust data quality based on data volume
    volume_adjustment = min(1.0, total_mentions / 10)  # Full data quality at 10+ sources
    final_data_quality = data_quality_score * volume_adjustment
    
    return composite_score, final_data_quality
```

#### 4.4.2 Data Quality Assessment

Sentiment analysis data quality depends on multiple factors:

1. **Data Completeness**: Number of successful metric calculations (0-4)
2. **Volume Adjustment**: Based on total mentions (full data quality at 10+ sources)
3. **Algorithm Agreement**: TextBlob and VADER consensus level
4. **Data Recency**: Availability of recent vs. historical data for momentum

**Final Data Quality Formula:**
```
Final Data Quality = (Valid Metrics / 4) × Volume Adjustment × Algorithm Reliability
```

### 4.5 Example Calculation: AAPL Sentiment Assessment

**Raw Metrics (as of implementation):**
- News Articles: 20 (30-day period)
- Reddit Posts: 5 (14-day period)
- News Sentiment: +0.048 (slightly positive)
- Social Sentiment: -0.002 (neutral)
- Sentiment Volume: 25 total mentions
- Sector: Technology

**Sector-Adjusted Scoring:**
- News Sentiment Score: 59.5/100 (slightly above neutral)
- Social Sentiment Score: 49.3/100 (nearly neutral)
- Momentum Score: 0.0/100 (insufficient historical data)
- Volume Score: 73.3/100 (good engagement level)

**Composite Calculation with Technology Weights:**
```
Sentiment Score = (59.5 × 0.40) + (49.3 × 0.35) + (0.0 × 0.20) + (73.3 × 0.05) / 0.80
                = (23.8 + 17.3 + 0.0 + 3.7) / 0.80  [reweighted for missing momentum]
                = 55.9/100
```

**Data Quality:** 75% (3 out of 4 metrics available, good data volume)

This score reflects neutral-to-slightly-positive sentiment for AAPL with good market attention but missing momentum data.

### 4.6 Data Quality and Validation

#### 4.6.1 Sentiment Analysis Accuracy

- **TextBlob Accuracy**: ~60-70% on financial text (polarity detection)
- **VADER Accuracy**: ~65-75% on social media text (optimized for informal language)
- **Combined Approach**: ~70-80% accuracy through ensemble method
- **Reliability Filtering**: Only predictions with >50% reliability included

#### 4.6.2 Data Source Reliability

- **Yahoo Finance News**: High-quality financial journalism, consistent formatting
- **Reddit Posts**: Variable quality, but engagement filtering improves signal
- **Volume Metrics**: Objective count-based metrics with high reliability
- **Temporal Consistency**: 30-day news, 14-day social windows balance recency vs. stability

### 4.7 Limitations and Considerations

#### 4.7.1 Technical Limitations

- **Algorithm Bias**: Pre-trained models may not capture financial language nuances
- **Context Missing**: Sentiment without understanding of business fundamentals
- **Sarcasm/Irony**: Difficulty detecting non-literal sentiment expressions
- **Market Noise**: Short-term sentiment may not predict long-term performance

#### 4.7.2 Data Limitations

- **Source Coverage**: Limited to Yahoo Finance and Reddit (not comprehensive)
- **Language Barriers**: English-only analysis misses international sentiment  
- **Real-time Lag**: Sentiment data may lag actual market sentiment shifts
- **Volume Bias**: Popular stocks get more coverage, affecting comparability

#### 4.7.3 Interpretation Guidelines

- **High scores (80-100)**: Strong positive sentiment, potential momentum
- **Medium scores (50-79)**: Mixed or neutral sentiment, monitor for changes
- **Low scores (0-49)**: Negative sentiment, potential headwinds or opportunities
- **Data Quality Levels**: Scores below 60% data quality should be interpreted cautiously

---

## Next Sections (To Be Added)

- **5. Composite Scoring** - Final weighted combination and ranking methodology (40%+25%+20%+15%)
- **6. Outlier Detection Framework** - Threshold-based and statistical approaches

---

**Document Version:** 1.3  
**Last Updated:** July 25, 2025  
**Implementation Status:** All 4 Components Complete - Fundamental (40%), Quality (25%), Growth (20%), Sentiment (15%)