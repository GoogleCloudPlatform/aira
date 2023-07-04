
## Creating Network ##

resource "google_compute_network" "private_network" {
  provider = google-beta
  project = var.project_id
  name = "private-network"
  auto_create_subnetworks = false
  depends_on = [
    google_project_service.project
  ]
}

resource "google_compute_subnetwork" "network" {
  name          = "us-east1-subnetwork"
  project = var.project_id
  ip_cidr_range = "10.2.0.0/16"
  region        = "us-east1"
  network       = google_compute_network.private_network.id
}

resource "google_compute_subnetwork" "subnet_serverless" {
  name          = "us-east1-serverless"
  project = var.project_id
  ip_cidr_range = "10.3.0.0/28"
  region        = "us-east1"
  network       = google_compute_network.private_network.id
}

resource "google_vpc_access_connector" "connector" {
  name          = "vpc-con"
  project = var.project_id
  region        = "us-east1"
  subnet {
    name = google_compute_subnetwork.subnet_serverless.name
  }
  machine_type = "e2-micro"
  min_instances = "2"
  max_instances = "3"
}


resource "google_compute_global_address" "private_ip_address" {
  provider = google-beta
  project = var.project_id
  name          = "private-ip-address"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.private_network.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  provider = google-beta
  network                 = google_compute_network.private_network.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}