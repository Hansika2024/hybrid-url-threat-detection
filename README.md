# Hybrid URL Threat Detection — DevOps CI/CD Pipeline

A DevOps-focused CI/CD setup for a **FastAPI-based machine learning application** that detects different types of malicious or suspicious URLs.

The machine learning application existed first. This project extends it with a complete delivery workflow using **Docker, Jenkins, Kubernetes, automated testing, Trivy security scanning, container health checks, and deployment verification**.

The primary goal of this project is to demonstrate how an ML inference API can be packaged, tested, scanned, deployed, and verified using a CI/CD pipeline.

---

## Project Overview

The application exposes a FastAPI service that performs URL threat classification.

The DevOps workflow is:

```text
Developer
    │
    │ git push
    ▼
 GitHub
    │
    ▼
 Jenkins
    │
    ├── Checkout
    │
    ├── Docker Build
    │
    ├── Automated Tests
    │
    ├── Trivy Security Scan
    │
    ├── Container Health Check
    │
    └── Kubernetes Deployment
             │
             ▼
      Docker Desktop
        Kubernetes
             │
             ▼
        Deployment
             │
             ▼
           Pod
             │
             ▼
          Service
             │
             ▼
        FastAPI API
             │
             ▼
      /health and /docs
```

---

# Architecture

```text
                         ┌──────────────────┐
                         │     Developer    │
                         └────────┬─────────┘
                                  │
                              git push
                                  │
                                  ▼
                         ┌──────────────────┐
                         │      GitHub      │
                         │    Repository    │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │      Jenkins     │
                         │   Jenkinsfile    │
                         └────────┬─────────┘
                                  │
                ┌─────────────────┼─────────────────┐
                │                 │                 │
                ▼                 ▼                 ▼
         Docker Build          Tests         Trivy Scan
                │                 │                 │
                └─────────────────┼─────────────────┘
                                  │
                                  ▼
                       Container Health Check
                                  │
                                  ▼
                       Kubernetes Deployment
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │  Docker Desktop K8s     │
                    │                         │
                    │  Deployment             │
                    │       │                 │
                    │       ▼                 │
                    │      Pod                │
                    │       │                 │
                    │       ▼                 │
                    │    Service              │
                    │       │                 │
                    │       ▼                 │
                    │    FastAPI              │
                    └─────────────────────────┘
```

---

# Tech Stack

| Area              | Technology                   |
| ----------------- | ---------------------------- |
| Programming       | Python                       |
| API               | FastAPI                      |
| ML Inference      | ONNX Runtime                 |
| Source Control    | Git, GitHub                  |
| Containerization  | Docker                       |
| CI/CD             | Jenkins                      |
| Pipeline          | Jenkins Declarative Pipeline |
| Orchestration     | Kubernetes                   |
| Local Kubernetes  | Docker Desktop Kubernetes    |
| Kubernetes CLI    | kubectl                      |
| Security Scanning | Trivy                        |
| Testing           | Python unittest                       |
| API Documentation | FastAPI Swagger UI           |

---

# Repository Structure

```text
Hybrid-URL-Threat-Detection/
│
├── app/
│   └── FastAPI application and ML inference code
│
├── tests/
│   └── Automated tests
│
├── k8s/
│   ├── deployment.yaml
│   └── service.yaml
│
├── screenshots/
│   └── Application and DevOps screenshots
│
├── training/
│   └── ML training-related files
│
├── Dockerfile
├── Jenkinsfile
├── requirements.txt
├── .dockerignore
├── .gitignore
└── README.md
```

---

# CI/CD Pipeline

The CI/CD pipeline is defined in [`Jenkinsfile`](Jenkinsfile).

The pipeline performs the following stages:

```text
Checkout
   ↓
Docker Build
   ↓
Test
   ↓
Security Scan
   ↓
Run Container + Health Check
   ↓
Deploy to Kubernetes
   ↓
Rollout Verification
```

---

## 1. Checkout

Jenkins checks out the source code from the GitHub repository.

The pipeline is configured as a Jenkins Pipeline job that uses the repository's `Jenkinsfile`.

The source repository is:

**GitHub:** `Hansika2024/hybrid-url-threat-detection`

---

## 2. Docker Build

