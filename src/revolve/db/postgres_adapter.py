import datetime
import json
import os
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, List, Any

import psycopg2
import sqlparse
from psycopg2 import sql, errors

# Add parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from revolve.utils import log
from revolve.db.adapter import DatabaseAdapter, db_tool


class PostgresAdapter(DatabaseAdapter):
    def __init__(self):
        self.config = {
            "dbname": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT"),
        }

    def get_raw_schemas(self):
        schemas_raw = self.run_query_on_db("""
        SELECT jsonb_object_agg(
               table_name,
               columns
           ) AS schema_dict
    FROM (
        SELECT
            c.table_name,
            jsonb_agg(
                jsonb_strip_nulls(
                    jsonb_build_object(
                        'column_name', c.column_name,
                        'data_type', c.data_type,
                        'data_type_s',
                            CASE
                                WHEN def.column_default LIKE 'nextval(%' AND pt.typname = 'int4' THEN 'serial'
                                WHEN def.column_default LIKE 'nextval(%' AND pt.typname = 'int8' THEN 'bigserial'
                                WHEN c.data_type IN ('character varying', 'varchar') AND c.character_maximum_length IS NOT NULL
                                    THEN 'varchar(' || c.character_maximum_length || ')'
                                WHEN c.data_type = 'numeric' AND c.numeric_precision IS NOT NULL
                                    THEN 'numeric(' || c.numeric_precision ||
                                         COALESCE(', ' || c.numeric_scale, '') || ')'
                                ELSE c.data_type
                            END,
                        'is_nullable', c.is_nullable,
                        'character_max_length', c.character_maximum_length,
                        'numeric_precision', c.numeric_precision,
                        'numeric_scale', c.numeric_scale,
                        'enum_values', ev.enum_values,
                        'foreign_key', jsonb_build_object(
                            'foreign_table', ccu.table_name,
                            'foreign_column', ccu.column_name
                        ),
                        'default_value', def.column_default
                    )
                )
            ) AS columns
        FROM information_schema.columns c
        LEFT JOIN information_schema.key_column_usage kcu
            ON c.table_name = kcu.table_name
            AND c.column_name = kcu.column_name
            AND c.table_schema = kcu.table_schema
        LEFT JOIN information_schema.table_constraints tc
            ON kcu.constraint_name = tc.constraint_name
            AND tc.constraint_type = 'FOREIGN KEY'
        LEFT JOIN information_schema.constraint_column_usage ccu
            ON tc.constraint_name = ccu.constraint_name
        LEFT JOIN LATERAL (
            SELECT jsonb_agg(e.enumlabel) AS enum_values
            FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            JOIN pg_namespace ns ON ns.oid = t.typnamespace
            WHERE t.typname = c.udt_name
        ) ev ON true
        LEFT JOIN LATERAL (
            SELECT
                pg_get_expr(ad.adbin, ad.adrelid) AS column_default
            FROM pg_attribute a
            JOIN pg_class cls ON cls.oid = a.attrelid
            JOIN pg_attrdef ad ON ad.adrelid = a.attrelid AND ad.adnum = a.attnum
            WHERE cls.relname = c.table_name AND a.attname = c.column_name
            LIMIT 1
        ) def ON true
        LEFT JOIN pg_type pt ON pt.typname = c.udt_name
        WHERE c.table_schema NOT IN ('pg_catalog', 'information_schema')
        GROUP BY c.table_name
    ) AS sub;
    
        """)
        return schemas_raw


    def get_table_dependencies(self):
        query_result = self.run_query_on_db("""
            WITH fk_info AS (
            SELECT
                kcu.table_name AS from_table,
                kcu.column_name AS from_column,
                ccu.table_name AS to_table,
                ccu.column_name AS to_column,
                -- Check if from_column is unique or part of primary key
                EXISTS (
                    SELECT 1 FROM information_schema.table_constraints tc2
                    JOIN information_schema.key_column_usage kcu2
                      ON tc2.constraint_name = kcu2.constraint_name
                    WHERE tc2.table_name = kcu.table_name
                      AND kcu2.column_name = kcu.column_name
                      AND tc2.constraint_type IN ('PRIMARY KEY', 'UNIQUE')
                ) AS is_from_unique,
                -- Check if to_column is unique or primary
                EXISTS (
                    SELECT 1 FROM information_schema.table_constraints tc3
                    JOIN information_schema.key_column_usage kcu3
                      ON tc3.constraint_name = kcu3.constraint_name
                    WHERE tc3.table_name = ccu.table_name
                      AND kcu3.column_name = ccu.column_name
                      AND tc3.constraint_type IN ('PRIMARY KEY', 'UNIQUE')
                ) AS is_to_unique
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu
                ON tc.constraint_name = ccu.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema NOT IN ('pg_catalog', 'information_schema')
        )
        SELECT jsonb_object_agg(
            from_table,
            column_mappings
        ) AS fk_relationships
        FROM (
            SELECT
                from_table,
                jsonb_object_agg(
                    from_column,
                    jsonb_build_object(
                        'links_to_table', to_table,
                        'reltype',
                            CASE
                                WHEN is_from_unique AND is_to_unique THEN 'one-to-one'
                                WHEN NOT is_from_unique AND is_to_unique THEN 'many-to-one'
                                ELSE 'uncertain' -- fallback
                            END
                    )
                ) AS column_mappings
            FROM fk_info
            GROUP BY from_table
        ) AS rels;
    
        """)
        return query_result


    def get_schemas_from_db(self):
        schemas_raw = self.get_raw_schemas()
        dependencies_raw = self.get_table_dependencies()

        schemas = json.loads(schemas_raw)[0][0]
        dependencies = json.loads(dependencies_raw)[0][0] if json.loads(dependencies_raw)[0][0] is not None else {}

        for table, columns in schemas.items():
            dep_columns = dependencies.get(table, {})
            for column in columns:
                col_name = column.get("column_name")
                if col_name in dep_columns:
                    # Merge the reltype and links_to_table
                    column.update(dep_columns[col_name])

        return schemas

        query_result = self.run_query_on_db("""
    SELECT jsonb_object_agg(
               table_name,
               columns
           ) AS schema_dict
    FROM (
        SELECT
            c.table_name,
            jsonb_agg(
                jsonb_strip_nulls(
                    jsonb_build_object(
                        'column_name', c.column_name,
                        'data_type', c.data_type,
                        'data_type_s',
                            CASE
                                WHEN def.column_default LIKE 'nextval(%' AND pt.typname = 'int4' THEN 'serial'
                                WHEN def.column_default LIKE 'nextval(%' AND pt.typname = 'int8' THEN 'bigserial'
                                WHEN c.data_type IN ('character varying', 'varchar') AND c.character_maximum_length IS NOT NULL
                                    THEN 'varchar(' || c.character_maximum_length || ')'
                                WHEN c.data_type = 'numeric' AND c.numeric_precision IS NOT NULL
                                    THEN 'numeric(' || c.numeric_precision ||
                                         COALESCE(', ' || c.numeric_scale, '') || ')'
                                ELSE c.data_type
                            END,
                        'is_nullable', c.is_nullable,
                        'character_max_length', c.character_maximum_length,
                        'numeric_precision', c.numeric_precision,
                        'numeric_scale', c.numeric_scale,
                        'enum_values', ev.enum_values,
                        'foreign_key', jsonb_build_object(
                            'foreign_table', ccu.table_name,
                            'foreign_column', ccu.column_name
                        )
                    )
                )
            ) AS columns
        FROM information_schema.columns c
        LEFT JOIN information_schema.key_column_usage kcu
            ON c.table_name = kcu.table_name
            AND c.column_name = kcu.column_name
            AND c.table_schema = kcu.table_schema
        LEFT JOIN information_schema.table_constraints tc
            ON kcu.constraint_name = tc.constraint_name
            AND tc.constraint_type = 'FOREIGN KEY'
        LEFT JOIN information_schema.constraint_column_usage ccu
            ON tc.constraint_name = ccu.constraint_name
        LEFT JOIN LATERAL (
            SELECT jsonb_agg(e.enumlabel) AS enum_values
            FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            JOIN pg_namespace ns ON ns.oid = t.typnamespace
            WHERE t.typname = c.udt_name
        ) ev ON true
        LEFT JOIN LATERAL (
            SELECT
                pg_get_expr(ad.adbin, ad.adrelid) AS column_default
            FROM pg_attribute a
            JOIN pg_class cls ON cls.oid = a.attrelid
            JOIN pg_attrdef ad ON ad.adrelid = a.attrelid AND ad.adnum = a.attnum
            WHERE cls.relname = c.table_name AND a.attname = c.column_name
            LIMIT 1
        ) def ON true
        LEFT JOIN pg_type pt ON pt.typname = c.udt_name
        WHERE c.table_schema NOT IN ('pg_catalog', 'information_schema')
        GROUP BY c.table_name
    ) AS sub
    """)

        return query_result


    def order_tables_by_dependencies(self, dependencies: Dict[str, Any]) -> List[str]:
        # Extract child tables and all referenced parent tables
        child_tables = set(dependencies)
        referenced_parents = {
            info["links_to_table"]
            for links in dependencies.values()
            for info in links.values()
        }

        # Build dependency map: table -> list of tables it links to
        final_dependency_map = {
            table: [info["links_to_table"] for info in links.values()]
            for table, links in dependencies.items()
        }

        # Identify and remove tables that are only referenced and have no outgoing links
        for table in list(final_dependency_map):
            if table in referenced_parents and not final_dependency_map[table]:
                del final_dependency_map[table]

        tp_sorted = self.topological_sort(dependencies)

        return final_dependency_map, tp_sorted


    def topological_sort(self, dependencies: Dict[str, Any]) -> List[str]:
        graph = defaultdict(list)  # parent -> list of children
        in_degree = defaultdict(int)
        all_tables = set(dependencies)  # explicitly defined tables

        # Parse dependencies to construct graph and in-degrees
        for child, columns in dependencies.items():
            if isinstance(columns, dict):
                for col_info in columns.values():
                    if isinstance(col_info, dict) and "links_to_table" in col_info:
                        parent = col_info["links_to_table"]
                        graph[parent].append(child)
                        in_degree[child] += 1
                        all_tables.add(parent)  # include implicit parent tables

        # Start with all tables that have no incoming edges
        queue = deque([table for table in all_tables if in_degree[table] == 0])
        sorted_tables = []

        # Kahn’s Algorithm for topological sorting
        while queue:
            table = queue.popleft()
            sorted_tables.append(table)

            for dependent in graph[table]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # Detect cycles
        if len(sorted_tables) != len(all_tables):
            raise ValueError("Cycle detected in table dependencies.")

        return sorted_tables

    def get_tables(self) -> List[Dict[str, Any]]:
        raise RuntimeError("get_tables is not supported")

    @db_tool
    def run_query_on_db(self, query: str) -> str:
        """
        This function runs the given query on the postgres database.
        Args:
            query (str): The query to be run.
        """
        # log("run_query_on_db", f"Running query: {query}")
        try:
            conn = psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
            )
            cur = conn.cursor()
            cur.execute(query)
            # if cur.rowcount:
            result = cur.fetchall()
            # else:
            #     result = None
            conn.commit()
            cur.close()
            conn.close()

        except Exception as e:
            log(f"Error running query: {e}")
            return f"Error running query: {e}"

        return json.dumps(result, default=default_serializer)


    def check_db(
        self, db_name: str, db_user: str, db_password: str, db_host: str, db_port: str
    ) -> str:
        """
        This function tests the database connection.
        Args:
            db_name (str): The name of the database.
            db_user (str): The user of the database.
            db_password (str): The password of the database.
            db_host (str): The host of the database.
            db_port (str): The port of the database.
        """
        log("Testing database connection...")
        try:
            conn = psycopg2.connect(
                dbname=db_name,
                user=db_user,
                password=db_password,
                host=db_host,
                port=db_port,
            )
            conn.close()
        except Exception as e:
            log(f"Database connection failed: {e}", level="ERROR")
            return False

        return True


    def recreate_database_psycopg2(self, dbname, user, password, host, port):
        """Drop and recreate the target database using psycopg2."""
        conn = psycopg2.connect(
            dbname="postgres",  # connect to control DB
            user=user,
            password=password,
            host=host,
            port=port
        )
        conn.set_session(autocommit=True)
        with conn.cursor() as cur:
            try:
                cur.execute(f"DROP DATABASE IF EXISTS {dbname};")
                print(f"✅ Dropped database '{dbname}'")
            except Exception as e:
                print(f"⚠️ Failed to drop: {e}")
            try:
                cur.execute(f"CREATE DATABASE {dbname};")
                print(f"✅ Created database '{dbname}'")
            except Exception as e:
                print(f"❌ Failed to create database: {e}")
                raise
        conn.close()


    def restore_schema_with_psycopg2(
        self,
        dump_file,
        dbname,
        user,
        password,
        host="localhost",
        port=5432,
        recreate_db=False
    ):
        if recreate_db:
            self.recreate_database_psycopg2(self, dbname, user, password, host, port)

        with open(dump_file, "r") as f:
            raw_sql = f.read()

        statements = sqlparse.split(raw_sql)

        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        conn.set_session(autocommit=False)
        with conn.cursor() as cur:
            for stmt in statements:
                stmt = stmt.strip()
                if not stmt:
                    continue
                try:
                    cur.execute(stmt)
                except psycopg2.errors.DuplicateTable:
                    print("⚠️ Table already exists. Skipped.")
                    conn.rollback()
                except psycopg2.errors.DuplicateObject:
                    print("⚠️ Object already exists. Skipped.")
                    conn.rollback()
                except Exception as e:
                    print(f"❌ Error executing statement:\n{stmt[:200]}...\n{e}")
                    conn.rollback()
                else:
                    conn.commit()

        conn.close()
        print(f"✅ Schema restored to '{dbname}'")


    def generate_create_table_sql(self, table_name: str, columns: List[Dict]) -> str:
        col_lines = []
        enum_defs = []
        requires_uuid_ossp = False

        for col in columns:
            data_type = col["data_type_s"]
            column_name = col["column_name"]

            # Handle user-defined enums
            if data_type == "USER-DEFINED" and col.get("enum_values"):
                enum_type_name = f"{table_name}_{column_name}_enum"
                data_type = enum_type_name
                enum_vals = ', '.join(f"'{v}'" for v in col["enum_values"])
                enum_defs.append(
                    f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{enum_type_name}') "
                    f"THEN CREATE TYPE {enum_type_name} AS ENUM ({enum_vals}); END IF; END $$;"
                )

            elif data_type == "ARRAY":
                data_type = "text[]"  # Customize as needed

            # Build column line
            line = f"  {column_name} {data_type}"

            # Add default value if present (skip if serial type)
            default_value = col.get("default_value")
            if default_value and not (data_type.lower() == "serial" and "nextval" in default_value.lower()):
                if (
                    col["data_type_s"] == "USER-DEFINED"
                    and "::" in default_value
                    and col.get("enum_values")
                ):
                    # Replace generic cast with the correct enum type name
                    enum_type_name = f"{table_name}_{column_name}_enum"
                    default_value = default_value.split("::")[0] + f"::{enum_type_name}"
                line += f" DEFAULT {default_value}"
                if "uuid_generate_v4()" in default_value:
                    requires_uuid_ossp = True

            # Add NOT NULL constraint
            if col["is_nullable"] == "NO":
                line += " NOT NULL"

            col_lines.append(line)

        ddl_parts = []

        # Add CREATE EXTENSION if required
        if requires_uuid_ossp:
            ddl_parts.append('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

        # Add ENUM definitions if any
        ddl_parts.extend(enum_defs)

        # Final CREATE TABLE statement
        body = ",\n".join(col_lines)
        ddl_parts.append(f"CREATE TABLE {table_name} (\n{body}\n);")

        return "\n".join(ddl_parts)


    def gen_table_map(self, map : Dict) -> Dict:
        # Regenerate with fixed function
        fixed_create_table_ddls = {
            table_name: self.generate_create_table_sql(table_name, columns)
            for table_name, columns in map.items()
        }
        return fixed_create_table_ddls


    def create_database_if_not_exists(self, existing_dbname, new_dbname, user, password, host='localhost', port=5432):
        method = "create_database_if_not_exists"
        try:
            conn = psycopg2.connect(
                dbname=existing_dbname,
                user=user,
                password=password,
                host=host,
                port=port
            )
            conn.set_session(autocommit=True)
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (new_dbname,))
                if cur.fetchone():
                    log(f"ℹ️ Database '{new_dbname}' already exists.")
                else:
                    log(f"📦 Creating database '{new_dbname}' owned by '{user}'...")
                    cur.execute(
                        sql.SQL("CREATE DATABASE {} OWNER {}")
                        .format(sql.Identifier(new_dbname), sql.Identifier(user))
                    )
                    log(f"✅ Database '{new_dbname}' created.")
            conn.close()
        except Exception as e:
            raise RuntimeError(f"[{method}] ❌ Failed to create database '{new_dbname}': {e}")


    def apply_create_table_ddls(self, table_ddl_map, existing_dbname, new_dbname, user, password, host='localhost', port=5432, drop_if_exists=False):
        method = "apply_create_table_ddls"
        self.create_database_if_not_exists(existing_dbname, new_dbname, user, password, host, port)
        conn = psycopg2.connect(
            dbname=new_dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        conn.set_session(autocommit=False)

        with conn.cursor() as cur:
            for table, ddl in table_ddl_map.items():
                log(f"▶️ Creating table: {table}")
                try:
                    cur.execute(ddl)
                except errors.DuplicateTable:
                    log(f"⚠️ Table '{table}' already exists.")
                    conn.rollback()
                    if drop_if_exists:
                        try:
                            log(f"🔁 Dropping and recreating table '{table}'...")
                            cur.execute(sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(sql.Identifier(table)))
                            conn.commit()
                            cur.execute(ddl)
                            conn.commit()
                            log(f"✅ Recreated table: {table}")
                        except Exception as drop_err:
                            log(f"❌ Error recreating '{table}': {drop_err}")
                            conn.rollback()
                    else:
                        log(f"⏩ Skipping '{table}' (already exists)")
                except Exception as e:
                    log(f"❌ Error creating '{table}': {e}")
                    conn.rollback()
                else:
                    conn.commit()
                    log(f"✅ Created table: {table}")
        conn.close()


    def clone_db(self):
        ddls = self.get_schemas_from_db()
        tables = self.gen_table_map(ddls)

        new_dbname = os.getenv("DB_NAME") + "_test"
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT")

        self.apply_create_table_ddls(tables, os.getenv("DB_NAME"), new_dbname, user, password, host=host, port=port, drop_if_exists=True)
        os.environ["DB_NAME_TEST"] = new_dbname


    def extract_permissions(self, result_data):
        if not isinstance(result_data, list):
            raise ValueError("Expected result_data to be a list.")

        if not result_data:
            raise ValueError("result_data is an empty list.")

        last_element = result_data[-1]
        if not isinstance(last_element, list):
            raise ValueError("Expected last element of result_data to be a list.")

        if not last_element:
            raise ValueError("The last list inside result_data is empty.")

        last_dict = last_element[-1]
        if not isinstance(last_dict, dict):
            raise ValueError("Expected last element of the nested list to be a dict.")

        if not last_dict:
            raise ValueError("The final dictionary is empty.")

        return last_dict


    def check_permissions(self):
        db_user_name = os.getenv("DB_USER")
        query = f"""
    SELECT jsonb_build_object(
      'can_connect', has_database_privilege('postgres', current_database(), 'CONNECT'),
      'can_use_schema', has_schema_privilege('postgres', 'public', 'USAGE'),
      'can_create_db', rolcreatedb,
      'can_create_role', rolcreaterole,
      'is_superuser', rolsuper
    ) AS permissions
    FROM pg_roles
    WHERE rolname = '{db_user_name}';
    """
        result = self.run_query_on_db(query)
        result_data = json.loads(result)
        permissions = self.extract_permissions(result_data)

        suggested_queries_template ={
        'can_connect': "GRANT CONNECT ON DATABASE {database} TO {username};",
        'is_superuser': "ALTER ROLE {username} WITH SUPERUSER;",
        'can_create_db': "ALTER ROLE {username} WITH CREATEDB;",
        'can_use_schema': "GRANT USAGE ON SCHEMA public TO {username};",
        'can_create_role': "ALTER ROLE {username} WITH CREATEROLE;",
        }
        suggested_queries = {}
        for key, value in permissions.items():
            if value is False:
                suggested_queries[key] = suggested_queries_template[key].format(database=os.getenv("DB_NAME"), username=db_user_name)

        if all(value == True for value in permissions.values()):
            return {
                "status": "success",
                "permissions": permissions,
                "message": "All required permissions are already granted. "
            }
        else:
            suggested_queries_str = "\n".join([f"{key}: {value}" for key, value in suggested_queries.items()])
            return {
                "status": "error",
                "permissions": permissions,
                "error": f"You do not have the necessary permissions to perform this operation. You can use the following "
                         f"SQL statements to grant the required permissions:<pre style={{ whiteSpace: 'pre-wrap', "
                         f"background: '#f6f8fa', padding: 10, borderRadius: 4 }}>{suggested_queries_str}</pre>",
            }


def default_serializer(obj):
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    return obj