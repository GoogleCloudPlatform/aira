This is a [python](https://www.python.org/) backend service with [PostgreSQL](https://www.postgresql.org/) as database.


## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `pages/index.tsx`. The page auto-updates as you edit the file.

## Docker

For ```Docker``` deploy:

### Dockerfile

````
docker build -t stt:0.0.1 --no-cache .
````
````
docker run -p 3000:3000 --env-file=.env -t stt:0.0.1
````

* ```docker cli``` is necessary to run a docker.
