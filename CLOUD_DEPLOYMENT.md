# Cloud Deployment Options

Since your laptop won't be on all the time, here are the best options to run the monitor in the cloud:

## 🏆 Option 1: GitHub Actions (RECOMMENDED - FREE)

**Best for**: Free, easy setup, runs on schedule automatically.

### Features
- ✅ **FREE** - 2,000 minutes/month for private repos, unlimited for public
- ✅ **No server management** - GitHub runs it for you
- ✅ **Automatic scheduling** - Runs every 15 minutes via cron
- ✅ **Manual triggers** - Can trigger manually from GitHub UI
- ✅ **State persistence** - Can save state between runs using artifacts

### Setup Steps

1. **Set up GitHub Secrets** (Settings → Secrets → Actions):
   - `EMAIL_FROM`: Your Gmail address
   - `EMAIL_TO`: Recipient email address
   - `EMAIL_PASSWORD`: Your Gmail App Password

2. **Push your code to GitHub**:
   ```bash
   git add .
   git commit -m "Add monitor"
   git push origin main
   ```

3. **Enable GitHub Actions**:
   - Go to your repo → Actions tab
   - The workflow will automatically run every 15 minutes

### How It Works

- GitHub Actions runs your workflow on a schedule (every 15 minutes)
- Each run executes `monitor.py --run-once` (single check)
- Checks all products and sends emails if needed
- State is saved between runs (optional, using artifacts)

### Limitations

- State persistence requires workarounds (artifacts or external storage)
- Runs are not truly continuous (runs every 15 minutes, not every minute)
- Free tier: 2,000 minutes/month (133 runs of ~15 minutes each)

---

## Option 2: AWS Lambda + EventBridge (Serverless)

**Best for**: Pay-per-execution, highly scalable, truly serverless.

### Features
- ✅ **Pay per execution** - ~$0.20 per million requests
- ✅ **Automatic scaling** - No server management
- ✅ **Scheduled via EventBridge** - Runs every 15 minutes automatically
- ✅ **State in S3** - Persistent state storage
- ✅ **Always running** - No server uptime concerns

### Setup Steps

1. **Create Lambda Function**:
   - Go to AWS Lambda Console
   - Create function with Python 3.12 runtime
   - Upload `lambda_function.py` and dependencies

2. **Set Environment Variables**:
   - `EMAIL_FROM`: Your Gmail address
   - `EMAIL_TO`: Recipient email address
   - `EMAIL_PASSWORD`: Your Gmail App Password
   - `S3_BUCKET_NAME`: S3 bucket for state storage (optional)

3. **Create EventBridge Rule**:
   - Schedule: `rate(15 minutes)`
   - Target: Your Lambda function

4. **Create S3 Bucket** (optional, for state persistence):
   - Create bucket for storing `monitor_state.json`

### Cost Estimate

- Lambda: ~$0.20 per million requests
- For 2,880 checks/month (every 15 minutes): ~$0.0006
- S3: ~$0.023 per GB/month (negligible)
- **Total: ~$0.01-0.10/month** (basically free)

### Deploy Script

```bash
# Install AWS CLI and configure
aws configure

# Create deployment package
zip -r lambda-deployment.zip lambda_function.py monitor.py urls.json requirements.txt

# Create Lambda function
aws lambda create-function \
  --function-name lululemon-monitor \
  --runtime python3.12 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-execution-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://lambda-deployment.zip \
  --timeout 300 \
  --memory-size 256
```

---

## Option 3: AWS EC2 (Always-On Server)

**Best for**: Full control, continuous monitoring, if you need more resources.

### Features
- ✅ **Always running** - Continuous monitoring
- ✅ **Full control** - SSH access, install anything
- ✅ **State persistence** - Local file storage
- ❌ **More expensive** - ~$3.50/month (t2.micro) or more
- ❌ **Requires management** - Server setup, security, updates

### Setup Steps

1. **Launch EC2 Instance**:
   - Choose Ubuntu 22.04 LTS
   - t2.micro (free tier eligible for 1 year)
   - Configure security group (SSH access)

2. **SSH into server**:
   ```bash
   ssh -i your-key.pem ubuntu@your-instance-ip
   ```

