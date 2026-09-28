pipeline {
    agent any

    stages {

        stage('Docker Build') {
            steps {
                echo 'Building Docker image'
                sh 'docker build -t hybrid-url-threat-api:ci .'
            }
        }

    }
}