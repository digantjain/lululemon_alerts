# Bot Detection Issue

## Problem

Lululemon is blocking all requests from GitHub Actions with **403 Forbidden** errors. This is because:

1. **IP-based blocking**: GitHub Actions uses cloud IP addresses that are flagged as "known bot/automation IPs"
2. **Advanced bot detection**: Lululemon uses sophisticated protection (likely Cloudflare or similar) that blocks automated requests
3. **Header manipulation won't help**: If they're blocking based on IP reputation, no amount of browser-like headers will bypass it

## Solutions

### Option 1: Run on Your Personal Computer (Recommended)
**Pros**: 
- Your home IP is residential, won't be blocked
- Already have the code ready
- Free

**Setup**: Use LaunchAgent (macOS) or a scheduled task to run every 30 minutes when your computer is on.

**See**: `AUTO_RUN_GUIDE.md` for setup instructions

### Option 2: Use a Headless Browser (Complex)
Use Playwright or Selenium to actually render pages like a real browser.

**Pros**: More likely to bypass detection
**Cons**: 
- Much slower (10-30 seconds per page)
- Higher resource usage
- Still may not work if they block GitHub Actions IPs

### Option 3: Use a Proxy Service (Paid)
Route requests through residential proxies.

**Cost**: ~$50-100/month for residential proxies
**Pros**: Should bypass IP blocking
**Cons**: Expensive for a free tool

### Option 4: Use a Different Hosting Service
Try Render.com, Railway, or AWS Lambda - they might have different IP ranges that aren't blocked yet. But this may also get blocked eventually.

## Recommendation

**Run it locally on your Mac** using the LaunchAgent method. It will:
- Work reliably (your IP won't be blocked)
- Be free
- Run automatically in the background
- Only run when your Mac is on

If your Mac isn't always on, you could:
- Leave it on overnight or during the day
- Run it on an old laptop/computer you can leave on
- Use a Raspberry Pi or similar device

## Why GitHub Actions Won't Work

Lululemon's bot protection specifically targets cloud IPs. This is a common practice for e-commerce sites to prevent:
- Price scraping
- Inventory monitoring
- Automated purchasing

The protection is working as intended - it's blocking automated requests from cloud infrastructure.