Jenkins builds the application into a Docker image.

```bash
docker build -t hybrid-url-threat-api:ci .
```

The Docker image contains:

* Python runtime
* FastAPI
* ONNX Runtime
* Required ML dependencies
* Application code
* Model/inference files

The resulting image is used for the following pipeline stages.

---

## 3. Automated Tests

The pipeline runs automated tests against the application.

The current test coverage focuses on basic API functionality, including the health endpoint.

Example:

```bash
python -m unittest discover -s tests -v
```

The purpose of this stage is to detect application-level problems before the image is deployed to Kubernetes.

---

## 4. Security Scan

The Docker image is scanned using **Trivy**.

The scan checks the image for known vulnerabilities in:

* Base operating-system packages
* Python packages
* Other installed dependencies

The current pipeline reports HIGH/CRITICAL findings without failing the build.

This provides visibility into container vulnerabilities while keeping the development pipeline usable.

---

## 5. Run Container and Health Check

After building and testing the image, Jenkins starts a temporary container.

The application exposes:

```text
GET /health
```

Expected response:

```json
{
  "status": "healthy"
}
```

The pipeline waits for the application to become available before continuing.

This is useful for this project because the ML application requires time to initialize its dependencies and inference environment.

The temporary CI container is removed in the Jenkins `post` section after the pipeline completes.

---

## 6. Deploy to Kubernetes

After the previous stages succeed, Jenkins deploys the Kubernetes configuration.

The Kubernetes manifests are stored in:

```text
k8s/
```

They include:

```text
deployment.yaml
service.yaml
```

The deployment is applied using `kubectl`.

---

## 7. Kubernetes Rollout Verification

The pipeline verifies that Kubernetes successfully rolls out the deployment.

Example:

```bash
kubectl rollout status deployment/hybrid-url-threat-api
```

This prevents the CI/CD pipeline from considering the deployment successful simply because Kubernetes accepted the manifest.

The application must actually reach the expected ready state.

---

# Docker Configuration

The application is packaged using the root-level `Dockerfile`.

Build locally:

```bash
docker build -t hybrid-url-threat-api:ci .
```

Run locally:

```bash
docker run -p 8000:8000 hybrid-url-threat-api:ci
```

Then open:

```text
http://localhost:8000/docs
```

Health endpoint:

```text
http://localhost:8000/health
```

---

# Jenkins Configuration

Jenkins itself runs inside a Docker container.

The Jenkins container uses:

```text
jenkins-k8s:latest
```

The custom Jenkins image contains:

* Jenkins
* Docker CLI
* kubectl

The Docker socket is mounted into Jenkins:

```text
/var/run/docker.sock
```

This allows Jenkins to communicate with the Docker Engine running on the host.

Therefore:

```text
Jenkins Container
       │
       │ Docker CLI
       ▼
Docker Engine
       │
       ├── Build image
       ├── Run container
       └── Remove container
```

The custom Jenkins image was created specifically so the pipeline can use both Docker and Kubernetes commands.

---

# Jenkins + Kubernetes Integration

Jenkins also needs access to the local Docker Desktop Kubernetes cluster.

A kubeconfig is mounted into the Jenkins container:

```text
/tmp/jenkins-kubeconfig
```

The Kubernetes connection was verified from inside Jenkins using:

```bash
docker exec \
  -e KUBECONFIG=/tmp/jenkins-kubeconfig \
  jenkins \
  kubectl get nodes
```

Expected output:

```text
NAME                    STATUS   ROLES           VERSION
desktop-control-plane   Ready    control-plane   v1.34.3
```

This confirms:

```text
Jenkins
   │
   │ kubectl
   ▼
Docker Desktop Kubernetes
```

---

# Kubernetes Configuration

The project uses a Docker Desktop Kubernetes cluster for local deployment.

The cluster currently contains one control-plane node.

Check the cluster:

```bash
kubectl get nodes
```

Example:

```text
NAME                    STATUS   ROLES           VERSION
desktop-control-plane   Ready    control-plane   v1.34.3
```

---

## Kubernetes Deployment

The application is deployed using:

```text
k8s/deployment.yaml
```

The Deployment currently uses one replica:

```yaml
replicas: 1
```

