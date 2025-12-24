# Datadog API Key Permissions Issue

## Problem

Getting `403 Forbidden` errors when trying to create monitors with the provided API keys.

```
HTTP response body: {'errors': ['Forbidden']}
```

## Root Cause

The API Key and Application Key need specific permissions to create monitors.

## Solution

### Option 1: Update Application Key Permissions (Recommended)

1. **Go to Datadog Application Keys page:**
   - Visit: https://app.datadoghq.com/organization-settings/application-keys

2. **Find your Application Key** (ending in ...b1a5)

3. **Edit the Application Key permissions:**
   - Click on the key
   - Under "Scopes", ensure these are checked:
     - ✅ **monitors_write** - Required to create/update/delete monitors
     - ✅ **monitors_read** - Required to list monitors
     - ✅ **monitors_downtime** - Optional, for setting downtimes
   
4. **Save changes**

5. **Test again:**
   ```bash
   cd pipeline
   python setup_monitors.py
   # Choose option 1
   ```

### Option 2: Create New Application Key with Correct Permissions

1. **Visit:** https://app.datadoghq.com/organization-settings/application-keys

2. **Click "New Key"**

3. **Name it:** "GuardianAI Monitor Management"

4. **Select scopes:**
   - ✅ monitors_read
   - ✅ monitors_write
   - ✅ monitors_downtime

5. **Copy the new Application Key**

6. **Update .env files:**
   - Replace `DD_APP_KEY` in [pipeline/.env](d:\SENTINEL (for the google accelerator hackerthon)\guardianai-project\pipeline\.env)
   - Replace `DD_APP_KEY` in [demo-app/.env](d:\SENTINEL (for the google accelerator hackerthon)\guardianai-project\demo-app\.env)

7. **Test again:**
   ```bash
   cd pipeline
   python setup_monitors.py
   # Choose option 1
   ```

## Verification Steps

Once permissions are updated:

1. **Test API connection:**
   ```bash
   cd pipeline
   python setup_monitors.py
   # Choose option 2 to list monitors (should work even if empty)
   ```

2. **Create monitors:**
   ```bash
   # Choose option 1 to create all 5 monitors
   ```

3. **Verify in Datadog UI:**
   - Visit: https://app.datadoghq.com/monitors/manage
   - Filter by tag: `guardianai`
   - You should see 5 new monitors

## Required Datadog Permissions

For GuardianAI to work fully, you need:

| Permission | Purpose | Required? |
|------------|---------|-----------|
| **monitors_read** | List and view monitors | ✅ Yes |
| **monitors_write** | Create/update/delete monitors | ✅ Yes |
| **monitors_downtime** | Schedule monitor downtimes | ⚪ Optional |
| **timeseries_query** | Query metrics data | ⚪ Optional |
| **dashboards_read** | View dashboards | ⚪ Optional |
| **dashboards_write** | Create dashboards | ⚪ Optional |

## Current Status

- ✅ API Key is valid (connected successfully)
- ✅ Application Key is valid (connected successfully)
- ❌ Application Key lacks `monitors_write` permission
- ⏸️ Waiting for permission update

## Next Steps

1. Update Application Key permissions in Datadog
2. Re-run `python setup_monitors.py`
3. Verify 5 monitors created successfully
4. Continue to Demo Mode implementation

## Alternative: API Key Issues

If the Application Key has correct permissions but still fails:

### Check API Key Permissions

1. **Go to:** https://app.datadoghq.com/organization-settings/api-keys

2. **Find your API Key** (ending in ...3f3b)

3. **Verify it's not restricted:**
   - Should show "Active" status
   - No IP restrictions (unless you need them)
   - Not expired

### Check Organization Role

Your Datadog user account needs **Admin** or **Standard** role:

1. **Go to:** https://app.datadoghq.com/organization-settings/users

2. **Find your user**

3. **Check role:**
   - ✅ Datadog Admin Role - Full access
   - ✅ Datadog Standard Role - Can create monitors
   - ❌ Datadog Read Only Role - Cannot create monitors

## Support

If issues persist:

1. **Check Datadog Status:** https://status.datadoghq.com/
2. **Review API Docs:** https://docs.datadoghq.com/api/latest/monitors/
3. **Contact Datadog Support:** https://help.datadoghq.com/

---

**Current Issue:** Application Key needs `monitors_write` permission  
**Action Required:** Update Application Key scopes in Datadog settings  
**ETA:** 2-5 minutes once permissions are updated
