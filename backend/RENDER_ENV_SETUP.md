# Render Environment Variables Setup Guide

## 📋 How to Set Up Environment Variables in Render

### Method 1: Manual Entry (Recommended)

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Select your **guardianai-backend** service
3. Click **Environment** in the left sidebar
4. Click **Add Environment Variable**
5. Copy each variable from `.env.render` file

---

## 🔑 Required Variables

### 1. Google Cloud Platform (GCP)

#### `GCP_PROJECT_ID`
```
lovable-clone-e08db
```

#### `GOOGLE_APPLICATION_CREDENTIALS_JSON`
**⚠️ IMPORTANT:** This must be your entire GCP service account JSON key as a **single line**.

**How to get it:**
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to **IAM & Admin** → **Service Accounts**
3. Find your service account or create new one
4. Click **Keys** → **Add Key** → **Create new key** → **JSON**
5. Download the JSON file
6. Open it in a text editor
7. **Copy the entire content** (it should start with `{"type":"service_account"...`)
8. Paste as **one continuous line** in Render (no line breaks)

**Example format:**
```json
{"type":"service_account","project_id":"lovable-clone-e08db","private_key_id":"abc123","private_key":"-----BEGIN PRIVATE KEY-----\nMIIE...","client_email":"guardianai@lovable-clone-e08db.iam.gserviceaccount.com","client_id":"123456","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs/guardianai%40lovable-clone-e08db.iam.gserviceaccount.com"}
```

**Required permissions for service account:**
- Cloud Datastore User
- Firestore Database User (or higher)

---

### 2. Datadog Configuration

#### `DD_API_KEY`
Get from: [Datadog → Organization Settings → API Keys](https://app.datadoghq.com/organization-settings/api-keys)

#### `DD_APP_KEY`
Get from: [Datadog → Organization Settings → Application Keys](https://app.datadoghq.com/organization-settings/application-keys)

#### `DD_SITE`
```
datadoghq.com
```
(or `datadoghq.eu` if you're in EU)

#### `DD_SERVICE`
```
guardianai-backend
```

#### `DD_ENV`
```
production
```

---

### 3. Application Settings

#### `ENVIRONMENT`
```
production
```

#### `DEBUG`
```
false
```

#### `LOG_LEVEL`
```
INFO
```

---

### 4. API Configuration

#### `API_HOST`
```
0.0.0.0
```

**Note:** `PORT` is automatically set by Render - **DO NOT** add this variable!

---

### 5. CORS Configuration

#### `CORS_ORIGINS`
**After deploying frontend**, update this to:
```json
["https://guardianai-frontend.onrender.com","http://localhost:3000"]
```

**⚠️ IMPORTANT:** Update `guardianai-frontend.onrender.com` with your actual frontend URL!

---

## 🔒 Optional Variables

### Slack Notifications
If you want Slack alerts:

#### `SLACK_WEBHOOK_URL`
Your Slack webhook URL

#### `SLACK_ESCALATION_CHANNEL`
Channel name (e.g., `#security-alerts`)

---

### JWT Secret
#### `JWT_SECRET_KEY`
Generate a secure random string:
```bash
# In PowerShell:
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | % {[char]$_})
```

---

## 📝 Quick Copy-Paste Checklist

Use this checklist while setting up in Render:

### Required (Must Set):
- [ ] `GCP_PROJECT_ID` = `lovable-clone-e08db`
- [ ] `GOOGLE_APPLICATION_CREDENTIALS_JSON` = `{entire JSON from GCP}`
- [ ] `DD_API_KEY` = `your_datadog_api_key`
- [ ] `DD_APP_KEY` = `your_datadog_app_key`
- [ ] `DD_SITE` = `datadoghq.com`
- [ ] `DD_SERVICE` = `guardianai-backend`
- [ ] `DD_ENV` = `production`
- [ ] `ENVIRONMENT` = `production`
- [ ] `DEBUG` = `false`
- [ ] `LOG_LEVEL` = `INFO`
- [ ] `API_HOST` = `0.0.0.0`

### Update After Frontend Deploy:
- [ ] `CORS_ORIGINS` = `["https://your-frontend-url.onrender.com","http://localhost:3000"]`

### Optional:
- [ ] `JWT_SECRET_KEY` = `your-generated-secret`
- [ ] `SLACK_WEBHOOK_URL` = `your-webhook-url`
- [ ] `SLACK_ESCALATION_CHANNEL` = `#channel-name`

---

## ✅ Verification

After setting all variables:

1. Click **Save Changes** in Render
2. Wait for automatic redeploy (~2-3 minutes)
3. Check **Logs** tab for any errors
4. Visit `https://your-backend.onrender.com/api/health`
5. Should return: `{"status": "healthy"}`

---

## 🚨 Troubleshooting

### "No module named 'backend'"
✅ Fixed - using relative imports

### "Cannot import name 'get_config'"
✅ Fixed - using `get_settings()`

### "Firestore permission denied"
❌ Check GCP service account has Firestore permissions
❌ Verify JSON credentials are pasted correctly (no extra quotes/spaces)

### "Datadog API error"
❌ Check API keys are correct
❌ Verify `DD_SITE` matches your Datadog region

### Backend won't start
1. Check Render logs for specific error
2. Verify all required variables are set
3. Ensure `GOOGLE_APPLICATION_CREDENTIALS_JSON` is valid JSON
4. Test locally with same environment variables

---

## 💡 Pro Tips

1. **Secret Variables:** In Render, environment variables are automatically encrypted
2. **Auto-Redeploy:** Changing env vars triggers automatic redeploy
3. **Groups:** You can group related variables for better organization
4. **Sync:** Don't use "sync from .env file" - manual entry is more reliable
5. **Testing:** After deploy, test `/api/health` endpoint first

---

## 📚 Additional Resources

- [Render Environment Variables Docs](https://render.com/docs/configure-environment-variables)
- [Google Cloud Service Accounts](https://cloud.google.com/iam/docs/service-accounts)
- [Datadog API Keys](https://docs.datadoghq.com/account_management/api-app-keys/)
