import pandas as pd
import importlib

class Routes:
    def configure(self, app):
        df = pd.read_csv('src/revolve/registered_routes.csv')

        for _, row in df.iterrows():
            path = row['path']
            class_name = row['class_name']
            module_name = row.get('module', 'services') 

            module = importlib.import_module( f"services.{module_name}")
            cls = getattr(module, class_name)

            app.add_route(path, cls())

        return app