# Innovation Hub - OpenShift Deployment Guide

## Förutsättningar

- Tillgång till OpenShift-klustret
- `oc` CLI installerat
- `helm` CLI installerat (v3+)
- API-nycklar för OpenRouter och OpenAI (fråga utvecklingsteamet)

## Snabbstart (5 minuter)

### 1. Logga in på OpenShift

```bash
oc login https://api.your-cluster.com --token=<din-token>
```

### 2. Skapa eller välj projekt

```bash
oc new-project innovation-hub
# eller om projektet redan finns:
oc project innovation-hub
```

### 3. Klona repot

```bash
git clone https://github.com/FRALLAN76/innovation-hub.git
cd innovation-hub
```

### 4. Installera med Helm

```bash
helm install innovation-hub ./helm \
  --set secrets.openrouterApiKey=<OPENROUTER_API_KEY> \
  --set secrets.openaiApiKey=<OPENAI_API_KEY>
```

### 5. Verifiera deployment

```bash
# Kolla att podden startar
oc get pods -w

# När STATUS är "Running", hämta URL:en
oc get route innovation-hub
```

### 6. Öppna applikationen

Öppna URL:en från route i webbläsaren. API-dokumentation finns på `/docs`.

---

## Konfiguration

### Anpassa domännamn

```bash
helm install innovation-hub ./helm \
  --set secrets.openrouterApiKey=<KEY> \
  --set secrets.openaiApiKey=<KEY> \
  --set route.host=innovation-hub.apps.your-domain.com
```

### Ändra resurser (CPU/minne)

```bash
helm install innovation-hub ./helm \
  --set secrets.openrouterApiKey=<KEY> \
  --set secrets.openaiApiKey=<KEY> \
  --set resources.requests.memory=2Gi \
  --set resources.limits.memory=8Gi
```

### Ändra storage-storlek

```bash
helm install innovation-hub ./helm \
  --set secrets.openrouterApiKey=<KEY> \
  --set secrets.openaiApiKey=<KEY> \
  --set persistence.data.size=5Gi \
  --set persistence.chromadb.size=10Gi
```

---

## Vanliga kommandon

| Kommando | Beskrivning |
|----------|-------------|
| `oc get pods` | Visa poddar |
| `oc logs -f deployment/innovation-hub` | Följ loggar |
| `oc get route` | Visa URL |
| `helm upgrade innovation-hub ./helm --set ...` | Uppdatera konfiguration |
| `helm uninstall innovation-hub` | Ta bort allt |

---

## Felsökning

### Pod startar inte

```bash
# Kolla events
oc describe pod -l app.kubernetes.io/name=innovation-hub

# Kolla loggar
oc logs deployment/innovation-hub
```

### Vanliga problem

| Problem | Lösning |
|---------|---------|
| `ImagePullBackOff` | Imagen kan inte laddas. Kolla att GHCR är nåbart. |
| `CrashLoopBackOff` | Kolla loggarna med `oc logs`. Ofta saknas API-nycklar. |
| `Pending` | Väntar på resurser. Kolla PVC med `oc get pvc`. |

---

## Kontakt

Vid problem, kontakta utvecklingsteamet.

**Image:** `ghcr.io/frallan76/innovation-hub:1.0.0`
**Repo:** https://github.com/FRALLAN76/innovation-hub
