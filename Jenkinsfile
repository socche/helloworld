pipeline {
    agent none

    environment {
        JAR_WIREMOCK = '/home/jenkins/tools/wiremock.jar'
    }

    stages {
        stage('Get Code') {
            agent { label 'raspberry-agent' }
            steps {
                echo 'Clonando repositorio en la Raspberry Pi'
                sh 'whoami && hostname && echo $WORKSPACE'
                git url: 'https://github.com/socche/helloworld.git'
                stash name: 'codigo', includes: '**/*'
                cleanWs()
            }
        }

        stage('Tests') {
            parallel {
                stage('Unit Tests') {
                    agent { label 'raspberry-agent' }
                    steps {
                        echo 'Ejecutando tests unitarios en Raspberry Pi'
                        sh 'whoami && hostname && echo $WORKSPACE'
                        unstash 'codigo'
                        sh '''
                            rm -rf venv
                            python3 -m venv venv
                            source venv/bin/activate
                            pip install --upgrade pip
                            pip install pytest flask
                            export PYTHONPATH=$WORKSPACE
                            pytest --junitxml=result-unit.xml test/unit
                        '''
                        echo 'Publicando resultados unitarios'
                        junit 'result-unit.xml'
                        cleanWs()
                    }
                }

                stage('Integration Tests') {
                    agent { label 'wsl-agent' }
                    steps {
                        echo 'Ejecutando tests de integración en WSL'
                        sh 'whoami && hostname && echo $WORKSPACE'
                        unstash 'codigo'
                        sh '''
                            rm -rf venv
                            python3 -m venv venv
                            source venv/bin/activate
                            pip install --upgrade pip
                            pip install pytest flask
                            mkdir -p mocks/mappings
                            cp test/wiremock/mappings/*.json mocks/mappings/
                            export FLASK_APP=app/api.py
                            export FLASK_ENV=development
                            flask run --host=127.0.0.1 --port=5000 &
                            java -jar $JAR_WIREMOCK --port 9090 --root-dir mocks &
                            echo 'Esperando a que WireMock exponga el puerto 9090...'
                            until nc -z localhost 9090; do sleep 1; done
                            echo 'WireMock disponible, continuamos con los tests'
                            export PYTHONPATH=$WORKSPACE
                            pytest --junitxml=result-rest.xml test/rest
                        '''
                        echo 'Publicando resultados de integración'
                        junit 'result-rest.xml'
                        cleanWs()
                    }
                }
            }
        }
    }
}