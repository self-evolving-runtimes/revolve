## Set up

Run the following commands to set up the project

```shell
brew install uv
uv sync
```

To run the project, create a `.env` with the `OPEN_AI_KEY` and use the `main` run configuration. 
Right now, it should print something like the code snippet printed below

To handle a GET request to fetch data about an account named "mahesh" from a PostgreSQL database using Python, you can use the `psycopg2` library. Below is a code snippet that demonstrates how to do this:

```python
import psycopg2
from psycopg2 import sql

def get_account_details(account_name):
    # Database connection parameters
    conn_params = {
        'dbname': 'your_database_name',
        'user': 'your_username',
        'password': 'your_password',
        'host': 'your_host',
        'port': 'your_port'
    }

    try:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(**conn_params)
        cursor = connection.cursor()

        # Query to fetch account details
        query = sql.SQL("SELECT * FROM accounts WHERE name = %s")
        
        # Execute the query
        cursor.execute(query, (account_name,))
        
        # Fetch the results
        account_details = cursor.fetchall()

        # Close the cursor and connection
        cursor.close()
        connection.close()

        return account_details

    except Exception as e:
        print(f"Error: {e}")
        return None

# Example usage
account_name = "mahesh"
account_data = get_account_details(account_name)

if account_data:
    for row in account_data:
        print(row)
else:
    print("No data found or error occurred.")
```

### Explanation:

1. **Database Connection**: Update the connection parameters (`dbname`, `user`, `password`, `host`, `port`) with your database credentials.

2. **SQL Query**: The query uses a parameterized SQL statement to prevent SQL injection.

3. **Fetching Data**: The `fetchall()` method retrieves all rows matching the query.

4. **Closing the Connection**: Ensure the connection is closed to free up resources.

Make sure you have the `psycopg2` library installed. You can install it using pip:

```bash
pip install psycopg2-binary
```

This code assumes there's a table named `accounts` with a column `name`. If the table doesn't exist, use the `Database Administrator Agent` to create it.
