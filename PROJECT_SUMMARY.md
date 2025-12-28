# 🌋 LOTR Data Cloud POC - Project Summary

## Project Overview

A complete, production-ready proof-of-concept that demonstrates how to integrate external API data into Salesforce Data Cloud using the Ingestion API, wrapped in a beautiful LOTR-themed web interface.

## What Was Built

### ✅ Core Components

1. **Gandalf Setup Wizard** (`setup.py`)
   - Interactive CLI configuration
   - Validates all inputs
   - Creates `.env` file
   - LOTR-themed prompts and quotes

2. **Data Cloud Authentication** (`auth.py`)
   - **Two-step token exchange** (critical learning!)
     1. Get Salesforce token (Client Credentials)
     2. Exchange for Data Cloud JWT token
   - Token caching with expiration
   - Automatic refresh
   - Returns Data Cloud instance URL

3. **LOTR API Client** (`lotr_client.py`)
   - Fetches all ~933 characters with pagination
   - Smart caching (24-hour TTL)
   - Rate limiting protection
   - Error handling

4. **Ingestion Pipeline** (`ingestion.py`)
   - Transforms LOTR data to LotrCharacter schema
   - **All fields required** (sends empty string for missing)
   - Batches records (200 per batch)
   - Uses Streaming API: `POST /api/v1/ingest/sources/{source}/{object}`
   - Payload format: `{"data": [...records...]}`

