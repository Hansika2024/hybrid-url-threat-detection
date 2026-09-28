pipeline {
    agent any

    environment {
        KUBECONFIG = '/tmp/jenkins-kubeconfig'
    }

    stages {

        stage('Docker Build') {
            steps {
                echo 'Building Docker image'
                sh 'docker build -t hybrid-url-threat-api:ci .'
            }
        }

        stage('Test') {
            steps {
                echo 'Running tests'
                sh 'docker run --rm --entrypoint python hybrid-url-threat-api:ci -m unittest discover -s tests -v'
            }
        }

        stage('Security Scan') {
            steps {
                echo 'Scanning Docker image for vulnerabilities'
                sh 'docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:latest image --timeout 15m --scanners vuln --severity HIGH,CRITICAL --exit-code 0 hybrid-url-threat-api:ci'
            }
        }

        stage('Run Container and Health Check') {
            steps {
                echo 'Starting application container'
                sh '''
                    docker rm -f hybrid-url-threat-api-ci || true
                    docker run -d --name hybrid-url-threat-api-ci -p 8001:8000 hybrid-url-threat-api:ci
                    echo "Waiting for application to start..."
                    for i in $(seq 1 30); do
                        if docker exec hybrid-url-threat-api-ci python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=2)"; then
                            echo "Health check passed"
                            exit 0
                        fi
                        sleep 2
                    done
                    echo "Health check failed"
                    docker logs hybrid-url-threat-api-ci
                    exit 1
                '''
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                echo 'Deploying application to Kubernetes'
                sh 'kubectl apply -f k8s/'
                sh 'kubectl rollout status deployment/hybrid-url-threat-api --timeout=180s'
            }
        }
    }

    post {
        always {
            sh 'docker rm -f hybrid-url-threat-api-ci || true'
        }
    }
}