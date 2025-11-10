# 🏗️ ARCHITECTURE SETUP SCRIPT
# Configuration automatique de l'infrastructure Kafka + Spark
# Compatible Windows PowerShell

import os
import sys
import subprocess
import time
import logging
from pathlib import Path
import requests
import zipfile
import shutil
from typing import Optional, Dict, List

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('setup.log'),
        logging.StreamHandler()
    ]
)

class InfrastructureSetup:
    """Classe pour configurer l'infrastructure Kafka + Spark sur Windows"""
    
    def __init__(self):
        self.logger = logging.getLogger("InfrastructureSetup")
        self.project_dir = Path(__file__).parent.absolute()
        self.downloads_dir = self.project_dir / "downloads"
        self.kafka_dir = None
        self.spark_dir = None
        
        # Versions recommandées
        self.kafka_version = "2.13-3.6.0"
        self.spark_version = "3.5.0"
        
        # URLs de téléchargement (URLs corrigées)
        self.kafka_url = f"https://archive.apache.org/dist/kafka/3.6.0/kafka_{self.kafka_version}.tgz"
        self.spark_url = f"https://archive.apache.org/dist/spark/spark-{self.spark_version}/spark-{self.spark_version}-bin-hadoop3.tgz"
        
        # Créer dossier downloads
        self.downloads_dir.mkdir(exist_ok=True)
    
    def check_java(self) -> bool:
        """Vérifie que Java est installé et configuré"""
        try:
            result = subprocess.run(
                ["java", "-version"], 
                capture_output=True, 
                text=True,
                shell=True
            )
            
            if result.returncode == 0:
                java_version = result.stderr.split('\n')[0]
                self.logger.info(f"✅ Java détecté: {java_version}")
                return True
            else:
                self.logger.error("❌ Java non trouvé")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Erreur vérification Java: {e}")
            return False
    
    def install_python_dependencies(self) -> bool:
        """Installe les dépendances Python"""
        try:
            self.logger.info("📦 Installation des dépendances Python...")
            
            # Mise à jour pip
            subprocess.run([
                sys.executable, "-m", "pip", "install", "--upgrade", "pip"
            ], check=True)
            
            # Installation requirements
            requirements_file = self.project_dir / "requirements.txt"
            if requirements_file.exists():
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
                ], check=True)
                
                self.logger.info("✅ Dépendances Python installées")
                return True
            else:
                self.logger.error("❌ Fichier requirements.txt non trouvé")
                return False
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"❌ Erreur installation dépendances: {e}")
            return False
    
    def download_and_extract(self, url: str, filename: str) -> Optional[Path]:
        """Télécharge et extrait une archive"""
        try:
            file_path = self.downloads_dir / filename
            
            # Télécharger si n'existe pas
            if not file_path.exists():
                self.logger.info(f"⬇️ Téléchargement {filename}...")
                
                response = requests.get(url, stream=True)
                response.raise_for_status()
                
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                self.logger.info(f"✅ {filename} téléchargé")
            else:
                self.logger.info(f"📁 {filename} déjà présent")
            
            # Extraction
            extract_dir = self.downloads_dir / filename.replace('.tgz', '').replace('.zip', '')
            
            if not extract_dir.exists():
                self.logger.info(f"📂 Extraction {filename}...")
                
                if filename.endswith('.tgz'):
                    import tarfile
                    with tarfile.open(file_path, 'r:gz') as tar:
                        tar.extractall(self.downloads_dir)
                elif filename.endswith('.zip'):
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        zip_ref.extractall(self.downloads_dir)
                
                self.logger.info(f"✅ {filename} extrait")
            
            # Trouver le dossier extrait
            for item in self.downloads_dir.iterdir():
                if item.is_dir() and filename.replace('.tgz', '').replace('.zip', '') in item.name:
                    return item
            
            return extract_dir
            
        except Exception as e:
            self.logger.error(f"❌ Erreur téléchargement/extraction {filename}: {e}")
            return None
    
    def setup_kafka(self) -> bool:
        """Configure Apache Kafka"""
        try:
            self.logger.info("🔧 Configuration Apache Kafka...")
            
            # Télécharger Kafka
            kafka_filename = f"kafka_{self.kafka_version}.tgz"
            self.kafka_dir = self.download_and_extract(self.kafka_url, kafka_filename)
            
            if not self.kafka_dir:
                return False
            
            # Créer scripts de démarrage Windows
            self.create_kafka_scripts()
            
            self.logger.info("✅ Apache Kafka configuré")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur configuration Kafka: {e}")
            return False
    
    def create_kafka_scripts(self):
        """Crée les scripts de démarrage Kafka pour Windows"""
        scripts_dir = self.project_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        
        # Script démarrage Zookeeper
        zookeeper_script = scripts_dir / "start_zookeeper.bat"
        zookeeper_content = f"""@echo off
echo Starting Zookeeper...
cd /d "{self.kafka_dir}"
bin\\windows\\zookeeper-server-start.bat config\\zookeeper.properties
"""
        with open(zookeeper_script, 'w') as f:
            f.write(zookeeper_content)
        
        # Script démarrage Kafka
        kafka_script = scripts_dir / "start_kafka.bat"
        kafka_content = f"""@echo off
echo Starting Kafka Server...
cd /d "{self.kafka_dir}"
bin\\windows\\kafka-server-start.bat config\\server.properties
"""
        with open(kafka_script, 'w') as f:
            f.write(kafka_content)
        
        # Script création topics
        topics_script = scripts_dir / "create_topics.bat"
        topics_content = f"""@echo off
echo Creating Kafka Topics...
cd /d "{self.kafka_dir}"

rem Topic pour Reddit
bin\\windows\\kafka-topics.bat --create --topic reddit_stream --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1

rem Topic pour Twitter  
bin\\windows\\kafka-topics.bat --create --topic twitter_stream --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1

rem Topic pour IoT Sensors
bin\\windows\\kafka-topics.bat --create --topic iot_sensors --bootstrap-server localhost:9092 --partitions 5 --replication-factor 1

rem Topic pour News Feed
bin\\windows\\kafka-topics.bat --create --topic news_feed --bootstrap-server localhost:9092 --partitions 2 --replication-factor 1

echo Topics created successfully!
pause
"""
        with open(topics_script, 'w') as f:
            f.write(topics_content)
        
        self.logger.info("✅ Scripts Kafka créés")
    
    def setup_spark(self) -> bool:
        """Configure Apache Spark"""
        try:
            self.logger.info("⚡ Configuration Apache Spark...")
            
            # Télécharger Spark
            spark_filename = f"spark-{self.spark_version}-bin-hadoop3.tgz"
            self.spark_dir = self.download_and_extract(self.spark_url, spark_filename)
            
            if not self.spark_dir:
                return False
            
            # Configurer variables d'environnement
            self.setup_spark_environment()
            
            # Créer scripts de démarrage
            self.create_spark_scripts()
            
            self.logger.info("✅ Apache Spark configuré")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur configuration Spark: {e}")
            return False
    
    def setup_spark_environment(self):
        """Configure les variables d'environnement Spark"""
        # Créer script d'environnement
        env_script = self.project_dir / "spark_env.bat"
        env_content = f"""@echo off
set SPARK_HOME={self.spark_dir}
set PYSPARK_PYTHON={sys.executable}
set PYSPARK_DRIVER_PYTHON={sys.executable}
set PATH=%SPARK_HOME%\\bin;%PATH%

echo Spark Environment configured
echo SPARK_HOME: %SPARK_HOME%
echo PYSPARK_PYTHON: %PYSPARK_PYTHON%
"""
        with open(env_script, 'w') as f:
            f.write(env_content)
        
        self.logger.info("✅ Variables environnement Spark configurées")
    
    def create_spark_scripts(self):
        """Crée les scripts de démarrage Spark"""
        scripts_dir = self.project_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        
        # Script démarrage Spark Master
        master_script = scripts_dir / "start_spark_master.bat"
        master_content = f"""@echo off
call "{self.project_dir}\\spark_env.bat"
echo Starting Spark Master...
cd /d "%SPARK_HOME%"
bin\\spark-class.cmd org.apache.spark.deploy.master.Master
"""
        with open(master_script, 'w') as f:
            f.write(master_content)
        
        # Script démarrage Spark Worker
        worker_script = scripts_dir / "start_spark_worker.bat"
        worker_content = f"""@echo off
call "{self.project_dir}\\spark_env.bat"
echo Starting Spark Worker...
cd /d "%SPARK_HOME%"
bin\\spark-class.cmd org.apache.spark.deploy.worker.Worker spark://localhost:7077
"""
        with open(worker_script, 'w') as f:
            f.write(worker_content)
        
        self.logger.info("✅ Scripts Spark créés")
    
    def setup_mongodb(self) -> bool:
        """Instructions pour MongoDB"""
        self.logger.info("📄 Instructions MongoDB:")
        self.logger.info("1. Télécharger MongoDB Community Server")
        self.logger.info("2. Installer avec configuration par défaut")
        self.logger.info("3. Démarrer service MongoDB")
        self.logger.info("4. MongoDB sera accessible sur mongodb://localhost:27017")
        return True
    
    def create_launch_script(self):
        """Crée le script de lancement principal"""
        launch_script = self.project_dir / "launch_system.bat"
        launch_content = f"""@echo off
echo ========================================
echo   Multi-Source Analytics System
echo   Apache Kafka + Spark Streaming
echo ========================================
echo.

echo Etape 1: Demarrage Zookeeper...
start "Zookeeper" cmd /k "scripts\\start_zookeeper.bat"
timeout /t 10

echo Etape 2: Demarrage Kafka...
start "Kafka" cmd /k "scripts\\start_kafka.bat"
timeout /t 15

echo Etape 3: Creation des topics...
call scripts\\create_topics.bat

echo Etape 4: Demarrage Spark Master...
start "Spark Master" cmd /k "scripts\\start_spark_master.bat"
timeout /t 10

echo Etape 5: Demarrage Spark Worker...
start "Spark Worker" cmd /k "scripts\\start_spark_worker.bat"
timeout /t 5

echo.
echo ========================================
echo   Systeme demarre avec succes!
echo ========================================
echo.
echo Services disponibles:
echo - Kafka: localhost:9092
echo - Spark Master: localhost:7077
echo - Spark UI: http://localhost:8080
echo - MongoDB: localhost:27017
echo.
echo Pour demarrer les producteurs:
echo   python kafka_producers.py
echo.
echo Pour demarrer le consumer Spark:
echo   python spark_streaming_consumer.py
echo.
echo Pour le dashboard:
echo   streamlit run dashboard_3d_realtime.py
echo.
pause
"""
        with open(launch_script, 'w', encoding='utf-8') as f:
            f.write(launch_content)
        
        self.logger.info("✅ Script de lancement créé")
    
    def create_readme(self):
        """Crée la documentation"""
        readme_content = """# 🚀 Multi-Source Real-Time Analytics System

## Architecture
- **Apache Kafka**: Message streaming platform
- **Apache Spark**: Real-time stream processing
- **MongoDB**: NoSQL storage for analytics
- **Streamlit**: Interactive 3D dashboard

## 🏗️ Installation Automatique

```bash
python setup_infrastructure.py
```

## 🚀 Démarrage Rapide

### Option 1: Script automatique
```bash
./launch_system.bat
```

### Option 2: Démarrage manuel

1. **Démarrer Zookeeper**
```bash
./scripts/start_zookeeper.bat
```

2. **Démarrer Kafka**
```bash
./scripts/start_kafka.bat
```

3. **Créer les topics**
```bash
./scripts/create_topics.bat
```

4. **Démarrer Spark**
```bash
./scripts/start_spark_master.bat
./scripts/start_spark_worker.bat
```

5. **Lancer les producteurs**
```bash
python kafka_producers.py
```

6. **Lancer le consumer Spark**
```bash
python spark_streaming_consumer.py
```

7. **Ouvrir le dashboard**
```bash
streamlit run dashboard_3d_realtime.py
```

## 📊 Dashboard Features

- **Visualizations 3D** des trending keywords
- **Surface plots** pour évolution sentiment
- **Détection d'anomalies** en temps réel
- **Analytics cross-platform** sans redémarrage
- **Monitoring multi-sources** (Reddit, Twitter, IoT, News)

## 🔧 Configuration

### Kafka Topics
- `reddit_stream`: Données Reddit (3 partitions)
- `twitter_stream`: Données Twitter (3 partitions)  
- `iot_sensors`: Capteurs IoT (5 partitions)
- `news_feed`: Flux d'actualités (2 partitions)

### Services URLs
- Kafka: `localhost:9092`
- Spark UI: `http://localhost:8080`
- MongoDB: `mongodb://localhost:27017`
- Dashboard: `http://localhost:8501`

## 📈 Analytics Capabilities

- **Sentiment Analysis**: VADER + TextBlob + Lexicon-based
- **Keyword Trending**: Fenêtres glissantes avec scoring
- **Anomaly Detection**: Z-score et seuils statistiques
- **Cross-Source Correlation**: Analyse inter-plateformes
- **Real-Time Visualization**: Mises à jour sans interruption

## 🎯 Final Project Compliance

✅ **Multi-Source Data Ingestion**: Reddit, Twitter, IoT, News  
✅ **Apache Kafka**: Message streaming  
✅ **Spark Streaming**: Real-time processing  
✅ **Text Analytics**: NLP et sentiment analysis  
✅ **NoSQL Storage**: MongoDB intégration  
✅ **3D Visualizations**: Plotly 3D plots  
✅ **Real-Time Monitoring**: Dashboard temps réel  

## 🔧 Troubleshooting

### Java non trouvé
```bash
# Installer Java 8 ou 11
# Configurer JAVA_HOME
```

### Erreurs Kafka
```bash
# Vérifier Zookeeper actif
# Ports 9092, 2181 libres
```

### Erreurs Spark
```bash
# Vérifier SPARK_HOME
# Python et PySpark compatibles
```
"""
        
        readme_file = self.project_dir / "README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        self.logger.info("✅ Documentation créée")

