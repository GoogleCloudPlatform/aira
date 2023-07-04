# Guide to deploying the Google Cloud Platform (GCP) resources for LIA.
All the resources needed to run the platform are being created through terraform.

## Compatibility

These deployment steps were tested using terraform v1.4.6.

## Software Requirements
- If you follow the steps below using your local machine do you need to have gcloud and Terraform installed on your machine.
- If you choose to follow the steps below using the Cloud Shell from GCP Console all the requirements are installed by default.


## Steps to deploy the application

Follow the steps below to deploy the Infrastructure requirements for the application.

1. Create a new GCP project and save the project ID and Project Number of this project.
2. Start your Cloud Shell and clone this repository.
3. Inside IAC folder go to the variables.tf file and replace the default value from the variables project_id and project_number for the values that you saved in the earlier step.
4. Do you need a place to store your terraform state file, so create a GCS bucket for this and you can use the name that you prefer. After this go to the backend.tf file and update the bucket value using the bucket name you choose.
5. Inside the IAC folder, run the commands bellow:
```bash
terraform init
```
```bash
terraform plan
```
```bash
terraform apply
```

It will take some time for all the resources to be created, last time it was tested it took approximately 27 minutes.

6. To build de container image and deploy the Cloud Run service for the backend environment, go to the folder X and run the command bellow on Cloud Shell:
```bash
gcloud builds submit --config cloudbuild.yaml . --substitutions=SHORT_SHA=00001
```

Go to the Cloud Run console inside the GCP platform, select the backend service and copy the service URL. Do you need to replace the default value from the variable backend_url inside variable.tf for this URL that you copy.

7. To build de container image and deploy the Cloud Run service for the frontend environment, go to the folder X and run the command bellow on Cloud Shell:
 ```bash
gcloud builds submit --config cloudbuild.yaml . --substitutions=SHORT_SHA=00001
```

Go to the Cloud Run console inside the GCP platform, select the frontend service and copy the service URL. Do you need to replace the default value from the variable frontend_url inside variable.tf for this URL that you copy.

8. Now that we have both URLs go back to the IAC folder and re-run the commands bellow:
```bash
terraform plan
```
```bash
terraform apply
```