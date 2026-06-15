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
    """Return a real or demo client depending on whether credentials are configured."""
    from django.conf import settings
    sid = getattr(settings, 'GOCARDLESS_SECRET_ID', '').strip()
    skey = getattr(settings, 'GOCARDLESS_SECRET_KEY', '').strip()
    if not sid or not skey:
        return DemoGoCardlessClient()
    return GoCardlessClient(sid, skey)


# ── Demo client (no credentials needed) ─────────────────────────────────────

_DEMO_INSTITUTIONS = [
    {'id': 'DEMO_PKO_BP',    'name': 'PKO Bank Polski (DEMO)',  'bic': 'BPKOPLPW', 'logo': ''},
    {'id': 'DEMO_MBANK',     'name': 'mBank (DEMO)',            'bic': 'BREXPLPW', 'logo': ''},
    {'id': 'DEMO_ING',       'name': 'ING Bank Śląski (DEMO)',  'bic': 'INGBPLPW', 'logo': ''},
    {'id': 'DEMO_SANTANDER', 'name': 'Santander Bank (DEMO)',   'bic': 'WBKPPLPP', 'logo': ''},
    {'id': 'DEMO_ALIOR',     'name': 'Alior Bank (DEMO)',       'bic': 'ALBPPLPW', 'logo': ''},
]

_DEMO_TRANSACTIONS = [
    {'transactionId': 'demo-1',  'transactionAmount': {'amount':  '5500.00', 'currency': 'PLN'}, 'bookingDate': '2026-06-01', 'remittanceInformationUnstructured': 'Wynagrodzenie czerwiec'},
    {'transactionId': 'demo-2',  'transactionAmount': {'amount':   '-89.99', 'currency': 'PLN'}, 'bookingDate': '2026-06-02', 'remittanceInformationUnstructured': 'Zakupy Biedronka'},
    {'transactionId': 'demo-3',  'transactionAmount': {'amount':   '-45.00', 'currency': 'PLN'}, 'bookingDate': '2026-06-03', 'remittanceInformationUnstructured': 'Paliwo Shell'},
    {'transactionId': 'demo-4',  'transactionAmount': {'amount':   '-12.50', 'currency': 'PLN'}, 'bookingDate': '2026-06-04', 'remittanceInformationUnstructured': 'Spotify Premium'},
    {'transactionId': 'demo-5',  'transactionAmount': {'amount':  '-230.00', 'currency': 'PLN'}, 'bookingDate': '2026-06-05', 'remittanceInformationUnstructured': 'Lidl sklep'},
    {'transactionId': 'demo-6',  'transactionAmount': {'amount':   '-65.00', 'currency': 'PLN'}, 'bookingDate': '2026-06-06', 'remittanceInformationUnstructured': 'Restauracja Sushi'},
    {'transactionId': 'demo-7',  'transactionAmount': {'amount':   '800.00', 'currency': 'PLN'}, 'bookingDate': '2026-06-07', 'remittanceInformationUnstructured': 'Freelance — faktura #12'},
    {'transactionId': 'demo-8',  'transactionAmount': {'amount':  '-150.00', 'currency': 'PLN'}, 'bookingDate': '2026-06-08', 'remittanceInformationUnstructured': 'Prąd i gaz — rachunki'},
    {'transactionId': 'demo-9',  'transactionAmount': {'amount':   '-32.00', 'currency': 'PLN'}, 'bookingDate': '2026-06-09', 'remittanceInformationUnstructured': 'Netflix'},
    {'transactionId': 'demo-10', 'transactionAmount': {'amount':  '-210.00', 'currency': 'PLN'}, 'bookingDate': '2026-06-10', 'remittanceInformationUnstructured': 'Apteka'},
]


class DemoGoCardlessClient(GoCardlessClient):
    """Local demo client — works without any API credentials."""

    def __init__(self):
        # no real credentials needed
        super().__init__('demo', 'demo')

    def _fetch_token(self) -> str:
        return 'demo-token'

    def get_institutions(self, country: str = 'pl') -> list:
        return _DEMO_INSTITUTIONS

    def create_requisition(self, institution_id: str, redirect_uri: str, reference: str) -> dict:
        from django.urls import reverse
        demo_link = f'/banking/demo-auth/?ref={reference}'
        return {'id': f'demo-req-{reference[:8]}', 'link': demo_link}

    def get_requisition(self, requisition_id: str) -> dict:
        return {'id': requisition_id, 'accounts': ['demo-account-001']}

    def delete_requisition(self, requisition_id: str):
        pass

    def get_account_transactions(self, account_id: str, date_from: date = None) -> dict:
        return {'transactions': {'booked': _DEMO_TRANSACTIONS, 'pending': []}}


