## Creating Repo in Artifact Registry ##

resource "google_artifact_registry_repository" "app-stt" {
  project = var.project_id  
  location      = "us-east1"
  repository_id = "app-stt"
  description   = "Docker repository from app-stt"
  format        = "DOCKER"
  depends_on = [
    google_project_service.project
  ]
}

