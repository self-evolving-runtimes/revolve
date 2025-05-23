import unittest
from revolve.functions import *


class MyTestCase(unittest.TestCase):
    def test_dependency_1(self):
        d_map = {"users": {}, "alerts": {"device_id": {"reltype": "many-to-one", "links_to_table": "devices"}},
                 "orders": {"payment_id": {"reltype": "one-to-one", "links_to_table": "payments"},
                            "customer_id": {"reltype": "many-to-one", "links_to_table": "customers"}}, "courses": {},
                 "devices": {"assigned_to": {"reltype": "many-to-one", "links_to_table": "employees"}}, "regions": {},
                 "feedback": {"order_id": {"reltype": "many-to-one", "links_to_table": "orders"},
                              "customer_id": {"reltype": "many-to-one", "links_to_table": "customers"}}, "patients": {},
                 "payments": {"transaction_id": {"reltype": "many-to-one", "links_to_table": "transactions"}},
                 "products": {"category_id": {"reltype": "many-to-one", "links_to_table": "categories"},
                              "supplier_id": {"reltype": "many-to-one", "links_to_table": "suppliers"}}, "settings": {},
                 "students": {}, "customers": {"referrer_id": {"reltype": "many-to-one", "links_to_table": "users"}},
                 "employees": {"department_id": {"reltype": "many-to-one", "links_to_table": "departments"}},
                 "inventory": {"product_id": {"reltype": "one-to-one", "links_to_table": "products"},
                               "warehouse_id": {"reltype": "many-to-one", "links_to_table": "warehouses"}},
                 "suppliers": {"region_id": {"reltype": "many-to-one", "links_to_table": "regions"}}, "categories": {},
                 "warehouses": {"region_id": {"reltype": "many-to-one", "links_to_table": "regions"}},
                 "audit_trail": {"user_id": {"reltype": "many-to-one", "links_to_table": "users"}}, "departments": {},
                 "device_logs": {"user_id": {"reltype": "many-to-one", "links_to_table": "users"},
                                 "device_id": {"reltype": "many-to-one", "links_to_table": "devices"}},
                 "enrollments": {"course_id": {"reltype": "many-to-one", "links_to_table": "courses"},
                                 "student_id": {"reltype": "many-to-one", "links_to_table": "students"}},
                 "order_items": {"order_id": {"reltype": "many-to-one", "links_to_table": "orders"},
                                 "product_id": {"reltype": "many-to-one", "links_to_table": "products"}},
                 "appointments": {"doctor_id": {"reltype": "many-to-one", "links_to_table": "employees"},
                                  "patient_id": {"reltype": "many-to-one", "links_to_table": "patients"}},
                 "transactions": {"processor_id": {"reltype": "many-to-one", "links_to_table": "payment_processors"}},
                 "payment_processors": {}}
        # d_map = {"users": {}, "courses": {}, "regions": {}, "patients": {}, "students": {}, "customers": {}, "employees": {}, "categories": {}, "departments": {}, "payment_processors": {}}
        d_map, _ = order_tables_by_dependencies(d_map)
        print(d_map)

        self.assertEqual(18, len(d_map.keys()))
        self.assertEqual("devices", d_map["alerts"][0])


if __name__ == '__main__':
    unittest.main()
