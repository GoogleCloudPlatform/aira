
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
