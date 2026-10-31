/**
 * Script: runner.js
 * Description: Cross-platform Node.js runner for database setup, migrations, seeds, and verification tests.
 * Scope: Brightloop SMS Database Layer - Member 3
 */

const fs = require('fs');
const path = require('path');
const { Client } = require('pg');

const config = {
  host: process.env.PGHOST || 'localhost',
  port: parseInt(process.env.PGPORT || '5432', 10),
  user: process.env.PGUSER || 'postgres',
  password: process.env.PGPASSWORD || 'postgres',
  database: process.env.PGDATABASE || 'brightloop_sms',
};

const migrationsDir = path.join(__dirname, '..', 'migrations');
const seedsDir = path.join(__dirname, '..', 'seeds');
const verifySqlPath = path.join(__dirname, 'verify_tests.sql');

async function getClient(targetDb = config.database) {
  const client = new Client({
    host: config.host,
    port: config.port,
    user: config.user,
    password: config.password,
    database: targetDb,
  });
  await client.connect();
  return client;
}

async function ensureDatabaseExists() {
  const adminClient = await getClient('postgres');
  try {
    const res = await adminClient.query(
      `SELECT 1 FROM pg_database WHERE datname = $1`,
      [config.database]
    );
    if (res.rowCount === 0) {
      console.log(`[INFO] Creating database "${config.database}"...`);
      await adminClient.query(`CREATE DATABASE "${config.database}"`);
      console.log(`[INFO] Database "${config.database}" created.`);
    } else {
      console.log(`[INFO] Database "${config.database}" exists.`);
    }
  } finally {
    await adminClient.end();
  }
}

async function runMigrations(client) {
  console.log('\n--- Running Migrations (001-008) ---');
  const files = fs
    .readdirSync(migrationsDir)
    .filter((f) => f.endsWith('.sql'))
    .sort();

  for (const file of files) {
    const filePath = path.join(migrationsDir, file);
    const sql = fs.readFileSync(filePath, 'utf-8');
    console.log(`Executing migration: ${file}...`);
    await client.query(sql);
    console.log(`  -> Completed ${file}`);
  }
}

async function runSeeds(client) {
  console.log('\n--- Running Seed Data ---');
  const seedFile = path.join(seedsDir, '001_seed_data.sql');
  const sql = fs.readFileSync(seedFile, 'utf-8');
  console.log(`Executing seed file: 001_seed_data.sql...`);
  await client.query(sql);
  console.log('  -> Seed data populated successfully.');
}

async function runVerificationTests(client) {
  console.log('\n--- Running Automated Verification Tests ---');
  const sql = fs.readFileSync(verifySqlPath, 'utf-8');
  await client.query(sql);
  console.log('  -> All verification tests executed.');
}

async function main() {
  const command = process.argv[2] || 'setup';

  console.log('========================================================');
  console.log(` Brightloop SMS Database Runner (Command: ${command})`);
  console.log(` Target: ${config.database} on ${config.host}:${config.port}`);
  console.log('========================================================');

  try {
    if (command === 'setup' || command === 'migrate') {
      await ensureDatabaseExists();
    }

    const client = await getClient();

    try {
      if (command === 'setup') {
        await runMigrations(client);
        await runSeeds(client);
        await runVerificationTests(client);
      } else if (command === 'migrate') {
        await runMigrations(client);
      } else if (command === 'seed') {
        await runSeeds(client);
      } else if (command === 'test') {
        await runVerificationTests(client);
      } else {
        console.error(`Unknown command "${command}". Available: setup, migrate, seed, test`);
        process.exit(1);
      }
      console.log('\n========================================================');
      console.log(' EXECUTION COMPLETED SUCCESSFULLY!');
      console.log('========================================================');
    } finally {
      await client.end();
    }
  } catch (err) {
    console.error('\n[ERROR] Execution failed:', err.message);
    process.exit(1);
  }
}

main();
