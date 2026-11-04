# Testing

Run the unit and frontend commands listed in the README first. They do not require a running MySQL server.

For MySQL checks, create a private JSON connection file outside the repository containing `host`, `port`, `user`, and `password` for a test administrator. Omit `database`. The account must be allowed to create and drop disposable databases and create tables/triggers. Never use a production server.

```powershell
$env:MYSQL_TEST_ADMIN_CONFIG = 'C:\private\mysql-test-admin.json'
.\.venv\Scripts\python.exe tests/test_mysql.py
.\.venv\Scripts\python.exe tests/test_order_api.py
```

Each script creates a uniquely named `groupcart_*_test_...` database and drops that database in cleanup. Neither script imports into the application database. The first checks triggers, totals and rollback; the second checks checkout grouping, order queries, seller search scope and item-removal permissions.
