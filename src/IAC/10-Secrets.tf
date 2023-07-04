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

### Declaring SA private Key as secret ###

resource "google_secret_manager_secret" "gcs_sa_key" {
  secret_id = "gcs_sa_key"
  project = var.project_id
  replication {
    user_managed {
      replicas {
        location = "us-east1"
      }
    }
  }
  depends_on = [
    google_project_service.project
  ]
}

resource "google_secret_manager_secret_version" "gcs_sa_key" {
  secret = google_secret_manager_secret.gcs_sa_key.name
  secret_data = base64decode(google_service_account_key.service_account_gcs.private_key)
}



### Declaring GCS Name as secret ###

resource "google_secret_manager_secret" "bucket" {
  secret_id = "bucket_name"
  project = var.project_id
  replication {
    user_managed {
      replicas {
        location = "us-east1"
      }
    }
  }
  depends_on = [
    google_project_service.project
  ]
}

resource "google_secret_manager_secret_version" "bucket" {
  secret = google_secret_manager_secret.bucket.name
  secret_data = google_storage_bucket.bucket_audio.name
}


#Secret processor_queue Topic Name#
resource "google_secret_manager_secret" "processor_queue" {
  secret_id = "processor_queue"
  project = var.project_id
  replication {
    user_managed {
      replicas {
        location = "us-east1"
      }
    }
  }
  depends_on = [
    google_project_service.project
  ]
}

resource "google_secret_manager_secret_version" "processor_queue" {
  secret = google_secret_manager_secret.processor_queue.name
  secret_data = google_pubsub_topic.processor_queue.name
}



#Secret conversion_queue Topic Name#
resource "google_secret_manager_secret" "conversion_queue" {
  secret_id = "conversion_queue"
  project = var.project_id
  replication {
    user_managed {
      replicas {
        location = "us-east1"
      }
    }
  }
  depends_on = [
    google_project_service.project
  ]
}

resource "google_secret_manager_secret_version" "conversion_queue" {
  secret = google_secret_manager_secret.conversion_queue.name
  secret_data = google_pubsub_topic.conversion_queue.name
}


### Declaring SQL url as Secret###

resource "google_secret_manager_secret" "sqlurl" {
  secret_id = "sql_connection_url"
  project = var.project_id
  replication {
    user_managed {
      replicas {
        location = "us-east1"
      }
    }
  }
  depends_on = [
    google_project_service.project
  ]
}

resource "google_secret_manager_secret_version" "sqlurl" {
  secret = google_secret_manager_secret.sqlurl.name
  secret_data = "postgresql+asyncpg://${google_sql_user.users.name}:${random_password.password.result}@${google_sql_database_instance.instance.private_ip_address}/${google_sql_database.database.name}"
}

### Declaring Firebase parameters as Secrets ###

# appId Secret #
resource "google_secret_manager_secret" "appId" {
  secret_id = "appId"
  project = var.project_id
  replication {
    user_managed {
      replicas {
        location = "us-east1"
      }
    }
  }
  depends_on = [
    google_project_service.project
  ]
}

resource "google_secret_manager_secret_version" "mykey_appId" {
  secret = google_secret_manager_secret.appId.name
  secret_data = google_firebase_web_app.basic.app_id
}

# apiKey Secret #
resource "google_secret_manager_secret" "apiKey" {
  secret_id = "apiKey"
  project = var.project_id
  replication {
    user_managed {
      replicas {
        location = "us-east1"
      }
    }
  }
  depends_on = [
    google_project_service.project
  ]
}

resource "google_secret_manager_secret_version" "mykey_apiKey" {
  secret = google_secret_manager_secret.apiKey.name
  secret_data = data.google_firebase_web_app_config.basic.api_key
}


# authDomain Secret #
resource "google_secret_manager_secret" "authDomain" {
  secret_id = "authDomain"
  project = var.project_id
  replication {
    user_managed {
      replicas {
        location = "us-east1"
      }
    }
  }
  depends_on = [
    google_project_service.project
  ]
}

resource "google_secret_manager_secret_version" "mykey_authDomain" {
  secret = google_secret_manager_secret.authDomain.name
  secret_data = data.google_firebase_web_app_config.basic.auth_domain
}


### Creating public and private key ###

resource "tls_private_key" "mykey" {
  algorithm = "RSA"
  rsa_bits = 2048
}

data "tls_public_key" "mykey_public" {
  private_key_pem = tls_private_key.mykey.private_key_pem
}

output "private_key" {
  value = tls_private_key.mykey.private_key_pem
  sensitive = true
}

output "public_key" {
  value = data.tls_public_key.mykey_public.public_key_pem
}


### Declaring Private and Public Key as Secret ###
#Private Key#
resource "google_secret_manager_secret" "private_key" {
  secret_id = "private-key"
  project = var.project_id
  replication {
    user_managed {
      replicas {
        location = "us-east1"
      }
    }
  }
  depends_on = [
    google_project_service.project
  ]
}

resource "google_secret_manager_secret_version" "mykey_private" {
  secret = google_secret_manager_secret.private_key.name
  secret_data = tls_private_key.mykey.private_key_pem
}

output "private_key_secret" {
  value = google_secret_manager_secret_version.mykey_private.name
}

#Public Key#
resource "google_secret_manager_secret" "public_key" {
  secret_id = "public-key"
  project = var.project_id
  replication {
    user_managed {
      replicas {
        location = "us-east1"
      }
    }
  }
  depends_on = [
    google_project_service.project
  ]
}

resource "google_secret_manager_secret_version" "mykey_public" {
  secret = google_secret_manager_secret.public_key.name
  secret_data = data.tls_public_key.mykey_public.public_key_pem
}

output "public_key_secret" {
  value = google_secret_manager_secret_version.mykey_public.name
}



### Declaring BQ Dataset and table Name as Secret ###

resource "google_secret_manager_secret" "dataset" {
  secret_id = "dataset_name"
  project = var.project_id
  replication {
    user_managed {
      replicas {
        location = "us-east1"
      }
    }
  }
  depends_on = [
    google_project_service.project
  ]
}

resource "google_secret_manager_secret_version" "dataset" {
  secret = google_secret_manager_secret.dataset.name
  secret_data = google_bigquery_dataset.dataset.dataset_id
  }

resource "google_secret_manager_secret" "table" {
  secret_id = "table_name"
  project = var.project_id
  replication {
    user_managed {
      replicas {
        location = "us-east1"
      }
    }
  }
  depends_on = [
    google_project_service.project
  ]
}

resource "google_secret_manager_secret_version" "table" {
  secret = google_secret_manager_secret.table.name
  secret_data = google_bigquery_table.resultados_alunos.table_id
  }


### Declaring the api URL from backend as Secret ###


resource "google_secret_manager_secret" "api_url" {
  secret_id = "api_url"
  project = var.project_id
  replication {
    user_managed {
      replicas {
        location = "us-east1"
      }
    }
  }
  depends_on = [
    google_project_service.project
  ]
}

resource "google_secret_manager_secret_version" "api_url" {
  secret = google_secret_manager_secret.api_url.name
  secret_data = "${var.backend_url}/api/v1/" 
  }

  resource "google_secret_manager_secret" "front_url" {
  secret_id = "front_url"
  project = var.project_id
  replication {
    user_managed {
      replicas {
        location = "us-east1"
      }
    }
  }
  depends_on = [
    google_project_service.project
  ]
}

resource "google_secret_manager_secret_version" "front_url" {
  secret = google_secret_manager_secret.front_url.name
  secret_data = var.frontend_url
  }