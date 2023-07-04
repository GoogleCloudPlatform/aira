
## Creating GCS Bucket ##

resource "google_storage_bucket" "bucket_audio" {
  name          = "${var.project_id}-store-audio"
  location      = "US-EAST1"
  force_destroy = true
  project = var.project_id
  public_access_prevention = "enforced"
  storage_class = "STANDARD"
  depends_on = [
    google_project_service.project
  ]
  cors {
    origin          = [var.frontend_url]  
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 3600
  }
}

## Giving permission for backend SA in GCS ##
resource "google_storage_bucket_iam_binding" "backend_objectAdmin" {
  bucket = google_storage_bucket.bucket_audio.name
  role = "roles/storage.objectAdmin"
  members = [
    "serviceAccount:${google_service_account.service_account_backend.email}",
    "serviceAccount:${google_service_account.service_account_gcs.email}",
  ]
}

