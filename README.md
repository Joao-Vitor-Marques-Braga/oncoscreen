# OncoScreen.AI (OralCare-Vision CDSS)

Sistema Multimodal de Apoio à Decisão Clínica (**CDSS**) para triagem precoce de **Câncer de Cabeça e Pescoço (HNSCC / Cavidade Oral)**, projetado para rodar **100% localmente em CPU** (sem dependência de GPU dedicada ou APIs pagas em nuvem), garantindo privacidade de dados clínicos (**LGPD**), explicabilidade visual (**Grad-CAM**) e segurança diagnóstica via **Guardrails Clínicos**.

---

## 1. Arquitetura Geral do Sistema

O projeto combina **Clean Architecture** no Backend (`FastAPI` + `PyTorch` + `Ollama`) e arquitetura **Feature-Based** no Frontend (`React 18` + `TypeScript Strict` + `Tailwind CSS` + `jsPDF`), com identidade visual inspirada na sobriedade científica do **PubMed / NCBI**.

```text
+-----------------------------------------------------------------------------+
|                    FRONTEND (React 18 + TypeScript + Vite)                  |
|  Features: auth | patients | triage | exam-history | metrics | settings     |
|  • Grad-CAM Interativo (Original / Heatmap / Overlay com opacidade 0-100%)  |
|  • Exportação de Relatório Clínico em PDF 100% no navegador (jsPDF)         |
+--------------------------------------+--------------------------------------+
                                       | REST / JWT (Axios + TanStack Query)
                                       v
+-----------------------------------------------------------------------------+
|                    BACKEND PRESENTATION (FastAPI /api/v1)                   |
|        Routers: /auth | /patients | /triage | /exams | /metrics | /settings |
+--------------------------------------+--------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------+
|                  APPLICATION LAYER (Casos de Uso & DTOs)                    |
|  AuthenticateUser | RegisterOrSelectPatientByCPF | ExecuteMultimodalTriage  |
|  ListExams | GetExamDetail | GetSystemMetrics                               |
+--------------------+-------------------------------------+------------------+
                     |                                     |
                     v                                     v
+---------------------------------------+  +----------------------------------+
|         DOMAIN LAYER (Pura)           |  |       INFRASTRUCTURE LAYER       |
|  • Entities: User, Patient, Exam,     |  |  • Vision Engine (PyTorch CPU):  |
|    Anamnesis, ClinicalReport          |  |    ConvNeXt-Tiny / EfficientNet  |
|  • Value Objects: CPF, RiskLevel,     |  |    + Grad-CAM + Quadrante        |
|    AnatomicalQuadrant                 |  |  • Local SLM Client (Ollama):    |
|  • ClinicalGuardrailsService          |  |    Qwen 2.5 3B GGUF (Q4_K_M)     |
|    (Análise Comparativa & Regras SUS) |  |  • Persistência Leve:            |
|  • Interfaces Abstratas (Ports)       |  |    SQLite Async + storage local  |
+---------------------------------------+  +----------------------------------+
```

---

## 2. Como o Sistema Recebe e Atua com os Artefatos do Treinamento

O OncoScreen.AI opera em um **pipeline multimodal de 4 estágios** conectando os dois artefatos binários gerados na etapa de treinamento (Colab / PyTorch / Unsloth):

```text
Foto Intraoral (.jpg/.png)                      Anamnese Estruturada (16 itens)
           |                                                   |
           v                                                   v
 [1] Vision Engine (PyTorch CPU)                   [2] Escore Clínico + Guardrails
     • Carrega backend/weights/                        • Pontuação ponderada HNSCC
       melhor_modelo_visao.pth                         • Cruzamento Visão vs. Clínica
     • Auto-detecta ConvNeXt-Tiny /                    • Proteção Falso-Negativo (SUS)
       EfficientNet-B0                                 • Proteção Falso-Positivo Visual
     • Probabilidade + Grad-CAM + Quadrante                    |
           |                                                   |
           +-------------------------+-------------------------+
                                     v
                      [3] SLM Local (Ollama / GGUF)
                          • Carrega Qwen2.5-3B-Instruct.Q4_K_M.gguf
                            via Modelfile (template ChatML)
                          • Gera parecer clínico estruturado em PT-BR
                          • Sanitização + Guardrail (apenas biópsia/Estomatologia)
                                     |
                                     v
                 [4] Persistência Leve + Relatório PDF (Frontend)
                     • Imagens comprimidas em backend/storage/
                     • Metadados no SQLite + PDF vetorial via jsPDF
```

