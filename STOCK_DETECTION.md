# How Stock Detection Works

This document explains how the Lululemon monitor accurately determines stock status for each product variant (color, size, inseam combination).

## Detection Strategy

The monitor uses a **multi-layered approach** to determine stock status, checking multiple indicators for accuracy:

### 1. JSON-LD Structured Data (Most Reliable)
- **What it is**: Standard schema.org markup that e-commerce sites use
- **What we look for**: `@type: "Product"` with `offers.availability` field
- **Reliability**: ⭐⭐⭐⭐⭐ Very reliable
- **Example**: `"availability": "https://schema.org/InStock"`

### 2. Embedded JavaScript JSON Data
- **What it is**: Product data embedded in `<script>` tags as JavaScript variables
- **What we look for**: Patterns like:
  - `window.__INITIAL_STATE__ = {...}`
  - `window.productData = {...}`
  - Variant arrays with availability flags
- **Reliability**: ⭐⭐⭐⭐ Reliable if present
- **Contains**: Variant-level stock, price per variant

### 3. Add to Bag Button Status (Primary Indicator)
- **What we check**:
  - Button exists and is enabled → Likely in stock
  - Button is disabled → Out of stock
  - Button text contains "Out of Stock", "Sold Out", "Notify Me" → Out of stock
  - Button text contains "Add to Bag" or "Add to Cart" → In stock
- **Reliability**: ⭐⭐⭐⭐⭐ Very reliable (direct user action indicator)
- **HTML attributes checked**: `disabled`, `aria-disabled`, CSS classes

### 4. Out of Stock Text Indicators
- **What we look for**: Text patterns on the page:
  - "Out of Stock"
  - "Sold Out"  
  - "Notify Me" (often replaces Add to Bag when out of stock)
- **Reliability**: ⭐⭐⭐⭐ Reliable
- **Search method**: Case-insensitive text search in button text and page content

### 5. Size Selector Status
- **What we check**: If size selectors (for the target size) are disabled
- **Reliability**: ⭐⭐⭐ Moderate (indirect indicator)
- **Note**: If size 8 selector is disabled, that variant is out of stock

## Price Detection

The monitor uses multiple methods to extract price:

1. **JSON-LD price**: `offers.price` field
2. **HTML price elements**: Elements with `data-testid="price"` or containing "price" in class name
3. **Meta tags**: `<meta property="product:price:amount">` or `<meta name="price">`
4. **Page scan**: Regex pattern matching `$XX.XX` format

When multiple prices are found, the monitor selects the **lowest price** (often a sale/discount price).

## Why Multiple Strategies?

Lululemon's website structure can vary, and they may:
- Change HTML structure over time
- Use different layouts for different product types
- Have A/B testing that changes elements
- Load some data via JavaScript (which requires more sophisticated parsing)

By checking multiple indicators, the monitor is more resilient to changes and provides more accurate results.

## How Each Product URL is Checked

Since you're providing **exact URLs** for each color/size/inseam combination:

1. Each URL already specifies the exact variant (via query parameters or path)
2. When we fetch that URL, Lululemon's server returns the page for that specific variant
3. The stock status on that page reflects **that exact variant's availability**
4. We don't need to parse color/size selectors because the URL already specifies them

## Example Detection Flow

For a URL like: `https://shop.lululemon.com/p/women-leggings/Align-High-Rise-Pant-25/_/PROD123?color=BLK&sz=8`

1. ✅ Fetch page for that exact URL (Black, Size 8, 25" inseam)
2. ✅ Look for JSON-LD: `{"@type": "Product", "offers": {"availability": "InStock", "price": 98}}`
3. ✅ Check Add to Bag button: `<button data-testid="add-to-bag">Add to Bag</button>` → Enabled
4. ✅ Extract price: $98 (or from JSON-LD)
5. ✅ Result: **In Stock** at $98
6. ❌ Alert sent? **No** (price > $60 threshold)

## Accuracy Considerations

**Strengths**:
- ✅ Multiple detection strategies reduce false negatives
- ✅ Direct button status is very reliable
- ✅ JSON-LD data is standardized and reliable
- ✅ Checking exact URLs means no guesswork about variants

**Limitations**:
- ⚠️ If Lululemon significantly changes their HTML structure, detection may need updates
- ⚠️ Dynamic content loaded via JavaScript may require headless browser (not currently implemented)
- ⚠️ Anti-bot measures could block requests (we use realistic User-Agent headers)

## Testing Your URLs

Use the test script to verify detection:

```bash
python test_product.py "YOUR_PRODUCT_URL"
```

This shows all detection indicators and helps debug if something seems incorrect.

## Debug Mode

Enable detailed logging by adding to `config.json`:

```json
{
  "debug": true,
  ...
}
```

This will show all detection indicators during each check, helping you understand why a product was marked in/out of stock.
