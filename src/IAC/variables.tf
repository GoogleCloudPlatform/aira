
variable "project_id" {
  description = "The project ID"
  type        = string
  default = "PROJECT_ID"
}

variable "project_number" {
  description = "The project number"
  type        = string
  default = "PROJECT_NUMBER"
}



### The variables below need to be changed after uploading Frontend and Backend in Cloud Run. ###

variable "backend_url" {
  type = string
  default = "https://backend_url"
}

variable "frontend_url" {
  type = string
  default = "https://frontend_url"
}