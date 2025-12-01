# Authentication: Cloud Run & Vertex AI

This document explains how the Backend service running on Cloud Run authenticates with Google Cloud services, specifically Vertex AI.

## Overview

The authentication mechanism relies on **Service Accounts** and **Application Default Credentials (ADC)**. Instead of managing long-lived API keys, the application uses the identity of the Service Account attached to the Cloud Run instance to authorize requests.

## 1. Service Account Configuration

The infrastructure is managed via Terraform. A specific Service Account is created for the backend engine.

*   **File**: `src/IAC/02-sa_and_iam.tf`
*   **Service Account ID**: `sa-${var.project_number}-back-engine`
*   **Display Name**: Service Account for the backend engine in Cloud Run

### IAM Roles

To allow the backend to access Vertex AI and other services, specific IAM roles are granted to this Service Account:

*   **`roles/aiplatform.user`**: **Crucial for Vertex AI.** Grants permission to use Vertex AI resources (Generative AI, Embeddings, etc.).
*   `roles/speech.admin`: For Speech-to-Text services.
*   `roles/secretmanager.secretAccessor`: To access secrets (DB credentials, API keys).
*   `roles/bigquery.dataViewer` / `roles/bigquery.dataOwner`: For BigQuery access.
*   `roles/pubsub.publisher`: To publish messages to Pub/Sub.

```hcl
# src/IAC/02-sa_and_iam.tf

resource "google_project_iam_member" "service_account_backend_role" {
  # ...
  for_each = toset([
    "roles/aiplatform.user", # Grants access to Vertex AI
    # ... other roles
  ])
  member  = "serviceAccount:${google_service_account.service_account_backend.email}"
}
```

## 2. Cloud Run Deployment

When the backend container is deployed to Cloud Run, it is explicitly configured to run as the Service Account created above.

*   **File**: `src/Backend/cloudbuild.yaml`

The `gcloud run deploy` command includes the `--service-account` flag:

```yaml
# src/Backend/cloudbuild.yaml

- name: "gcr.io/google.com/cloudsdktool/cloud-sdk"
  entrypoint: gcloud
  args:
    [
      "run",
      "deploy",
      "backend",
      # ...
      "--service-account",
      "sa-$PROJECT_NUMBER-back-engine@$PROJECT_ID.iam.gserviceaccount.com",
      # ...
    ]
```

This ensures that the Cloud Run instance has the identity and permissions of that Service Account.

## 3. Backend Implementation (Vertex AI)

The Python backend uses the Google Cloud Client Libraries, which automatically detect the environment credentials (ADC).

*   **File**: `src/Backend/src/api/adapters/google/generative_ai.py`

### Initialization

The code initializes Vertex AI without providing explicit credentials files. It relies on the environment to provide them.

```python
import vertexai
from vertexai.generative_models import GenerativeModel

# ...

def __init__(self, project_id: str, location: str = "us-central1", ...):
    # Initializes the SDK. ADC is used automatically.
    vertexai.init(project=project_id, location=location)
    self.model = GenerativeModel("gemini-2.0-flash-exp")
```

### Embeddings

For embeddings, the code explicitly fetches the default credentials to pass to the `GoogleVertexEmbeddingFunction`, although `vertexai.init` handles most cases globally.

```python
import google.auth
from chromadb.utils import embedding_functions

# ...

# Fetch default credentials (from the Service Account when in Cloud Run)
credentials, _ = google.auth.default()

self.embedding_function = (
    embedding_functions.GoogleVertexEmbeddingFunction(
        api_key="",  # Empty string - uses default credentials
        project_id=project_id,
        region=location,
        model_name=self.embedding_model,
    )
)
```

## Summary of Flow

1.  **Terraform** creates the Service Account `sa-...-back-engine` and assigns `roles/aiplatform.user`.
2.  **Cloud Build** deploys the Backend to Cloud Run, attaching this Service Account.
3.  **Cloud Run** injects the Service Account credentials into the container environment.
4.  **Backend Code** (`vertexai.init`) detects these credentials (ADC) and authenticates requests to Vertex AI automatically.
