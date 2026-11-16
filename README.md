# OncoScreen.AI (OralCare-Vision CDSS)

Sistema Multimodal de Apoio à Decisão Clínica (CDSS) para triagem precoce de **Câncer de Cabeça e Pescoço (HNSCC / Cavidade Oral)**, projetado com arquitetura **CPU-First**, **Clean Architecture** no Backend (FastAPI + PyTorch + Ollama) e arquitetura **Feature-Based** no Frontend (React + TypeScript + Tailwind CSS) inspirada na sobriedade científica do **PubMed / NCBI**.

---

## 1. Arquitetura do Sistema

```text
+-------------------------------------------------------------------------+
|                        FRONTEND (React + Vite + TS)                     |
|  Features: auth | patients | triage | exam-history | metrics | settings |
+------------------------------------+------------------------------------+
                                     | REST / JWT (Axios + TanStack Query)
                                     v
+-------------------------------------------------------------------------+
|                    BACKEND PRESENTATION (FastAPI v1)                    |
|        Routers: /auth, /patients, /triage, /exams, /metrics, /settings  |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                   APPLICATION LAYER (Use Cases & DTOs)                  |
|  AuthenticateUser | RegisterOrSelectPatientByCPF | ExecuteMultimodal... |
+------------------------------------+------------------------------------+
                                     |
              +----------------------+----------------------+
              v                                             v
+---------------------------+                 +---------------------------+
|   DOMAIN LAYER (Pura)     |                 |   INFRASTRUCTURE LAYER    |
|  - Entities & VOs (CPF)   |                 | - SQLite (AsyncAlchemy)   |
|  - ClinicalGuardrailsSvc  |                 | - EfficientNet-B0+GradCAM |
|  - Abstract Interfaces    |                 | - Ollama SLM (qwen2.5:3b) |
+---------------------------+                 | - ReportLab PDF Generator |
                                              | - Evolution API WhatsApp  |
                                              +---------------------------+
```

### Guardrails Clínicos & Análise Comparativa
O serviço `ClinicalGuardrailsService` (`backend/app/domain/services/clinical_guardrails.py`) cruza a predição visual da CNN (`EfficientNet-B0`) com o escore clínico determinístico da anamnese:
- **Concordância Alta (`CONCORDANCIA_ALTA`)**: `CNN >= threshold` e risco clínico elevado $\rightarrow$ **Risco CRÍTICO**.
- **Discordância Crítica (`DISCORDANCIA_CRITICA` — Risco de Falso-Negativo)**: Mesmo com `CNN < threshold`, se o paciente apresentar **Evolução > 14 dias (Regra SUS)** associada a **Tabagismo ativo**, **Eritroplasia** ou **Endurecimento / Bordas elevadas**, o Guardrail eleva compulsoriamente o risco para **ALTO** e sinaliza a divergência para o SLM.

---

## 2. Configuração do Modelo SLM Local (Ollama)

1. Instale o [Ollama](https://ollama.com) na máquina host.
2. Baixe o modelo base quantizado ou importe seu `.gguf` customizado usando o `Modelfile` da raiz:

```bash
# Opção A: Usando o modelo base qwen2.5:3b
ollama pull qwen2.5:3b
ollama create oncoscreen -f Modelfile

# Opção B: Para importar um arquivo .gguf próprio, edite a linha FROM do Modelfile:
# FROM ./caminho/para/seu-modelo-quantizado.gguf
ollama create oncoscreen -f Modelfile
```

3. No `.env`, defina `OLLAMA_MODEL=oncoscreen` (ou `qwen2.5:3b`).
> **Nota:** Caso o Ollama esteja offline durante uma demonstração, o sistema aciona automaticamente um fallback clínico determinístico para não interromper a triagem.

---

## 3. Como Executar SEM Docker (Ambiente Corporativo / Notebook)

### Pré-requisitos
- Python **3.11+**
- Node.js **18+**
- *(Opcional)* Arquivo de pesos `melhor_modelo_visao.pth` em `backend/weights/melhor_modelo_visao.pth`

### Windows
Dê um duplo clique ou execute no terminal:
```bat
start.bat
```

### Linux / macOS
```bash
chmod +x run.sh
./run.sh
```

Após iniciar:
- **Frontend:** http://localhost:5173
- **Backend API / Swagger:** http://127.0.0.1:8000/docs
- **Credencial inicial (Médico):** `doutor@oncoscreen.ai` / `admin123`
- **Acesso do Paciente:** Login via **CPF** + senha inicial igual à data de nascimento (`DDMMAAAA`).

---

## 4. Como Executar COM Docker

1. Copie `.env.example` para `.env` e ajuste suas variáveis (como `EVOLUTION_API_KEY` se for usar WhatsApp).
2. Suba os containers com `network_mode: host` (permitindo comunicação direta com o Ollama local em `localhost:11434`):

```bash
cp .env.example .env
docker-compose up --build
```

Acesse http://localhost (ou porta configurada no Nginx).

---

## 5. Testes Automatizados

### Backend (Pytest)
```bash
cd backend
.venv/Scripts/python -m pytest -v   # Windows
# ou: .venv/bin/pytest -v           # Linux/Mac
```

### Frontend (Vitest + React Testing Library)
```bash
cd frontend
npm test
```

