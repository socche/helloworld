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
                            . venv/bin/activate
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
                            echo "== Preparando entorno de pruebas de integración =="
                            rm -rf venv
                            python3 -m venv venv
                            . venv/bin/activate
                            pip install --upgrade pip
                            pip install pytest flask

                            mkdir -p mocks/mappings
                            cp test/wiremock/mappings/*.json mocks/mappings/

                            export FLASK_APP=app/api.py
                            export FLASK_ENV=development
                            flask run --host=127.0.0.1 --port=5000 &

                            echo "== Lanzando WireMock =="
                            nohup java -jar $JAR_WIREMOCK --port 9090 --root-dir mocks > wiremock.log 2>&1 &

                            echo "== Esperando a que WireMock exponga el puerto 9090... =="
                            for i in {1..30}; do
                                nc -z localhost 9090 && break
                                sleep 1
                            done

                            if ! nc -z localhost 9090; then
                                echo "ERROR: WireMock no está disponible en el puerto 9090 tras 30s"
                                tail -n 20 wiremock.log || true
                                exit 1
                            fi

                            echo "== WireMock disponible, continuamos con los tests =="
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