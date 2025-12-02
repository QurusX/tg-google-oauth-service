import logging
from typing import Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from utils.config import settings


logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/spreadsheets",
]


def build_flow(state: str) -> Flow:
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.google_redirect_uri],
            }
        },
        scopes=SCOPES,
        state=state,
    )
    flow.redirect_uri = settings.google_redirect_uri
    return flow


def generate_authorization_url(state: str) -> str:
    flow = build_flow(state)
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url


def exchange_code_for_tokens(code: str, state: str) -> Tuple[str, Credentials]:
    """
    Обменивает authorization_code на refresh_token и access_token.
    Возвращает refresh_token и объект Credentials (в котором есть access_token).
    """
    flow = build_flow(state)
    flow.fetch_token(code=code)
    creds: Credentials = flow.credentials

    refresh_token = creds.refresh_token
    if not refresh_token:
        # В редких случаях Google может не вернуть refresh_token,
        # если пользователь уже выдавал доступ. Логируем это.
        logger.warning("Google did not return refresh_token for state=%s", state)

    return refresh_token, creds


def build_services(creds: Credentials):
    """
    Создаёт сервисы для работы с Drive и Sheets.
    """
    # Обновление access_token при необходимости
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    drive_service = build("drive", "v3", credentials=creds)
    sheets_service = build("sheets", "v4", credentials=creds)
    return drive_service, sheets_service


def create_folder_and_sheets(creds: Credentials) -> Tuple[str, str, str]:
    """
    Создаёт папку 'Маржа24' и три таблицы внутри: 'ОПиУ', 'SKU', 'Настройки'.
    Возвращает URL-ы таблиц (opiu_url, sku_url, settings_url).
    """
    drive_service, sheets_service = build_services(creds)

    # Создаём папку
    folder_metadata = {
        "name": "Маржа24",
        "mimeType": "application/vnd.google-apps.folder",
    }
    folder = (
        drive_service.files()
        .create(body=folder_metadata, fields="id")
        .execute()
    )
    folder_id = folder["id"]

    def _create_sheet(title: str) -> str:
        file_metadata = {
            "name": title,
            "mimeType": "application/vnd.google-apps.spreadsheet",
            "parents": [folder_id],
        }
        sheet_file = (
            drive_service.files()
            .create(body=file_metadata, fields="id, webViewLink")
            .execute()
        )
        return sheet_file["webViewLink"]

    opiu_url = _create_sheet("ОПиУ")
    sku_url = _create_sheet("SKU")
    settings_url = _create_sheet("Настройки")

    return opiu_url, sku_url, settings_url


