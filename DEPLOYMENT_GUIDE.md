# GuardianAI Deployment Guide

## Free Hosting Setup: Render.com (Both Frontend & Backend)

### Why Render?
- ✅ **One platform** for both services
- ✅ **Completely FREE** forever
- ✅ Auto-deploy from GitHub
- ✅ Free SSL certificates
- ✅ Custom domains supported
- ✅ 750 hours/month (enough for 24/7 backend)
- ✅ Unlimited static site hosting

---

## 🚀 Part 1: Backend Deployment (Render Web Service)

### Step 1: Create Render Account
1. Go to https://render.com
2. Click **"Get Started for Free"**
3. Sign up with your **GitHub account**
4. Authorize Render to access your repositories

### Step 2: Deploy Backend Web Service
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

## 🎨 Part 2: Frontend Deployment (Render Static Site)

### Step 1: Create Static Site
1. In the same Render dashboard, click **"New +"** → **"Static Site"**
2. Connect your **GUARDIAN-AI** repository (already authorized)
3. Configure the static site:
   - **Name:** `guardianai-frontend`
   - **Branch:** `main`
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Publish Directory:** `dist`

### Step 2: Set Environment Variables
In the static site settings, go to **Environment** tab and add:

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

**⚠️ Important:** Replace the `VITE_API_BASE_URL` with your actual backend URL from Step 1.

### Step 3: Deploy
Click **"Create Static Site"** and wait for build to complete (2-3 minutes).

Your frontend will be live at:
```
https://guardianai-frontend.onrender.com
```

**✨ Bonus:** Add a custom domain in Settings → Custom Domain (free!)

---

## 🔧 Post-Deployment Configuration

### 1. Update Firebase Auth Domain
1. Go to Firebase Console → Authentication → Settings
2. Add your Vercel domain to **Authorized domains**:
   ```
   guardianai-platform.vercel.app
   ```Render domain to **Authorized domains**:
   ```
   guardianai-frontend.onrender.com
   ```

### 2. Update CORS on Backend (Optional)
The backend is already configured in `main.py` with:
```python
allow_origins=["*"]  # Allows all domains
```

For better security in production, update to:
```python
allow_origins=[
    "https://guardianai-frontend.onrender.com

### 3. Test the Deployment
1. Visit your Render frontend URL: `https://guardianai-frontend.onrender.com`
2. Test login with Firebase Auth
3. Check Dashboard loads metrics
4. Try Demo Mode attack simulation
5. View Threats page
6. ✅ Everything should work seamlessly!

---

## 📊 Monitoring (All in Render Dashboard)

### Backend Logs
1. Go to Render Dashboard → **guardianai-backend** → **Logs**
2. Monitor API requests in real-time
3. Check for errors and performance

### Frontend Deploys
1. Go to Render Dashboard → **guardianai-frontend** → **Events**
2. View build logs
3. Check deployment status

### Datadog (Optional)
- Already integrated in backend
- Configure Datadog API keys in Render environment variables for advanced monitoring

---

## 🔄 Continuous Deployment

Both services auto-deploy when you push to GitHub:

```bash
git add .
git commit -m "Update feature"
git push origin main
```

**What happens:**
1. ⚡ Render detects the push
2. 🏗️ Backend rebuilds (2-3 minutes)
3. 🎨 Frontend rebuilds (2-3 minutes)
4. ✅ Both services live with new changes

---

## 💰 Free Tier Limits (All on Render)

### Static Site (Frontend):
- ✅ **FREE forever**
- ✅ Unlimited bandwidth
- ✅ Automatic HTTPS
- ✅ Custom domains
- ✅ Always online (no cold starts)
- ✅ Global CDN

### Web Service (Backend):
- ✅ 750 hours/month (one service running 24/7)
- ⚠️ Spins down after 15 min inactivity
- ⚠️ Cold start: ~30 seconds (first request after idle)
- ✅ 512 MB RAM
- ✅ Shared CPBuild Fails:
1. **Check environment variables:** Make sure all `VITE_*` variables are set in Render
2. **Build command error:** Verify `npm run build` works locally
3. **Wrong directory:** Ensure Root Directory is `frontend` and Publish Directory is `dist`

### Frontend Can't Connect to Backend:
1. **Check VITE_API_BASE_URL:** Should be `https://guardianai-backend.onrender.com/api`
2. **Backend not running:** Visit backend URL directly, wait for cold start
3. **CORS error:** Check `main.py` allows your frontend domain

### Backend Won't Start:
1. **Check logs:** Render Dashboard → guardianai-backend → Logs
2. **Import errors:** Verify all dependencies in `requirements.txt`
3. **Firestore errors:** Check GCP credentials JSON is valid (no extra quotes)
4. **Port binding:** Ensure start command uses `--port $PORT`

### Backend Cold Starts (Normal):
- First request after 15 min idle takes ~30 seconds
- This is expected on free tier
- Solution: Upgrade to paid plan ($7/mo) for always-on service
3. **Auth not working:** Check Firebase authorized domains

### Backend Issues:
1. **Service won't start:** Check logs in Render dashboard
2. **Import errors:** Verify all dependencies in requirements.txt
3. **Firestore errors:** Check GCP credentials JSON is valid
4. **Cold starts:** First request after inactivity takes 30s (normal)

### Backend Code Fix for Render:
Update `backend/config.py` to load credentials from environment variable:
**Backend (5 minutes):**
- [ ] Create Render account with GitHub
- [ ] New + → Web Service → Connect GUARDIAN-AI repo
- [ ] Configure: Root=`backend`, Build=`pip install -r requirements.txt`, Start=`uvicorn main:app --host 0.0.0.0 --port $PORT`
- [ ] Set environment variables (GCP credentials JSON, Datadog keys)
- [ ] Wait for deploy → Copy backend URL

**Frontend (3 minutes):**
- [ ] New + → Static Site → Connect GUARDIAN-AI repo
- [ ] Configure: Root=`frontend`, Build=`npm run build`, Publish=`dist`
- [ ] Set environment variables (VITE_API_BASE_URL + Firebase config)
- [ ] Wait for deploy → Copy frontend URL

**Post-Deploy (2 minutes):**
- [ ] Add frontend domain to Firebase authorized domains
- [ ] Test login, dashboard, demo mode, threats
- [ ] Update README with live URLs
- [ ] Share on Devpost! 🎉

---

## 🎉 Done!

Your GuardianAI platform is now live and **completely FREE** on Render!

**Live URLs:**
- 🎨 Frontend: `https://guardianai-frontend.onrender.com`
- ⚡ Backend: `https://guardianai-backend.onrender.com`
- 📚 API Docs: `https://guardianai-backend.onrender.com/docs`

**All on ONE platform - Render.com!** 🚀

---

## 🎯 Why This Setup is Perfect

✅ **One Account:** Manage both services in one dashboard  
✅ **One Platform:** No need to juggle Vercel + Render  
✅ **Free Forever:** Both services stay free permanently  
✅ **Auto-Deploy:** Push to GitHub = instant deployment  
✅ **Professional:** Custom domains, SSL, monitoring included  
✅ **Simple:** Easiest deployment for hackathons/demos  

Share your GuardianAI platform link on Devpost and win! 🏆
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
