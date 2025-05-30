from typing import Dict, Any, List
from abc import ABC, abstractmethod


def db_tool(fn):
    """Marks a method to be included for tools."""
    fn._db_tool = True
    return fn


class DatabaseAdapter(ABC):
    """
    Abstract base class for database adapters. This class defines methods for interacting with databases
    and generating SQL code, which can be extended to support multiple SQL dialects.
    """

    @abstractmethod
    def get_raw_schemas(self):
        """
        Retrieve raw schema information from the database.
        This method can be used to extract schema details for generating SQL code for other dialects.
        """
        pass

    @abstractmethod
    def get_table_dependencies(self):
        """
        Retrieve table dependencies from the database.
        Useful for generating SQL code that respects table relationships in other dialects.
        """
        pass

    @abstractmethod
    def get_schemas_from_db(self):
        """
        Fetch processed schema information from the database.
        This can be used to generate dialect-specific schema definitions.
        """
        pass

    @abstractmethod
    def order_tables_by_dependencies(self, dependencies: Dict[str, Any]) -> List[str]:
        """
        Order tables based on their dependencies.
        This ensures that SQL code for creating tables is generated in the correct order for other dialects.
        """
        pass

    @abstractmethod
    def topological_sort(self, dependencies: Dict[str, Any]) -> List[str]:
        """
        Perform a topological sort on table dependencies.
        This is essential for generating SQL scripts that respect dependency order in other dialects.
        """
        pass

    @abstractmethod
    def get_tables(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def run_query_on_db(self, query: str) -> str:
        """
        Execute a raw SQL query on the database.
        This method can be used to test or validate SQL code generated for other dialects.
        """
        pass

    @abstractmethod
    def check_db(
            self, db_name: str, db_user: str, db_password: str, db_host: str, db_port: str
    ) -> str:
        """
        Check the connection to the database.
        This can be used to validate database configurations for different SQL dialects.
        """
        pass

    @abstractmethod
    def recreate_database_psycopg2(self, dbname, user, password, host, port):
        """
        Recreate a database using psycopg2.
        This method can be adapted to generate equivalent commands for other SQL dialects.
        """
        pass

    @abstractmethod
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
        """
        Restore a database schema from a dump file using psycopg2.
        This can be extended to generate restore commands for other SQL dialects.
        """
        pass

    @abstractmethod
    def generate_create_table_sql(self, table_name: str, columns: List[Dict]) -> str:
        """
        Generate a CREATE TABLE SQL statement for the given table and columns.
        This method can be used to produce dialect-specific SQL code.
        """
        pass

    @abstractmethod
    def gen_table_map(self, map: Dict) -> Dict:
        """
        Generate a mapping of table relationships.
        This can be used to create SQL scripts that respect relationships in other dialects.
        """
        pass

    @abstractmethod
    def create_database_if_not_exists(self, existing_dbname, new_dbname, user, password, host='localhost', port=5432):
        """
        Create a database if it does not already exist.
        This can be adapted to generate equivalent SQL commands for other dialects.
        """
        pass

    @abstractmethod
    def clone_db(self):
        """
        Clone an existing database.
        This method can be extended to generate SQL commands for cloning databases in other dialects.
        """
        pass

    @abstractmethod
    def extract_permissions(self, result_data):
        """
        Extract permissions from the database.
        This can be used to generate SQL code for setting permissions in other dialects.
        """
        pass

    @abstractmethod
    def check_permissions(self):
        """
        Check user permissions in the database.
        This can be used to validate or generate permission-related SQL code for other dialects.
        """
        pass