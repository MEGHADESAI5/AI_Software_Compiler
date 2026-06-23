import json
from typing import Dict, List, Tuple, Set
from config import client

class RepairEngine:
    """
    Validates and surgically repairs inconsistencies across DB, API, UI, and Auth schemas.
    """
    
    def __init__(self, db_schema: dict, api_schema: dict, ui_schema: dict, auth_schema: dict):
        self.db = db_schema
        self.api = api_schema
        self.ui = ui_schema
        self.auth = auth_schema
        self.errors = []
        self.repairs_made = []
        # Track which fields have been added to which table to avoid duplicates
        self._added_fields = {}  # table_name -> set(field_names)
    
    def validate_all(self) -> Tuple[bool, List[str]]:
        """
        Runs all validation checks and returns (is_valid, list_of_errors)
        """
        self.errors = []
        self._check_db_has_tables()
        self._check_api_endpoints_have_auth()
        self._check_api_fields_exist_in_db()
        self._check_ui_components_map_to_api()
        self._check_roles_have_permissions()
        return len(self.errors) == 0, self.errors
    
    def _check_db_has_tables(self):
        """Ensures database has at least one table."""
        if not self.db.get("tables") or len(self.db["tables"]) == 0:
            self.errors.append("❌ Database has no tables defined.")
            # Repair: Add default users table
            self.db["tables"] = [{
                "name": "users",
                "columns": [
                    {"name": "id", "type": "uuid", "required": True},
                    {"name": "email", "type": "string", "required": True},
                    {"name": "name", "type": "string", "required": False}
                ]
            }]
            self.repairs_made.append("✅ Added default 'users' table")
        else:
            # Ensure each table has at least an 'id' column
            for table in self.db["tables"]:
                if not any(col.get("name") == "id" for col in table.get("columns", [])):
                    table["columns"].insert(0, {"name": "id", "type": "uuid", "required": True})
                    self.repairs_made.append(f"✅ Added 'id' column to table '{table.get('name')}'")
    
    def _check_api_endpoints_have_auth(self):
        """Ensures every API endpoint has auth_required defined."""
        for endpoint in self.api.get("endpoints", []):
            if "auth_required" not in endpoint:
                endpoint["auth_required"] = True
                self.repairs_made.append(f"✅ Added auth_required=True to {endpoint.get('path', 'unknown')}")
    
    def _check_api_fields_exist_in_db(self):
        """
        Ensures fields in API response_schema exist in DB tables.
        If a field is missing, adds it to the first table (or the most relevant one).
        Prevents duplicate additions.
        """
        # First, collect all missing fields across all endpoints
        missing_fields = set()
        for endpoint in self.api.get("endpoints", []):
            response = endpoint.get("response_schema", {})
            # Look for field names in the response
            if response.get("type") == "array":
                items = response.get("items", {})
                if items.get("type") == "object":
                    for prop in items.get("properties", {}).keys():
                        if prop != "id":
                            missing_fields.add(prop)
            elif response.get("type") == "object":
                for prop in response.get("properties", {}).keys():
                    if prop != "id":
                        missing_fields.add(prop)
        
        if not missing_fields:
            return
        
        # Get the first table (or create one if none)
        if not self.db.get("tables") or len(self.db["tables"]) == 0:
            self.db["tables"] = [{
                "name": "default",
                "columns": []
            }]
            self.repairs_made.append("✅ Created default table for missing fields")
        
        target_table = self.db["tables"][0]
        table_name = target_table.get("name", "default")
        
        # Initialize tracking set for this table
        if table_name not in self._added_fields:
            self._added_fields[table_name] = set()
        
        # Get existing column names
        existing_columns = {col.get("name") for col in target_table.get("columns", [])}
        
        # Add only fields that are not already present
        for field in missing_fields:
            if field not in existing_columns and field not in self._added_fields[table_name]:
                target_table["columns"].append({
                    "name": field,
                    "type": "string",
                    "required": False
                })
                self._added_fields[table_name].add(field)
                self.repairs_made.append(f"✅ Added missing DB field '{field}'")
            elif field in existing_columns:
                # Already exists, no repair needed
                pass
            else:
                # Already added in this repair cycle
                pass
    
    def _check_ui_components_map_to_api(self):
        """
        Ensures UI components correspond to actual API endpoints.
        If a page references a component that needs data, ensures the API exists.
        """
        api_paths = [e.get("path") for e in self.api.get("endpoints", [])]
        
        # Common mappings: component name -> API path
        component_to_api = {
            "DataTable": "/api/data",
            "ContactTable": "/api/contacts",
            "UserTable": "/api/users",
            "StatsCards": "/api/stats",
            "RecentActivity": "/api/activity",
            "Dashboard": "/api/dashboard",
        }
        
        for page in self.ui.get("pages", []):
            for component in page.get("components", []):
                if component in component_to_api:
                    needed_api = component_to_api[component]
                    if needed_api not in api_paths:
                        # Repair: Add the missing API endpoint
                        self.api["endpoints"].append({
                            "path": needed_api,
                            "method": "GET",
                            "auth_required": True,
                            "response_schema": {"type": "object", "properties": {"status": {"type": "string"}}}
                        })
                        self.repairs_made.append(f"✅ Added missing API endpoint '{needed_api}' for UI component '{component}'")
    
    def _check_roles_have_permissions(self):
        """Ensures every role has at least one permission."""
        for role in self.auth.get("roles", []):
            if not role.get("permissions") or len(role["permissions"]) == 0:
                role["permissions"] = ["view_profile"]
                self.repairs_made.append(f"✅ Added default 'view_profile' permission to role '{role.get('name', 'unknown')}'")
    
    def get_repair_summary(self) -> Dict:
        """Returns a summary of all repairs made."""
        return {
            "repairs_made": self.repairs_made,
            "repair_count": len(self.repairs_made),
            "is_valid": len(self.errors) == 0
        }


def validate_and_repair(db: dict, api: dict, ui: dict, auth: dict) -> Tuple[dict, dict, dict, dict, List[str]]:
    """
    Convenience function: validates and repairs all schemas.
    Returns: (repaired_db, repaired_api, repaired_ui, repaired_auth, repair_log)
    """
    engine = RepairEngine(db, api, ui, auth)
    is_valid, errors = engine.validate_all()
    
    print("\n🔧 Repair Engine Report:")
    if errors:
        print(f"   ⚠️  Found {len(errors)} issues:")
        for error in errors:
            print(f"      - {error}")
    else:
        print("   ✅ No issues found!")
    
    if engine.repairs_made:
        print(f"   🔧 Made {len(engine.repairs_made)} repair(s):")
        for repair in engine.repairs_made:
            print(f"      - {repair}")
    else:
        print("   ✅ No repairs needed.")
    
    return engine.db, engine.api, engine.ui, engine.auth, engine.repairs_made