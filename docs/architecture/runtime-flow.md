# Runtime Flow

The runtime stack is defined by `infra/docker-compose.yml` with a gateway, three workers, Redis, and Postgres.

- `gateway` receives ingress traffic and routes requests.
- `asr-worker`, `mt-worker`, and `soap-worker` process pipeline stages.
- `redis` provides queue/state transport.
- `postgres` stores session metadata created through migrations in `backend/alembic/versions`.
