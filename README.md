# PROD-2026 Recommender System

Гибридная рекомендательная система для дейтинг-сервиса, созданная для командного тура PROD-2026

Система превращает обезличенную историю банковских транзакций и пользовательских взаимодействий в персональную ленту анкет, сочетая быстрый ANN-поиск, ML-реранжирование, бизнес-фильтры и объяснимые рекомендации

## Что реализовано

- Построение поведенческого профиля пользователя по транзакциям, MCC-кодам, категориям, времени и структуре расходов
- Генерация кандидатов через FAISS HNSW по транзакционным и interaction-признакам
- Объединение нескольких источников кандидатов с контролируемыми квотами
- CatBoost-реранжирование кандидатов по вероятности полезного взаимодействия
- Учёт лайков, дизлайков, мэтчей, блокировок и истории уже показанных анкет
- Hard-фильтры по таргетингу и ограничениям продукта
- Cold-start и fallback-стратегии для пользователей без достаточной истории
- Три объясняющих признака для каждой рекомендации
- Отдельный FastAPI ML-сервис с health checks и прогревом ANN-индексов
- Интеграция с продуктовым backend через HTTP API
- Воспроизводимый запуск и deployment через Docker Compose

## Архитектура

```text
Транзакции + взаимодействия
             │
    Feature engineering
             │
  FAISS HNSW candidate retrieval
             │
 Targeting и safety-фильтры
             │
      CatBoost reranking
             │
  Top-5 анкет + explanations
             │
       Backend -> клиент
```

ANN-слой сокращает пространство поиска до нескольких сотен релевантных кандидатов, после чего CatBoost-реранжирование учитывает зависимости между пользователем и кандидатом

Такой двухэтапный подход совмещает скорость поиска с качеством персонализации и подходит для online-serving

## Технологии

`Python 3.12` · `FAISS` · `CatBoost` · `pandas` · `Polars` · `scikit-learn` · `FastAPI` · `PostgreSQL` · `SQLAlchemy` · `Docker Compose`

## Структура проекта

- `ml/` — feature pipeline, ANN retrieval, ML-реранжирование, API и offline-артефакты
- `backend/` — продуктовый API, анкеты, взаимодействия, мэтчи и интеграция с ML-сервисом
- `synthetic/` — генерация синтетических событий и проверка recommendation lifecycle
- `*.ipynb` — воспроизводимые эксперименты по признакам, ANN и качеству рекомендаций
- `artifacts/` — результаты offline-валидации и исследовательские артефакты

## Быстрый запуск ML-сервиса

Нужны Docker и Docker Compose

```powershell
cd ml
Copy-Item .env.example .env
docker compose up --build
```

После запуска доступны

- API — `http://localhost:8080`
- Swagger — `http://localhost:8080/docs`
- Liveness — `GET http://localhost:8080/health`
- Readiness — `GET http://localhost:8080/health/ready`

Пример запроса рекомендаций

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8080/recommendation `
  -ContentType 'application/json' `
  -Body '{"user_id":"<USER_ID>"}'
```

Ответ содержит до пяти кандидатов, общий идентификатор выдачи и три причины рекомендации для каждой анкеты

## Подключение к backend

Backend уже содержит HTTP-провайдер рекомендаций и отправляет запросы в `POST /recommendation`

В конфигурации backend нужно указать

```dotenv
ML_RECOMMENDATION_PROVIDER=http
ML_BASE_URL=http://localhost:8080
```

Если сервисы запущены в общей Docker-сети, используйте внутренний адрес

```dotenv
ML_RECOMMENDATION_PROVIDER=http
ML_BASE_URL=http://ml-internal:8080
```

## Deployment

Production-конфигурации находятся в `ml/docker-compose.deploy.yaml` и `backend/docker-compose.deploy.yaml`

Оба compose-файла используют внешнюю сеть `app_shared_net`, через которую backend обращается к ML-контейнеру по имени `ml-internal`

```powershell
docker network create app_shared_net

cd ml
Copy-Item .env.example .env
docker compose -f docker-compose.deploy.yaml up -d

cd ..\backend
docker compose -f docker-compose.deploy.yaml up -d
```

Перед deployment необходимо задать образы `ML_IMAGE` и `API_IMAGE`, параметры PostgreSQL и остальные секреты окружения

ML-контейнер перед стартом проверяет готовность offline-артефактов, прогревает FAISS-индексы и только после этого начинает принимать запросы

## Локальная разработка

```powershell
cd ml
Copy-Item .env.example .env
uv sync
docker compose up -d postgres
uv run build-offline-artifacts --all --force
uv run api
```

Повторное обучение моделей на накопленной истории взаимодействий

```powershell
uv run train-models
```

Основные offline-артефакты сохраняются в `ml/data_out/`
