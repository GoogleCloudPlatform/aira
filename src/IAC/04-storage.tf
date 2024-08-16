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



## Creating GCS Bucket to store audios ##

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

  cors {
    origin          = [var.dev_local_url]  
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 3600
  }

  cors {
    origin          = [var.localhost_url]  
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



## Creating GCS Bucket to store public file##


resource "google_storage_bucket" "bucket_files" {
  name          = "${var.project_id}-store-public-files"
  location      = "US-EAST1"
  force_destroy = true
  project = var.project_id
  public_access_prevention = "inherited"
  storage_class = "STANDARD"
  uniform_bucket_level_access = false

}