# ── Open Bank Project client (Direct Login, real sandbox) ────────────────────

class OBPError(Exception):
    def __init__(self, status_code: int, detail):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f'OBP {status_code}: {detail}')


class OBPNetworkError(OBPError):
    def __init__(self, reason: str):
        super().__init__(0, reason)


class OBPClient:
    """
    Open Bank Project sandbox client.
    Uses Direct Login (username + password + consumer_key) — no OAuth redirect needed.
    Docs: https://github.com/OpenBankProject/OBP-API/wiki/Direct-Login
    """

    def __init__(self, base_url: str, consumer_key: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.consumer_key = consumer_key
        self.username = username
        self.password = password
        self._token: str | None = None

    # ── auth ──────────────────────────────────────────────────────────────────

    def _login(self) -> str:
        """Obtain a DirectLogin token and cache it on the instance."""
        req = urllib.request.Request(
            f'{self.base_url}/my/logins/direct',
            data=b'',
            headers={
                'Authorization': (
                    f'DirectLogin username="{self.username}",'
                    f'password="{self.password}",'
                    f'consumer_key="{self.consumer_key}"'
                ),
                'Content-Type': 'application/json',
            },
            method='POST',
        )
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                data = json.loads(resp.read())
                self._token = data['token']
                return self._token
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode('utf-8', errors='replace')
            try:
                detail = json.loads(raw)
            except Exception:
                detail = raw
            raise OBPError(exc.code, detail) from exc
        except urllib.error.URLError as exc:
            raise OBPNetworkError(f'Nie można połączyć z OBP: {exc.reason}') from exc
        except TimeoutError as exc:
            raise OBPNetworkError('Przekroczono czas oczekiwania OBP.') from exc

    def _request(self, method: str, path: str, body: dict = None) -> Union[dict, list]:
        if not self._token:
            self._login()
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            f'{self.base_url}{path}',
            data=data,
            headers={
                'Authorization': f'DirectLogin token="{self._token}"',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode('utf-8', errors='replace')
            try:
                detail = json.loads(raw)
            except Exception:
                detail = raw
            raise OBPError(exc.code, detail) from exc
        except urllib.error.URLError as exc:
            raise OBPNetworkError(f'Nie można połączyć z OBP: {exc.reason}') from exc
        except TimeoutError as exc:
            raise OBPNetworkError('Przekroczono czas oczekiwania OBP.') from exc

    def _get(self, path: str) -> Union[dict, list]:
        return self._request('GET', path)

    def _post(self, path: str, body: dict) -> Union[dict, list]:
        return self._request('POST', path, body)

    # ── public API ────────────────────────────────────────────────────────────

    def get_accounts(self) -> list:
        """Return list of accounts for the logged-in user."""
        data = self._get('/obp/v4.0.0/my/accounts')
        return data.get('accounts', []) if isinstance(data, dict) else []

    # ── sandbox bootstrap ─────────────────────────────────────────────────────

    _DEMO_BANK_ID = 'finance-app-demo-bank'
    _DEMO_ACCOUNT_ID = 'finance-app-acc-1'

    _SANDBOX_PAYLOAD = {
        'banks': [
            {'id': 'finance-app-demo-bank', 'short_name': 'FinanceApp', 'full_name': 'FinanceApp Demo Bank',
             'logo': '', 'website': 'https://example.com'},
        ],
        'users': [
            {'email': 'joe.bloggs@example.com', 'password': 'qwerty', 'display_name': 'Joe Bloggs'},
        ],
        'accounts': [
            {
                'id': 'finance-app-acc-1',
                'bank': 'finance-app-demo-bank',
                'label': 'Demo Checking Account',
                'currency': 'EUR',
                'balance': {'currency': 'EUR', 'amount': '5000.00'},
                'owner': 'joe.bloggs@example.com',
                'generate_public_transactions': False,
                'branches': [], 'atms': [], 'products': [], 'crm_events': [], 'fx': [],
            }
        ],
        'transactions': [
            {'id': 'fa-tx-1', 'this_account': {'id': 'finance-app-acc-1', 'bank': 'finance-app-demo-bank'},
             'counterparty': {'name': 'Grocery Store'},
             'details': {'type': 'SEPA', 'description': 'Grocery Shopping',
                         'posted': '2026-06-01T10:00:00Z', 'completed': '2026-06-01T10:00:00Z',
                         'new_balance': {'currency': 'EUR', 'amount': '4950.00'},
                         'value': {'currency': 'EUR', 'amount': '-50.00'}}},
            {'id': 'fa-tx-2', 'this_account': {'id': 'finance-app-acc-1', 'bank': 'finance-app-demo-bank'},
             'counterparty': {'name': 'Employer'},
             'details': {'type': 'SEPA', 'description': 'Monthly salary',
                         'posted': '2026-06-05T08:00:00Z', 'completed': '2026-06-05T08:00:00Z',
                         'new_balance': {'currency': 'EUR', 'amount': '7450.00'},
                         'value': {'currency': 'EUR', 'amount': '2500.00'}}},
            {'id': 'fa-tx-3', 'this_account': {'id': 'finance-app-acc-1', 'bank': 'finance-app-demo-bank'},
             'counterparty': {'name': 'Netflix'},
             'details': {'type': 'SEPA', 'description': 'Netflix subscription',
                         'posted': '2026-06-10T12:00:00Z', 'completed': '2026-06-10T12:00:00Z',
                         'new_balance': {'currency': 'EUR', 'amount': '7418.00'},
                         'value': {'currency': 'EUR', 'amount': '-32.00'}}},
            {'id': 'fa-tx-4', 'this_account': {'id': 'finance-app-acc-1', 'bank': 'finance-app-demo-bank'},
             'counterparty': {'name': 'Shell Petrol'},
             'details': {'type': 'SEPA', 'description': 'Fuel payment',
                         'posted': '2026-06-12T15:30:00Z', 'completed': '2026-06-12T15:30:00Z',
                         'new_balance': {'currency': 'EUR', 'amount': '7368.00'},
                         'value': {'currency': 'EUR', 'amount': '-50.00'}}},
            {'id': 'fa-tx-5', 'this_account': {'id': 'finance-app-acc-1', 'bank': 'finance-app-demo-bank'},
             'counterparty': {'name': 'Freelance Client'},
             'details': {'type': 'SEPA', 'description': 'Freelance invoice #42',
                         'posted': '2026-06-15T09:00:00Z', 'completed': '2026-06-15T09:00:00Z',
                         'new_balance': {'currency': 'EUR', 'amount': '8168.00'},
                         'value': {'currency': 'EUR', 'amount': '800.00'}}},
        ],
    }

    def bootstrap_sandbox_data(self) -> tuple[str, str]:
        """
        Ensure demo bank/account/transactions exist in the OBP sandbox.
        Uses POST /sandbox/data-import (requires allow_sandbox_data_import = Enabled).
        Returns (bank_id, account_id).
        """
        try:
            self._post('/obp/v4.0.0/sandbox/data-import', self._SANDBOX_PAYLOAD)
        except OBPError as exc:
            if exc.status_code not in (200, 201, 409):
                raise
        return self._DEMO_BANK_ID, self._DEMO_ACCOUNT_ID

    def get_account_views(self, bank_id: str, account_id: str) -> list[str]:
        """Return view IDs available for an account (e.g. ['owner', 'public'])."""
        try:
            data = self._get(f'/obp/v4.0.0/banks/{bank_id}/accounts/{account_id}/views')
            views = data.get('views', []) if isinstance(data, dict) else []
            return [v['id'] for v in views if v.get('id')]
        except OBPError:
            return []

    def get_transactions(self, bank_id: str, account_id: str, limit: int = 100) -> list:
        """Return transactions, trying available views in order."""
        candidate_views = self.get_account_views(bank_id, account_id)
        # always also try the standard views as fallback
        for view in dict.fromkeys(candidate_views + ['owner', 'public', 'accountant']):
            try:
                data = self._get(
                    f'/obp/v4.0.0/banks/{bank_id}/accounts/{account_id}/{view}/transactions'
                    f'?limit={limit}&sort_direction=DESC'
                )
                return data.get('transactions', []) if isinstance(data, dict) else []
            except OBPError as exc:
                if exc.status_code in (400, 403, 404, 500):
                    continue
                raise
        return []


# ── NBP (Narodowy Bank Polski) client — no auth needed ───────────────────────

NBP_BASE_URL = 'https://api.nbp.pl/api'


class NBPError(Exception):
    pass


class NBPClient:
    """
    Client for the Polish National Bank (NBP) public API.
    No API key or registration required.
    Docs: https://api.nbp.pl/en.html
    """

    def get_exchange_rates(self) -> list[dict]:
        """Return today's Table A exchange rates (PLN mid rates)."""
        req = urllib.request.Request(
            f'{NBP_BASE_URL}/exchangerates/tables/A/?format=json',
            headers={'Accept': 'application/json'},
        )
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                data = json.loads(resp.read())
                return data[0].get('rates', [])
        except urllib.error.HTTPError as exc:
            raise NBPError(f'NBP HTTP {exc.code}') from exc
        except urllib.error.URLError as exc:
            raise NBPError(f'Nie można połączyć z NBP: {exc.reason}') from exc
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise NBPError(f'Nieoczekiwany format odpowiedzi NBP') from exc


def get_obp_client() -> OBPClient:
    """Build OBP client from Django settings."""
    from django.conf import settings
    base_url = getattr(settings, 'OBP_BASE_URL', 'https://apisandbox.openbankproject.com')
    consumer_key = getattr(settings, 'OBP_CONSUMER_KEY', '').strip()
    username = getattr(settings, 'OBP_DEMO_USERNAME', 'joe.bloggs@example.com')
    password = getattr(settings, 'OBP_DEMO_PASSWORD', 'qwerty')
    if not consumer_key:
        raise ValueError('OBP_CONSUMER_KEY nie jest skonfigurowany w settings.py.')
    return OBPClient(base_url, consumer_key, username, password)


# ── Plaid Sandbox client ──────────────────────────────────────────────────────

class PlaidError(Exception):
    def __init__(self, status_code: int, detail):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f'Plaid {status_code}: {detail}')


class PlaidNetworkError(PlaidError):
    def __init__(self, reason: str):
        super().__init__(0, reason)


class PlaidClient:
    """
    Plaid Sandbox client.
    Sandbox shortcut: POST /sandbox/public_token/create bypasses the Link UI —
    no browser redirect needed, works purely server-side.
    Docs: https://plaid.com/docs/api/sandbox/
    """
    BASE_URL = 'https://sandbox.plaid.com'
    # Pre-loaded test institution with realistic transaction history
    SANDBOX_INSTITUTION = 'ins_109508'  # First Platypus Bank

    def __init__(self, client_id: str, secret: str):
        self.client_id = client_id
        self.secret = secret

    def _post(self, path: str, body: dict) -> dict:
        payload = {'client_id': self.client_id, 'secret': self.secret}
        payload.update(body)
        req = urllib.request.Request(
            f'{self.BASE_URL}{path}',
            data=json.dumps(payload).encode(),
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
            method='POST',
        )
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode('utf-8', errors='replace')
            try:
                detail = json.loads(raw)
            except Exception:
                detail = raw
            raise PlaidError(exc.code, detail) from exc
        except urllib.error.URLError as exc:
            raise PlaidNetworkError(str(exc.reason)) from exc
        except TimeoutError as exc:
            raise PlaidNetworkError('Przekroczono czas oczekiwania Plaid.') from exc

    def get_access_token(self) -> str:
        """
        Sandbox-only: create a test item directly (no Link UI),
        then exchange the public token for an access token.
        """
        pub = self._post('/sandbox/public_token/create', {
            'institution_id': self.SANDBOX_INSTITUTION,
            'initial_products': ['transactions'],
        })
        exch = self._post('/item/public_token/exchange', {
            'public_token': pub['public_token'],
        })
        return exch['access_token']

    def _fire_webhook(self, access_token: str):
        """Trigger sandbox transaction loading (fire INITIAL_UPDATE webhook)."""
        try:
            self._post('/sandbox/item/fire_webhook', {
                'access_token': access_token,
                'webhook_type': 'TRANSACTIONS',
                'webhook_code': 'INITIAL_UPDATE',
            })
        except PlaidError:
            pass  # best-effort

    def get_transactions(self, access_token: str, days: int = 90) -> list:
        """Fetch booked transactions for the last N days, with retry for PRODUCT_NOT_READY."""
        import time
        end = date.today().isoformat()
        start = date.fromordinal(date.today().toordinal() - days).isoformat()
        body = {
            'access_token': access_token,
            'start_date': start,
            'end_date': end,
            'options': {'count': 500, 'offset': 0},
        }
        for attempt in range(4):
            try:
                data = self._post('/transactions/get', body)
                return [t for t in data.get('transactions', []) if not t.get('pending')]
            except PlaidError as exc:
                detail = exc.detail if isinstance(exc.detail, dict) else {}
                if detail.get('error_code') == 'PRODUCT_NOT_READY' and attempt < 3:
                    if attempt == 0:
                        self._fire_webhook(access_token)
                    time.sleep(3 * (attempt + 1))
                    continue
                raise
        return []


def get_plaid_client() -> PlaidClient:
    """Build Plaid client from Django settings."""
    from django.conf import settings
    client_id = getattr(settings, 'PLAID_CLIENT_ID', '').strip()
    secret = getattr(settings, 'PLAID_SECRET', '').strip()
    if not client_id or not secret:
        raise ValueError('PLAID_CLIENT_ID i PLAID_SECRET muszą być skonfigurowane w settings.py.')
    return PlaidClient(client_id, secret)