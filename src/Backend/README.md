# AIRA Backend 🤖🎙️

Este repositório contém o código-fonte do backend da aplicação **AIRA (Artificial Intelligence Reading Assessor)**. AIRA é uma solução desenvolvida em parceria com o Senai e Google Cloud para diagnosticar a proficiência de leitura e auxiliar na identificação de casos de analfabetismo funcional em contextos educacionais e profissionais.

## 📚 Visão Geral

AIRA utiliza Inteligência Artificial e serviços do Google Cloud para processar respostas orais de estudantes. O sistema transcreve, analisa e pontua automaticamente as respostas com base em critérios de fluência, compreensão e lógica.

O backend é responsável por:
* Gerenciar autenticação de usuários.
* Administrar e aplicar avaliações.
* Integrar-se com APIs de IA (Speech-to-Text, Gemini).
* Orquestrar tarefas assíncronas (via Pub/Sub).
* Persistir dados (Cloud SQL, BigQuery, Cloud Storage, ChromaDB).
* Fornecer relatórios analíticos via Looker.

## ⚙️ Tecnologias Utilizadas

* **Linguagem/Framework:** Python + FastAPI
* **Containerização:** Docker + Docker Compose
* **Banco de Dados Relacional:** PostgreSQL (Cloud SQL)
* **Banco Vetorial:** ChromaDB (para embeddings de temas)
* **Autenticação:** Firebase Authentication (OIDC via WSO2)
* **Google Cloud Platform:**
    * Google Kubernetes Engine (GKE)
    * Speech-to-Text API
    * Gemini API
    * Pub/Sub
    * BigQuery
    * Cloud Storage
    * Looker (para BI e relatórios)
* **Migrações:** Alembic
* **CI/CD:** Azure DevOps, Artifact Registry

## 📁 Estrutura do Projeto
```bash
aira-backend/
├── chroma_data/               # Embeddings gerados para temas da indústria
├── migrations/                # Scripts de migração com Alembic
├── src/
│   └── api/
│       ├── adapters/          # Integrações externas (Google, IA, etc.)
│       ├── domain/            # Lógica de negócio e entidades
│       ├── helpers/           # Utilitários e funções auxiliares
│       ├── models/            # Modelos ORM e enums
│       ├── ports/             # Interfaces para injeção de dependência
│       └── routers/           # Definição de endpoints da API
├── tests/                     # Testes automatizados
├── versions/                  # Controle de versões do Alembic
├── docker-compose.yml
├── .env.example               # Exemplo de variáveis de ambiente
└── README.md
```

## 🚀 Como Executar Localmente

**Pré-requisitos:**
* Docker
* Docker Compose

**Passos:**

1.  Clone o repositório.
2.  Crie um arquivo `.env` a partir do `.env.example` e preencha as variáveis de ambiente necessárias.
3.  Execute o comando abaixo na raiz do projeto:
    ```bash
    docker compose up --build
    ```
4.  A aplicação será iniciada e estará disponível em `http://localhost:8000`.

## 🔐 Variáveis de Ambiente

As variáveis de ambiente necessárias para a configuração da aplicação (conexões com banco de dados, chaves de API, etc.) estão documentadas no arquivo `.env.example`. Crie seu próprio arquivo `.env` na raiz do projeto com base neste exemplo.

## 🧠 Como adicionar novos temas (ChromaDB)

Para adicionar um novo tema de avaliação que será usado para gerar questões e embeddings:

1.  Converta o conteúdo do novo tema para um arquivo `.txt`.
2.  Mova este arquivo `.txt` para o diretório `chroma_data/`.
3.  Registre o novo tema no enum `QuestionTheme` localizado em `src/api/models/exams.py`.
4.  Gere uma nova migration usando o Alembic para refletir as mudanças no modelo, se necessário.
5.  Atualize o dicionário `THEMES_DICT` no módulo de IA correspondente.
6.  Teste a criação de uma nova questão com este tema via API. Isso irá disparar o processo de geração e armazenamento dos embeddings no ChromaDB.
7.  Faça commit do novo arquivo `.txt` e dos arquivos de embeddings gerados no diretório `chroma_data/`.

## 📊 Relatórios e Dashboards

O backend integra-se ao **Looker** para visualização de dados analíticos. Isso inclui:

* Desempenho individual dos alunos.
* Progresso por turma.
* Métricas de uso da plataforma.

A autenticação e autorização para *embed* de dashboards no frontend seguem o padrão SSO (Single Sign-On), com tokens seguros gerados pela aplicação backend para garantir o acesso adequado aos dados.

## 👥 Perfis de Usuário

A plataforma suporta diferentes perfis de usuário com permissões específicas:

* **Administrador:** Gerenciamento completo da plataforma, criação/gestão de avaliações, turmas, usuários e acesso a todos os relatórios.
* **Professor:** Aplicação de avaliações para suas turmas e acompanhamento do desempenho dos seus alunos.
* **Aluno:** Realização das avaliações atribuídas e visualização dos próprios resultados.

## ✅ Testes

Os testes automatizados estão localizados na pasta `tests/` e utilizam `pytest`. Eles cobrem os principais fluxos da aplicação, incluindo lógica de domínio, endpoints da API e integrações.

Para executar os testes (com os containers rodando):

docker compose exec backend pytest

## 📦 CI/CD

O processo de Integração Contínua e Entrega Contínua (CI/CD) é gerenciado pelo Azure DevOps. O pipeline inclui:

* Build das imagens Docker da aplicação.
* Publicação das imagens no Google Artifact Registry.
* Deploy automatizado no Google Kubernetes Engine (GKE).