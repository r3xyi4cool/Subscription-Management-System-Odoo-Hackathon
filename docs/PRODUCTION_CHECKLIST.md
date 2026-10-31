# Brightloop SMS - Future Production Deployment Checklist

This checklist documents requirements and architectural considerations for deploying Brightloop SMS beyond local development.

---

## 1. Database Infrastructure
- [ ] Provision a managed PostgreSQL instance (version 15 or higher).
- [ ] Update `DATABASE_URL` in `.env`:
  ```env
  DATABASE_URL=postgresql://<db_user>:<db_password>@<db_host>:5432/<db_name>
  ```
- [ ] Install production driver: `pip install psycopg2-binary`.
- [ ] Execute database migrations: `flask --app backend.run:app db upgrade`.
- [ ] Enable automated daily snapshots and write-ahead log (WAL) archiving.

---

## 2. Secrets & Security Hardening
- [ ] Generate cryptographically secure keys for production:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- [ ] Set `SECRET_KEY` and `JWT_SECRET_KEY` in production environment variables.
- [ ] Configure `CORS_ORIGINS` to accept only the official production domain (disallowing localhost).
- [ ] Enforce HTTPS termination and enable HSTS, Secure cookies, and strict Content-Security-Policy headers.

---

## 3. Email & Notification Delivery
- [ ] Switch `MAIL_BACKEND` from `dev` to `smtp` or integrate a dedicated transactional mail API (SendGrid, Postmark, AWS SES).
- [ ] Configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, and `MAIL_DEFAULT_SENDER`.
- [ ] Verify DNS records (SPF, DKIM, and DMARC) for the sending domain.

---

## 4. Application Server & Background Worker
- [ ] Run Flask behind a production WSGI server (e.g. Gunicorn / Uvicorn with Gevent or multiprocessing).
- [ ] Configure systemd service units or supervisor daemons for:
  1. The API application server.
  2. The background worker (`python -m backend.app.worker --interval 300`).
- [ ] Verify single-instance lock `.worker.lock` to ensure multiple worker containers do not create duplicate billing cycles.

---

## 5. Frontend Production Serving
- [ ] Build production assets: `npm --prefix frontend run build`.
- [ ] Serve `frontend/dist/` through a high-performance static server (Nginx, Caddy, or Cloud CDN).
- [ ] Ensure single-page application (SPA) routing fallback: redirect all unmatched paths to `/index.html`.