### 2.1. Modelo de Visão Computacional (`melhor_modelo_visao.pth`)
- **Onde colocar o artefato:** `backend/weights/melhor_modelo_visao.pth` *(ignorado pelo Git devido ao tamanho; deve ser copiado localmente após o treino)*.
- **Carregamento com Auto-Detecção** (`backend/app/infrastructure/ml/efficientnet_vision_engine.py`):
  1. Ao inicializar o backend, o motor lê o arquivo `.pth` na CPU (`torch.device("cuda" if torch.cuda.is_available() else "cpu")`) com threads configuráveis (`TORCH_NUM_THREADS=4`).
  2. Remove automaticamente o prefixo `backbone.` (gerado por wrappers de treino como `OncoScreenNet`) e inspeciona as chaves do `state_dict`:
     - Se encontrar chaves `layer_scale`, instancia automaticamente **ConvNeXt-Tiny** e reconstrói a cabeça classificadora (`Dropout(0.4)` + `Linear(768, 1)` ou `Linear(768, 2)`).
     - Caso contrário, instancia **EfficientNet-B0** com a cabeça correspondente.
  3. Caso o arquivo `.pth` ainda não esteja presente, o sistema não falha: inicializa a arquitetura sem pesos treinados e informa o status `Pesos (.pth): Inicializado` na aba **Configurações & Modelos**.
- **Pré-processamento e Inferência:**
  - A fotografia intraoral enviada pelo usuário é convertida para RGB, redimensionada para `224×224` e normalizada com média/desvio padrão da ImageNet (`mean=[0.485, 0.456, 0.406]`, `std=[0.229, 0.224, 0.225]`).
  - A saída passa por `Sigmoid` (1 logit) ou `Softmax` (2 logits), produzindo a probabilidade calibrada de suspeita visual.
- **Explicabilidade Visual (Grad-CAM) e Quadrante Anatômico:**
  - O motor registra *hooks* de `forward` e `backward` na última camada convolucional (`model.features[-1]`).
  - Calcula a média espacial dos gradientes por canal, pondera os mapas de ativação, aplica `ReLU` e normaliza para `[0, 1]`.
  - A posição de maior ativação no mapa é convertida em um **Quadrante Anatômico** (ex.: *Quadrante Superior Direito*, *Região Central / Anterior*, *Região Posterior / Orofaringe*).
  - O mapa de calor é renderizado com `cv2.COLORMAP_JET` e composto sobre a foto original, permitindo ao médico ajustar a opacidade em tempo real (`0%` a `100%`) na interface.

### 2.2. Small Language Model — SLM Local (`Qwen2.5-3B-Instruct.Q4_K_M.gguf`)
- **Origem do artefato:** Modelo `Qwen 2.5 3B` adaptado via **QLoRA (4-bit NF4)** no **Unsloth** (formato **ChatML**), fundido (*Merge & Unload*) e quantizado para **GGUF (`Q4_K_M`)** para execução leve em CPU.
- **Onde colocar o artefato:** `backend/weights/Qwen2.5-3B-Instruct.Q4_K_M.gguf` *(ignorado pelo Git)*.
- **Registro no Ollama via `Modelfile`:**
  O arquivo [Modelfile](./Modelfile) na raiz do projeto aponta diretamente para `./backend/weights/Qwen2.5-3B-Instruct.Q4_K_M.gguf`, define o template **ChatML** (`<|im_start|>` / `<|im_end|>`), os parâmetros de geração (`temperature 0.2`, `min_p 0.1`, `num_ctx 4096`) e as diretrizes clínicas do `SYSTEM` prompt.