The container exposes:

```text
8000
```

The Deployment also defines:

* Readiness probe
* Liveness probe
* `/health` endpoint

---

## Readiness Probe

The readiness probe checks:

```text
/health
```

A pod is considered ready only after the application successfully responds to the health check.

This prevents Kubernetes from sending traffic to a pod that has not finished initializing.

---

## Liveness Probe

The liveness probe also checks:

```text
/health
```

This allows Kubernetes to detect a container that has become unhealthy.

The probe delays are relatively long because the ML application takes time to initialize.

---

# Kubernetes Service

The application is exposed through a Kubernetes Service.

The service configuration is stored in:

```text
k8s/service.yaml
```

The Service maps:

```text
Service type: ClusterIP
Service port: 8000
Target port: 8000
```

Check the Service:

```bash
kubectl get services
```

Check the endpoints:

```bash
kubectl get endpoints
```

The endpoint should point to the application pod on port `8000`.

---

# Accessing the Kubernetes Application

For local development and demonstration, the application can be accessed using `kubectl port-forward`.

The currently working command is:

```powershell
kubectl port-forward svc/hybrid-url-threat-api 8090:8000
```

Keep this terminal open while accessing the application.

Then open:

```text
http://localhost:8090/health
```

Expected response:

```json
{
  "status": "healthy"
}
```

FastAPI Swagger UI:

```text
http://localhost:8090/docs
```

The request flow is:

```text
Browser
   │
   │ localhost:8090
   ▼
kubectl port-forward
   │
   │ Kubernetes Service :8000
   ▼
FastAPI Pod :8000
```

### Note about port 8002

Port `8002` was previously used for port-forwarding.

If another port-forward process is still running, attempting to reuse `8002` results in:

```text
bind: Only one usage of each socket address
```

This is a local port conflict, not a Kubernetes application failure.

A different local port such as `8090` can be used.

---

# Kubernetes Verification Commands

Useful commands for checking the deployment:

### Nodes

```bash
kubectl get nodes
```

### Deployments

```bash
kubectl get deployments
```

### Pods

```bash
kubectl get pods
```

### Services

```bash
kubectl get services
```

### Pod details

```bash
kubectl describe pod <pod-name>
```

### Deployment status

```bash
kubectl rollout status deployment/hybrid-url-threat-api
```

### Deployment history

```bash
kubectl rollout history deployment/hybrid-url-threat-api
```

---

# Kubernetes Troubleshooting Exercise

As part of the project, a deployment failure was intentionally created to practice the Kubernetes troubleshooting workflow.

The Deployment image was changed to an image tag that does not exist.

Example:

```bash
kubectl set image deployment/hybrid-url-threat-api \
  hybrid-url-threat-api=hybrid-url-threat-api:invalid
```

The resulting pod can enter an image-pull failure state such as:

```text
ErrImagePull
```

or:

```text
ImagePullBackOff
```

---

## Investigation

First check the pods:

```bash
kubectl get pods
```

Then inspect the affected pod:

```bash
kubectl describe pod <pod-name>
```

The Events section provides information about the image-pull failure.

The troubleshooting workflow is:

```text
Deployment failure
       ↓
kubectl get pods
       ↓
Identify failing pod
       ↓
kubectl describe pod
       ↓
Inspect Events
       ↓
Identify root cause
       ↓
Rollback/fix deployment
       ↓
Verify rollout
```

---

## Recovery

The deployment can be rolled back to the previous revision:

```bash
kubectl rollout undo deployment/hybrid-url-threat-api
```

Then verify:

```bash
kubectl rollout status deployment/hybrid-url-threat-api
```

Finally:

```bash
kubectl get pods
```

This provides practical experience with:

* Kubernetes rollout history
* Pod failure investigation
* Image-pull errors
* Deployment rollback
* Post-rollback verification

---

# Kubernetes Service Connectivity Test

The Kubernetes Service was also tested from inside the cluster.

A temporary curl pod was created:

```bash
kubectl run curl-test \
  --rm \
  -it \
  --image=curlimages/curl \
  --restart=Never \
  -- curl -s http://hybrid-url-threat-api:8000/health
```

The application returned:

```json
{
  "status": "healthy"
}
```

