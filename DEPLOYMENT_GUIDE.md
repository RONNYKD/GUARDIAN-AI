# GuardianAI Deployment Guide

## Free Hosting Setup: Vercel (Frontend) + Render (Backend)

---

## 🚀 Backend Deployment (Render)

### Step 1: Create Render Account
1. Go to https://render.com
2. Sign up with your GitHub account
3. Authorize Render to access your repositories

### Step 2: Deploy Backend
1. Click **"New +"** → **"Web Service"**
2. Connect your **GUARDIAN-AI** repository
3. Configure the service:
   - **Name:** `guardianai-backend`
   - **Region:** Oregon (Free)
   - **Branch:** `main`
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free

### Step 3: Set Environment Variables on Render
In the Render dashboard, go to **Environment** tab and add:

```bash
GCP_PROJECT_ID=lovable-clone-e08db
ENVIRONMENT=production
DATADOG_API_KEY=your_datadog_api_key
DATADOG_APP_KEY=your_datadog_app_key
```

**For Google Cloud credentials:**
1. Go to Google Cloud Console → IAM & Admin → Service Accounts
2. Create a new service account with Firestore permissions
3. Generate JSON key
4. Copy the entire JSON content
5. Add as environment variable:
   ```
   GOOGLE_APPLICATION_CREDENTIALS_JSON=<paste entire JSON here>
   ```

### Step 4: Update Backend Config
The backend needs to read credentials from environment variable instead of file.

Update `backend/config.py` to handle JSON credentials from env var (already configured).

### Step 5: Get Backend URL
After deployment completes, Render will give you a URL like:
```
https://guardianai-backend.onrender.com
```

⚠️ **Important:** Free tier spins down after 15 minutes of inactivity. First request after spin-down takes ~30 seconds.

---

## 🎨 Frontend Deployment (Vercel)

### Step 1: Create Vercel Account
1. Go to https://vercel.com
2. Sign up with your GitHub account
3. Authorize Vercel to access your repositories

### Step 2: Deploy Frontend
1. Click **"Add New"** → **"Project"**
2. Import your **GUARDIAN-AI** repository
3. Configure the project:
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
   - **Install Command:** `npm install`

### Step 3: Set Environment Variables on Vercel
In the Vercel dashboard, go to **Settings** → **Environment Variables** and add:

```bash
VITE_API_BASE_URL=https://guardianai-backend.onrender.com/api
VITE_ENVIRONMENT=production
```

**Firebase Configuration (from your Firebase console):**
```bash
VITE_FIREBASE_API_KEY=your_firebase_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=lovable-clone-e08db
VITE_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
VITE_FIREBASE_APP_ID=your_app_id
```

### Step 4: Deploy
Click **"Deploy"** and wait for build to complete.

Your frontend will be live at:
```
https://guardianai-platform.vercel.app
```

Or use a custom domain!

---

## 🔧 Post-Deployment Configuration

### 1. Update Firebase Auth Domain
1. Go to Firebase Console → Authentication → Settings
2. Add your Vercel domain to **Authorized domains**:
   ```
   guardianai-platform.vercel.app
   ```

### 2. Update CORS on Backend
The backend should allow requests from your Vercel domain. This is already configured in `main.py` with:
```python
allow_origins=["*"]  # Change to specific domain in production
```

For production, update to:
```python
allow_origins=[
    "https://guardianai-platform.vercel.app",
    "http://localhost:3000"  # Keep for local development
]
```

### 3. Test the Deployment
1. Visit your Vercel URL
2. Test login with Firebase Auth
3. Check Dashboard loads metrics
4. Try Demo Mode attack simulation
5. View Threats page

---

## 📊 Monitoring

### Vercel Analytics
- Automatically enabled for deployments
- View in Vercel dashboard → Analytics

### Render Logs
- View in Render dashboard → Logs
- Monitor backend API requests
- Check for errors

### Datadog (Optional)
- Already integrated in backend
- Configure Datadog API keys in Render environment variables

---

## 🔄 Continuous Deployment

Both Vercel and Render auto-deploy when you push to GitHub:

```bash
git add .
git commit -m "Update feature"
git push origin main
```

- **Vercel:** Rebuilds frontend automatically
- **Render:** Rebuilds backend automatically

---

## 💰 Free Tier Limits

### Vercel Free Tier:
- ✅ Unlimited personal projects
- ✅ 100GB bandwidth/month
- ✅ Automatic HTTPS
- ✅ Custom domains
- ✅ Instant rollbacks

### Render Free Tier:
- ✅ 750 hours/month (enough for 1 service 24/7)
- ⚠️ Spins down after 15 min inactivity
- ✅ 512 MB RAM
- ✅ Shared CPU
- ⚠️ Cold start: ~30 seconds

---

## 🚨 Troubleshooting

### Frontend Issues:
1. **Build fails:** Check environment variables are set
2. **API not responding:** Verify VITE_API_BASE_URL is correct
3. **Auth not working:** Check Firebase authorized domains

### Backend Issues:
1. **Service won't start:** Check logs in Render dashboard
2. **Import errors:** Verify all dependencies in requirements.txt
3. **Firestore errors:** Check GCP credentials JSON is valid
4. **Cold starts:** First request after inactivity takes 30s (normal)

### Backend Code Fix for Render:
Update `backend/config.py` to load credentials from environment variable:

```python
import json
import os
from google.oauth2 import service_account

# Load credentials from environment variable
credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if credentials_json:
    credentials_dict = json.loads(credentials_json)
    credentials = service_account.Credentials.from_service_account_info(credentials_dict)
```

---

## 📝 Quick Deployment Checklist

- [ ] Create Render account
- [ ] Deploy backend to Render
- [ ] Set Render environment variables (GCP credentials, Datadog keys)
- [ ] Get backend URL from Render
- [ ] Create Vercel account
- [ ] Deploy frontend to Vercel
- [ ] Set Vercel environment variables (API URL, Firebase config)
- [ ] Add Vercel domain to Firebase authorized domains
- [ ] Test login, dashboard, demo mode
- [ ] Update README with live URLs

---

## 🎉 Done!

Your GuardianAI platform is now live and free forever!

**Live URLs:**
- Frontend: https://guardianai-platform.vercel.app
- Backend: https://guardianai-backend.onrender.com
- API Docs: https://guardianai-backend.onrender.com/docs

Share your project link on Devpost! 🚀
