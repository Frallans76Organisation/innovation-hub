#!/usr/bin/env python3
"""
AI-analys av ideer for Innovation Hub.

Anvander vLLM (Goteborgs Stad) som primär LLM,
med Bifrost och OpenRouter som fallback.
"""

import argparse
import json
import os
import sys
from typing import Optional

import httpx

# Timeout for API-anrop
TIMEOUT = 60.0


def get_issue_body(repo: str, issue_number: int, github_token: str) -> str:
    """Hamta issue body fran GitHub API."""
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    response = httpx.get(url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json().get("body", "")


def call_vllm(prompt: str) -> Optional[str]:
    """Anropa Goteborgs Stads vLLM."""
    base_url = os.environ.get("VLLM_BASE_URL", "https://esbst.goteborg.se/vllm-19020/v1")
    auth = os.environ.get("VLLM_AUTH")
    
    if not auth:
        print("VLLM_AUTH not set, skipping vLLM")
        return None
    
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive"
    }
    
    payload = {
        "model": "mistralai/Devstral-2-123B-Instruct-2512",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 2000
    }
    
    try:
        response = httpx.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"vLLM error: {e}")
        return None


def call_bifrost(prompt: str) -> Optional[str]:
    """Anropa Bifrost Gateway."""
    api_key = os.environ.get("BIFROST_API_KEY")
    
    if not api_key:
        print("BIFROST_API_KEY not set, skipping Bifrost")
        return None
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "anthropic/claude-sonnet-4-5-20250929",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 2000
    }
    
    try:
        response = httpx.post(
            "https://llm.innovationsarenan.se/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Bifrost error: {e}")
        return None


def call_openrouter(prompt: str) -> Optional[str]:
    """Anropa OpenRouter som sista fallback."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    
    if not api_key:
        print("OPENROUTER_API_KEY not set, skipping OpenRouter")
        return None
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "anthropic/claude-3-haiku",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 2000
    }
    
    try:
        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"OpenRouter error: {e}")
        return None


def analyze_idea(issue_title: str, issue_body: str) -> tuple[str, list[str]]:
    """
    Analysera en ide med AI.
    Returnerar (markdown-analys, lista med labels).
    """
    
    prompt = f"""Du ar en AI-assistent for Goteborgs Stads Innovation Hub.
Analysera foljande ide och ge en strukturerad bedomning.

## Ide att analysera

**Titel:** {issue_title}

**Beskrivning:**
{issue_body}

---

## Instruktioner

Ge en analys i foljande format (pa svenska):

### Sammanfattning
En kort sammanfattning av iden (2-3 meningar).

### Problemanalys
- Vilket problem loser iden?
- Hur stort ar problemet? (beror manga/fa?)

### Genomforbarhet
- Teknisk komplexitet (lag/medel/hog)
- Uppskattad tidsatgang
- Beroenden till andra system

### Strategisk koppling
- Hur passar iden med digital transformation?
- Potential for ateranvandning

### Rekommendation
En av: **Prioritera hogt**, **Utreda vidare**, **Parkera**, **Avsta**

### Foreslagna labels
Lista exakt de labels som bor laggas till (valj fran: priority:hog, priority:medel, priority:lag, kategori:digital-transformation, kategori:medborgarservice, kategori:intern-effektivisering, kategori:sakerhet, service:befintlig, service:ny)

Svara ENDAST med analysen i markdown-format. Avsluta med en JSON-array av labels pa en egen rad efter "LABELS:".
"""

    # Forsok med vLLM forst, sedan Bifrost, sedan OpenRouter
    result = call_vllm(prompt)
    if not result:
        result = call_bifrost(prompt)
    if not result:
        result = call_openrouter(prompt)
    
    if not result:
        return (
            "## AI-analys kunde inte genomforas\n\nIngen LLM-tjänst var tillgänglig. En handläggare kommer granska idén manuellt.",
            []
        )
    
    # Extrahera labels fran svaret
    labels = []
    analysis = result
    
    if "LABELS:" in result:
        parts = result.split("LABELS:")
        analysis = parts[0].strip()
        try:
            labels_str = parts[1].strip()
            # Hitta JSON-array
            start = labels_str.find("[")
            end = labels_str.find("]") + 1
            if start >= 0 and end > start:
                labels = json.loads(labels_str[start:end])
        except (json.JSONDecodeError, IndexError):
            pass
    
    # Lagg till analyserad-label
    labels.append("status:analyserad")
    
    # Formatera analysen
    formatted_analysis = f"""## AI-analys

{analysis}

---
*Denna analys ar automatiskt genererad av Innovation Hub AI. Kontakta en handlaggare for fragor.*
"""
    
    return formatted_analysis, labels


def main():
    parser = argparse.ArgumentParser(description="Analysera en ide med AI")
    parser.add_argument("--issue-number", required=True, type=int)
    parser.add_argument("--issue-title", required=True)
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()
    
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print("GITHUB_TOKEN not set")
        sys.exit(1)
    
    # Hamta issue body
    print(f"Fetching issue #{args.issue_number} from {args.repo}")
    issue_body = get_issue_body(args.repo, args.issue_number, github_token)
    
    # Analysera
    print("Running AI analysis...")
    analysis, labels = analyze_idea(args.issue_title, issue_body)
    
    # Spara resultat
    with open("analysis_result.md", "w") as f:
        f.write(analysis)
    
    with open("analysis_labels.json", "w") as f:
        json.dump(labels, f)
    
    print(f"Analysis complete. Labels: {labels}")


if __name__ == "__main__":
    main()
