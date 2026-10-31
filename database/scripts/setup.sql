-- Script: setup.sql
-- Description: Master runner executing all migrations (001-008) and seed data in transactional order
-- Scope: Brightloop SMS Database Setup (PostgreSQL 15+)

\echo '====================================================='
\echo '  Brightloop Software: Subscription Management System'
\echo '  Executing Database Setup (Migrations 001-008 & Seeds)'
\echo '====================================================='

\set ON_ERROR_STOP on

\echo '[1/9] Running 001_extensions_and_enums.sql...'
\ir ../migrations/001_extensions_and_enums.sql

\echo '[2/9] Running 002_account_tables.sql...'
\ir ../migrations/002_account_tables.sql

\echo '[3/9] Running 003_catalog_tables.sql...'
\ir ../migrations/003_catalog_tables.sql

\echo '[4/9] Running 004_sales_tables.sql...'
\ir ../migrations/004_sales_tables.sql

\echo '[5/9] Running 005_billing_tables.sql...'
\ir ../migrations/005_billing_tables.sql

\echo '[6/9] Running 006_integrity_triggers.sql...'
\ir ../migrations/006_integrity_triggers.sql

\echo '[7/9] Running 007_performance_indexes_views.sql...'
\ir ../migrations/007_performance_indexes_views.sql

\echo '[8/9] Running 008_audit_log.sql...'
\ir ../migrations/008_audit_log.sql

\echo '[9/9] Running 001_seed_data.sql...'
\ir ../seeds/001_seed_data.sql

\echo '====================================================='
\echo '  DATABASE SETUP & SEEDING COMPLETED SUCCESSFULLY!   '
\echo '====================================================='
