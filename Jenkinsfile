pipeline {
    agent none

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

        stage('Unit Tests') {
            agent { label 'raspberry-agent' }
            steps {
                echo 'Ejecutando tests unitarios en Raspberry Pi'
                sh 'whoami && hostname && echo $WORKSPACE'
                unstash 'codigo'
                sh '''
                    bash -c "
                        rm -rf venv
                        python3 -m venv venv
                        source venv/bin/activate
                        pip install --upgrade pip
                        pip install pytest flask
                        export PYTHONPATH=$WORKSPACE
                        pytest --junitxml=result-unit.xml test/unit
                    "
                '''
                echo 'Publicando resultados unitarios'
                junit 'result-unit.xml'
                cleanWs()
            }
        }

        stage('Download Wiremock') {
            agent { label 'wsl-agent' }
            steps {
                echo 'Descargando WireMock en WSL'
                sh 'whoami && hostname && echo $WORKSPACE'
                unstash 'codigo'
                sh '''
                    mkdir -p mocks
                    wget -O mocks/wiremock.jar https://repo1.maven.org/maven2/com/github/tomakehurst/wiremock-standalone/2.9.0/wiremock-standalone-2.9.0.jar
                '''
                stash name: 'codigo_con_wiremock', includes: '**/*'
                cleanWs()
            }
        }

        stage('Integration Tests') {
            agent { label 'wsl-agent' }
            steps {
                echo 'Ejecutando tests de integración en WSL'
                sh 'whoami && hostname && echo $WORKSPACE'
                unstash 'codigo_con_wiremock'
                sh '''
                    bash -c "
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
                        java -jar mocks/wiremock.jar --port 9090 --root-dir mocks &
                        echo "Esperando a que WireMock exponga el puerto 9090..."
                        until nc -z localhost 9090; do
                        sleep 1
                        done
                        echo "WireMock disponible, continuamos con los tests"
                        sleep 0.5
                        export PYTHONPATH=$WORKSPACE
                        pytest --junitxml=result-rest.xml test/rest
                    "
                '''
                echo 'Publicando resultados de integración'
                junit 'result-rest.xml'
                cleanWs()
            }
        }
    }
}