pipeline {
    agent any
    
    parameters {
        choice(
            name: 'COMPONENT',
            choices: ['all', 'agents', 'frontend'],
            description: 'Which component to build and deploy'
        )
        choice(
            name: 'ENVIRONMENT',
            choices: ['staging', 'prod'],
            description: 'Deployment environment'
        )
        booleanParam(
            name: 'DEPLOY_ONLY',
            defaultValue: false,
            description: 'Skip build and only deploy latest images'
        )
    }
    
    environment {
        AWS_REGION = 'us-west-1'
        AWS_ACCOUNT_ID = '816069170416'
        ECR_URL = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        AGENTS_IMAGE_NAME = "mysuperagent-agents"
        FRONTEND_IMAGE_NAME = "mysuperagent-frontend"
        
        // Environment-specific variables
        S3_BUCKET = "${params.ENVIRONMENT == 'staging' ? 'mysuperagent-staging-deploy-' : 'mysuperagent-deploy-'}${AWS_ACCOUNT_ID}"
        APPLICATION_NAME = "${params.ENVIRONMENT == 'staging' ? 'MySuperAgentApp-Staging' : 'MySuperAgentApp'}"
        DEPLOYMENT_GROUP = "${params.ENVIRONMENT == 'staging' ? 'MySuperAgentDeploymentGroup-Staging' : 'MySuperAgentDeploymentGroup'}"
        IMAGE_TAG = "${params.ENVIRONMENT}-${BUILD_NUMBER}"
        STABLE_TAG = "${params.ENVIRONMENT == 'staging' ? 'latest' : 'stable'}"
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('ECR Authentication') {
            steps {
                script {
                    sh "aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_URL}"
                }
            }
        }
        
        stage('Build & Push Agents Image') {
            when {
                expression { 
                    return !params.DEPLOY_ONLY && (params.COMPONENT == 'all' || params.COMPONENT == 'agents')
                }
            }
            steps {
                script {
                    dir('submodules/agents') {
                        // Check if repository exists, create if it doesn't
                        sh """
                            if ! aws ecr describe-repositories --repository-names "${AGENTS_IMAGE_NAME}" --region ${AWS_REGION} &> /dev/null; then
                                aws ecr create-repository --repository-name "${AGENTS_IMAGE_NAME}" --region ${AWS_REGION}
                            fi
                        """
                        
                        // Build image
                        sh "docker build -t ${AGENTS_IMAGE_NAME}:${IMAGE_TAG} -f build/Dockerfile ."
                        
                        // Tag image
                        sh "docker tag ${AGENTS_IMAGE_NAME}:${IMAGE_TAG} ${ECR_URL}/${AGENTS_IMAGE_NAME}:${IMAGE_TAG}"
                        sh "docker tag ${AGENTS_IMAGE_NAME}:${IMAGE_TAG} ${ECR_URL}/${AGENTS_IMAGE_NAME}:${STABLE_TAG}"
                        
                        // Push image
                        sh "docker push ${ECR_URL}/${AGENTS_IMAGE_NAME}:${IMAGE_TAG}"
                        sh "docker push ${ECR_URL}/${AGENTS_IMAGE_NAME}:${STABLE_TAG}"
                    }
                }
            }
        }
        
        stage('Build & Push Frontend Image') {
            when {
                expression { 
                    return !params.DEPLOY_ONLY && (params.COMPONENT == 'all' || params.COMPONENT == 'frontend')
                }
            }
            steps {
                script {
                    dir('submodules/frontend') {
                        // Check if repository exists, create if it doesn't
                        sh """
                            if ! aws ecr describe-repositories --repository-names "${FRONTEND_IMAGE_NAME}" --region ${AWS_REGION} &> /dev/null; then
                                aws ecr create-repository --repository-name "${FRONTEND_IMAGE_NAME}" --region ${AWS_REGION}
                            fi
                        """
                        
                        // Build image
                        sh "docker build -t ${FRONTEND_IMAGE_NAME}:${IMAGE_TAG} ."
                        
                        // Tag image
                        sh "docker tag ${FRONTEND_IMAGE_NAME}:${IMAGE_TAG} ${ECR_URL}/${FRONTEND_IMAGE_NAME}:${IMAGE_TAG}"
                        sh "docker tag ${FRONTEND_IMAGE_NAME}:${IMAGE_TAG} ${ECR_URL}/${FRONTEND_IMAGE_NAME}:${STABLE_TAG}"
                        
                        // Push image
                        sh "docker push ${ECR_URL}/${FRONTEND_IMAGE_NAME}:${IMAGE_TAG}"
                        sh "docker push ${ECR_URL}/${FRONTEND_IMAGE_NAME}:${STABLE_TAG}"
                    }
                }
            }
        }
        
        stage('Prepare Deployment Package') {
            steps {
                script {
                    // Create a temporary directory for our deployment files
                    sh "mkdir -p deployment"
                    
                    // Create appspec.yml
                    writeFile file: 'deployment/appspec.yml', text: """version: 0.0
os: linux
files:
  - source: /scripts
    destination: /tmp/deployment
hooks:
  ApplicationStop:
    - location: scripts/stop_application.sh
      timeout: 300
      runas: root
  BeforeInstall:
    - location: scripts/before_install.sh
      timeout: 300
      runas: root
  AfterInstall:
    - location: scripts/after_install.sh
      timeout: 600
      runas: root
  ApplicationStart:
    - location: scripts/start_application.sh
      timeout: 300
      runas: root
"""
                    
                    // Create scripts directory
                    sh "mkdir -p deployment/scripts"
                    
                    // Get scripts from the repo's code_deploy directory
                    sh "cp build/code_deploy/*.sh deployment/scripts/"
                    
                    // Ensure scripts are executable
                    sh "chmod +x deployment/scripts/*.sh"
                    
                    // Inject environment variable to scripts
                    sh """
                        for script in deployment/scripts/*.sh; do
                            sed -i '1a\\nexport DEPLOY_ENV=${params.ENVIRONMENT}' \$script
                        done
                    """
                    
                    // Add deployment info file for reference
                    writeFile file: 'deployment/deployment_info.txt', text: """Deployment Info:
Build: ${BUILD_NUMBER}
Environment: ${params.ENVIRONMENT}
Component: ${params.COMPONENT}
Date: ${new Date()}
"""
                    
                    // Create zip file
                    sh "cd deployment && zip -r ../mysuperagent-${params.ENVIRONMENT}-deployment-${BUILD_NUMBER}.zip ."
                }
            }
        }
        
        stage('Upload to S3') {
            steps {
                sh "aws s3 cp mysuperagent-${params.ENVIRONMENT}-deployment-${BUILD_NUMBER}.zip s3://${S3_BUCKET}/"
            }
        }
        
        stage('Deploy with CodeDeploy') {
            steps {
                script {
                    def deploymentId = sh(
                        script: """
                            aws deploy create-deployment \\
                            --application-name ${APPLICATION_NAME} \\
                            --deployment-group-name ${DEPLOYMENT_GROUP} \\
                            --deployment-config-name CodeDeployDefault.AllAtOnce \\
                            --s3-location bucket=${S3_BUCKET},key=mysuperagent-${params.ENVIRONMENT}-deployment-${BUILD_NUMBER}.zip,bundleType=zip \\
                            --region ${AWS_REGION} \\
                            --query 'deploymentId' \\
                            --output text
                        """,
                        returnStdout: true
                    ).trim()
                    
                    echo "Deployment created with ID: ${deploymentId}"
                    
                    // Monitor deployment status
                    def status = "InProgress"
                    while (status == "InProgress" || status == "Created" || status == "Queued" || status == "Ready") {
                        echo "Deployment status: ${status}"
                        sleep(10)
                        status = sh(
                            script: """
                                aws deploy get-deployment \\
                                --deployment-id ${deploymentId} \\
                                --query 'deploymentInfo.status' \\
                                --output text
                            """,
                            returnStdout: true
                        ).trim()
                    }
                    
                    if (status == "Succeeded") {
                        echo "Deployment to ${params.ENVIRONMENT} succeeded!"
                    } else {
                        error "Deployment to ${params.ENVIRONMENT} failed with status: ${status}"
                    }
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            echo "Build and deployment successful!"
        }
        failure {
            echo "Build or deployment failed!"
        }
    }
}