- **Como o Backend atua sobre o modelo** (`backend/app/infrastructure/llm/ollama_slm_client.py`):
  1. Envia uma requisição assíncrona (`httpx`) para `http://localhost:11434/api/generate` contendo a probabilidade visual, o limiar configurado, o quadrante anatômico, a pontuação da anamnese, os fatores marcados e o parecer dos Guardrails.
  2. **Sanitização e Segurança Clínica:** A saída da SLM passa por `sanitize_report_text()`, que remove cercas de código (```` ```markdown ````), símbolos `#`/`**` e aplica um **guardrail determinístico de conduta**: uma triagem nunca pode recomendar cirurgia diretamente, garantindo que qualquer risco elevado direcione exclusivamente para **Estomatologia e biópsia (exame anatomopatológico)**.
  3. **Resiliência (Fallback):** Se o Ollama estiver offline durante uma demonstração, o cliente gera automaticamente um parecer clínico determinístico coerente e sinaliza `(fallback clínico)` no cabeçalho do exame.

### 2.3. Motor de Guardrails Clínicos Determinísticos (`ClinicalGuardrailsService`)
Implementado na camada pura de domínio (`backend/app/domain/services/clinical_guardrails.py`), realiza a **análise comparativa entre visão computacional e contexto clínico** com base em 16 fatores ponderados da anamnese:

| Cenário Comparativo | Condição | Risco Final | Ação Clínica |
| :--- | :--- | :--- | :--- |
| **Concordância Alta** | `CNN >= threshold` e risco clínico `ALTO` (≥ 7 pts) | **CRÍTICO** | Alerta crítico prioritário para Estomatologia e biópsia. |
| **Discordância Crítica (Falso-Negativo)** | `CNN < threshold`, mas **Evolução > 14 dias (Regra SUS)** + (*Tabagismo ativo* OU *Eritroplasia* OU *Endurecimento*) ou escore ≥ 7 pts | **ALTO** | Elevação compulsória de risco: a clínica prevalece sobre a imagem. |
| **Falso-Positivo Visual** | `CNN >= threshold`, porém escore clínico = **0 pontos** | **BAIXO** | Sinaliza possível artefato de iluminação/instrumento; prevalece o baixo risco clínico. |
| **Alerta Visual Isolado** | `CNN >= threshold` e risco clínico `BAIXO` (> 0 pts) ou `MODERADO` | **MODERADO / ALTO** | Recomenda correlação clínica presencial detalhada. |
| **Concordância Baixa** | `CNN < threshold` e risco clínico `BAIXO` ou `MODERADO` | **BAIXO / MODERADO** | Acompanhamento de rotina e orientação de retorno caso persista > 14 dias. |

### 2.4. Armazenamento Leve e Exportação de PDF no Frontend
- **Armazenamento:** As fotografias originais, heatmaps e overlays Grad-CAM são salvos como arquivos comprimidos em `backend/storage/exams/<id>/`, mantendo o banco **SQLite** leve (apenas metadados e caminhos relativos).
- **Relatório PDF Client-Side (`frontend/src/shared/utils/generateClinicalPdf.ts`):** Gerado 100% no navegador via **jsPDF**, em formato de relatório médico tradicional (cabeçalho clínico com emblema vetorial, identificação com CPF mascarado `***.XXX.XXX-**`, tabela de histórico clínico em 2 colunas com checkboxes `[X]`/`[ ]`, fotos lado a lado, parecer clínico limpo, assinatura centralizada e rodapé fixo em todas as páginas).

---

## 3. Estrutura de Diretórios

```text
oncoscreen/
├── backend/
│   ├── app/
│   │   ├── domain/                  # Camada Pura (Entities, Value Objects, Guardrails, Interfaces)
│   │   ├── application/             # Casos de Uso (Auth, Patients, Triage, Exams, Metrics) & DTOs
│   │   ├── infrastructure/          # SQLite Async, PyTorch Vision+GradCAM, Ollama SLM, JWT/Bcrypt, Storage
│   │   └── presentation/            # FastAPI Routers (/api/v1), Schemas Pydantic v2 e RBAC
│   ├── weights/                     # Colocar aqui: melhor_modelo_visao.pth e Qwen2.5-3B-Instruct.Q4_K_M.gguf
│   ├── storage/                     # SQLite local e imagens comprimidas dos exames
│   ├── tests/                       # Testes unitários e integração (Pytest)
│   ├── requirements.txt
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── shared/                  # Layout PubMed, UI, Auth/Theme Context, Cliente HTTP, Gerador PDF (jsPDF)
│   │   └── features/                # auth, patients, triage, exam-history, metrics-dashboard, model-settings
│   ├── tests/                       # Testes unitários Zod e RBAC (Vitest + Testing Library)
│   └── package.json
├── Modelfile                        # Definição ChatML + regras clínicas para importar o GGUF no Ollama
├── start.bat                        # Inicialização nativa Windows (sem Docker)
├── run.sh                           # Inicialização nativa Linux/macOS (sem Docker)
├── docker-compose.yml               # Orquestração opcional com Docker
├── .env.example                     # Modelo de variáveis de ambiente
└── README.md
```

---

## 4. Como Executar Localmente SEM Docker (Recomendado)

### Pré-requisitos
- **Python 3.11+**
- **Node.js 18+**
- **Ollama** instalado na máquina ([ollama.com/download](https://ollama.com/download))

### Passo 1 — Posicionar os Pesos Treinados
Copie os dois arquivos gerados no treinamento para a pasta `backend/weights/`:
1. `backend/weights/melhor_modelo_visao.pth` (modelo PyTorch `ConvNeXt-Tiny` ou `EfficientNet-B0`)
2. `backend/weights/Qwen2.5-3B-Instruct.Q4_K_M.gguf` (SLM quantizada exportada pelo Unsloth)

### Passo 2 — Importar o Modelo `.gguf` no Ollama
Na raiz do projeto, execute:
```bash
ollama create oncoscreen -f Modelfile
ollama list
```
*(Verifique se `oncoscreen:latest` aparece listado. No `.env`, certifique-se de manter `OLLAMA_MODEL=oncoscreen`.)*

### Passo 3 — Iniciar Backend e Frontend

**Windows:**
```bat
start.bat
```

**Linux / macOS:**
```bash
chmod +x run.sh
./run.sh
```

### Passo 4 — Acessar e Validar os Motores
- **Frontend:** `http://localhost:5173`
- **API / Swagger:** `http://127.0.0.1:8000/docs`
- Na aba **Configurações & Modelos**, confirme:
  - **PyTorch Vision Engine:** `Pesos (.pth): Carregados`
  - **Ollama Local SLM:** status **ONLINE** com `Modelo: oncoscreen`

---

## 5. Como Executar COM Docker (Opcional)

1. Copie `.env.example` para `.env` e garanta que os pesos estejam em `backend/weights/` e o modelo `oncoscreen` esteja ativo no Ollama da máquina host.
2. Execute:
```bash
cp .env.example .env
docker-compose up --build
```
*(Os containers utilizam `network_mode: host` para comunicação direta com o Ollama local em `localhost:11434`.)*

---

## 6. Perfis de Acesso (RBAC) e Demonstração

- **Médico (`DOCTOR`):**
  - **Login inicial (seed automático):** `doutor@oncoscreen.ai` / `admin123`
  - Acesso completo: busca/cadastro rápido de pacientes por CPF, triagem multimodal, Grad-CAM interativo, histórico geral, dashboard de métricas clínicas e calibração de threshold em **Configurações & Modelos**.
- **Paciente (`PATIENT`):**
  - Cadastrado automaticamente pelo médico ao iniciar a triagem por CPF (sem auto-cadastro público).
  - **Login:** CPF do paciente + senha inicial igual à data de nascimento no formato `DDMMAAAA`.
  - Acesso estritamente de leitura (`GET`) apenas aos próprios exames e exportação do próprio relatório em PDF.

---

## 7. Testes Automatizados

### Backend (`Pytest`)
Valida regras de domínio (`ClinicalGuardrailsService`), cadastro/seleção por CPF, RBAC ponta a ponta na API FastAPI e sanitização/segurança clínica do laudo:
```bash
cd backend
.venv\Scripts\python.exe -m pytest -v   # Windows
# .venv/bin/pytest -v                   # Linux / macOS
```

### Frontend (`Vitest` + `React Testing Library`)
Valida schemas `Zod` da anamnese/CPF, limpeza de texto clínico e renderização condicional RBAC (`DOCTOR` vs. `PATIENT`):
```bash
cd frontend
npm test
npm run build
```

---

> **Aviso Clínico:** O OncoScreen.AI é um protótipo acadêmico de **Sistema de Apoio à Decisão Clínica (CDSS)** voltado à triagem precoce. Ele não substitui a avaliação médica/estomatológica presencial nem o diagnóstico definitivo por exame anatomopatológico (biópsia).
