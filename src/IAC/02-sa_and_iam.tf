
## Creating the Service Accounts ##

resource "google_service_account" "service_account_backend" {
  account_id   = "${var.project_id}-backend-engine"
  display_name = "Service Account for the backend engine in Cloud Run"
  project = var.project_id
  depends_on = [
    google_project_service.project
  ]
}

resource "google_service_account" "service_account_frontend" {
  account_id   = "${var.project_id}-frontend-engine"
  display_name = "Service Account for the frontend engine in Cloud Run"
  project = var.project_id
  depends_on = [
    google_project_service.project
  ]
}


resource "google_service_account" "service_account_gcs" {
  account_id   = "${var.project_id}-backend-gcs"
  display_name = "Service Account for backend call GCS"
  project = var.project_id
  depends_on = [
    google_project_service.project
  ]
}


resource "google_service_account_key" "service_account_gcs" {
  service_account_id = google_service_account.service_account_gcs.name
  public_key_type    = "TYPE_X509_PEM_FILE"
}


resource "google_service_account" "service_account_looker" {
  account_id   = "${var.project_id}-looker"
  display_name = "Service Account for looker conection"
  project = var.project_id
  depends_on = [
    google_project_service.project
  ]
}



## Giving IAM Roles for the Service Accounts ##

resource "google_project_iam_member" "service_account_backend_role" {
  project = var.project_id
  provider = google-beta
  for_each = toset(["roles/speech.admin","roles/secretmanager.secretAccessor","roles/firebaseauth.admin","roles/iam.serviceAccountTokenCreator","roles/bigquery.dataViewer","roles/bigquery.dataOwner","roles/pubsub.publisher","roles/cloudtrace.agent"])
  role    = each.key
  member  = "serviceAccount:${google_service_account.service_account_backend.email}"
}


resource "google_project_iam_member" "service_account_cloud_build" {
  project = var.project_id
  provider = google-beta
  for_each = toset(["roles/run.admin","roles/secretmanager.secretAccessor","roles/iam.serviceAccountUser"])
  role    = each.key
  member  = "serviceAccount:${var.project_number}@cloudbuild.gserviceaccount.com"
  depends_on = [
    google_project_service.project
  ]
}


resource "google_project_iam_member" "service_account_frontend_role" {
  project = var.project_id
  provider = google-beta
  for_each = toset(["roles/secretmanager.secretAccessor"])
  role    = each.key
  member  = "serviceAccount:${google_service_account.service_account_frontend.email}"
}

resource "google_project_iam_member" "service_account_gcs" {
  project = var.project_id
  provider = google-beta
  for_each = toset(["roles/iam.serviceAccountTokenCreator"])
  role    = each.key
  member  = "serviceAccount:${google_service_account.service_account_gcs.email}"
}


resource "google_project_iam_member" "service_account_looker" {
  project = var.project_id
  provider = google-beta
  for_each = toset(["roles/bigquery.jobUser","roles/bigquery.dataViewer"])
  role    = each.key
  member  = "serviceAccount:${google_service_account.service_account_looker.email}"
}
