## About Looker requirements
As we are using Looker embedded, both applications (frontend and backend) do require some information from Looker, the same way Looker also require some information from our application to allow the requests from the web app to properly happen.

### Frontend

The frontend application requires 3 variables from Looker. They are:

* ```LOOKER``` is your Looker URL, each Looker instance has a specific URL and you should add yours as the value of this variable.
* ```LOOKER_GENERAL_DASHBOARD_ID``` is the ID of the dashboard which you want to embeed within the app. Each dashboard you create in Looker has a specific ID. The dashboard ID that you add here will appears on the General dashboard page.
* ```LOOKER_LEARNERS_DASHBOARD_ID``` if you wish the ID of your dashboard that you want to embeed within the app, each dashboard you create in Looker has a specific ID, the dashboard id that you add here will appears on the Learners dashboard page.

You can change the values ​​of these variables in the ```.env.example``` file in the /src/Frontend/ directory to test locally and don't forget to make the change directly in the /src/Frontend/cloudbuild.yaml file before deploying the app.


### Backend

The backend  application requires 2 variables from Looker. They are:

* ```_LOOKER_HOST``` is your looker URL, each looker instance has a specific URL add yours as the value of this variable.
* ```_LOOKER_SECRET``` is the Embed secret, and is used to ensure that embed SSO requests are valid. Only people with this embed secret will be able to generate valid SSO request URIs. To generate this key you can follow the step Generating Looker's secret key on this [documentation](https://developers.looker.com/embed/getting-started/sso/#:~:text=Generating%20Looker's%20secret%20key&text=Go%20to%20the%20Embed%20page,to%20generate%20your%20embed%20secret.).


You can change the values ​​of these variables in the .env.example file in the /src/Backend/ directory to test locally and don't forget to make the change directly in the /src/Backend/cloudbuild.yaml file before deploying the app.

### Looker Configuration

To enable message passing and event notification from the embedded Looker iframe to the parent web page, you must include embed_domain=https://parent_domain.com as a query parameter in your SSO embed URL, AND you must add that same domain https://parent_domain.com to this allowlist to tell the Looker server that the domain is allowed as a cross-domain message destination.

In the looker console, go to Admin > Embed. The first option will be Embedded Domain Allowlist where you need to add your frontend URL to allow the frontend to call the looker service.
