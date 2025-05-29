from typing import Dict, Any, List
from abc import ABC, abstractmethod

class DatabaseAdapter(ABC):
    @abstractmethod
    def get_raw_schemas(self):
        pass

    @abstractmethod
    def get_table_dependencies(self):
        pass

    @abstractmethod
    def get_schemas_from_db(self):
        pass
    @abstractmethod
    def order_tables_by_dependencies(self, dependencies: Dict[str, Any]) -> List[str]:
        pass

    @abstractmethod
    def topological_sort(self, dependencies: Dict[str, Any]) -> List[str]:
        pass

    @abstractmethod
    def run_query_on_db(self, query: str) -> str:
        pass

    @abstractmethod
    def check_db(
            self, db_name: str, db_user: str, db_password: str, db_host: str, db_port: str
    ) -> str:
        pass

    @abstractmethod
    def recreate_database_psycopg2(self, dbname, user, password, host, port):
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
        pass

    @abstractmethod
    def generate_create_table_sql(self, table_name: str, columns: List[Dict]) -> str:
        pass

    @abstractmethod
    def gen_table_map(self, map: Dict) -> Dict:
        pass

    @abstractmethod
    def create_database_if_not_exists(self, existing_dbname, new_dbname, user, password, host='localhost', port=5432):
        pass

    @abstractmethod
    def clone_db(self):
        pass

    @abstractmethod
    def extract_permissions(self, result_data):
        pass

    @abstractmethod
    def check_permissions(self):
        pass