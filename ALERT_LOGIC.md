# Alert Logic - Dual Tier System

## Overview

The monitor uses a **two-tier alert system** to distinguish between different price ranges and prevent duplicate alerts.

## Price Tiers

### S1 - Best Deal
- **Price Range**: < $50
- **Email Subject**: "Best lululemon deal"
- **Trigger Condition**: Product becomes in stock at S1 price AND it wasn't in S1 before
- **Mathematical**: `new S1 - old S1`

### S2 - Great Deal
- **Price Range**: >= $50 and < $60
- **Email Subject**: "Great lululemon deal"
- **Trigger Condition**: Product becomes in stock at S2 price AND it wasn't in S1 or S2 before
- **Mathematical**: `new S2 - (old S1 + old S2)`

## How It Works

### State Tracking

For each product URL, the monitor tracks:
- `was_in_s1`: Whether the product was previously in stock at S1 price (< $50)
- `was_in_s2`: Whether the product was previously in stock at S2 price ($50-$60)
- `last_tier`: The last tier the product was in (S1, S2, or None)
- `last_alerted_tier`: The tier for which we last sent an alert

### Alert Logic

#### S1 Alert Trigger
```
IF product is in stock
AND current price < $50
AND was_in_s1 == False
THEN send S1 alert ("Best lululemon deal")
```

#### S2 Alert Trigger
```
IF product is in stock
AND current price >= $50 AND < $60
AND was_in_s1 == False
AND was_in_s2 == False
THEN send S2 alert ("Great lululemon deal")
```

### Examples

**Example 1: New Product at S1 Price**
- Product was out of stock → Comes in stock at $45
- `was_in_s1 = False`, `was_in_s2 = False`
- ✅ **S1 Alert Sent**: "Best lululemon deal"
- State updated: `was_in_s1 = True`, `last_tier = 'S1'`

**Example 2: Product Already in S1**
- Product is already in stock at $45 (already alerted)
- `was_in_s1 = True`, `was_in_s2 = False`
- ❌ **No Alert**: Already in S1

**Example 3: Product Moves from S1 to S2**
- Product was at $45 (S1), price changes to $55 (S2)
- `was_in_s1 = True`, `was_in_s2 = False`
- ❌ **No S2 Alert**: Was already in S1

**Example 4: New Product at S2 Price**
- Product was out of stock → Comes in stock at $55
- `was_in_s1 = False`, `was_in_s2 = False`
- ✅ **S2 Alert Sent**: "Great lululemon deal"
- State updated: `was_in_s2 = True`, `last_tier = 'S2'`

**Example 5: Product Was in S2, Comes Back**
- Product was at $55, went out of stock, comes back at $55
- Previous state: `was_in_s2 = True`
- ❌ **No Alert**: Was already in S2

**Example 6: Product Price Drops from S2 to S1**
- Product was at $55 (S2), price drops to $45 (S1)
- Previous state: `was_in_s1 = False`, `was_in_s2 = True`
- ✅ **S1 Alert Sent**: "Best lululemon deal" (new tier entry)
- State updated: `was_in_s1 = True`, `was_in_s2 = True`, `last_tier = 'S1'`

## Why This System?

This prevents duplicate alerts while ensuring you're notified when:
1. **New products arrive** in either price tier
2. **Prices drop** into a better tier (S2 → S1)
3. **Products return** in a different tier than before

It avoids alerting you multiple times for the same product at the same tier.
