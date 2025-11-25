terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.20.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = ">= 5.20.0"
    }
  }
}

provider "google" {
  # This is the default provider for GA resources
  project = var.project_id
  region  = var.region
  # Add these lines to solve the quota project issue
  user_project_override = true
  billing_project       = var.project_id
}

provider "google-beta" {
  # This provider is ONLY used for resources that specify it by its alias
  alias   = "beta"
  project = var.project_id
  region  = var.region
  
  # Add these lines to solve the quota project issue
  user_project_override = true
  billing_project       = var.project_id
}