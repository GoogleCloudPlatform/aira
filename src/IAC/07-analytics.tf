
## Create Dataset and BQ Table ##


resource "google_bigquery_dataset" "dataset" {
  project = var.project_id 
  dataset_id                  = "dataset_lia"
  friendly_name               = "LIA Dataset"
  description                 = "Dataset with the main table with the students results"
  location                    = "southamerica-east1"
  depends_on = [
    google_project_service.project
  ]
}

resource "google_bigquery_table" "resultados_alunos" {
  project = var.project_id 
  dataset_id = google_bigquery_dataset.dataset.dataset_id
  table_id   = "student_results"
  schema = file("${path.module}/bq/schema.json")
  deletion_protection = "false"

}