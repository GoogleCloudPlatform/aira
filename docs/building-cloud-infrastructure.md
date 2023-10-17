# Guide to deploying the Google Cloud Platform (GCP) resources for AIRA
All the resources needed to run the platform are being created through terraform.

## Compatibility

These deployment steps were tested using terraform v1.4.6.

## Software Requirements
- If you follow the steps below using your local machine do you need to have gcloud and Terraform installed on your machine.
- If you choose to follow the steps below using the Cloud Shell from GCP Console all the requirements are installed by default.


## Steps to deploy the infrastructure

Follow the steps below to deploy the Infrastructure requirements for the application.

1. Create a new GCP project and save the project ID and Project Number of this project.
2. Start your Cloud Shell and clone this repository.
3. Inside IAC folder go to the variables.tf file and replace the default value from the variables `project_id` and `project_number` for the values that you saved in the earlier step.
4. You're going to need a place to store your terraform state file, so [create a GCS bucket](https://cloud.google.com/storage/docs/creating-buckets) for this. You can use the name that you prefer.
5. Next, go to the `backend.tf` file and update the bucket value using the bucket name you choose.
6. Inside the `IAC` folder, run the commands bellow:
```bash
terraform init
```
```bash
terraform plan
```
```bash
terraform apply
```

It will take several minutes some time for all the resources to be created. It might be a good time for a coffee.