# 🚀 LOTR Data Cloud POC - Quick Start Guide

This guide will get you up and running in under 10 minutes!

## Prerequisites Checklist

Before you begin, make sure you have:

- [ ] **Python 3.8+** installed (`python3 --version`)
- [ ] **LOTR API Key** from [The One API](https://the-one-api.dev/sign-up)
- [ ] **Salesforce Data Cloud org** with admin access
- [ ] **Data Cloud Ingestion API Connector** configured
- [ ] **OAuth Connected App** credentials (Client ID + Secret)

## Data Cloud Setup (One-Time)

### 1. Create an Ingestion API Connector

1. Log into your Data Cloud org
2. Navigate to **Data Cloud Setup** → **Ingestion API**
3. Click **New Connector**
4. Configure:
   - **Source API Name**: `lotr`
   - Upload schema from `schema/lotr_character.yaml`

### 2. Create Data Stream

| Setting | Value |
|---------|-------|
| Object API Name | `LotrCharacter` |
| Category | **Profile** |
| Primary Key | `characterId` |
| Record Modified Field | `ingestedAt` |
| Refresh Mode | `Upsert` |

**Deploy** the data stream when done.

### 3. Create OAuth Connected App

1. **Setup** → **App Manager** → **New Connected App**
2. Enable OAuth with scopes:
   - `cdp_ingest_api`
   - `api`
   - `refresh_token, offline_access`
3. **Enable Client Credentials Flow**
4. Set **Run As** user in policies
5. Note your **Client ID** and **Client Secret**

## Application Setup

### Step 1: Install Dependencies

```bash
cd /path/to/lotr
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Run Gandalf's Setup Wizard

```bash
python setup.py
```

The wizard will ask for:

| Setting | Example |
|---------|---------|
| LOTR API Key | `abc123...` |
| Client ID | `3MVG9...` |
| Client Secret | `31B66...` |
| Auth URL | `https://your-sandbox.sandbox.my.salesforce.com` |
| Ingestion URL | `https://your-subdomain.c360a.salesforce.com` |
| Source Name | `lotr` |
| Object Name | `LotrCharacter` |

### Step 3: Start the Application

```bash
python app.py
```

Open: **http://localhost:5001**

## Using the Application

### 1. Fetch Data 📜

Click **"Fetch LOTR Data 📜"** to load ~933 characters from The One API.

### 2. Send to Data Cloud 🌋

Click **"Send to Data Cloud 🌋"** to ingest the data.

**Note:** Processing is async - data appears in ~3 minutes!

### 3. Verify in Data Cloud

1. Go to **Data Explorer**
2. Select Object: `lotr-LotrCharacter`
3. Should see ~933 records after refresh

### 4. Wipe Data 🧹

Click **"Wipe LOTR Data 🧹"** to delete all data.

This:
- Deletes Salesforce Accounts with `characterId__c`
- Submits Bulk API delete job for Data Cloud
- Wait ~3-5 minutes for processing

## Key Things to Know

### ⏱️ Async Processing (~3 minutes)

Both ingestion and deletion are **asynchronous**:
- API returns `202 Accepted` immediately
- Data appears after Data Stream refresh (~3 mins)
- Check **Refresh History** tab for job status

### 🔑 Two-Step Authentication

The app handles this automatically:
1. Gets Salesforce token
2. Exchanges for Data Cloud JWT token

### 🗑️ Bulk API for Deletes

Streaming DELETE doesn't work with Upsert refresh mode.  
The app uses **Bulk API** which requires:
- Creating a delete job
- Uploading CSV (no header, 2 columns)
- Closing the job

### 📋 All Fields Required

Data Cloud schema requires ALL fields be present.  
Missing values are sent as empty strings `""`.

## Troubleshooting

### "400 Bad Request" on ingestion

**Cause:** Schema mismatch - not all fields present

**Fix:** The app should handle this. If not, check `ingestion.py` includes all fields.

### Data not appearing after ingestion

**Cause:** Async processing

**Fix:** Wait ~3 minutes, check Data Stream Refresh History

### Deletes not working

**Cause:** Streaming DELETE doesn't work with Upsert mode

**Fix:** The app uses Bulk API. Check Refresh History for "Delete" type jobs.

### "401 Unauthorized" errors

**Cause:** Token issues

**Fix:** 
1. Check Connected App has correct scopes
2. Verify Client Credentials Flow is enabled
3. Run As user is set in policies

## Verify Success

### After Ingestion

```sql
-- In Data Cloud Query Editor
SELECT COUNT(*) FROM lotr_LotrCharacter__dll
-- Should return ~933
```

### After Deletion

- Data Stream Refresh History shows "Delete" job with `Success`
- Total Records = 0

## Quick Reference

| Action | What Happens |
|--------|--------------|
| **Fetch** | Loads 933 characters from LOTR API (cached 24h) |
| **Send** | Streams to Data Cloud in batches of 200 |
| **Wipe** | Bulk API delete + SF Account delete |

| Timing | Duration |
|--------|----------|
| Fetch | ~2 seconds (cached) |
| Send | ~5 seconds (API calls) |
| Processing | ~3 minutes (async) |
| Delete | ~2-5 minutes (bulk job) |

---

## Need Help?

Check:
- [README.md](README.md) - Full documentation
- [SALESFORCE_SETUP.md](SALESFORCE_SETUP.md) - Data Cloud setup details
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Technical implementation

---

*"Even the smallest person can change the course of the future."* - Gandalf

Now go forth and ingest data like the hero Middle-earth needs! 🚀