3. **Install dependencies**:
   ```bash
   sudo apt update
   sudo apt install python3-pip git
   git clone https://github.com/yourusername/lululemon_alerts.git
   cd lululemon_alerts
   pip3 install -r requirements.txt
   ```

4. **Set up systemd service**:
   ```bash
   sudo nano /etc/systemd/system/lululemon-monitor.service
   ```

5. **Start service**:
   ```bash
   sudo systemctl enable lululemon-monitor
   sudo systemctl start lululemon-monitor
   ```

### Cost

- t2.micro: Free for first year, then ~$3.50/month
- t3.micro: ~$7.50/month
- Better for continuous monitoring if cost is acceptable

---

## Option 4: Render.com (Free Tier Available)

**Best for**: Easy deployment, free tier, no AWS knowledge needed.

### Features
- ✅ **Free tier available** - Limited hours/month
- ✅ **Easy setup** - Connect GitHub repo, auto-deploy
- ✅ **Web dashboard** - Monitor logs easily
- ✅ **Automatic restarts** - Keeps service running

### Setup Steps

1. **Connect GitHub repo** to Render
2. **Create Background Worker** service
3. **Set environment variables** (email settings)
4. **Deploy** - Render handles the rest

### Cost

- Free tier: 750 hours/month (limited)
- Paid: $7/month for always-on

---

## Option 5: Railway.app

**Best for**: Simple deployment, good free tier.

### Features
- ✅ **Easy setup** - GitHub integration
- ✅ **Free tier** - $5 credit/month
- ✅ **Automatic deploys** - Push to GitHub = deploy
- ✅ **Simple configuration** - Environment variables in UI

### Cost

- Free: $5 credit/month (usually enough for small apps)
- Paid: Pay as you go

---

## Option 6: Heroku

**Best for**: Simple deployment, but limited free tier.

### Features
- ✅ **Easy setup** - Git push to deploy
- ❌ **No free tier** - Paid plans only now
- ✅ **Add-ons** - Scheduler add-on for cron jobs

### Cost

- Basic: $7/month

---

## 📊 Comparison Table

| Option | Cost | Setup Complexity | Best For |
|--------|------|------------------|----------|
| **GitHub Actions** | Free | Easy | Most users, free tier |
| **AWS Lambda** | ~$0.01/month | Medium | Serverless, scalable |
| **AWS EC2** | ~$3.50+/month | Medium | Full control, continuous |
| **Render** | Free/$7/month | Easy | Easy deployment |
| **Railway** | Free/$5 credit | Easy | Simple, GitHub integration |
| **Heroku** | $7/month | Easy | Simple, but paid |

---

## 🎯 Recommended: GitHub Actions

**Why GitHub Actions is best for most users:**

1. ✅ **FREE** - No cost at all
2. ✅ **Easy setup** - Just push code and set secrets
3. ✅ **No server management** - GitHub handles everything
4. ✅ **Reliable** - GitHub's infrastructure is very reliable
5. ✅ **State management** - Can use artifacts or external storage

**Setup Time**: 5 minutes

**Maintenance**: None - runs automatically

---

## Setting Up GitHub Actions (Step-by-Step)

1. **Create `.github/workflows/monitor.yml`** (already created in this repo)

2. **Set up secrets** in GitHub:
   - Go to repo → Settings → Secrets and variables → Actions
   - Add secrets:
     - `EMAIL_FROM`
     - `EMAIL_TO`
     - `EMAIL_PASSWORD`

3. **Push to GitHub**:
   ```bash
   git add .github/workflows/monitor.yml
   git commit -m "Add GitHub Actions workflow"
   git push
   ```

4. **Verify it's running**:
   - Go to Actions tab
   - You'll see workflow runs every 15 minutes
   - Check logs to see it working

5. **Manual trigger** (optional):
   - Go to Actions → Lululemon Monitor → Run workflow

That's it! Your monitor will now run automatically in the cloud every 15 minutes! 🎉

---

## State Persistence (For GitHub Actions)

To persist state between runs, you have options:

### Option A: GitHub Artifacts (Simple)
- The workflow already uploads state as artifact
- State persists for 90 days
- Simple but limited

### Option B: External Storage (Better)
- Store state in S3, Google Cloud Storage, or database
- Update workflow to download/upload state
- More reliable for long-term use

I can help set up external state storage if needed!
