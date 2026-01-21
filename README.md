# Lululemon Product Monitor

Automatically monitors Lululemon products for stock availability and price alerts. Sends email notifications when products come in stock at your specified price threshold.

## Features

- Monitors 30+ product URLs simultaneously
- Checks stock availability and price every 30 minutes
- Sends email notifications when products meet your criteria (in stock + price under threshold)
- Tracks state to avoid duplicate alerts
- Runs automatically in the cloud via GitHub Actions (free)

## Two-Tier Alert System

### S1 - Best Deal (< $50)
- **Email Subject**: "Best lululemon deal"
- **Trigger**: Product becomes in stock at < $50 AND wasn't in S1 before

### S2 - Great Deal ($50-$60)
- **Email Subject**: "Great lululemon deal"
- **Trigger**: Product becomes in stock at $50-$60 AND wasn't in S1 or S2 before

## Setup

### 1. GitHub Actions Setup (Free, Automated)

1. **Set up GitHub Secrets** (Settings → Secrets → Actions):
   - `EMAIL_FROM` → Your Gmail address
   - `EMAIL_TO` → Recipient email address
   - `EMAIL_PASSWORD` → Your Gmail App Password (generate from Google Account settings)

2. **Push to GitHub**:
   ```bash
   git push origin main
   ```

3. **That's it!** The workflow runs automatically every 30 minutes.

### 2. Gmail App Password Setup

1. Go to your Google Account settings
2. Enable 2-Factor Authentication
3. Generate an App Password:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and your device
   - Copy the generated password

## How It Works

1. The monitor checks each product URL in `urls.json`
2. For each URL (which includes specific color, size, inseam):
   - Fetches the product page
   - Extracts product name, current price, and stock status
   - Uses multiple detection strategies for accuracy
3. If a product is:
   - **In stock** AND
   - **Price is under your max_price threshold** AND
   - **Meets tier alert conditions**
   
   Then it sends you an email notification!

4. The monitor runs automatically every 30 minutes via GitHub Actions

## Files

- `monitor.py` - Main monitoring script
- `urls.json` - Product URLs to monitor
- `requirements.txt` - Python dependencies
- `.github/workflows/monitor.yml` - GitHub Actions workflow

## Manual Testing

To test locally:

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create config.json with your email settings (see config.example.json)
# Then run once:
python monitor.py --run-once
```

## Troubleshooting

**Not receiving emails?**
- Check that GitHub Secrets are set correctly
- Verify Gmail App Password is correct
- Check GitHub Actions logs for errors

**Workflow not running?**
- Check that GitHub Actions is enabled in repository settings
- Verify the workflow file is in `.github/workflows/` directory
- Check Actions tab for workflow runs and errors

**State not persisting?**
- State is saved via GitHub Actions artifacts
- First run will start with fresh state
- Subsequent runs will use previous state

## Notes

- The monitor is respectful and includes delays between requests
- State tracking prevents duplicate alerts for the same product/price
- All 30 products in `urls.json` are monitored simultaneously
