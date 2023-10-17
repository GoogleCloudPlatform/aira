# Guide to deploying the Google Cloud Platform (GCP) resources for AIRA

AIRA's infraestructure gets deployed by leveraging the approach of Infrastructure as a Code (IaC). For that, we rely on Terraform.

## Compatibility

The deployment steps described here were tested using Terraform v1.4.6.

## Software Requirements

- If you follow the steps below using your local machine, you're going to need to have both `gcloud` and Terraform installed on your machine.
- If you choose to follow the steps below using the Cloud Shell from GCP Console all the requirements are installed by default.

Please, make sure you comply with all the [pre-requisites](./pre-requisites.md) before moving on with this process.

## Steps to deploy the infrastructure

Follow the steps below to deploy the Infrastructure requirements for the application.

1. [Create a new GCP project](https://developers.google.com/workspace/guides/create-project) and save the `project ID` and `Project Number` of this project.
2. [Start your Cloud Shell](https://cloud.google.com/shell/docs/using-cloud-shell#:~:text=Cloud%20Shell%20session.-,Start%20a%20new%20session,the%20session%20to%20be%20initialized.) and clone this repository.
3. Inside IAC folder go to the `variables.tf` file and replace the default value from the variables `project_id` and `project_number` by the values that you saved in step 1.
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

It will take several minutes for all the resources to be created. It might be a good time for a cup of coffee.