# Salesforce Data Cloud Setup Guide

Complete guide to prepare your Salesforce org for the LOTR Data Cloud POC.

Based on [Salesforce Data Cloud Ingestion API Documentation](https://developer.salesforce.com/docs/data/data-cloud-int/guide/c360-a-ingestion-api.html)

---

## Overview

### Two Ingestion Patterns

| Pattern | Use Case | Format | Our Usage |
|---------|----------|--------|-----------|
| **Streaming** | Real-time JSON payloads (up to 200KB) | JSON | ✅ Ingestion |
| **Bulk** | Large datasets, periodic syncs (up to 150MB) | CSV | ✅ Deletion |

### Key Learnings

1. **Authentication** requires two-step token exchange
2. **All schema fields** must be present in payload (use empty string for missing)
3. **Streaming DELETE** doesn't work with Upsert refresh mode
4. **Bulk API** required for deletes with Profile category
5. **Processing is async** (~3 minutes for data to appear)

---

## Step 1: Enable Data Cloud & Permissions

### 1.1 Assign Permission Sets
```
Setup → Users → [Your User] → Permission Set Assignments → Edit
```

Add these permission sets:
- `Data Cloud Admin`
- `Data Cloud User`

---

## Step 2: Create Connected App (OAuth)

### 2.1 Create App
```
Setup → App Manager → New Connected App
```

| Field | Value |
|-------|-------|
| Connected App Name | `LOTR Data Cloud POC` |
| API Name | `LOTR_Data_Cloud_POC` |
| Contact Email | *your email* |

### 2.2 OAuth Settings

Check **Enable OAuth Settings**

| Field | Value |
|-------|-------|
| Callback URL | `https://login.salesforce.com/services/oauth2/callback` |

**Required OAuth Scopes:**
- `Access and manage your Data Cloud Ingestion API data (cdp_ingest_api)`
- `Access and manage your data (api)`
- `Perform requests at any time (refresh_token, offline_access)`

### 2.3 Enable Client Credentials Flow

1. Check **Enable Client Credentials Flow**
2. After saving, click **Manage** on the Connected App
3. Click **Edit Policies**
4. Set **Permitted Users** = "Admin approved users are pre-authorized"
5. Under **Client Credentials Flow**, set **Run As** = your admin user

### 2.4 Get Credentials

Click **Manage Consumer Details** → Verify with 2FA

Copy:
- **Consumer Key** → `DATA_CLOUD_CLIENT_ID`
- **Consumer Secret** → `DATA_CLOUD_CLIENT_SECRET`

---

## Step 3: Set Up Ingestion API Connector

### 3.1 Create the Connector
```
Data Cloud Setup → Ingestion API → New
```

### 3.2 Configure Connector

| Field | Value |
|-------|-------|
| Connector Name | `LOTR` |
| Connector API Name | `lotr` |

**Important:** The Source API Name will be `lotr` (not `lotr_characters`)

---

## Step 4: Create Data Stream & Schema

### 4.1 Upload Schema File

Upload the OpenAPI schema file:
```
schema/lotr_character.yaml
```

### 4.2 Configure Data Stream

| Field | Value |
|-------|-------|
| Object Label | `LOTR Character` |
| Object API Name | `LotrCharacter` |
| Category | **Profile** (to treat characters as "people") |
| Refresh Mode | `Upsert` |
| Primary Key | `characterId` |
| Record Modified Field | `ingestedAt` |

### 4.3 Schema Fields

| Field | API Name | Type | Notes |
|-------|----------|------|-------|
| Character ID | `characterId` | Text | **Primary Key** |
| Name | `name` | Text | |
| Race | `race` | Text | |
| Gender | `gender` | Text | |
| Birth | `birth` | Text | |
| Death | `death` | Text | |
| Realm | `realm` | Text | |
| Wiki URL | `wikiUrl` | Text | |
| Height | `height` | Text | |
| Hair | `hair` | Text | |
| Spouse | `spouse` | Text | |
| Ingested At | `ingestedAt` | DateTime | **Record Modified Field** |

**Important:** All fields will be marked as required by Data Cloud. Your API must send ALL fields (use empty string for missing values).

### 4.4 Deploy the Data Stream

After saving, click **Deploy** to activate the stream.

---

## Step 5: Note the Data Cloud Instance URL

After deployment, find the **Ingestion API endpoint** in the connector details.

It will look like:
```
https://{subdomain}.c360a.salesforce.com
```

Example: `https://gmywkztdg-zd0mzzg82ggntgms.c360a.salesforce.com`

This URL is also returned by the token exchange process.

---

## Step 6: Configure .env

```bash
# LOTR API
LOTR_API_KEY=your_lotr_api_key

# Salesforce Data Cloud OAuth
DATA_CLOUD_CLIENT_ID=your_consumer_key
DATA_CLOUD_CLIENT_SECRET=your_consumer_secret

# For SANDBOX:
DATA_CLOUD_AUTH_URL=https://your-sandbox.sandbox.my.salesforce.com

# Data Cloud Ingestion URL (from connector or token exchange)
DATA_CLOUD_INGESTION_URL=https://your-subdomain.c360a.salesforce.com

# Must match EXACTLY what you configured:
DATA_CLOUD_SOURCE_NAME=lotr
DATA_CLOUD_OBJECT_NAME=LotrCharacter
```

---

## Authentication Flow

### Two-Step Token Exchange

**Step 1: Get Salesforce Access Token**
```http
POST {auth_url}/services/oauth2/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_id={client_id}
&client_secret={client_secret}
```

Response includes `access_token` and `instance_url`.

**Step 2: Exchange for Data Cloud Token**
```http
POST {instance_url}/services/a360/token
Content-Type: application/x-www-form-urlencoded

grant_type=urn:salesforce:grant-type:external:cdp
&subject_token={access_token}
&subject_token_type=urn:ietf:params:oauth:token-type:access_token
```

Response includes:
- `access_token` (JWT for Data Cloud)
- `instance_url` (e.g., `subdomain.c360a.salesforce.com`)

---

## API Endpoints Reference

### Streaming Ingestion (JSON)

```http
POST https://{dc_instance}/api/v1/ingest/sources/{source}/{object}
Authorization: Bearer {dc_token}
Content-Type: application/json

{"data": [...records...]}
```

### Streaming Validation (Test Endpoint)

```http
POST https://{dc_instance}/api/v1/ingest/sources/{source}/{object}/actions/test
Authorization: Bearer {dc_token}
Content-Type: application/json

{"data": [...records...]}
```

### Bulk Delete (Required for Profile Category)

```http
# 1. Create job
POST https://{dc_instance}/api/v1/ingest/jobs
{"object": "LotrCharacter", "sourceName": "lotr", "operation": "delete"}

# 2. Upload CSV (NO HEADER!)
PUT https://{dc_instance}/api/v1/ingest/jobs/{job_id}/batches
Content-Type: text/csv
"primary_key","future_datetime"

# 3. Close job
PATCH https://{dc_instance}/api/v1/ingest/jobs/{job_id}
{"state": "UploadComplete"}

# 4. Check status
GET https://{dc_instance}/api/v1/ingest/jobs/{job_id}
```

---

## Delete CSV Format

### For Profile Category (with Record Modified Field)

**NO HEADER** - Two columns:
1. Primary key value
2. DateTime **greater than** the original `ingestedAt`

```csv
"5cd99d4bde30eff6ebccfbbe","2025-12-01T03:12:50.000Z"
"5cd99d4bde30eff6ebccfc15","2025-12-01T03:12:50.000Z"
```

### For Engagement Category

**NO HEADER** - One column (primary key only):

```csv
"5cd99d4bde30eff6ebccfbbe"
"5cd99d4bde30eff6ebccfc15"
```

---

## Key Insights Learned

| Topic | Insight |
|-------|---------|
| **Auth** | Requires two-step token exchange for Data Cloud |
| **Payload** | All schema fields must be present (empty string for missing) |
| **Processing** | Async - data appears after ~3 minutes |
| **Streaming DELETE** | Doesn't work with Upsert refresh mode |
| **Bulk DELETE** | Required for Profile category with Record Modified Field |
| **CSV Format** | NO header for deletes; 2 columns for Profile category |

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| `400 Bad Request` (empty body) | Missing token exchange - using Salesforce token instead of Data Cloud token |
| `400 Schema mismatch` | Not all fields present in payload - include empty strings |
| `Streaming DELETE returns 202 but nothing deleted` | Use Bulk API for deletes with Profile category |
| `Bulk job stuck InProgress` | Check CSV format - no header, correct columns |
| `Data not appearing` | Wait ~3 mins for async processing; check Data Stream Refresh History |

---

*"All we have to decide is what to do with the data that is given to us."* — Gandalf
