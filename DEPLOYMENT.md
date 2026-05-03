# Sovereign Alpha - Deployment Guide

This guide explains how to deploy the Sovereign Alpha dashboard FREE on Render.com.

## Prerequisites

- GitHub account
- Groq API key (free at https://console.groq.com)

## Step 1: Push Code to GitHub

```powershell
# In your project directory
cd C:\Users\lokes\Downloads\project\sovereign-alpha

git init
git add .
git commit -m "Initial Sovereign Alpha"

# Create GitHub repo first, then:
git remote add origin https://github.com/YOUR_USERNAME/sovereign-alpha.git
git push -u origin main
```

## Step 2: Connect to Render.com

1. Go to https://render.com and sign up with GitHub
2. Click "New +" → "Web Service"
3. Find your `sovereign-alpha` repo and connect it
4. Configure:
   - Name: `sovereign-alpha-dashboard`
   - Environment: `Python`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn --bind 0.0.0.0:$PORT dashboard.app:app`

## Step 3: Add Environment Variables

In Render dashboard, go to "Environment" tab:

| Key | Value |
|-----|-------|
| GROQ_API_KEY | (your key from console.groq.com) |
| PORT | 10000 |
| RENDER | true |

**Important:** Set GROQ_API_KEY as "Secret" to hide it.

## Step 4: Deploy

Click "Create Web Service". Wait 2-3 minutes for build.

Your URL: `https://sovereign-alpha-dashboard.onrender.com`

## Step 5: Push Updates

```powershell
git add .
git commit -m "Updates"
git push
```

Render auto-deploys on push.

## Syncing Local Results to Cloud

Your results are stored locally in `results/`. To see them in cloud:

1. Copy `results/` folder contents to a GitHub gist or external storage
2. Or add them to your GitHub repo and push

For persistent results storage on Render, use:
- Render's free PostgreSQL (create via Render dashboard)
- Or upload results JSON to GitHub and pull in build

## Cloud Mode Features

When `RENDER=true`:
- Dashboard shows read-only data
- "Run New Analysis" button is disabled
- All analysis runs locally on your machine
- Use local dashboard for full features

## Files for Deployment

| File | Purpose |
|------|---------|
| render.yaml | Render config |
| Procfile | Gunicorn start command |
| runtime.txt | Python version |
| requirements.txt | Dependencies |

## Troubleshooting

**Build fails**: Check Python version in runtime.txt (use 3.11)

**No data**: Results stored locally - either push results folder to GitHub or use Render's disk

**API errors**: Check GROQ_API_KEY is set correctly in Render

## Support

- GitHub Issues: Report bugs
- Console output in Render shows startup logs