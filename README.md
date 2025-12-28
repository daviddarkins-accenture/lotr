# 🌋 LOTR API to Data 360 Ingestion API POC

> *"One Ring to Rule Them All, One POC to Bind Them"*

A Python-based proof-of-concept that ingests Lord of the Rings character data from [The One API](https://the-one-api.dev) into Salesforce Data 360 via the Ingestion API, complete with a Flask web UI featuring LOTR-themed messaging.

![The One API Homepage](assets/lotrapihome.png)
*The One API - Source of our Middle-earth data*

## 🗺️ What This Does

- **Fetches** ~933 LOTR characters + 2,383 quotes from The One API
- **Ingests Characters** into Data 360 as `LotrCharacter` (Profile DMO)
- **Ingests Quotes** into Data 360 as `LotrQuote` (Engagement DMO)
- **Displays Quotes** on Person Account pages via **Data Cloud Related Lists**
- **Deletes** both characters and quotes using Bulk API
- **Triggers Salesforce Flows** via Data 360 → Account creation
- **Provides** a web UI to trigger ingestion/deletion with live status updates
- **Features** Gandalf-themed setup wizard and LOTR quotes throughout

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- A LOTR API key ([sign up here](https://the-one-api.dev/sign-up))
- Salesforce Data 360 org with admin access

### Installation

1. **Clone this repository:**
   ```bash
   git clone https://github.com/daviddarkins-accenture/lotr.git
   cd lotr
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
   
   On Windows, use: `venv\Scripts\activate`

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Salesforce Data 360** (see [Salesforce Data 360 Setup](#-salesforce-data-360-setup) section below):
   - Create OAuth Connected App
   - Create Ingestion API Connector (Source API Name: `lotr`)
   - Create Data Streams for `LotrCharacter` and `LotrQuote`

5. **Configure environment variables:**
   
   **Option A - Use the setup wizard (Recommended):**
   ```bash
   python setup.py
   ```
   
   The wizard will guide you through:
   1. **LOTR API Key** - Get one at https://the-one-api.dev/sign-up
   2. **Data Cloud Client ID** - From your OAuth Connected App
   3. **Data Cloud Client Secret** - From your OAuth Connected App
   4. **Data Cloud Auth URL** - Default: `https://login.salesforce.com` (or your sandbox URL)
   5. **Data Cloud Ingestion API URL** - Your Data 360 instance URL (e.g., `https://your-instance.c360a.salesforce.com`)
   6. **Source API Name** - Default: `lotr` (must match your Data Stream configuration)
   7. **Object API Name** - Default: `LotrCharacter` (must match your Data Stream configuration)
   
   This creates a `.env` file with all your credentials.
   
   **Option B - Manual setup:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

6. **Start the Flask app:**
   ```bash
   python app.py
   ```
   
   Or use the quick start script: `./start.sh`

7. **Open your browser:**
   ```
   http://localhost:5001
   ```

8. **Click "Fetch LOTR Data 📜"** to load characters and quotes
9. **Click "Send Characters 🌋"** to ingest character data
10. **Click "Send Quotes 💬"** to ingest quotes (for Related Lists!)

![Data Cloud Setup](assets/dcsetup.png)
*Data 360 Data Stream configuration*

![Data Cloud Stream](assets/dcstream.png)
*Data appearing in Data 360 after ingestion*

## 📦 Project Structure

```
lotr/
├── schema/
│   ├── lotr_character.yaml     # Character schema (Profile DMO)
│   ├── lotr_quote.yaml         # Quote schema (Engagement DMO)
│   └── lotr_schema.yaml        # Combined schema for Data 360
├── static/                     # Flask static files
│   ├── bg.png                  # Background image
│   ├── style.css               # UI styling
│   └── app.js                  # Frontend JavaScript
├── templates/
│   └── index.html              # Main UI template
├── SFDC/lotr/
│   ├── force-app/              # Salesforce metadata
│   └── manifest/               # Package manifest
├── assets/                     # Screenshots and images
├── app.py                      # Flask web application
├── auth.py                     # Data 360 OAuth2 + Token Exchange
├── config.py                   # Configuration validation
├── deletion.py                 # Bulk API deletion pipeline
├── ingestion.py                # Streaming ingestion pipeline
├── lotr_client.py              # LOTR API client
├── setup.py                    # Gandalf's setup wizard
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🔑 Key Technical Details

### Authentication (Two-Step Token Exchange)

Data 360 requires a **two-step authentication**:

1. **Get Salesforce Access Token** (Client Credentials Flow)
   ```
   POST {auth_url}/services/oauth2/token
   grant_type=client_credentials
   ```

2. **Exchange for Data 360 Token**
   ```
   POST {instance_url}/services/a360/token
   grant_type=urn:salesforce:grant-type:external:cdp
   subject_token={salesforce_token}
   ```

This returns a JWT token and the Data 360 instance URL (`*.c360a.salesforce.com`).

**Reference:** [Data Cloud Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.c360a_api.meta/c360a_api/c360a_api_get_token.htm)

### Ingestion (Streaming API)

```
POST https://{dc_instance}/api/v1/ingest/sources/{source}/{object}
Authorization: Bearer {dc_token}
Content-Type: application/json

{"data": [{...record...}, {...record...}]}
```

**Important:**
- All schema fields must be present (use empty string for missing values)
- Processing is async (~3 minutes)
- Returns `202 Accepted`

**Reference:** [Streaming Ingestion API](https://developer.salesforce.com/docs/atlas.en-us.c360a_api.meta/c360a_api/c360a_api_streaming_ingest.htm)

### Deletion (Bulk API)

Streaming DELETE doesn't work with "Upsert" refresh mode. Must use **Bulk API**:

```python
# 1. Create job
POST /api/v1/ingest/jobs
{"object": "LotrCharacter", "sourceName": "lotr", "operation": "delete"}

# 2. Upload CSV (NO HEADER, 2 columns for Profile category)
PUT /api/v1/ingest/jobs/{id}/batches
"primary_key_value","datetime_greater_than_ingestedAt"

# 3. Close job
PATCH /api/v1/ingest/jobs/{id}
{"state": "UploadComplete"}
```

**CSV Format for Profile Category:**
```csv
"5cd99d4bde30eff6ebccfbbe","2025-12-01T03:12:50.000Z"
"5cd99d4bde30eff6ebccfc15","2025-12-01T03:12:50.000Z"
```

## 💬 Data Cloud Related Lists

This POC demonstrates how to show Data 360 data directly on Salesforce record pages using **Data Cloud Related Lists**.

![Characters in Salesforce](assets/SFLOTR Characters.png)
*LOTR Characters as Person Accounts in Salesforce*

![Related List on Account](assets/treebeard-quoterelatedlist.png)
*Data Cloud Related List showing quotes on Treebeard's Account page*

### How It Works

1. **LotrQuote** is configured as an **Engagement** category DMO
2. Quotes link to **Account** via `characterId`
3. A **Data Cloud Related List** displays quotes on Person Account pages

### Setup Requirements

- DMO Category: **Engagement** (required for Related Lists!)
- Primary Key: `quoteId`
- Event Time Field: `ingestedAt`
- Relationship: `LotrQuote.characterId` → `Account.characterId`

## 🏗️ Salesforce Data 360 Setup

### Step 1: Create OAuth Connected App

1. **Setup** → **App Manager** → **New Connected App**
2. Enable OAuth with scopes:
   - `cdp_ingest_api`
   - `api`
   - `refresh_token, offline_access`
3. **Enable Client Credentials Flow**
4. Set **Run As** user in policies
5. Note your **Client ID** and **Client Secret**

### Step 2: Create Ingestion API Connector

1. **Data Cloud Setup** → **Ingestion API** → **New**
2. Configure:
   - **Connector API Name**: `lotr`
   - Upload schema from `schema/lotr_character.yaml`

### Step 3: Create Data Stream

| Setting | Value |
|---------|-------|
| Object API Name | `LotrCharacter` |
| Category | **Profile** |
| Primary Key | `characterId` |
| Record Modified Field | `ingestedAt` |
| Refresh Mode | `Upsert` |

**Deploy** the data stream when done.

### Step 4: Note Data 360 Instance URL

After deployment, find the **Ingestion API endpoint** in the connector details:
```
https://{subdomain}.c360a.salesforce.com
```

This URL is also returned by the token exchange process.

### Step 5: Configure Data Cloud Triggered Flow (Optional)

If you want to automatically create Person Accounts when characters are ingested, you'll need to update the Flow metadata:

1. **Find your Data Cloud object API name:**
   - Go to **Data Cloud Setup** → **Data Streams** → Select your stream
   - Note the **Object API Name** (format: `{source}_{object}_{orgId}__dlm`)
   - Example: `lotr_LotrCharacter_D737044C__dlm`

2. **Update the Flow metadata:**
   - Open `SFDC/lotr/force-app/main/default/flows/lotrCreateAccount.flow-meta.xml`
   - Update line 107: Replace `lotr_LotrCharacter_D737044C__dlm` with your actual object API name
   - The `D737044C` part is org-specific — you'll have a different identifier

3. **Deploy the Flow:**
   ```bash
   cd SFDC/lotr
   sf project deploy start --source-dir force-app/main/default/flows
   ```

**Reference:** [Data Cloud Connectors and Integrations (Trailhead)](https://trailhead.salesforce.com/content/learn/modules/data-cloud-connectors-and-integrations)

## ✅ Validation

After ingestion, verify in Data 360 Data Explorer:

**Characters:**
- Select Object: `lotr-LotrCharacter`
- Should see ~933 records

**Quotes:**
- Select Object: `lotr-LotrQuote`
- Should see ~2,383 records

**Related Lists:**
- Open a Person Account (e.g., "Treebeard" or "Bilbo Baggins")
- Quotes should appear in the Related List panel

![Treebeard Character](assets/treebeard.png)
*Example: Treebeard character profile with related quotes*

After deletion:
- Check Data Stream Refresh History for "Delete" operations
- Both Character and Quote records should go to 0

## 🔐 Security Notes

- **Never commit `.env`** - it contains your secrets
- All API calls happen **server-side** in Flask
- Browser never sees your credentials
- Keep your LOTR API key and Data 360 credentials safe

## 🧙‍♂️ Troubleshooting

**"Configuration Incomplete!" error:**
- Run `python setup.py` to set up your `.env` file

**"400 Bad Request" on ingestion:**
- Check that all schema fields are present (even with empty strings)
- Verify schema matches Data Stream configuration
- Ensure you're using Data 360 token (not Salesforce token)

**"Deletes not working":**
- Streaming DELETE doesn't work with Upsert refresh mode
- Must use Bulk API for deletes
- CSV must have NO header
- For Profile category, need 2 columns: primary key + future datetime

**Data not appearing after ingestion:**
- Processing is async (~3 minutes)
- Check Data Stream Refresh History for job status

**"401 Unauthorized" errors:**
- Verify Connected App has correct scopes
- Check Client Credentials Flow is enabled
- Verify Run As user is set in policies

## 🌠 Future Enhancements

- Link Salesforce Contacts to favorite LOTR characters
- Create behavioral event tracking (e.g., "viewed character profile")
- Deploy Agentforce to answer questions about customer LOTR preferences
- Build Data Actions to trigger campaigns based on character affinities

## 📝 License

MIT - This is a learning POC, not a production system.

---

## 📚 Additional Resources

- [Data Cloud Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.c360a_api.meta/c360a_api/c360a_api_quick_start.htm)
- [Data Cloud Connectors and Integrations (Trailhead)](https://trailhead.salesforce.com/content/learn/modules/data-cloud-connectors-and-integrations)
- [Data Cloud Quick Look (Trailhead)](https://trailhead.salesforce.com/content/learn/modules/data-cloud-quick-look)
- [The One API Documentation](https://the-one-api.dev/documentation)

---

*"Even the smallest person can change the course of the future." - Gandalf*

Now go forth and ingest data like the hero Middle-earth needs! 🚀
