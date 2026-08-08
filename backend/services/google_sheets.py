# services/google_sheets.py
import gspread
from google.oauth2.service_account import Credentials
import os
import json

class GoogleSheetsService:
    def __init__(self):
        self.client = None
        self.sheet = None
        self.connected = False
        self.initialize()

    def initialize(self):
        try:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]

            # For Vercel: Read from environment variable
            creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')

            if creds_json:
                creds_dict = json.loads(creds_json)
                creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
                print("✅ Using credentials from environment variable")
            else:
                # Local development: Read from file
                creds_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    'credentials',
                    'service-account.json'
                )
                if os.path.exists(creds_path):
                    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
                    print("✅ Using credentials from file")
                else:
                    print("❌ No Google credentials found")
                    return False

            self.client = gspread.authorize(creds)

            sheet_id = os.environ.get('GOOGLE_SHEET_ID')
            if not sheet_id:
                print("❌ GOOGLE_SHEET_ID not set")
                return False

            self.sheet = self.client.open_by_key(sheet_id)
            self.connected = True
            print(f"✅ Google Sheets connected: {self.sheet.title}")
            return True

        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def get_worksheet(self, sheet_name):
        if not self.connected:
            return None
        try:
            return self.sheet.worksheet(sheet_name)
        except:
            return None

    def get_all_records(self, sheet_name):
        worksheet = self.get_worksheet(sheet_name)
        if not worksheet:
            return []
        try:
            return worksheet.get_all_records()
        except:
            return []

    def insert_record(self, sheet_name, data):
        worksheet = self.get_worksheet(sheet_name)
        if not worksheet:
            return None

        headers = worksheet.row_values(1)
        row_data = []
        for header in headers:
            value = data.get(header, '')
            row_data.append(str(value) if value is not None else '')

        worksheet.append_row(row_data)
        return data

    def update_record(self, sheet_name, id_field, id_value, data):
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
        records = self.get_all_records(sheet_name)
        for record in records:
            if str(record.get(id_field)) == str(id_value):
                return record
        return None

    def delete_record(self, sheet_name, id_field, id_value):
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
        records = self.get_all_records(sheet_name)
        results = []
        for record in records:
            if str(record.get(field)) == str(value):
                results.append(record)
        return results

    def query_by_fields(self, sheet_name, **kwargs):
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

# Singleton
sheet_service = GoogleSheetsService()