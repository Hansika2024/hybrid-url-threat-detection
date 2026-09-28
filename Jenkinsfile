pipeline {
    agent any

    stages {

        stage('Environment Check') {
            steps {
                sh 'python3 --version || true'
                sh 'python --version || true'
                sh 'git --version'
                sh 'pwd'
                sh 'ls -la'
            }
        }

    }
}