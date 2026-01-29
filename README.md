# Innovation Hub - GitHub-First

Ett GitHub-baserat system for att samla in, analysera och hantera ideer och behov fran medarbetare inom Goteborgs Stad.

## Koncept

**GitHub Issues AR idedatabasen.** Innovation Hub ar ett tunt lager ovanpa GitHub som automatiserar analys och prioritering.

```
Anvandare → Issue Template → GitHub Issue → AI-analys → Labels & Kommentar → Project Board
```

## Funktioner

### 1. Ideinlamning via Issue Template
Anvandare skapar en ny issue via ett strukturerat formular med:
- Titel och beskrivning
- Typ av forslag (ide/forbattring/problem/behov)
- Malgrupp (medborgare/medarbetare/foretag)
- Bradskande-grad

### 2. Automatisk AI-analys
Nar en ny ide lamnas in kors en GitHub Action som:
- Analyserar iden med AI (vLLM/Bifrost/OpenRouter)
- Bedomer genomforbarhet och strategisk koppling
- Foreslar prioritet och kategorisering
- Laggar till analys som kommentar och labels

### 3. Kanban-board i GitHub Projects
Ideer foljs upp i ett project board med kolumner:
- Inbox → Analyserad → Godkand → I utveckling → Implementerad

## Kom igang

### 1. Skapa labels
Kor kommandona i [.github/LABELS.md](.github/LABELS.md) for att skapa alla labels.

### 2. Lagg till secrets
I repo Settings → Secrets and variables → Actions:

| Secret | Varde |
|--------|-------|
| `VLLM_BASE_URL` | `https://esbst.goteborg.se/vllm-19020/v1` |
| `VLLM_AUTH` | Base64-kodad auth |
| `BIFROST_API_KEY` | Bifrost API-nyckel |
| `OPENROUTER_API_KEY` | OpenRouter API-nyckel (backup) |

### 3. Skapa GitHub Project
1. Ga till Projects-fliken
2. Skapa nytt project (Board-vy)
3. Lagg till kolumner: Inbox, Analyserad, Godkand, I utveckling, Implementerad

### 4. Testa!
Skapa en ny issue via "New Issue" → "Ny Ide"

## Arkitektur

```
┌─────────────────────────────────────────────────────────────────────┐
│  ANVANDARE → IDE-FORMULAR → GITHUB ISSUE                            │
│                                  │                                   │
│                                  ▼                                   │
│              GITHUB ACTION (on: issues.opened)                       │
│                     │                                                │
│                     ├── 1. Las issue body                           │
│                     ├── 2. AI-analys (vLLM/Bifrost/OpenRouter)      │
│                     ├── 3. Service mapping                          │
│                     ├── 4. Strategialignment                        │
│                     │                                                │
│                     └── 5. Uppdatera issue:                         │
│                           - Labels (prioritet, kategori)            │
│                           - Kommentar med AI-analys                 │
│                           - Lagg till i GitHub Project              │
│                                  │                                   │
│                                  ▼                                   │
│              GITHUB PROJECTS (Kanban-board)                          │
│              ┌────────┬──────────┬────────┬───────────┐             │
│              │ Inbox  │Analyserad│Godkand │Utveckling │             │
│              └────────┴──────────┴────────┴───────────┘             │
│                                  │                                   │
│                                  ▼                                   │
│              UTVECKLING → PR → DEPLOY → FEEDBACK                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Filer

| Fil | Beskrivning |
|-----|-------------|
| `.github/ISSUE_TEMPLATE/idea.yml` | Formular for ideinlamning |
| `.github/workflows/ai-analyze-idea.yml` | GitHub Action for AI-analys |
| `.github/LABELS.md` | Labels att skapa + CLI-kommandon |
| `scripts/analyze_idea.py` | Python-script for AI-analys |
| `agent.md` | Instruktioner for AI-agenter |

## LLM-infrastruktur

Systemet anvander tre LLM-providers med fallback:

1. **vLLM (primar)** - Goteborgs Stads egen instans
   - Modell: `mistralai/Devstral-2-123B-Instruct-2512`
   
2. **Bifrost Gateway** - Innovationsarenans gateway
   - Modell: `anthropic/claude-sonnet-4-5-20250929`
   
3. **OpenRouter (backup)** - Extern fallback
   - Modell: `anthropic/claude-3-haiku`

## Kontakt

Fredrik Hallberg - AI-kompetensansvarig, Goteborgs Stad