5. **Deletion Pipeline** (`deletion.py`)
   - **Uses Bulk API** (Streaming DELETE doesn't work with Upsert mode!)
   - Creates bulk job with `operation: delete`
   - CSV format: NO header, 2 columns for Profile category
   - Also deletes Salesforce Accounts with `characterId__c`

6. **Flask Web Application** (`app.py`)
   - Routes: `/`, `/fetch`, `/ingest`, `/wipe`
   - Server-side processing (secrets never exposed)
   - JSON responses for frontend

7. **Beautiful Web UI**
   - `templates/index.html` - Semantic HTML structure
   - `static/style.css` - LOTR-themed styling
   - `static/app.js` - Interactive frontend
   - Live activity log with LOTR quotes

## Key Technical Learnings

### 🔑 Authentication: Two-Step Token Exchange

This was a critical discovery! Data Cloud requires:

```python
# Step 1: Get Salesforce token
POST {auth_url}/services/oauth2/token
→ Returns: access_token, instance_url

# Step 2: Exchange for Data Cloud token  
POST {instance_url}/services/a360/token
grant_type=urn:salesforce:grant-type:external:cdp
subject_token={salesforce_token}
→ Returns: JWT access_token, Data Cloud instance_url (*.c360a.salesforce.com)
```

### 📤 Ingestion: Streaming API

```python
POST https://{dc_instance}/api/v1/ingest/sources/lotr/LotrCharacter
Authorization: Bearer {dc_jwt_token}
Content-Type: application/json

{"data": [{...all fields, empty string for missing...}]}
```

**Critical:** All schema fields must be present. Use empty string `""` for missing values.

### 🗑️ Deletion: Bulk API Required

Streaming DELETE returns `202 Accepted` but **doesn't delete** with Upsert refresh mode!

**Solution: Use Bulk API**

```python
# 1. Create delete job
POST /api/v1/ingest/jobs
{"object": "LotrCharacter", "sourceName": "lotr", "operation": "delete"}

# 2. Upload CSV (NO HEADER!)
PUT /api/v1/ingest/jobs/{id}/batches
"primary_key","datetime_greater_than_ingestedAt"

# 3. Close job
PATCH /api/v1/ingest/jobs/{id}
{"state": "UploadComplete"}
```

### ⏱️ Async Processing

Both ingestion and deletion are **async** with ~3 minute delay:
- API returns `202 Accepted` immediately
- Data appears in Data Lake after Data Stream refresh (~3 mins)
- Check **Data Stream Refresh History** for job status

## Data Flow Architecture

```
┌─────────────┐
│ LOTR API    │ → fetch_characters() → Cache (24h TTL)
└─────────────┘                             ↓
                                    transform_character()
                                    (include ALL fields!)
                                            ↓
                                    batch_records(200)
                                            ↓
┌──────────────────────┐           Two-Step Token Exchange
│ Data Cloud          │ ←─────── 1. Salesforce Token
│ Ingestion API       │          2. Data Cloud JWT Token
│  └─ LotrCharacter   │                    ↓
│     (DLO)           │ ←─────── POST /api/v1/ingest/sources/lotr/LotrCharacter
└──────────────────────┘          {"data": [...]}
        ↓
    ~3 min async
        ↓
┌──────────────────────┐
│ Data Lake Object     │ → Can trigger Flows → Create Accounts
└──────────────────────┘

DELETION (Bulk API):
┌──────────────────────┐
│ Bulk Delete Job      │ ← POST /api/v1/ingest/jobs {operation: delete}
│  └─ CSV Upload       │ ← PUT /api/v1/ingest/jobs/{id}/batches
│     (no header!)     │    "pk","future_datetime"
│  └─ Close Job        │ ← PATCH {state: UploadComplete}
└──────────────────────┘
```

## Project Structure

```
lotr/
├── app.py                      # Flask web application
├── auth.py                     # Two-step token exchange!
├── config.py                   # Configuration validation
├── deletion.py                 # Bulk API deletion (not streaming!)
├── ingestion.py                # Streaming ingestion
├── lotr_client.py              # LOTR API wrapper
├── setup.py                    # Gandalf wizard
├── schema/
│   └── lotr_character.yaml     # OpenAPI schema
├── static/
│   ├── style.css
│   └── app.js
├── templates/
│   └── index.html
├── README.md
├── SALESFORCE_SETUP.md
├── QUICKSTART.md
└── PROJECT_SUMMARY.md          # This file
```

## Success Metrics

### Technical Success

✅ **~933 characters ingested** from The One API  
✅ **Zero duplicates** via idempotent upserts  
✅ **Bulk API deletes** work with Profile category  
✅ **Two-step auth** properly implemented  
✅ **All fields included** (empty strings for missing)  
✅ **Flow triggers** Salesforce Account creation  

### Lessons Learned

| Topic | Before | After |
|-------|--------|-------|
| **Auth** | Single Salesforce token | Two-step exchange for Data Cloud JWT |
| **Payload** | Only include non-null fields | ALL fields required (empty string) |
| **Delete** | Streaming DELETE | Bulk API (for Upsert mode) |
| **CSV Format** | With headers | NO headers for deletes |
| **Processing** | Expected instant | Async ~3 minutes |

## Configuration Summary

```bash
# .env file
LOTR_API_KEY=your_key
DATA_CLOUD_CLIENT_ID=your_client_id
DATA_CLOUD_CLIENT_SECRET=your_secret
DATA_CLOUD_AUTH_URL=https://your-sandbox.sandbox.my.salesforce.com
DATA_CLOUD_INGESTION_URL=https://your-subdomain.c360a.salesforce.com
DATA_CLOUD_SOURCE_NAME=lotr
DATA_CLOUD_OBJECT_NAME=LotrCharacter
```

## Final Notes

This POC demonstrates the complete Data Cloud Ingestion API workflow including the nuances that aren't immediately obvious from documentation:

1. **Token exchange is required** - Salesforce token alone won't work
2. **Schema strictness** - All fields must be present
3. **Delete complexity** - Bulk API required for certain configurations
4. **Async nature** - Plan for ~3 minute delays

---

**Project Status**: ✅ Complete and working

**Last Updated**: December 1, 2025

**Version**: 2.0.0 (with Bulk API deletes)

*"All we have to decide is what to do with the data that is given to us."* — Gandalf
