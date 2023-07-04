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