from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account


class Sheets:
    def __init__(self, service_account_file: str, sheet_id: str):
        self.service_account_file = service_account_file
        self.creds = service_account.Credentials.from_service_account_file(
            self.service_account_file,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        self.sheet_id = sheet_id

    def append_row(
        self, range_name: str, value_input_option: str, values: list
    ) -> None:

        try:
            service = build("sheets", "v4", credentials=self.creds)

            body = {"values": values}
            result = (
                service.spreadsheets()
                .values()
                .append(
                    spreadsheetId=self.sheet_id,
                    range=range_name,
                    valueInputOption=value_input_option,
                    body=body,
                )
                .execute()
            )
            print(f"{(result.get('updates').get('updatedCells'))} cells appended.")
            return result

        except HttpError as error:
            print(f"An error occurred: {error}")
