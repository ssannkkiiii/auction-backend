# Auction Backend

Сервіс на FastAPI з підтримкою WebSocket: створення лотів, ставки через REST, оновлення в реальному часі.

## Можливості

- **Лоти**: стартова ціна, поточна ціна (найвища ставка або стартова), статус `running` / `ended`
- **REST**: створити лот, зробити ставку, отримати список активних лотів
- **WebSocket**: підписка на події лота — хто яку ставку зробив, стартова/поточна ціна, подовження часу

## Запуск через Docker (рекомендовано)

Потрібні: [Docker](https://docs.docker.com/get-docker/) та [Docker Compose](https://docs.docker.com/compose/install/).

```bash
# Клонувати репозиторій (або перейти в каталог проєкту)
git clone <repo-url>
cd auction-backend

# Запустити контейнери (PostgreSQL + додаток)
docker compose up --build

# Сервіс доступний на http://localhost:8000
# Документація API: http://localhost:8000/docs
```

Зупинити та видалити контейнери:

```bash
docker compose down
```

Дані PostgreSQL зберігаються у volume `pgdata`. Щоб видалити і їх:

```bash
docker compose down -v
```

## Запуск локально (без Docker)

1. Python 3.11+, PostgreSQL.

2. Створити віртуальне середовище та встановити залежності:

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

3. Запустити PostgreSQL і створити БД `auction` (або використати існуючу).

4. Файл `.env` в корені проєкту:

```env
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/auction
```

5. Запуск сервера:

```bash
# З кореня проєкту (auction-backend)
set PYTHONPATH=%cd%   # Windows
# export PYTHONPATH=$(pwd)  # Linux/macOS
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Додаток: http://localhost:8000, документація: http://localhost:8000/docs.

## API

### REST

| Метод | Шлях | Опис |
|-------|------|------|
| `POST` | `/lots` | Створити лот (title, description, start_price) |
| `GET`  | `/lots` | Список активних лотів (status=running) |
| `GET`  | `/lots/{lot_id}` | Деталі лота (start_price, current_price) |
| `POST` | `/lots/{lot_id}/bids` | Зробити ставку (bidder, amount) |

### WebSocket

| Підключення | Опис |
|-------------|------|
| `GET /ws/lots/{lot_id}` | Підписка на події лота. Повідомлення: нові ставки та подовження часу. |

### Формат повідомлень WebSocket

Нова ставка (хто яку ставку зробив + стартова та поточна ціна лота):

```json
{
  "type": "bid_placed",
  "lot_id": 1,
  "bidder": "John",
  "amount": 105,
  "start_price": 100,
  "current_price": 105,
  "new_bid_display": "John поставив 105.00"
}
```

Подовження часу лота (після ставки):

```json
{
  "type": "time_extended",
  "lot_id": 1,
  "end_time": "2025-03-01T12:00:00+00:00"
}
```

## GitHub

Репозиторій: створити на GitHub та надати доступ користувачам **Sergeony** та **DimaSerebrich** (Collaborators або через організацію).

## Ліцензія

Див. файл [LICENSE](LICENSE).
