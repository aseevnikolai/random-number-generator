# Развёртывание генератора случайных чисел

Два компонента: **приложение** (FastAPI, образ из `Dockerfile`) и **отдельная база PostgreSQL 17**.
Приложение не хранит данных само — все числа лежат в базе, поэтому его можно масштабировать.

| Файл | Назначение |
|---|---|
| `Dockerfile`, `.dockerignore` | образ приложения `rng-app` на python:3.13-alpine |
| `compose.yaml`, `.env.example` | запуск приложения и базы через Docker Compose |
| `k8s/` | манифесты Kubernetes: Namespace, ConfigMap, Secret (образец), PostgreSQL (PVC + Deployment + Service), приложение (Deployment + Service NodePort) |
| `cluster/kind-config.yaml` | локальный кластер kind из одного узла с пробросом порта 30090 |

Настройки — переменные окружения (см. README.md). Пароль к базе — только в `.env` и `k8s/secret.yaml`,
оба файла в Git не попадают.

## Docker Compose

```bash
git clone https://github.com/aseevnikolai/random-number-generator.git && cd random-number-generator
cp .env.example .env          # задать свой POSTGRES_PASSWORD
docker compose up -d
# приложение: http://localhost:8090
```

## Kubernetes (kind)

```bash
kind create cluster --config cluster/kind-config.yaml
docker build -t rng-app:1.0.0 .
kind load docker-image rng-app:1.0.0 --name cloud
cp k8s/secret.yaml.example k8s/secret.yaml   # задать свой DB_PASSWORD
kubectl apply -f k8s/
kubectl get pods,services,deployments,pvc -n rng
# приложение: http://localhost:30090
```
