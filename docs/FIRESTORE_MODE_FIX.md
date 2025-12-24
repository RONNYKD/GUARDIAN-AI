# Firestore Database Mode Issue - Solution Guide

## Problem

The current Firestore database is in **DATASTORE_MODE** instead of **FIRESTORE_NATIVE** mode.

```yaml
type: DATASTORE_MODE  # ❌ Wrong mode
```

This causes errors when trying to use Firestore document operations:
```
Error: The Cloud Firestore API is not available for Datastore Mode databases
```

## Why This Happened

Your Google Cloud project was created with Datastore enabled, which automatically sets the default database to Datastore mode.

## Solution Options

### Option 1: Create a New Named Database (Recommended)

Since you can't change the mode of an existing database, create a new database in Native mode:

```bash
# Create a new Firestore database in Native mode
gcloud firestore databases create \
  --database=guardianai \
  --location=nam5 \
  --type=firestore-native \
  --project=lovable-clone-e08db
```

Then update your code to use the named database:

**In `pipeline/config.py`:**
```python
@dataclass
class FirestoreConfig:
    """Firestore configuration."""
    database_id: str = "guardianai"  # Use named database
    # ... rest of config
```

**In `backend/services/firestore_client.py`:**
```python
from google.cloud import firestore

# Use named database
db = firestore.Client(
    project="lovable-clone-e08db",
    database="guardianai"  # Named database
)
```

### Option 2: Use a Different Project (Clean Start)

Create a new Google Cloud project with Firestore Native mode from the start:

```bash
# Create new project
gcloud projects create guardianai-prod --name="GuardianAI Production"

# Set as active project
gcloud config set project guardianai-prod

# Create Firestore database in Native mode
gcloud firestore databases create \
  --location=nam5 \
  --type=firestore-native
```

### Option 3: Keep Datastore Mode (Workaround)

Use Datastore API instead of Firestore:

```python
from google.cloud import datastore

# Use Datastore client
client = datastore.Client(project="lovable-clone-e08db")

# Create entity instead of document
entity = datastore.Entity(key=client.key("Incident"))
entity.update({
    "id": "inc_123",
    "severity": "high",
    "timestamp": datetime.now()
})
client.put(entity)
```

## Recommended Approach

**Use Option 1** - Create a named database called "guardianai" in Firestore Native mode.

### Step-by-Step Implementation:

1. **Create the new database:**
   ```bash
   gcloud firestore databases create \
     --database=guardianai \
     --location=nam5 \
     --type=firestore-native \
     --project=lovable-clone-e08db
   ```

2. **Wait for creation** (takes 1-2 minutes)

3. **Verify creation:**
   ```bash
   gcloud firestore databases describe \
     --database=guardianai \
     --project=lovable-clone-e08db
   ```

4. **Update configuration files** to use the named database

5. **Test the connection**

## Limitations

- You can have multiple Firestore databases in one project
- The "(default)" database cannot be deleted or changed
- Named databases can be deleted if needed
- Free tier applies to total usage across all databases

## Next Steps

Would you like me to:
- **A)** Create the named database "guardianai" and update the code
- **B)** Implement Datastore compatibility layer (keep current database)
- **C)** Skip Firestore for now (use in-memory storage for demo)

**Recommendation:** Choose **A** - it's the cleanest solution for production.