def main():
    """Fonction principale d'installation"""
    print("🚀 INSTALLATION INFRASTRUCTURE MULTI-SOURCE ANALYTICS")
    print("=" * 60)
    print("Configuration automatique:")
    print("• ☕ Vérification Java")
    print("• 📦 Installation dépendances Python")
    print("• 🔧 Configuration Apache Kafka")
    print("• ⚡ Configuration Apache Spark")
    print("• 📄 Création scripts de démarrage")
    print("• 📚 Génération documentation")
    print()
    
    setup = InfrastructureSetup()
    
    # Étapes d'installation
    steps = [
        ("☕ Vérification Java", setup.check_java),
        ("📦 Installation dépendances Python", setup.install_python_dependencies),
        ("🔧 Configuration Apache Kafka", setup.setup_kafka),
        ("⚡ Configuration Apache Spark", setup.setup_spark),
        ("💾 Instructions MongoDB", setup.setup_mongodb),
        ("🚀 Création script de lancement", setup.create_launch_script),
        ("📚 Génération documentation", setup.create_readme)
    ]
    
    success_count = 0
    
    for step_name, step_func in steps:
        try:
            print(f"\n{step_name}...")
            if step_func():
                print(f"✅ {step_name} - SUCCESS")
                success_count += 1
            else:
                print(f"❌ {step_name} - FAILED")
        except Exception as e:
            print(f"❌ {step_name} - ERROR: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 INSTALLATION TERMINÉE: {success_count}/{len(steps)} étapes réussies")
    
    if success_count == len(steps):
        print("✅ Installation complète avec succès!")
        print("\n🚀 PROCHAINES ÉTAPES:")
        print("1. Démarrer le système: ./launch_system.bat")
        print("2. Ou suivre les instructions dans README.md")
        print("3. Accéder au dashboard: http://localhost:8501")
    else:
        print("⚠️ Installation partiellement réussie")
        print("Consulter setup.log pour plus de détails")
    
    print("\n📚 Documentation complète disponible dans README.md")

if __name__ == "__main__":
    main()