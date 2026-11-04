# Database setup

`database/seed.sql` is a portable SQL script, not a live database file. It is the original schema and sample dataset, with only the filename changed. It creates `ecommerceplatform` with seven tables: customer, vendor, product, tag, producttag, transaction and transactionitem, together with the original triggers.

After import, MySQL stores actual records inside its configured data directory. New purchases update MySQL; they do not rewrite this SQL file. Each person running the project has a separate database instance and connection configuration.

## Application account

Import the script as an administrator first. Then create a dedicated application account in MySQL Workbench, replacing the example password:

```sql
CREATE USER 'groupcart_app'@'127.0.0.1' IDENTIFIED BY 'REPLACE_WITH_A_NEW_PASSWORD';
GRANT SELECT, INSERT, UPDATE, DELETE ON ecommerceplatform.* TO 'groupcart_app'@'127.0.0.1';
```

Set matching values in `app/db_config.json`. If your MySQL installation resolves local clients as `localhost`, create/grant the account for that host instead. Use the host shown by MySQL in an access-denied error. A different configured port is supported by the JSON `port` field.

## Different database name

Before the first import, change both `CREATE DATABASE ecommerceplatform;` and `USE ecommerceplatform;` at the top of your copy of the script, then change the `database` connection setting and account grant to match. Do not change the table definitions or trigger bodies merely to rename the database.

## Troubleshooting

- Connection refused: confirm MySQL is running and check the configured host/port.
- Access denied: verify the MySQL account, password and allowed host. Website account passwords are unrelated.
- Unknown database: import the SQL on the same MySQL instance/port configured for the app.
- Database already exists: stop and inspect it; do not drop an existing database just to bypass this message.
- Trigger import errors: use an importing account with trigger privileges; consult your MySQL administrator if binary-logging restrictions apply.

The previous developer-only `comp7640_test` instance, local startup scripts and machine-specific passwords are intentionally absent from this distribution. No database server is bundled. Install MySQL separately.
