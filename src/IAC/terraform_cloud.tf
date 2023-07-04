
terraform {
 backend "gcs" {
   bucket  = "BUCKET-NAME" # <-- Add the bucket name here
   prefix  = "terraform/state"
 }
}