# 🚀 SUPER SIMPLE RUNPOD SETUP - JUST 3 STEPS!

## Step 1: Open RunPod Terminal (1 minute)
1. Go to: https://www.runpod.io/console/pods
2. Click your pod "SeedVr2Test"
3. Click "Connect" → "Connect to Jupyter Lab" or "Web Terminal"

## Step 2: Copy & Paste ONE Command (5 minutes)
Copy this ENTIRE block and paste it in the terminal:

```bash
cd /workspace && \
curl -sSL https://raw.githubusercontent.com/Dreamrealai/SeedVr2Test/main/runpod/easy_install.sh | bash
```

**That's it!** The script will:
- ✅ Install all dependencies
- ✅ Create the API server
- ✅ Start everything automatically
- ✅ Show you the URL when ready

## Step 3: Expose Port 8888 (30 seconds)
1. Go back to RunPod console
2. Click "Edit Pod" or "Expose Ports"
3. Add HTTP Port: `8888`
4. Save

## ✅ DONE! Test Your API:
Open: https://lh0wm9g482zr28-8888.proxy.runpod.net/health

---

### If Something Goes Wrong:
Just run this to restart:
```bash
cd /workspace && python api_server.py
```