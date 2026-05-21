# Copyright 2022 Google LLC (Updated 2025)
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

## FIREBASE & IDENTITY PLATFORM (AUTH) ##

# Adds the Firebase capability to the Google Cloud project.
resource "google_firebase_project" "default" {
  provider = google-beta
  project  = var.project_id
  # This depends_on is useful if google_project_service.project enables firebase.googleapis.com
  depends_on = [
    google_project_service.project
  ]
}

# Configures Google Cloud Identity Platform (the backend for Firebase Auth).
# This single resource now manages all auth settings.
resource "google_identity_platform_config" "default" {
  provider = google-beta
  project  = var.project_id

  autodelete_anonymous_users = true
  authorized_domains = [
        "localhost",
        "${var.project_id}.firebaseapp.com",
        "${var.project_id}.web.app",
        replace(replace(var.frontend_url, "https://", ""), "http://", ""),
      ]
  sign_in {
    allow_duplicate_emails = false
    anonymous {
      enabled = false
    }
    email {
      enabled           = true
      password_required = true
    }
  }

  # This depends_on is useful if google_project_service.project enables identitytoolkit.googleapis.com
  depends_on = [
    google_project_service.project
  ]
}

## FIREBASE WEB APP ##

# Creates the Firebase Web App within the project.
resource "google_firebase_web_app" "basic" {
  provider        = google-beta
  project         = var.project_id
  display_name    = "Display Name Basic"
  deletion_policy = "DELETE"
  depends_on = [
    google_firebase_project.default
  ]
}

# Fetches the configuration details (like API keys) for the web app.
data "google_firebase_web_app_config" "basic" {
  provider   = google-beta
  project    = var.project_id
  web_app_id = google_firebase_web_app.basic.app_id

  # Terraform knows this data source depends on the web_app resource
  # because we are using its app_id attribute.
}

## STORAGE FOR WEB APP CONFIG ##

# Creates a Google Cloud Storage bucket to hold the config file.
resource "google_storage_bucket" "default" {
  provider = google-beta
  project  = var.project_id
  name     = "${var.project_id}-fb-webapp"
  location = "US"
  uniform_bucket_level_access = true
  
  # This depends_on is useful if google_project_service.project enables storage.googleapis.com
  depends_on = [
    google_project_service.project
  ]
}

# Creates the firebase-config.json object in the bucket.
resource "google_storage_bucket_object" "default" {
  provider = google-beta
  bucket   = google_storage_bucket.default.name
  name     = "firebase-config.json"

  content = jsonencode({
    appId             = google_firebase_web_app.basic.app_id
    apiKey            = data.google_firebase_web_app_config.basic.api_key
    authDomain        = data.google_firebase_web_app_config.basic.auth_domain
    databaseURL       = lookup(data.google_firebase_web_app_config.basic, "database_url", "")
    storageBucket     = data.google_firebase_web_app_config.basic.storage_bucket
    messagingSenderId = lookup(data.google_firebase_web_app_config.basic, "messaging_sender_id", "")
    measurementId     = lookup(data.google_firebase_web_app_config.basic, "measurement_id", "")
  })
}