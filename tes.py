import os

# Nama proyek
project_name = "duplicate-detection-enterprise"

# 1. Buat folder utama
os.makedirs(project_name, exist_ok=True)
print(f"✅ Folder utama: {project_name}")

# 2. Masuk ke folder proyek
os.chdir(project_name)

# 3. Daftar semua folder yang perlu dibuat
folders = [
    "src/core/domain",
    "src/core/usecases",
    "src/core/ports",
    "src/infrastructure/persistence",
    "src/infrastructure/cache",
    "src/infrastructure/storage",
    "src/infrastructure/messaging",
    "src/api/routes",
    "src/api/middlewares",
    "src/api/dtos",
    "src/worker/tasks",
    "src/worker/consumers",
    "tests/unit",
    "tests/integration",
    "migrations/versions",
    "deployments/docker",
    "deployments/kubernetes",
    "monitoring/prometheus",
    "monitoring/grafana/dashboards",
    "scripts",
]

# 4. Buat semua folder
for folder in folders:
    os.makedirs(folder, exist_ok=True)
    print(f"  📁 Folder: {folder}")

# 5. Buat file __init__.py di setiap folder Python
python_folders = [
    "src",
    "src/core",
    "src/core/domain",
    "src/core/usecases",
    "src/core/ports",
    "src/infrastructure",
    "src/infrastructure/persistence",
    "src/infrastructure/cache",
    "src/infrastructure/storage",
    "src/infrastructure/messaging",
    "src/api",
    "src/api/routes",
    "src/api/middlewares",
    "src/api/dtos",
    "src/worker",
    "src/worker/tasks",
    "src/worker/consumers",
    "tests",
    "tests/unit",
    "tests/integration",
]

for folder in python_folders:
    init_file = f"{folder}/__init__.py"
    with open(init_file, 'w') as f:
        f.write(f"# {folder} package\n")
    print(f"  📄 __init__.py di: {folder}")

# 6. Buat file-file Python utama (kosong)
python_files = [
    "src/main.py",
    "src/core/domain/claim.py",
    "src/core/domain/photo.py",
    "src/core/domain/hash.py",
    "src/core/usecases/detect_duplicate.py",
    "src/core/ports/repositories.py",
    "src/core/ports/services.py",
    "src/infrastructure/persistence/postgres_repositories.py",
    "src/infrastructure/persistence/elasticsearch_hash_repo.py",
    "src/infrastructure/cache/redis_cache.py",
    "src/infrastructure/storage/s3_storage.py",
    "src/infrastructure/messaging/kafka_producer.py",
    "src/infrastructure/container.py",
    "src/api/routes/upload.py",
    "src/api/routes/health.py",
    "src/api/middlewares/logging.py",
    "src/api/middlewares/rate_limit.py",
    "src/api/dtos/requests.py",
    "src/worker/celery_app.py",
    "src/worker/tasks/process_photo.py",
    "src/worker/consumers/kafka_consumer.py",
    "tests/unit/test_domain.py",
    "tests/unit/test_usecases.py",
    "tests/integration/test_api.py",
    "tests/conftest.py",
    "migrations/env.py",
    "scripts/init_elasticsearch.py",
]

for file_path in python_files:
    with open(file_path, 'w') as f:
        f.write(f"# {file_path}\n")
    print(f"  📄 File: {file_path}")

# 7. Buat file-file konfigurasi
root_files = [
    ".env.example",
    "requirements.txt",
    "requirements-dev.txt",
    "Makefile",
    "README.md",
    ".gitignore",
    "pyproject.toml",
    "alembic.ini",
]

for file_name in root_files:
    with open(file_name, 'w') as f:
        f.write(f"# {file_name}\n")
    print(f"  📄 Root: {file_name}")

# 8. Buat file docker
docker_files = [
    "deployments/docker/Dockerfile.api",
    "deployments/docker/Dockerfile.worker",
    "deployments/docker/docker-compose.yml",
]

for file_path in docker_files:
    with open(file_path, 'w') as f:
        f.write(f"# {file_path}\n")
    print(f"  📄 Docker: {file_path}")

# 9. Buat file kubernetes
k8s_files = [
    "deployments/kubernetes/namespace.yaml",
    "deployments/kubernetes/configmap.yaml",
    "deployments/kubernetes/secrets.yaml",
    "deployments/kubernetes/api-deployment.yaml",
    "deployments/kubernetes/worker-deployment.yaml",
]

for file_path in k8s_files:
    with open(file_path, 'w') as f:
        f.write(f"# {file_path}\n")
    print(f"  📄 K8s: {file_path}")

# 10. Buat file monitoring
monitoring_files = [
    "monitoring/prometheus/prometheus.yml",
]

for file_path in monitoring_files:
    with open(file_path, 'w') as f:
        f.write(f"# {file_path}\n")
    print(f"  📄 Monitoring: {file_path}")

print("\n" + "="*50)
print("✅✅ SELESAI! Semua folder dan file sudah dibuat.")
print("="*50)
print(f"\n📁 Lokasi proyek: {os.getcwd()}")
print("\nStruktur lengkap:")
os.system("find . -type d | sort")  # Linux/Mac
# os.system("dir /s /b")  # Windows