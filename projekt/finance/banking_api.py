"""
Bank data API clients used by the finance app.
"""
import json
import urllib.request
import urllib.error
from datetime import date
from typing import Union


REQUEST_TIMEOUT = 20


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