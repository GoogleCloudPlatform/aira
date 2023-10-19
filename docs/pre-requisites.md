# Pre-requisites

If you want to evolve or customize the application code, you need some basic components to build and run the application. Below is the list of these components:

* ```Install python >= 3.11``` is necessary for the backend service.
* ```Install node >= 16.16.0 and pnpm >= 8.6.6``` is necessary for the frontend service.
* ```Install the gcloud sdk``` if you want to do operations in GCP using your local terminal.
* ```Install docker ``` is required to build the container images and host locally.
* ```Install terraform >= v1.4.6.``` if you want to execute the step [building-cloud-infrastructure](./building-cloud-infrastructure.md) using your local terminal.

## About Backend and Frontend 
Both the frontend and backend use Docker and all necessary requirements are declared in the Dockerfile files for each component. The requirements present here regarding the frontend and backend are necessary for local execution without building and using Docker. That is, if you want to develop and test locally using Docker, all the necessary requirements will already be installed when the applications are built.

## About terraform and gcloud sdk
Instead of running terraform using your local terminal, a good option is to use [Cloud Shell](https://cloud.google.com/shell) on GCP. In the Cloud Shell environment, you will already be authenticated and the terraform and gcloud SDK requirements are already installed, thus avoiding the need to install these two requirements locally to perform the step [building-cloud-infrastructure](./building-cloud-infrastructure.md).