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

// Create a Pub/Sub topic for processor_queue.

resource "google_pubsub_topic" "processor_queue" {
  project = var.project_id
  name     = "processor_queue_topic"
  provider = google-beta
  depends_on = [
    google_project_service.project
  ]
}

resource "google_pubsub_subscription" "processor_queue" {
  name  = "processor_queue_subs"
  project = var.project_id
  topic = google_pubsub_topic.processor_queue.name

  ack_deadline_seconds = 600

  expiration_policy {
    ttl = ""
  }

  push_config {
    push_endpoint = "${var.backend_url}/api/v1/processor/_handle" 

    attributes = {
      x-goog-version = "v1"
    }
  }
}

// Create a Pub/Sub topic for conversion_queue.

resource "google_pubsub_topic" "conversion_queue" {
  project = var.project_id
  name     = "conversion_queue_topic"
  provider = google-beta
  depends_on = [
    google_project_service.project
  ]
}

resource "google_pubsub_subscription" "conversion_queue" {
  name  = "conversion_queue_subs"
  project = var.project_id
  topic = google_pubsub_topic.conversion_queue.name

  ack_deadline_seconds = 600

  expiration_policy {
    ttl = ""
  }
  
  push_config {
    push_endpoint = "${var.backend_url}/api/v1/processor/convert/_handle" 

    attributes = {
      x-goog-version = "v1"
    }
  }
}

