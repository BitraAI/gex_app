# Flow Ratio and Net Flow Improvements

## Summary

Implemented **Option A: Unified Delta-Weighted Flow Metrics** to address inconsistencies in order flow analysis.

## Problem Statement

### Original Issues

1. **Inconsistent Metrics**: Flow Ratio used raw contracts while Net Flow used delta-weighted exposure
2. **No Raw Metrics**: Could not compare raw contract volume with delta-weighted flow
3. **Limited Context**: No way to assess flow strength or quality

### Key Differences

| Metric | Calculation | Use Case |
|--------|-------------|----------|
| **Raw Flow Ratio** | `(call_buy + put_sell) / total_contracts` | Raw contract count bias |
| **Delta-Weighted Flow Ratio** | `bullish_delta / (bullish_delta + bearish_delta)` | True market sentiment |

### Example

If 60s trades include:
- 10 call contracts @ delta=0.6 (bullish)
- 5 put contracts @ delta=0.3 (bearish)

**Raw View:**
- Bullish: 10 calls + 5 puts = 15
- Bearish: 5 calls + 0 puts = 5
- Flow Ratio: 15/20 = **0.75**

**Delta-Weighted View:**
- Bullish: 10 × 0.6 = 6 delta
- Bearish: 5 × 0.3 = 1.5 delta
- Flow Ratio: 6/7.5 = **0.80**

## Implementation

### 1. Added `flow_metrics_delta_weighted()` in `_utils.py`

```python
def flow_metrics_delta_weighted(
    call_buy, call_sell, put_buy, put_sell,
    call_delta, put_delta
) -> tuple[float, int, float | None]:
    """Delta-weighted flow metrics accounting for options' delta sensitivity."""
```

**Features:**
- Weights trades by contract delta
- Falls back to delta=0.5 if not provided
- Returns delta-weighted net, total, and ratio

### 2. Added `get_ticker_flow_metrics_raw_60s()` in `option_streaming_service.py`

```python
def get_ticker_flow_metrics_raw_60s(display_symbol: str) -> tuple[int, int, float | None]:
    """Rolling 60 s raw contract metrics — (net_flow, total_flow, flow_ratio)."""
```

**Features:**
- Returns raw contract-based metrics
- Complements existing delta-weighted metrics
- Enables comparison between raw and delta-weighted views

### 3. Updated Order Flow Grid in `flow.py`

**Added Columns:**
- **Flow Ratio (Raw)**: Raw contract-based ratio
- **Flow Ratio (ΔWt)**: Delta-weighted ratio
- **Flow Vol (raw)**: Total raw volume (60s)
- Added tooltips with explanations

**Updated Row Structure:**
```python
rows.append({
    "Flow Ratio (Raw)": _raw_flow_ratio,      # NEW
    "Flow Ratio (ΔWt)": _flow_ratio,          # EXISTING
    "Flow Vol (raw)": _raw_total,             # NEW
    "Net Flow": _net_flow,
    # ... other metrics
})
```

**Column Tooltips:**
- Hover over column headers to see definitions
- Explains delta-weighting concept
- Clarifies metric purpose

## Benefits

### 1. **Dual Perspective**
- Raw ratio shows contract count bias
- Delta-weighted ratio shows true market sensitivity

### 2. **Flow Quality Assessment**
- High ratio + high volume = strong signal
- High ratio + low volume = weak/noisy signal

### 3. **Better Decision Making**
- Traders can see both raw activity and delta exposure
- Understand if flow is driven by many small trades or few large ones

### 4. **Backward Compatibility**
- Existing delta-weighted metrics unchanged
- New raw metrics added alongside
- Telegram alerts use delta-weighted (already appropriate)

## Usage Examples

### In the Order Flow Grid

```
Ticker | Flow Ratio (Raw) | Flow Ratio (ΔWt) | Flow Vol (raw) | Net Flow
-------|------------------|------------------|----------------|----------
SPY    | 0.72             | 0.78             | 1,243          | +452
```

**Interpretation:**
- Raw ratio: 72% bullish contracts
- Delta-weighted: 78% bullish delta exposure
- The difference indicates deeper ITM options are driving the flow
- 1,243 contracts traded in 60s
- Net +452 delta-weighted flow

### When to Use Each

**Use Raw Flow Ratio when:**
- Analyzing contract count distribution
- Comparing to historical volume patterns
- Checking for unusual options activity by contract count

**Use Delta-Weighted Flow Ratio when:**
- Assessing true market sentiment
- Understanding price impact potential
- Evaluating dealer hedging requirements
- Analyzing gamma exposure

## Testing Recommendations

1. **Verify delta-weighting is working:**
   - Check that high-delta options contribute more to flow ratio
   - Verify low-delta options have minimal impact

2. **Compare raw vs delta-weighted:**
   - During volatile periods, delta-weighted should differ more
   - In quiet periods, both should be similar

3. **Check volume context:**
   - Low volume with extreme ratio may be noisy
   - High volume with moderate ratio may be significant

## Future Enhancements

Potential improvements:
1. **Exponential weighting**: Weight recent trades more heavily
2. **Standard deviation**: Show flow strength/confidence
3. **Volume percentiles**: Compare to historical volume levels
4. **Delta-gamma flow**: Include gamma exposure in metrics
5. **Real-time alerts**: Flag when delta-weighted ratio diverges from raw

## Files Modified

1. `scripts/_utils.py` - Added `flow_metrics_delta_weighted()`
2. `scripts/option_streaming_service.py` - Added `get_ticker_flow_metrics_raw_60s()`
3. `scripts/flow.py` - Updated grid with dual metrics, tooltips, styling

## Notes

- The existing `get_ticker_flow_metrics_60s()` continues to provide delta-weighted metrics for Telegram alerts and existing displays
- No breaking changes to existing functionality
- All existing code using delta-weighted metrics continues to work as before
