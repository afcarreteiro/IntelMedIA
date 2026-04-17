# RunPod Image via GitHub Actions

## Goal
Build the `runpod` image in GitHub Actions, push it to Docker Hub, and use that image in RunPod.

## 1. Create the Docker Hub repository
Create a Docker Hub repo:

`afcarreteiro/intelmedai-runpod-asr`

## 2. Add Docker Hub credentials to GitHub
In GitHub, open:

`Settings -> Secrets and variables -> Actions`

Add these repository secrets:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

Use a Docker Hub access token, not your password.

## 3. Create the GitHub Actions workflow
Create this file:

`.github/workflows/runpod-image.yml`

Use this content:

```yaml
name: Build and Push RunPod Image

on:
  push:
    branches: [main]
    paths:
      - "runpod/**"
      - ".github/workflows/runpod-image.yml"
  workflow_dispatch:

jobs:
  docker:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: ./runpod
          file: ./runpod/Dockerfile
          push: true
          tags: |
            afcarreteiro/intelmedai-runpod-asr:latest
            afcarreteiro/intelmedai-runpod-asr:${{ github.sha }}
```

## 4. Commit and push
Commit:

- `runpod/Dockerfile`
- `runpod/asr_qwen3_ws.py`
- `runpod/requirements.txt`
- `.github/workflows/runpod-image.yml`

Then push to `main`.

## 5. Confirm the image was published
In GitHub Actions, confirm the workflow passed.

In Docker Hub, confirm these tags exist:

- `latest`
- the commit SHA

## 6. Use the image in RunPod
In RunPod, set the container image to:

`afcarreteiro/intelmedai-runpod-asr:latest`

For safer deployments, use the SHA tag instead.

## 7. Set RunPod environment variables
Configure the env vars RunPod needs, such as:

- `ASR_MODEL_ID`
- `ASR_API_KEY` if enabled
- any overrides for the defaults in `runpod/Dockerfile`

## 8. Deploy and test
After RunPod starts, test:

- `GET /healthz`
- `GET /readyz`
- websocket: `/ws/transcribe`

## Notes
- GitHub Actions still builds a Docker image; it just does it in GitHub instead of on your machine.
- Using Docker Hub keeps RunPod deployment simple and repeatable.
