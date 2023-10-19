This is a [python](https://www.python.org/) backend service with [PostgreSQL](https://www.postgresql.org/) as database.


## Getting Started

Run the app locally:

```bash
poetry install
poetry run uvicorn --host=0.0.0.0 --port 8080 --reload --reload-dir=src main:app
```

## Docker

For ```Docker``` deploy:

### Dockerfile

````
docker build -t backend:0.0.1 --no-cache .
````
````
docker run -p 8080:8080 --env-file=.env -t backend:0.0.1
````

* ```docker cli``` is necessary to run a docker.