This verified the internal Kubernetes networking path:

```text
curl-test Pod
     │
     ▼
Kubernetes Service
     │
     ▼
FastAPI Pod
     │
     ▼
/health
```

---

# DevOps Troubleshooting Experience

During implementation, several issues were encountered and resolved.

## Issue 1 — Kubernetes API connection from Jenkins

The Docker Desktop Kubernetes API was initially configured for:

```text
https://127.0.0.1:63227
```

This works from the Windows host but does not represent the same network path from inside the Jenkins container.

The Jenkins kubeconfig was adjusted so Jenkins could reach the Kubernetes API through the Docker host.

The Kubernetes TLS configuration also had to be handled because the API certificate did not contain `host.docker.internal` as a certificate name.

The final Jenkins connectivity was verified using:

```bash
docker exec \
  -e KUBECONFIG=/tmp/jenkins-kubeconfig \
  jenkins \
  kubectl get nodes
```

---

## Issue 2 — kubectl was missing from Jenkins

The initial Jenkins container did not contain `kubectl`.

Running:

```bash
docker exec jenkins kubectl version --client
```

returned:

```text
kubectl: executable file not found
```

A custom Jenkins Docker image was created with kubectl installed.

After rebuilding:

```bash
docker exec jenkins kubectl version --client
```

returned:

```text
Client Version: v1.34.3
```

---

## Issue 3 — Docker CLI was missing from Jenkins

The first pipeline execution failed during the Docker Build stage with:

```text
docker: not found
```

The Jenkins image was rebuilt to include Docker CLI.

Docker was then verified using:

```bash
docker exec jenkins docker --version
```

The Docker client became available inside Jenkins.

The Docker socket was also mounted so the Jenkins container could communicate with the host Docker Engine.

---

## Issue 4 — Kubernetes pod stuck in ContainerCreating

The initial Kubernetes pod entered:

```text
ContainerCreating
```

The pod events showed that Kubernetes was attempting to pull the local image.

After troubleshooting the local container runtime/image availability and recreating the pod, it reached:

```text
1/1 Running
```

The Deployment eventually reported:

```text
READY   UP-TO-DATE   AVAILABLE
1/1     1            1
```

---

## Issue 5 — Local port conflict

A previously running port-forward occupied port `8002`.

Attempting:

```bash
kubectl port-forward svc/hybrid-url-threat-api-service 8002:8000
```

returned:

```text
bind: Only one usage of each socket address
```

A different local port was used:

```bash
kubectl port-forward svc/hybrid-url-threat-api 8090:8000
```

The forwarding then worked:

```text
Forwarding from 127.0.0.1:8090 -> 8000
Forwarding from [::1]:8090 -> 8000
```

This demonstrated the difference between:

* Local host port
* Kubernetes Service port
* Container target port

---

# Application Overview

The underlying application is a **Hybrid URL Threat Detection API**.

The application classifies URLs into four categories:

| Category      |
| ------------- |
| Benign        |
| Phishing      |
| Piracy        |
| Typosquatting |

The ML inference pipeline uses a hybrid approach involving URL/lexical features and a MiniLM-based representation with a BiLSTM model served through ONNX Runtime.

The FastAPI application provides an API layer around the model.

The focus of this repository's DevOps work is not retraining the model, but building a reliable delivery workflow around the existing ML application.

---

# Running Locally Without Docker

Create a virtual environment:

```powershell
python -m venv venv
```

Activate it:

```powershell
venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Start FastAPI:

```powershell
python -m uvicorn app.main:app --reload
```

Open:

```text
http://localhost:8000/docs
```

Health endpoint:

```text
http://localhost:8000/health
```

---

# Running with Docker

Build:

```powershell
docker build -t hybrid-url-threat-api:ci .
```

Run:

```powershell
docker run -p 8000:8000 hybrid-url-threat-api:ci
```

Open:

```text
http://localhost:8000/docs
```

Health:

```text
http://localhost:8000/health
```

---

# Manual Kubernetes Deployment

Apply the Kubernetes configuration:

```powershell
kubectl apply -f k8s/
```

Check the Deployment:

```powershell
kubectl get deployments
```

Check the Pod:

```powershell
kubectl get pods
```

Check the Service:

```powershell
kubectl get services
```

Check rollout:

```powershell
kubectl rollout status deployment/hybrid-url-threat-api
```

Access locally:

```powershell
kubectl port-forward svc/hybrid-url-threat-api 8090:8000
```

Then:

```text
http://localhost:8090/docs
```

---

# Known Limitations

## Local environment

The current CI/CD environment runs locally using:

```text
Docker Desktop
    ├── Jenkins container
    ├── Docker Engine
    └── Kubernetes cluster
