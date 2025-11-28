terraform {
  backend "gcs" {
    bucket = "update-bucket-name"
    prefix = "terraform/state"
  }
}