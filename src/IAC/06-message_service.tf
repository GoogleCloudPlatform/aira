
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