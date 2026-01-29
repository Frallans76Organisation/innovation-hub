# Labels for Innovation Hub

Skapa dessa labels i GitHub-repot for att aktivera automatisk kategorisering.

## Hur man skapar labels

1. Ga till https://github.com/Frallans76Organisation/innovation-hub/labels
2. Klicka "New label" for varje label nedan
3. Anvand exakt samma namn och fargkod

---

## Typ-labels (automatiskt fran Issue Template)

| Label | Farg | Beskrivning |
|-------|------|-------------|
| `ide` | `#7057ff` | Ny ide eller forslag |
| `behov` | `#0075ca` | Behov fran verksamheten |
| `problem` | `#d73a4a` | Problem att losa |
| `feedback` | `#a2eeef` | Feedback pa befintligt |

## Status-labels

| Label | Farg | Beskrivning |
|-------|------|-------------|
| `inbox` | `#fbca04` | Ny, ej bedomd |
| `status:analyserad` | `#c5def5` | AI-analys genomford |
| `status:utreds` | `#bfd4f2` | Under utredning |
| `status:godkand` | `#0e8a16` | Godkand for utveckling |
| `status:avstadd` | `#ffffff` | Avstadd |
| `status:parkerad` | `#d4c5f9` | Parkerad for framtiden |

## Prioritet-labels

| Label | Farg | Beskrivning |
|-------|------|-------------|
| `priority:hog` | `#b60205` | Hog prioritet |
| `priority:medel` | `#fbca04` | Medel prioritet |
| `priority:lag` | `#c2e0c6` | Lag prioritet |

## Kategori-labels

| Label | Farg | Beskrivning |
|-------|------|-------------|
| `kategori:digital-transformation` | `#1d76db` | Digital transformation |
| `kategori:medborgarservice` | `#5319e7` | Tjanster for medborgare |
| `kategori:intern-effektivisering` | `#006b75` | Intern effektivisering |
| `kategori:sakerhet` | `#d93f0b` | Sakerhet och integritet |
| `kategori:integration` | `#0052cc` | Systemintegration |
| `kategori:ai-automation` | `#7057ff` | AI och automation |

## Service-labels

| Label | Farg | Beskrivning |
|-------|------|-------------|
| `service:befintlig` | `#c5def5` | Kan losas med befintlig tjanst |
| `service:ny` | `#d4c5f9` | Kraver ny tjanst/system |
| `service:utveckla` | `#bfdadc` | Kraver vidareutveckling |

## Malgrupp-labels

| Label | Farg | Beskrivning |
|-------|------|-------------|
| `malgrupp:medborgare` | `#006b75` | Berör medborgare |
| `malgrupp:medarbetare` | `#0e8a16` | Berör medarbetare |
| `malgrupp:foretag` | `#fbca04` | Berör foretag |

---

## Snabbkommando: Skapa alla labels via CLI

```bash
# Installera gh CLI och logga in forst
gh label create "ide" --color "7057ff" --description "Ny ide eller forslag"
gh label create "behov" --color "0075ca" --description "Behov fran verksamheten"
gh label create "problem" --color "d73a4a" --description "Problem att losa"
gh label create "feedback" --color "a2eeef" --description "Feedback pa befintligt"
gh label create "inbox" --color "fbca04" --description "Ny, ej bedomd"
gh label create "status:analyserad" --color "c5def5" --description "AI-analys genomford"
gh label create "status:utreds" --color "bfd4f2" --description "Under utredning"
gh label create "status:godkand" --color "0e8a16" --description "Godkand for utveckling"
gh label create "status:avstadd" --color "ffffff" --description "Avstadd"
gh label create "status:parkerad" --color "d4c5f9" --description "Parkerad for framtiden"
gh label create "priority:hog" --color "b60205" --description "Hog prioritet"
gh label create "priority:medel" --color "fbca04" --description "Medel prioritet"
gh label create "priority:lag" --color "c2e0c6" --description "Lag prioritet"
gh label create "kategori:digital-transformation" --color "1d76db" --description "Digital transformation"
gh label create "kategori:medborgarservice" --color "5319e7" --description "Tjanster for medborgare"
gh label create "kategori:intern-effektivisering" --color "006b75" --description "Intern effektivisering"
gh label create "kategori:sakerhet" --color "d93f0b" --description "Sakerhet och integritet"
gh label create "kategori:integration" --color "0052cc" --description "Systemintegration"
gh label create "kategori:ai-automation" --color "7057ff" --description "AI och automation"
gh label create "service:befintlig" --color "c5def5" --description "Kan losas med befintlig tjanst"
gh label create "service:ny" --color "d4c5f9" --description "Kraver ny tjanst/system"
gh label create "service:utveckla" --color "bfdadc" --description "Kraver vidareutveckling"
gh label create "malgrupp:medborgare" --color "006b75" --description "Berör medborgare"
gh label create "malgrupp:medarbetare" --color "0e8a16" --description "Berör medarbetare"
gh label create "malgrupp:foretag" --color "fbca04" --description "Berör foretag"
```
