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

## Creating CloudSQL ##

resource "google_sql_database_instance" "instance" {
  provider = google-beta
  project = var.project_id
  name             = "${var.project_id}-sql-instance"
  region           = "us-east1"
  database_version = "POSTGRES_14"
  deletion_protection = false
  depends_on = [google_service_networking_connection.private_vpc_connection,google_project_service.project]

  settings {
    tier = "db-f1-micro"
    ip_configuration {
      ipv4_enabled                                  = false
      private_network                               = google_compute_network.private_network.id
      enable_private_path_for_google_cloud_services = true
    }
    location_preference {
      zone           = "us-east1-b"
    }
  }
}

resource "google_sql_database" "database" {
  name     = "stt-db"
  instance = google_sql_database_instance.instance.name
  project = var.project_id

}

resource "random_password" "password" {
  length           = 16
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "google_sql_user" "users" {
  name     = "sttuserdb"
  project = var.project_id
  instance = google_sql_database_instance.instance.name
  password = random_password.password.result
}
