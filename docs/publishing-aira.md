# Publishing AIRA

At this point, you should be done with both [pre-requisites](./pre-requisites.md) and the [deployment of the infrastructure](./building-cloud-infrastructure.md) for the application.

Now, it is time to publish the application into Google Cloud. To do that, please, follow the steps below.

1. To build the container image and deploy it to [Cloud Run](https://cloud.google.com/run/) service, for the backend environment, go to the folder `Backend` and run the command bellow on Cloud Shell:

```bash
gcloud builds submit --config cloudbuild.yaml .
```

Next, in Cloud Run console inside the GCP, select the backend service and copy the service URL. You will need to replace the default value from the variable `backend_url` inside the file `variable.tf` on IAC folder by the one you just copied.

2. To build de container image and deploy the Cloud Run service for the frontend environment, go to the folder `Frontend` and run the command bellow on Cloud Shell:

 ```bash
gcloud builds submit --config cloudbuild.yaml .
```

Next, in Cloud Run console inside the GCP, select the frontend service and copy the service URL. You will need to replace the default value from the variable `frontend_url` inside the file `variable.tf` on IAC folder by the one you just copied.

3. Now that we have both URLs go back to the IAC folder and re-run the commands bellow:

```bash
terraform plan
```

```bash
terraform apply
```

4. After the execution of the command above, you will need to redeploy the backend and frontend service so run the commands bellow on frontend and backend folders:

 ```bash
gcloud builds submit --config cloudbuild.yaml .
```