# agent.md - Innovation Hub

> **Standard:** Innovation Hub Agent Configuration v1.0
> **Organisation:** Frallans76Organisation
> **Senast uppdaterad:** 2026-01-29

---

## Projektöversikt

**Projektnamn:** Innovation Hub
**Beskrivning:** AI-drivet system för idéinsamling, analys och tjänstemappning mot kommunal tjänsteportfölj
**Status:** development
**Projekttyp:** platform

---

## Referensarkitektur & Standarder

| Resurs | Länk |
|--------|------|
| Referensarkitektur | https://github.com/Frallans76Organisation/docs (kommer) |
| Detta projekt | https://github.com/Frallans76Organisation/innovation-hub |
| Anonymisering (relaterat) | https://github.com/Frallans76Organisation/Anonymisering |

---

## Kommandon

```bash
# Utvecklingsmiljö
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Starta applikationen
python start.py

# Tester
pytest tests/ -v

# Med Docker
docker compose up -d
```

---

## Projektstruktur

```
innovation-hub/
├── agent.md              # Denna fil - AI-agent instruktioner
├── README.md             # Användarfokuserad dokumentation
├── start.py              # Applikationens startpunkt
├── main.py               # FastAPI application
├── models.py             # Pydantic datamodeller
├── ai_service.py         # AI-analystjänster (OpenRouter/Qwen3)
├── rag_service.py        # RAG med ChromaDB (202 tjänster)
├── static/               # Frontend (HTML, CSS, JS)
├── tests/                # 81 tester
├── helm/                 # Helm charts för OpenShift
├── chroma_db/            # Vector store för tjänster
└── .github/workflows/    # CI/CD
```

---

## Kodkonventioner

- **Språk i kod:** Engelska (variabelnamn, funktioner, klasser)
- **Språk i kommentarer:** Svenska (domänspecifik terminologi)
- **Formattering:** black, isort
- **Typning:** Type hints, Pydantic för validering
- **API:** FastAPI med OpenAPI-dokumentation

---

## Domänterminologi

| Term | Förklaring |
|------|------------|
| Idé | Inlämnat förslag från medarbetare |
| Service Mapping | RAG-baserad matchning mot 202 kommunala tjänster |
| Gap-analys | Identifiering av saknade tjänster (<30% match) |
| Strategialignment | Koppling till Stratsys-mål |
| Utlysning | Finansieringsmöjlighet (Vinnova, EU Horizon, etc.) |

---

## GitHub Integration

### Issue-format
```
[TYP] Kort beskrivning

Typer: [FEL] [FUNKTION] [FÖRBÄTTRING] [DOCS] [REFACTOR]
```

### Labels
- `innovation-hub`: Kärnfunktionalitet
- `ai-analysis`: AI/ML-relaterat
- `rag`: Vector search / ChromaDB
- `frontend`: UI-ändringar
- `api`: Backend API

### Branch-namngivning
```
feature/[issue-nr]-kort-beskrivning
fix/[issue-nr]-kort-beskrivning
```

---

## CI/CD Pipeline

### GitHub Actions Stages
1. **test** - pytest med coverage
2. **lint** - black, isort, flake8
3. **build** - Docker image → GHCR
4. **deploy** - Helm upgrade (manuell trigger)

### ArgoCD (framtida)
- **GitOps repo:** https://github.com/Frallans76Organisation/gitops
- **Manifest path:** apps/innovation-hub/

---

## MCP-servrar (konfiguration)

```json
{
  "mcpServers": {
    "github": {
      "comment": "Issues, PRs - för att koppla idéer till utveckling"
    },
    "kubernetes": {
      "comment": "OpenShift-status för deployment"
    },
    "lightrag": {
      "comment": "RAG-sökning i referensarkitektur",
      "url": "http://localhost:9621"
    }
  }
}
```

---

## Testning

| Typ | Plats | Antal | Krav |
|-----|-------|-------|------|
| Enhetstester | `tests/` | 81 | Coverage >= 80% |
| API-tester | `tests/test_api.py` | - | Alla endpoints |
| AI-validering | `tests/test_ai_service.py` | - | Analysflöde |

---

## Säkerhet

- API-nycklar i `.env` (ALDRIG commit:a)
- OpenRouter API för AI-analys
- OpenAI API för embeddings
- Följ OWASP riktlinjer

---

## Innovation Hub Flöde

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────┐
│ Idéformulär │───▶│ AI-analys    │───▶│ Service     │───▶│ GitHub   │
│             │    │ - Kategori   │    │ Mapping     │    │ Issue    │
│             │    │ - Prioritet  │    │ (RAG 202)   │    │ (auto)   │
│             │    │ - Sentiment  │    │             │    │          │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────┘
                                              │
                         ┌────────────────────┴────────────────────┐
                         ▼                                         ▼
                 ┌──────────────┐                          ┌──────────────┐
                 │ Befintlig    │                          │ Gap-analys   │
                 │ tjänst ≥60%  │                          │ Ny behövs    │
                 └──────────────┘                          └──────────────┘
```

---

## Relaterade projekt

| Projekt | Relation |
|---------|----------|
| Anonymisering | Innovationsprojekt - MVP-exempel på idé→implementation |
| docs | Referensarkitektur och standarder |
| gitops | ArgoCD deployment manifests |

---

## Kontakt

- **Projektägare:** Fredrik Hallgren
- **Organisation:** Frallans76Organisation
