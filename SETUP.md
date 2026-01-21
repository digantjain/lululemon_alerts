# Quick Setup Guide

## ✅ Code is Pushed!

Your monitor code has been committed and pushed to GitHub. Now you just need to set up the secrets.

## 🔐 Set Up GitHub Secrets (5 minutes)

1. **Go to your GitHub repository**:
   - Navigate to: `https://github.com/YOUR_USERNAME/lululemon_alerts`

2. **Go to Settings → Secrets and variables → Actions**:
   - Click on "Secrets and variables" → "Actions"
   - Or go to: `https://github.com/YOUR_USERNAME/lululemon_alerts/settings/secrets/actions`

3. **Add these 3 secrets** (click "New repository secret" for each):

   **Secret 1:**
   - Name: `EMAIL_FROM`
   - Value: `digant.jain1993@gmail.com`

   **Secret 2:**
   - Name: `EMAIL_TO`
   - Value: `digant.jain1993@gmail.com`

   **Secret 3:**
   - Name: `EMAIL_PASSWORD`
   - Value: `umpa wpil qpvp gldj`

4. **Save each secret** (click "Add secret")

## ✅ That's It!

The workflow will:
- ✅ Run automatically every 30 minutes
- ✅ Check all 30 products in `urls.json`
- ✅ Send email alerts when products are in stock at the right price
- ✅ Track state between runs (no duplicate alerts)

## 🔍 Verify It's Working

1. **Go to the Actions tab** in your GitHub repo
2. **You should see** "Lululemon Monitor" workflow
3. **Click on it** to see run history
4. **The first run** should happen within 30 minutes (or trigger manually)

### Manual Trigger (Optional)

To test immediately:
1. Go to Actions tab
2. Click "Lululemon Monitor" workflow
3. Click "Run workflow" button (top right)
4. Click "Run workflow" again

## 📧 Email Alerts

You'll receive emails with:
- **Subject**: "Best lululemon deal" (for products < $50)
- **Subject**: "Great lululemon deal" (for products $50-$60)

Each email includes:
- Product name
- Price
- Direct URL to the product
- Stock status

## 🔍 Monitoring

- **Check workflow runs**: Go to Actions tab
- **View logs**: Click on any workflow run to see detailed logs
- **State tracking**: State is saved between runs (prevents duplicate alerts)

## ⚙️ Configuration

- **Change schedule**: Edit `.github/workflows/monitor.yml` (change `*/30 * * * *` to your desired frequency)
- **Add products**: Edit `urls.json` and push changes
- **Modify price tiers**: Edit `monitor.py` if needed

---

**Need help?** Check the logs in the Actions tab if something doesn't work!