```

The application is not currently deployed to a cloud Kubernetes platform such as AWS EKS, Azure AKS, or Google GKE.

---

## Single replica

The Kubernetes Deployment currently uses:

```yaml
replicas: 1
```

The application image is relatively large and takes time to initialize, so the current local deployment uses a single replica.

---

## Static CI image tag

The current pipeline builds:

```text
hybrid-url-threat-api:ci
```

For a production-oriented pipeline, immutable tags should be used, for example:

```text
hybrid-url-threat-api:build-42
```

or:

```text
hybrid-url-threat-api:<git-commit-sha>
```

This would make deployments easier to identify and roll back.

---

## Limited automated test coverage

The current automated tests focus on basic API functionality.

Additional tests can be added for:

* Prediction endpoint
* Valid URL inputs
* Invalid inputs
* Model inference
* Error handling
* Response schema

---

## Trivy findings

The current image scan can report vulnerabilities in the base image and dependencies.

The pipeline currently reports these findings without failing the build.

A production implementation should define a vulnerability threshold and fail builds when unacceptable vulnerabilities are detected.

---

## No production monitoring stack

The current project uses:

* Kubernetes health probes
* FastAPI `/health`
* `kubectl`
* Container logs

It does not currently include:

* Prometheus
* Grafana
* Centralized logging
* Distributed tracing

---

## Local Jenkins Kubernetes credentials

The current Jenkins-to-Kubernetes configuration is designed for the local Docker Desktop environment.

A production implementation should use a dedicated Kubernetes identity/service account with appropriately restricted RBAC permissions rather than a local development kubeconfig.

---

# Future Improvements

Potential improvements include:

1. Use immutable Docker image tags based on Jenkins build numbers or Git commit SHA.
2. Push Docker images to a container registry.
3. Deploy to a managed Kubernetes cluster.
4. Configure GitHub webhook-triggered Jenkins builds.
5. Expand automated test coverage.
6. Add prediction endpoint tests.
7. Enforce Trivy vulnerability thresholds.
8. Add Kubernetes resource requests and limits.
9. Add Horizontal Pod Autoscaling.
10. Add Prometheus and Grafana monitoring.
11. Add centralized logging.
12. Implement deployment versioning and automated rollback.
13. Configure dedicated Kubernetes RBAC permissions for Jenkins.
14. Add separate development and production environments.

---

# DevOps Skills Demonstrated

This project demonstrates hands-on work with:

```text
Git / GitHub
      │
      ▼
Jenkins Pipeline as Code
      │
      ▼
Docker
      │
      ├── Image Build
      └── Container Execution
      │
      ▼
Automated Testing
      │
      ▼
Trivy Security Scanning
      │
      ▼
Container Health Validation
      │
      ▼
Kubernetes
      │
      ├── Deployment
      ├── Service
      ├── Readiness Probe
      ├── Liveness Probe
      ├── Rollout Verification
      └── Rollback
      │
      ▼
FastAPI ML Application
```

---

# Key Learning Outcome

The project demonstrates the complete path from application source code to a running Kubernetes workload:

```text
Source Code
     ↓
GitHub
     ↓
Jenkins
     ↓
Docker Build
     ↓
Automated Tests
     ↓
Security Scan
     ↓
Container Health Check
     ↓
Kubernetes Deployment
     ↓
Pod Readiness
     ↓
Service
     ↓
Application Verification
```

The project also includes practical troubleshooting of:

* Jenkins container tooling
* Docker CLI integration
* Docker socket access
* Kubernetes API connectivity
* Kubernetes kubeconfig configuration
* TLS configuration
* Container image availability
* Pod startup failures
* Kubernetes Service connectivity
* Local port conflicts
* Deployment rollback
