pipeline {
    agent none

    environment {
        PYTHONUNBUFFERED = '1'
        PYTHONPATH = "${WORKSPACE}"
    }

    stages {
        stage('Preparar entorno') {
            agent { label 'master' }

            steps {
                echo 'Descargando código y preparando entorno...'
                deleteDir()
                checkout scm

                stash name: 'source_code', includes: '**'
            }
        }

        stage('Tests paralelos') {
            parallel {
                stage('Unit Tests') {
                    agent { label 'raspi' }

                    steps {
                        unstash 'source_code'

                        sh '''
                            echo "== Ejecutando tests unitarios en Raspberry Pi =="
                            rm -rf venv
                            python3 -m venv venv
                            . venv/bin/activate
                            pip install --upgrade pip
                            pip install pytest flask

                            export PYTHONPATH=$WORKSPACE
                            pytest --junitxml=result-unit.xml test/unit
                        '''
                    }

                    post {
                        always {
                            echo 'Publicando resultados unitarios'
                            junit 'result-unit.xml'
                        }
                    }
                }

                stage('Integration Tests') {
                    agent { label 'wsl' }

                    steps {
                        unstash 'source_code'

                        sh '''
                            echo "== Ejecutando tests de integración en WSL =="
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
                            nohup java -jar tools/wiremock.jar --port 9090 --root-dir mocks > wiremock.log 2>&1 &

                            sleep 3
                            echo "=== Últimas líneas del log de WireMock ==="
                            tail -n 20 wiremock.log || true

                            echo "== Esperando a que WireMock exponga el puerto 9090... =="
                            until nc -z localhost 9090; do sleep 1; done
                            echo "== WireMock disponible, continuamos con los tests =="

                            export PYTHONPATH=$WORKSPACE
                            pytest --junitxml=result-rest.xml test/rest
                        '''
                    }

                    post {
                        always {
                            echo 'Publicando resultados de integración'
                            junit 'result-rest.xml'
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}