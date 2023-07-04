# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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