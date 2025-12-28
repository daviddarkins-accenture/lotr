# 🌋 LOTR API to Data 360 Ingestion API POC

> *"One Ring to Rule Them All, One POC to Bind Them"*

A Python-based proof-of-concept that ingests Lord of the Rings character data from [The One API](https://the-one-api.dev) into Salesforce Data Cloud via the Ingestion API, complete with a Flask web UI featuring LOTR-themed messaging.

![The One API Homepage](assets/lotrapihome.png)
*The One API - Source of our Middle-earth data*

## 🗺️ What This Does

- **Fetches** ~933 LOTR characters + 2,383 quotes from The One API
- **Ingests Characters** into Data Cloud as `LotrCharacter` (Profile DMO)
- **Ingests Quotes** into Data Cloud as `LotrQuote` (Engagement DMO)
- **Displays Quotes** on Person Account pages via **Data Cloud Related Lists**
- **Deletes** both characters and quotes using Bulk API
- **Triggers Salesforce Flows** via Data Cloud → Account creation
- **Provides** a web UI to trigger ingestion/deletion with live status updates
- **Features** Gandalf-themed setup wizard and LOTR quotes throughout

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- A LOTR API key ([sign up here](https://the-one-api.dev/sign-up))
- Salesforce Data Cloud org with:
  - Ingestion API connector configured
  - OAuth Connected App with client credentials
  - Source API Name: `lotr`
  - Object API Names: `LotrCharacter`, `LotrQuote`

### Installation

1. **Clone or navigate to this directory**

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

4. **Configure environment variables:**
   
   Option A - Use the setup wizard:
   ```bash
   python setup.py
   ```
   Follow the prompts to configure your API keys and Data Cloud credentials. This creates a `.env` file.
   
   Option B - Manual setup:
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

5. **Start the Flask app:**
   ```bash
   python app.py
   ```
   
   Or use the quick start script: `./start.sh`

6. **Open your browser:**
   ```
   http://localhost:5001
   ```

7. **Click "Fetch LOTR Data 📜"** to load characters and quotes
8. **Click "Send Characters 🌋"** to ingest character data
9. **Click "Send Quotes 💬"** to ingest quotes (for Related Lists!)

![Data Cloud Setup](assets/dcsetup.png)
*Data Cloud Data Stream configuration*

![Data Cloud Stream](assets/dcstream.png)
*Data appearing in Data Cloud after ingestion*

## 📦 Project Structure

```
lotr/
├── schema/
│   ├── lotr_character.yaml     # Character schema (Profile DMO)
│   ├── lotr_quote.yaml         # Quote schema (Engagement DMO)
│   └── lotr_schema.yaml        # Combined schema for Data Cloud
├── static/                     # Flask static files
│   ├── bg.png                  # Background image
│   ├── style.css               # UI styling
│   └── app.js                  # Frontend JavaScript
├── templates/
│   └── index.html              # Main UI template
├── data/                       # Cache directory (auto-created)
├── app.py                      # Flask web application
├── auth.py                     # Data Cloud OAuth2 + Token Exchange
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

Data Cloud requires a **two-step authentication**:

1. **Get Salesforce Access Token** (Client Credentials Flow)
   ```
   POST {auth_url}/services/oauth2/token
   grant_type=client_credentials
   ```

2. **Exchange for Data Cloud Token**
   ```
   POST {instance_url}/services/a360/token
   grant_type=urn:salesforce:grant-type:external:cdp
   subject_token={salesforce_token}
   ```

This returns a JWT token and the Data Cloud instance URL (`*.c360a.salesforce.com`).

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

This POC demonstrates how to show Data Cloud data directly on Salesforce record pages using **Data Cloud Related Lists**.

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

For complete setup instructions, see the Salesforce Data Cloud documentation or refer to the setup wizard (`python setup.py`).

---

## 🔐 Security Notes

- **Never commit `.env`** - it contains your secrets
- All API calls happen **server-side** in Flask
- Browser never sees your credentials
- Keep your LOTR API key and Data Cloud credentials safe

## ✅ Validation

After ingestion, verify in Data Cloud Data Explorer:

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

## 🌠 Future Enhancements

- Link Salesforce Contacts to favorite LOTR characters
- Create behavioral event tracking (e.g., "viewed character profile")
- Deploy Agentforce to answer questions about customer LOTR preferences
- Build Data Actions to trigger campaigns based on character affinities

## 🧙‍♂️ Troubleshooting

**"Configuration Incomplete!" error:**
- Run `python setup.py` to set up your `.env` file

**"400 Bad Request" on ingestion:**
- Check that all schema fields are present (even with empty strings)
- Verify schema matches Data Stream configuration

**"Deletes not working":**
- Streaming DELETE doesn't work with Upsert refresh mode
- Must use Bulk API for deletes
- CSV must have NO header
- For Profile category, need 2 columns: primary key + future datetime

**Data not appearing after ingestion:**
- Processing is async (~3 minutes)
- Check Data Stream Refresh History for job status

## 📝 License

MIT - This is a learning POC, not a production system.

---

*"Even the smallest person can change the course of the future." - Gandalf*

Now go forth and ingest data like the hero Middle-earth needs! 🚀
