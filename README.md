# ✈️ AeroAgent — Autonomous AI Flight Booking Agent

AeroAgent is a multi-step autonomous agent built on **Azure AI Foundry** that searches for flights, compares options using GPT-4o, and completes bookings end-to-end — without manual intervention.

Built for the **Microsoft Build with AI Hackathon** under the **Agentic Web** theme.

---

## 🎯 What it does

1. User types a natural language request — *"Find me the cheapest flight from New York to London on August 15th"*
2. Agent parses intent using GPT-4o
3. Asks clarifying questions (time preference, email)
4. Searches real flights via SerpAPI Google Flights
5. Scores and ranks options using GPT-4o reasoning
6. Fills the booking form autonomously via Playwright
7. Sends an approval request before charging
8. Completes payment and returns a PNR confirmation

---

## 🏗️ Architecture
User (React Web App)
↓
FastAPI Backend (api_server.py)
↓
Orchestrator Agent (main.py)
↓
┌─────────────────────────────────┐
│  Search Agent  → SerpAPI        │
│  Compare Agent → GPT-4o         │
│  Booking Agent → Playwright     │
│  Notify Agent  → GPT-4o         │
└─────────────────────────────────┘
↓
Azure AI Search (cache + approvals)
Azure Key Vault (secrets)
Azure Logic Apps (approval flow)

---

## 🛠️ Azure Stack

| Service | Purpose |
|---|---|
| Azure AI Foundry | Project hub, model deployment |
| Azure OpenAI GPT-4o | Intent parsing, flight scoring, confirmations |
| Azure OpenAI text-embedding-3-large | Vector embeddings |
| Azure AI Search | Flight cache + approval state store |
| Azure Key Vault | All secrets — API keys, passenger data, card tokens |
| Azure Logic Apps | Human-in-the-loop approval email workflow |
| Azure Container Apps | Playwright headless browser (production) |
| Azure Static Web Apps | React frontend hosting (production) |

---

## 🚀 Getting started

### Prerequisites
- Python 3.11+
- Node.js 20+
- Azure account with active subscription
- Azure CLI installed and logged in (`az login`)

### 1. Clone the repo
```bash
git clone https://github.com/YOURUSERNAME/aeroagent.git
cd aeroagent
```

### 2. Set up Python environment
```bash
python -m venv .venv

# Mac/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install azure-ai-inference azure-identity azure-keyvault-secrets \
  azure-search-documents playwright fastapi uvicorn httpx \
  python-dotenv pydantic requests openai

playwright install chromium
```

### 3. Create your `.env` file
```bash
cp .env.example .env
```

Fill in all values in `.env` — see `.env.example` for the required keys.

### 4. Create Azure resources
Follow the setup guide in `docs/azure-setup.md` to provision:
- Azure AI Foundry project
- GPT-4o and text-embedding-3-large deployments
- Azure AI Search (indexes created by `create_indexes.py`)
- Azure Key Vault with all secrets
- Azure Logic Apps approval workflow

### 5. Create AI Search indexes
```bash
python create_indexes.py
```

### 6. Run the backend
```bash
uvicorn api_server:app --reload --port 8000
```

### 7. Run the frontend
```bash
cd aeroagent-frontend
npm install
npm start
```

Open `http://localhost:3000` and start booking!

---

## 🧪 Test the agent directly
```bash
python main.py
```

---

## 📁 Project structure
aeroagent/
├── agents/
│   ├── search_agent.py     # SerpAPI Google Flights search
│   ├── compare_agent.py    # GPT-4o flight scoring
│   ├── booking_agent.py    # Playwright form automation
│   ├── notify_agent.py     # Confirmation message generation
│   └── logicapps.py        # Approval trigger + polling
├── tools/
│   ├── keyvault_tool.py    # Azure Key Vault secret fetcher
│   └── search_cache.py     # AI Search cache read/write
├── aeroagent-frontend/     # React web app
├── main.py                 # Orchestrator agent
├── api_server.py           # FastAPI backend
├── config.py               # Environment config
├── create_indexes.py       # AI Search index setup
└── test_model.py           # GPT-4o connection test

---

## 🔐 Security

- All secrets stored in **Azure Key Vault** — never in code
- Payment credentials fetched at runtime only
- Human approval required before any charge
- Demo mode (`DEMO_MODE=true`) sandboxes all payments

---

## 🌐 Live demo
URL:     https://witty-flower-0e99f2c10.7.azurestaticapps.net
Email:    judge@aeroagent.dev
Password: AeroAgent2026!

---

## 📄 License
MIT