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