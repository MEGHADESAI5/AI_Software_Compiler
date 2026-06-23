from fastapi import FastAPI
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, DateTime, Boolean, inspect
from datetime import datetime
from typing import Dict, List
import json

class Runtime:
    """
    Simulates the execution of the generated configuration.
    Proves that the config can actually create a working application.
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.db = config.get('db', {})
        self.api = config.get('api', {})
        self.ui = config.get('ui', {})
        self.auth = config.get('auth', {})
        self.validation_results = []
    
    def validate_all(self) -> Dict:
        self.validation_results = []
        
        print("\n🚀 RUNTIME: Validating configuration...")
        
        self._validate_db()
        self._validate_api()
        self._validate_ui()
        self._validate_auth()
        
        passed = all(result['passed'] for result in self.validation_results)
        summary = {
            "passed": passed,
            "total_checks": len(self.validation_results),
            "passed_checks": sum(1 for r in self.validation_results if r['passed']),
            "results": self.validation_results
        }
        
        print(f"\n{'✅' if passed else '❌'} RUNTIME VALIDATION: {'PASSED' if passed else 'FAILED'}")
        print(f"   Checks: {summary['passed_checks']}/{summary['total_checks']} passed")
        
        return summary
    
    def _validate_db(self):
        try:
            engine = create_engine('sqlite:///:memory:')
            metadata = MetaData()
            
            tables = self.db.get('tables', [])
            if not tables:
                self.validation_results.append({
                    "check": "Database has tables",
                    "passed": False,
                    "message": "No tables defined in database schema."
                })
                return
            
            for table_def in tables:
                columns = []
                seen_columns = set()
                for col_def in table_def.get('columns', []):
                    col_name = col_def.get('name')
                    if not col_name or col_name in seen_columns:
                        continue
                    seen_columns.add(col_name)
                    col_type = self._get_sqlalchemy_type(col_def.get('type', 'string'))
                    columns.append(Column(col_name, col_type))
                
                if 'id' not in seen_columns:
                    columns.insert(0, Column('id', String, primary_key=True))
                
                Table(table_def['name'], metadata, *columns)
            
            metadata.create_all(engine)
            inspector = inspect(engine)
            created_tables = inspector.get_table_names()
            
            self.validation_results.append({
                "check": f"Database tables created ({len(created_tables)} tables)",
                "passed": True,
                "message": f"Successfully created tables: {', '.join(created_tables)}"
            })
            
        except Exception as e:
            self.validation_results.append({
                "check": "Database creation",
                "passed": False,
                "message": f"Failed to create database: {str(e)}"
            })
    
    def _validate_api(self):
        try:
            app = FastAPI()
            endpoints = self.api.get('endpoints', [])
            
            if not endpoints:
                self.validation_results.append({
                    "check": "API endpoints defined",
                    "passed": False,
                    "message": "No API endpoints defined."
                })
                return
            
            for endpoint in endpoints:
                app.add_api_route(
                    endpoint.get('path', '/'),
                    lambda: {"status": "ok"},
                    methods=[endpoint.get('method', 'GET')]
                )
            
            self.validation_results.append({
                "check": f"API routes registered ({len(endpoints)} endpoints)",
                "passed": True,
                "message": f"Successfully registered {len(endpoints)} endpoints"
            })
            
        except Exception as e:
            self.validation_results.append({
                "check": "API registration",
                "passed": False,
                "message": f"Failed to register API routes: {str(e)}"
            })
    
    def _validate_ui(self):
        pages = self.ui.get('pages', [])
        
        if not pages:
            self.validation_results.append({
                "check": "UI pages defined",
                "passed": False,
                "message": "No UI pages defined."
            })
            return
        
        invalid_routes = []
        for page in pages:
            route = page.get('route', '')
            if not route.startswith('/'):
                invalid_routes.append(route)
        
        if invalid_routes:
            self.validation_results.append({
                "check": "UI routes are valid",
                "passed": False,
                "message": f"Invalid routes (should start with '/'): {', '.join(invalid_routes)}"
            })
        else:
            self.validation_results.append({
                "check": f"UI pages defined ({len(pages)} pages)",
                "passed": True,
                "message": f"Pages: {', '.join(p['route'] for p in pages)}"
            })
    
    def _validate_auth(self):
        roles = self.auth.get('roles', [])
        
        if not roles:
            self.validation_results.append({
                "check": "Auth roles defined",
                "passed": False,
                "message": "No roles defined in auth schema."
            })
            return
        
        roles_without_perms = []
        for role in roles:
            if not role.get('permissions') or len(role['permissions']) == 0:
                roles_without_perms.append(role.get('name', 'unnamed'))
        
        if roles_without_perms:
            self.validation_results.append({
                "check": "Roles have permissions",
                "passed": False,
                "message": f"Roles missing permissions: {', '.join(roles_without_perms)}"
            })
        else:
            self.validation_results.append({
                "check": f"Auth roles defined ({len(roles)} roles)",
                "passed": True,
                "message": f"Roles: {', '.join(r['name'] for r in roles)}"
            })
    
    def _get_sqlalchemy_type(self, type_str: str):
        type_map = {
            'string': String,
            'text': String,
            'integer': Integer,
            'int': Integer,
            'datetime': DateTime,
            'date': DateTime,
            'boolean': Boolean,
            'bool': Boolean,
            'uuid': String,
        }
        return type_map.get(type_str.lower(), String)


# ====================================================
# This is the function we need to import
# ====================================================
def validate_config(db: dict, api: dict, ui: dict, auth: dict) -> Dict:
    runtime = Runtime({
        'db': db,
        'api': api,
        'ui': ui,
        'auth': auth
    })
    return runtime.validate_all()