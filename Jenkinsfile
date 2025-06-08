pipeline {
    agent none

    environment {
        JAR_WIREMOCK = '/home/jenkins/tools/wiremock.jar'
        PYTHONUNBUFFERED = '1'
    }

    stages {
        stage('Get Code') {
            agent { label 'raspberry-agent' }
            steps {
                echo 'Clonando repositorio en la Raspberry Pi'
                sh 'whoami && hostname && echo $WORKSPACE'
                git url: 'https://github.com/socche/helloworld.git'
                stash name: 'codigo', includes: '**/*'
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

                        catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                            sh '''
                                rm -rf venv
                                python3 -m venv venv
                                . venv/bin/activate
                                pip install --upgrade pip
                                pip install pytest flask

                                export PYTHONPATH=$WORKSPACE
                                pytest --junitxml=result-unit.xml test/unit
                            '''
                        }

                        stash name: 'unit-results', includes: 'result-unit.xml'
                    }
                }

                stage('Integration Tests') {
                    agent { label 'wsl-agent' }
                    steps {
                        echo 'Ejecutando tests de integración en WSL'
                        sh 'whoami && hostname && echo $WORKSPACE'
                        unstash 'codigo'

                        catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
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
                        }

                        stash name: 'rest-results', includes: 'result-rest.xml'
                    }
                }
            }
        }

        stage('Coverage') {
            agent { label 'wsl-agent' }
            steps {
                echo 'Ejecutando análisis de cobertura en WSL'
                sh 'whoami && hostname && echo $WORKSPACE'
                unstash 'codigo'

                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    sh '''
                        rm -rf venv
                        python3 -m venv venv
                        . venv/bin/activate
                        pip install --upgrade pip
                        pip install pytest coverage

                        export PYTHONPATH=$WORKSPACE
                        coverage erase
                        coverage run --branch --source=app --omit=app/__init__.py,app/api.py -m pytest test/unit
                        coverage report -m
                        coverage xml
                    '''
                }

                cobertura coberturaReportFile: 'coverage.xml',
                          lineCoverageTargets: '80,0,90'
            }
        }

        stage('Static') {
            agent { label 'wsl-agent' }
            steps {
                echo 'Ejecutando análisis estático con Flake8 en el agente WSL'
                sh 'whoami && hostname && echo $WORKSPACE'
                unstash 'codigo'

                sh '''
                    rm -rf venv
                    python3 -m venv venv
                    . venv/bin/activate

                    pip install --upgrade pip
                    pip install flake8

                    flake8 --exit-zero --format=pylint app > flake8.out
                '''

                recordIssues tools: [flake8(name: 'Flake8', pattern: 'flake8.out')],
                             qualityGates: [
                                 [threshold: 10, type: 'TOTAL', unstable: true],
                                 [threshold: 11, type: 'TOTAL', unstable: false]
                             ]
            }
        }

        stage('Security') {
            agent { label 'wsl-agent' }
            steps {
                echo 'Ejecutando análisis de seguridad con Bandit en el agente WSL'
                sh 'whoami && hostname && echo $WORKSPACE'
                unstash 'codigo'

                sh '''
                    rm -rf venv
                    python3 -m venv venv
                    . venv/bin/activate

                    pip install --upgrade pip
                    pip install bandit

                    bandit --exit-zero -r app -f custom -o bandit.out --msg-template "{abspath}:{line}: [{test_id}] {msg}"
                '''

                recordIssues tools: [pyLint(name: 'Bandit', pattern: 'bandit.out')],
                             qualityGates: [
                                 [threshold: 1, type: 'TOTAL', unstable: true],
                                 [threshold: 2, type: 'TOTAL', unstable: false]
                             ]
            }
        }

        stage('Performance') {
            agent { label 'wsl-agent' }
            steps {
                echo 'Ejecutando pruebas de rendimiento con JMeter'
                sh 'whoami && hostname && echo $WORKSPACE'
                unstash 'codigo'

                sh '''
                    export PATH=$PATH:/opt/jmeter/bin
                    rm -rf venv
                    python3 -m venv venv
                    . venv/bin/activate

                    pip install --upgrade pip
                    pip install flask

                    export FLASK_APP=app/api.py
                    export FLASK_ENV=development
                    flask run --host=127.0.0.1 --port=5000 > flask.log 2>&1 &

                    echo "== Esperando a que Flask esté disponible en el puerto 5000... =="
                    for i in {1..30}; do
                        nc -z localhost 5000 && break
                        sleep 1
                    done

                    if ! nc -z localhost 5000; then
                        echo "ERROR: Flask no está disponible en el puerto 5000 tras 30s"
                        tail -n 20 flask.log || true
                        exit 1
                    fi

                    echo "== Flask disponible, lanzando pruebas JMeter =="
                    rm -rf test/jmeter/reports
                    rm -f test/jmeter/results.jtl
                    jmeter -n -t test/jmeter/flask.jmx -l test/jmeter/results.jtl -e -o test/jmeter/reports

                    echo "== Pruebas de rendimiento finalizadas =="
                    pkill -f "flask run" || true
                '''
            }
            post {
                always {
                    perfReport sourceDataFiles: 'test/jmeter/results.jtl'
                }
            }
        }

        stage('Results') {
            agent { label 'raspberry-agent' }
            steps {
                echo 'Mostrando resultados finales de los tests'
                unstash 'unit-results'
                unstash 'rest-results'
                junit 'result-*.xml'
            }
            post {
                always {
                    cleanWs()
                }
            }
        }
    }
}