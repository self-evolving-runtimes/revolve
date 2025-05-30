from typing import Dict, Any, List
from abc import ABC
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os
import json

from revolve.db.adapter import db_tool


class MongodbAdapter(ABC):
    """
    MongoDB adapter for interacting with MongoDB databases.
    Implements methods for schema retrieval, dependency management, and CRUD operations.
    """

    def __init__(self):
        self.client = MongoClient(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 27017)),
            username=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
        )
        self.db_name = os.getenv("DB_NAME")
        self.db = self.client[self.db_name]

    def get_raw_schemas(self):
        """
        Retrieve raw schema information from MongoDB collections.
        """
        collections = self.db.list_collection_names()
        schemas = {}
        for collection in collections:
            sample_doc = self.db[collection].find_one()
            if sample_doc:
                schemas[collection] = {key: type(value).__name__ for key, value in sample_doc.items()}
        return schemas

    def get_table_dependencies(self):
        """
        MongoDB does not enforce foreign key relationships, so this method will return an empty dependency map.
        """
        return {}

    def get_schemas_from_db(self):
        """
        Fetch processed schema information from MongoDB.
        """
        return self.get_raw_schemas()

    def order_tables_by_dependencies(self, dependencies: Dict[str, Any]) -> List[str]:
        """
        Since MongoDB does not enforce table dependencies, return collections in alphabetical order.
        """
        return sorted(dependencies.keys())

    def topological_sort(self, dependencies: Dict[str, Any]) -> List[str]:
        """
        MongoDB does not enforce table dependencies, so return collections in alphabetical order.
        """
        return sorted(dependencies.keys())

    @db_tool
    def get_tables(self) -> List[Dict[str, Any]]:
        """
        Retrieve the collections  and their info in the MongoDB database.
        """
        return list(self.db.list_collections())

    def run_query_on_db(self, query: str) -> str:
        """
        Execute a query on a MongoDB collection.
        Args:
            query (Dict): A dictionary containing the collection name and query parameters.
        """
        raise RuntimeError("run_query_on_db is not supported")

    def check_db(self, db_name: str, db_user: str, db_password: str, db_host: str, db_port: str) -> bool:
        """
        Check the connection to the MongoDB database.
        """
        try:
            self.client.admin.command("ping")
            return True
        except ConnectionFailure:
            return False

    def recreate_database(self, dbname: str):
        """
        MongoDB does not support dropping and recreating databases directly.
        This method will drop all collections in the database.
        """
        self.client.drop_database(dbname)
        self.db = self.client[dbname]

    def restore_schema(self, schema: Dict):
        """
        Restore a schema to MongoDB by creating collections and inserting sample documents.
        """
        for collection_name, sample_doc in schema.items():
            self.db[collection_name].insert_one(sample_doc)

    def generate_create_table_sql(self, table_name: str, columns: List[Dict]) -> str:
        """
        MongoDB does not use SQL, so this method will return a JSON schema for the collection.
        """
        schema = {col["column_name"]: col["data_type"] for col in columns}
        return json.dumps(schema, indent=4)

    def gen_table_map(self, map: Dict) -> Dict:
        """
        Generate a mapping of MongoDB collections and their schemas.
        """
        return {collection: self.generate_create_table_sql(collection, schema) for collection, schema in map.items()}

    def create_database_if_not_exists(self, existing_dbname, new_dbname, user, password, host='localhost', port=27017):
        """
        MongoDB automatically creates databases when a collection is created, so this method is a no-op.
        """
        pass

    def clone_db(self):
        """
        Clone an existing MongoDB database by copying all collections and documents.
        """
        new_dbname = f"{self.db_name}_test"
        self.client.drop_database(new_dbname) 
        new_db = self.client[new_dbname] # Drop the new database if it exists
        for collection_name in self.db.list_collection_names():
            documents = list(self.db[collection_name].find())
            if documents:
                new_db[collection_name].insert_many(documents)
        os.environ["DB_NAME_TEST"] = new_dbname

    def extract_permissions(self, result_data):
        """
        MongoDB permissions are managed at the user level. This method will return a placeholder.
        """
        return {"permissions": "MongoDB permissions are managed at the user level."}

    def check_permissions(self):
        """
        Check user permissions in MongoDB.
        """
        try:
            self.client.admin.command("usersInfo")
            return {"status": "success", "message": "User has necessary permissions."}
        except Exception as e:
            return {"status": "error", "message": str(e)}