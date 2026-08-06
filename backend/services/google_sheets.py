import gspread
from google.oauth2.service_account import Credentials
from google.auth.exceptions import GoogleAuthError
import os
import json
from config import config

class GoogleSheetsService:
    def __init__(self):
        self.client = None
        self.sheet = None
        self.connected = False
        self.initialize()

    def initialize(self):
        """Initialize Google Sheets with credentials from .env"""
        try:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Get credentials from .env
            creds_json = config.GOOGLE_CREDENTIALS_JSON
            
            if not creds_json:
                print("❌ GOOGLE_CREDENTIALS_JSON not found in .env")
                return False
            
            # Parse the JSON credentials
            creds_dict = json.loads(creds_json)
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            
            self.client = gspread.authorize(creds)
            
            # Get sheet ID from .env
            sheet_id = config.GOOGLE_SHEET_ID
            if not sheet_id:
                print("❌ GOOGLE_SHEET_ID not found in .env")
                return False
            
            self.sheet = self.client.open_by_key(sheet_id)
            self.connected = True
            print(f"✅ Google Sheets connected: {self.sheet.title}")
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ Invalid GOOGLE_CREDENTIALS_JSON format: {e}")
            return False
        except GoogleAuthError as e:
            print(f"❌ Google Auth Error: {e}")
            return False
        except Exception as e:
            print(f"❌ Error connecting to Google Sheets: {e}")
            return False

    def get_worksheet(self, sheet_name):
        """Get a worksheet by name"""
        if not self.connected:
            return None
        try:
            return self.sheet.worksheet(sheet_name)
        except:
            return None

    def get_all_records(self, sheet_name):
        """Get all records from a worksheet"""
        worksheet = self.get_worksheet(sheet_name)
        if not worksheet:
            return []
        try:
            return worksheet.get_all_records()
        except:
            return []

    def insert_record(self, sheet_name, data):
        """Insert a new record with auto-generated ID"""
        worksheet = self.get_worksheet(sheet_name)
        if not worksheet:
            return None
        
        headers = worksheet.row_values(1)
        
        # ✅ Auto-generate ID if 'user_id' or 'id' is missing
        id_field = 'user_id' if 'user_id' in headers else 'id'
        
        if id_field in data and data.get(id_field):
            # ID already provided
            pass
        else:
            # Auto-generate ID
            records = self.get_all_records(sheet_name)
            max_id = 0
            for record in records:
                try:
                    rid = int(record.get(id_field, 0))
                    if rid > max_id:
                        max_id = rid
                except (ValueError, TypeError):
                    pass
            data[id_field] = max_id + 1
        
        # Prepare row data
        row_data = []
        for header in headers:
            value = data.get(header, '')
            row_data.append(str(value) if value is not None else '')
        
        worksheet.append_row(row_data)
        return data

    def update_record(self, sheet_name, id_field, id_value, data):
        """Update a record by ID"""
        worksheet = self.get_worksheet(sheet_name)
        if not worksheet:
            return None
        
        records = self.get_all_records(sheet_name)
        headers = worksheet.row_values(1)
        
        for idx, record in enumerate(records, start=2):
            if str(record.get(id_field)) == str(id_value):
                for i, header in enumerate(headers):
                    if header in data:
                        cell_value = str(data[header]) if data[header] is not None else ''
                        worksheet.update_cell(idx, i + 1, cell_value)
                return self.get_record_by_id(sheet_name, id_field, id_value)
        
        return None

    def get_record_by_id(self, sheet_name, id_field, id_value):
        """Get a record by ID"""
        records = self.get_all_records(sheet_name)
        for record in records:
            if str(record.get(id_field)) == str(id_value):
                return record
        return None

    def delete_record(self, sheet_name, id_field, id_value):
        """Delete a record by ID"""
        worksheet = self.get_worksheet(sheet_name)
        if not worksheet:
            return False
        
        records = self.get_all_records(sheet_name)
        
        for idx, record in enumerate(records, start=2):
            if str(record.get(id_field)) == str(id_value):
                worksheet.delete_rows(idx)
                return True
        
        return False

    def query_by_field(self, sheet_name, field, value):
        """Query records by field value"""
        records = self.get_all_records(sheet_name)
        results = []
        for record in records:
            if str(record.get(field)) == str(value):
                results.append(record)
        return results

    def query_by_fields(self, sheet_name, **kwargs):
        """Query records by multiple fields"""
        records = self.get_all_records(sheet_name)
        results = []
        for record in records:
            match = True
            for key, value in kwargs.items():
                if str(record.get(key)) != str(value):
                    match = False
                    break
            if match:
                results.append(record)
        return results

# Singleton instance
sheet_service = GoogleSheetsService()