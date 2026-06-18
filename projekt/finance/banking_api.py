"""
GoCardless Bank Account Data API client (formerly Nordigen).
Sandbox docs: https://developer.gocardless.com/bank-account-data/sandbox
"""
import json
import urllib.request
import urllib.error
from datetime import date
from typing import Union

from django.core.cache import cache

BASE_URL = 'https://bankaccountdata.gocardless.com/api/v2'
SANDBOX_INSTITUTION_ID = 'SANDBOXFINANCE_SFIN0000'
TOKEN_CACHE_KEY = 'gc_access_token'
REQUEST_TIMEOUT = 20


class GoCardlessError(Exception):
    def __init__(self, status_code: int, detail):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f'GoCardless {status_code}: {detail}')


class GoCardlessNetworkError(GoCardlessError):
    """Raised when there's no network connectivity or request times out."""
    def __init__(self, reason: str):
        super().__init__(0, reason)


class GoCardlessClient:
    def __init__(self, secret_id: str, secret_key: str):
        self.secret_id = secret_id
        self.secret_key = secret_key

    # ── token management ──────────────────────────────────────────────

    def _fetch_token(self) -> str:
        payload = json.dumps({'secret_id': self.secret_id, 'secret_key': self.secret_key}).encode()
        result = self._raw('POST', '/token/new/', payload, auth=False)
        try:
            token = result['access']
            ttl = max(int(result.get('access_expires', 86400)) - 60, 60)
        except (KeyError, TypeError, ValueError) as exc:
            raise GoCardlessError(0, f'Unexpected token response: {result}') from exc
        cache.set(TOKEN_CACHE_KEY, token, ttl)
        return token

    def _token(self) -> str:
        return cache.get(TOKEN_CACHE_KEY) or self._fetch_token()

    # ── low-level HTTP ────────────────────────────────────────────────

    def _raw(self, method: str, path: str, body: bytes = None,
             auth: bool = True) -> Union[dict, list]:
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        if auth:
            headers['Authorization'] = f'Bearer {self._token()}'

        req = urllib.request.Request(
            f'{BASE_URL}{path}',
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode('utf-8', errors='replace')
            try:
                detail = json.loads(raw)
            except Exception:
                detail = raw
            raise GoCardlessError(exc.code, detail) from exc
        except urllib.error.URLError as exc:
            raise GoCardlessNetworkError(
                f'Nie można połączyć się z GoCardless: {exc.reason}'
            ) from exc
        except TimeoutError as exc:
            raise GoCardlessNetworkError('Przekroczono czas oczekiwania na odpowiedź.') from exc

    def _get(self, path: str) -> Union[dict, list]:
        return self._raw('GET', path)

    def _post(self, path: str, payload: dict) -> dict:
        return self._raw('POST', path, json.dumps(payload).encode())

    def _delete(self, path: str):
        self._raw('DELETE', path)

    # ── public API ────────────────────────────────────────────────────

    def get_institutions(self, country: str = 'pl') -> list:
        sandbox = {
            'id': SANDBOX_INSTITUTION_ID,
            'name': 'Sandbox Finance (test)',
            'bic': 'SFIN0000',
            'logo': 'https://cdn.nordigen.com/ais/SANDBOXFINANCE_SFIN0000.png',
        }
        try:
            result = self._get(f'/institutions/?country={country}')
            institutions = list(result) if isinstance(result, list) else []
        except GoCardlessError:
            institutions = []
        return [sandbox] + institutions

    def create_requisition(self, institution_id: str, redirect_uri: str, reference: str) -> dict:
        result = self._post('/requisitions/', {
            'redirect': redirect_uri,
            'institution_id': institution_id,
            'reference': reference,
            'user_language': 'PL',
        })
        if not isinstance(result, dict) or 'id' not in result or 'link' not in result:
            raise GoCardlessError(0, f'Nieoczekiwana odpowiedź: {result}')
        return result

    def get_requisition(self, requisition_id: str) -> dict:
        result = self._get(f'/requisitions/{requisition_id}/')
        if not isinstance(result, dict):
            raise GoCardlessError(0, f'Nieoczekiwana odpowiedź: {result}')
        return result

    def delete_requisition(self, requisition_id: str):
        self._delete(f'/requisitions/{requisition_id}/')

    def get_account_details(self, account_id: str) -> dict:
        return self._get(f'/accounts/{account_id}/details/')

    def get_account_balances(self, account_id: str) -> dict:
        return self._get(f'/accounts/{account_id}/balances/')

    def get_account_transactions(self, account_id: str, date_from: date = None) -> dict:
        suffix = f'?date_from={date_from}' if date_from else ''
        result = self._get(f'/accounts/{account_id}/transactions/{suffix}')
        if not isinstance(result, dict):
            return {'transactions': {'booked': [], 'pending': []}}
        return result


def get_client() -> GoCardlessClient:
    """Build a client from Django settings. Raises ValueError if credentials are missing."""
    from django.conf import settings
    sid = getattr(settings, 'GOCARDLESS_SECRET_ID', '').strip()
    skey = getattr(settings, 'GOCARDLESS_SECRET_KEY', '').strip()
    if not sid or not skey:
        raise ValueError(
            'Credentials GoCardless nie są skonfigurowane. '
            'Ustaw GOCARDLESS_SECRET_ID i GOCARDLESS_SECRET_KEY w settings.py.'
        )
    return GoCardlessClient(sid, skey)