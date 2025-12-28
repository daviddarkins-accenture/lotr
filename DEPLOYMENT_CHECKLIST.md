# 🌋 LOTR Data Cloud POC - Deployment Checklist

Use this checklist to ensure everything is properly configured before your first ingestion.

## ✅ Pre-Deployment Checklist

### 1. Data Cloud Configuration

- [ ] **Ingestion API Connector Created**
  - Source API Name: `lotr`
  - Status: Active
  
- [ ] **Data Stream Configured**
  - Object API Name: `LotrCharacter`
  - Category: **Profile** (to treat characters as people)
  - Primary Key Field: `characterId`
  - **Record Modified Field: `ingestedAt`** (required for deletes!)
  - Refresh Mode: `Upsert`
  
- [ ] **All 12 Fields Mapped** (see schema below)
  
- [ ] **OAuth Connected App Created**
  - Client Credentials Flow: **Enabled**
  - Run As user: **Set in policies**
  - Scopes: `cdp_ingest_api`, `api`, `refresh_token`
  - Client ID and Secret obtained

### 2. LOTR API Access

- [ ] **Account Created** at https://the-one-api.dev/sign-up
- [ ] **API Key Obtained** from https://the-one-api.dev/account
- [ ] **API Key Tested** (optional): 
  ```bash
  curl -H "Authorization: Bearer YOUR_KEY" https://the-one-api.dev/v2/character?limit=1
  ```

### 3. Local Environment

- [ ] **Python 3.8+ Installed**
  ```bash
  python3 --version
  ```

- [ ] **Virtual Environment Created**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

- [ ] **Dependencies Installed**
  ```bash
  pip install -r requirements.txt
  ```

- [ ] **Gandalf Wizard Completed**
  ```bash
  python setup.py
  ```
  
- [ ] **.env File Created** with all required variables

### 4. Validation Tests

- [ ] **Config Validation Passes**
  ```bash
  python -c "from config import Config; Config.validate(); print('✅ Config valid')"
  ```

- [ ] **LOTR API Connection Works**
  ```bash
  python -c "from lotr_client import fetch_characters; chars = fetch_characters(); print(f'✅ Fetched {len(chars)} characters')"
  ```
  
- [ ] **Data Cloud OAuth + Token Exchange Works**
  ```bash
  python -c "from auth import get_auth; auth = get_auth(); token = auth.get_token(); print('✅ DC Token:', token[:30] + '...'); print('✅ Instance:', auth.dc_instance_url)"
  ```

- [ ] **Flask App Starts**
  ```bash
  python app.py
  # Should start on http://localhost:5001
  ```

## 📋 LotrCharacter Schema Reference

Make sure your Data Cloud Data Stream has these fields:

| Field Name | Type | Notes |
|------------|------|-------|
| characterId | Text | **Primary Key** |
| name | Text | |
| race | Text | |
| gender | Text | |
| birth | Text | |
| death | Text | |
| realm | Text | |
| wikiUrl | Text | |
| height | Text | |
| hair | Text | |
| spouse | Text | |
| ingestedAt | DateTime | **Record Modified Field** |

**Important**: 
- `characterId` MUST be set as the **Primary Key**
- `ingestedAt` SHOULD be set as **Record Modified Field** (needed for bulk deletes)
- All fields will appear as "required" - the API must send all fields (empty string for missing)

## 🔑 Critical Technical Details

### Two-Step Token Exchange

The app automatically handles this:
1. Get Salesforce token (Client Credentials)
2. Exchange for Data Cloud JWT token

Verify with:
```bash
python -c "
from auth import get_auth
auth = get_auth()
token = auth.get_token()
print(f'Token starts with: {token[:10]}...')
print(f'Instance URL: {auth.dc_instance_url}')
"
```

### All Fields Required

Data Cloud requires ALL schema fields in every record. Missing values should be empty strings:

```json
{
  "characterId": "abc123",
  "name": "Frodo",
  "race": "Hobbit",
  "gender": "Male",
  "birth": "TA 2968",
  "death": "",
  "realm": "",
  "wikiUrl": "",
  "height": "",
  "hair": "",
  "spouse": "",
  "ingestedAt": "2025-12-01T00:00:00.000Z"
}
```

### Async Processing (~3 minutes)

Data doesn't appear immediately! 
- API returns `202 Accepted` right away
- Data appears after Data Stream refresh (~3 mins)
- Check **Refresh History** tab for job status

### Bulk API for Deletes

Streaming DELETE doesn't work with Upsert refresh mode!
- App uses Bulk API for deletes
- Creates job, uploads CSV, closes job
- CSV format: NO header, 2 columns (primary key + future datetime)

## 🚀 First Ingestion Run

1. **Start the Flask app:**
   ```bash
   source venv/bin/activate
   python app.py
   ```

2. **Open browser to:** http://localhost:5001

3. **Click:** "Fetch LOTR Data 📜"

4. **Click:** "Send to Data Cloud 🌋"

5. **Wait ~3 minutes** for async processing

6. **Verify in Data Cloud:**
   - Go to Data Explorer
   - Select Object: `lotr-LotrCharacter`
   - Should see ~933 records

## 🧪 Testing the Full Flow

### Test 1: Initial Ingestion
- [ ] Click "Fetch LOTR Data 📜"
- [ ] Click "Send to Data Cloud 🌋"
- [ ] Wait ~3 minutes
- [ ] Verify ~933 records in Data Explorer

### Test 2: Verify Salesforce Flow (if configured)
- [ ] Check if Salesforce Accounts were created
- [ ] Accounts should have `characterId__c` populated

### Test 3: Idempotency
- [ ] Click "Send to Data Cloud 🌋" again
- [ ] Wait ~3 minutes
- [ ] Verify count stays at ~933 (no duplicates)

### Test 4: Deletion
- [ ] Click "Wipe LOTR Data 🧹"
- [ ] Wait ~3-5 minutes for Bulk API job
- [ ] Verify:
  - Salesforce Accounts deleted (if any)
  - Data Stream Refresh History shows "Delete" job
  - Total Records = 0

### Test 5: Re-ingestion
- [ ] Click "Fetch LOTR Data 📜"
- [ ] Click "Send to Data Cloud 🌋"
- [ ] Verify ~933 records reappear

## 🔧 Troubleshooting

### Issue: "400 Bad Request" with empty body
**Cause:** Using Salesforce token instead of Data Cloud token
**Fix:** Verify two-step token exchange is working

### Issue: "400 Schema mismatch"
**Cause:** Not all fields present in payload
**Fix:** Code should send ALL fields with empty strings for missing

### Issue: Data not appearing after ingestion
**Cause:** Async processing
**Fix:** Wait ~3 minutes, check Data Stream Refresh History

### Issue: Deletes not working
**Cause:** Streaming DELETE doesn't work with Upsert mode
**Fix:** App uses Bulk API - check Refresh History for "Delete" type

### Issue: Bulk delete job stuck "InProgress"
**Cause:** Incorrect CSV format
**Fix:** CSV must have NO header, 2 columns for Profile category

### Issue: "401 Unauthorized"
**Cause:** Token issues
**Fix:** 
- Verify Connected App has correct scopes
- Check Client Credentials Flow is enabled
- Verify Run As user is set

## 📸 Success Criteria

You'll know it's working when:

✅ Data Stream Refresh History shows "Upsert" job with 933+ records

✅ Data Explorer shows ~933 rows in `lotr-LotrCharacter`

✅ Salesforce Accounts created (if Flow configured)

✅ Wipe button triggers "Delete" job in Refresh History

✅ After delete, Total Records = 0

## 🎉 Post-Success Actions

1. **Take Screenshots** for LinkedIn
2. **Document any customizations**
3. **Plan next phases** (Agentforce, Flows, etc.)
4. **Share your learnings!**

---

*"All we have to decide is what to do with the time that is given us."* - Gandalf

You've got this! 🧙‍♂️✨
