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

## Enable APIs ##

resource "google_project_service" "project" {
  project = var.project_id
  for_each = toset([ "iam.googleapis.com","storage.googleapis.com","speech.googleapis.com","compute.googleapis.com","secretmanager.googleapis.com","servicenetworking.googleapis.com","sqladmin.googleapis.com","cloudbuild.googleapis.com","artifactregistry.googleapis.com","run.googleapis.com","run.googleapis.com","vpcaccess.googleapis.com","firebase.googleapis.com","cloudbilling.googleapis.com","cloudresourcemanager.googleapis.com","serviceusage.googleapis.com","identitytoolkit.googleapis.com","pubsub.googleapis.com"])
  service = each.key

  timeouts {
    create = "30m"
    update = "40m"
  }

  disable_dependent_services = true
}