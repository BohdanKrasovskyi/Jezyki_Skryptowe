# FinanceTracker — Aplikacja do zarządzania finansami osobistymi

Projekt zaliczeniowy z przedmiotu **Języki Skryptowe** (PWr).  
Aplikacja webowa zbudowana w Django do śledzenia przychodów i wydatków, importu transakcji z zewnętrznych API bankowych oraz generowania raportów z wykresami.

---

## Technologie

| Warstwa | Technologia |
|---|---|
| Backend | Python 3.12, Django 6.0 |
| Baza danych | SQLite (Django ORM) |
| Frontend | Bootstrap 5, Chart.js, Bootstrap Icons |
| API bankowe | Plaid Sandbox, GoCardless Bank Account Data |
| HTTP client | `urllib` (biblioteka standardowa — bez requests/httpx) |
| Konteneryzacja | Docker, docker-compose |

---

## Funkcjonalności

- **Dashboard** — podsumowanie bieżącego miesiąca: przychody, wydatki, saldo, ostatnie transakcje
- **Transakcje** — dodawanie, edytowanie, usuwanie z atomową aktualizacją salda konta; filtrowanie po typie, kategorii, koncie i zakresie dat; paginacja; eksport do CSV
- **Kategorie** — zarządzanie kategoriami przychodów i wydatków z kolorem do wykresów
- **Konta** — konto bieżące, oszczędnościowe, karta kredytowa, gotówka; wielowalutowość (kody ISO 4217)
- **Raporty** — wykresy kołowe i słupkowe z podziałem na kategorie i miesiące (Chart.js + AJAX)
- **Import bankowy** — import CSV z polskich banków + integracja z zewnętrznymi API bankowymi

---

## Architektura

Projekt stosuje warstwową architekturę z wyraźnym podziałem odpowiedzialności:

```
HTTP Request → Views → Services → Repositories → ORM / SQLite
```

### Wzorzec Repository

Wszystkie repozytoria dziedziczą po `BaseRepository` (ABC):

```python
class BaseRepository(ABC):
    def get_by_id(self, pk): ...
    def get_all(self): ...
    def save(self, entity): ...
    def delete(self, pk): ...
```

Implementacje: `TransactionRepository`, `CategoryRepository`, `AccountRepository`, `BankImportRepository`.

### Warstwa serwisów (`FinanceService`)

- `add_transaction` / `update_transaction` / `delete_transaction` — atomowa aktualizacja salda (`select_for_update`)
- `import_csv` — parsowanie CSV z obsługą wielu kodowań i formatów dat
- `import_from_plaid` — import transakcji z Plaid Sandbox z deduplikacją po `external_id`
- `import_from_obp` — import z Open Bank Project (Direct Login)
- `sync_linked_account` — synchronizacja z GoCardless Bank Account Data
- `get_dashboard_data` / `get_report_data` — agregacje dla widoków

---

## Integracja z API bankowym

### Plaid Sandbox

Główna integracja testowa. Import wykonuje 3 rzeczywiste żądania HTTP do `sandbox.plaid.com`:

```
POST /sandbox/public_token/create  →  public_token dla First Platypus Bank (ins_109508)
POST /item/public_token/exchange   →  access_token
POST /transactions/get             →  historia transakcji (ostatnie 90 dni)
```

Konfiguracja w `settings.py` (lub zmienne środowiskowe):

```python
PLAID_CLIENT_ID = 'twój-client-id'
PLAID_SECRET    = 'twój-secret'
```

### GoCardless Bank Account Data

Integracja z PSD2 Open Banking — ponad 2000 banków w Europie. Flow:

```
Wybór banku → POST /banking/link/ → redirect do banku → callback → sync transakcji
```

Tryb demo działa bez kluczy (fikcyjne dane). Prawdziwe klucze (bezpłatne):

```python
GOCARDLESS_SECRET_ID  = 'twój-secret-id'
GOCARDLESS_SECRET_KEY = 'twój-secret-key'
```

### Import CSV

Obsługuje pliki `.csv` / `.txt` do 10 MB. Automatyczna detekcja kodowania: `UTF-8`, `CP1250`, `latin-1`. Rozpoznaje polskie i angielskie nagłówki: `Kwota`/`Amount`, `Data`/`Date`, `Opis`/`Description`.

Przykładowy format:

```csv
Data,Kwota,Opis
2024-01-15,3500.00,Wynagrodzenie
2024-01-16,-89.99,Zakupy Biedronka
2024-01-17,-45.00,Paliwo
```

---

## Instalacja i uruchomienie

### Docker (zalecane)

```bash
cd projekt
docker compose up --build
```

Aplikacja: `http://localhost:8000/`

Przy pierwszym uruchomieniu automatycznie wykonywane są migracje i `seed_data` (przykładowe dane).

### Lokalnie

```bash
cd projekt

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS

pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data   # opcjonalnie — ~60 przykładowych transakcji
python manage.py runserver
```

Aplikacja: `http://127.0.0.1:8000/`

### Testy

```bash
python manage.py test finance
```

---

## Modele danych

| Model | Opis |
|---|---|
| `Account` | Konto bankowe (typ, saldo, waluta) |
| `Category` | Kategoria transakcji z kolorem HEX |
| `Transaction` | Transakcja z `external_id` do deduplikacji importów |
| `LinkedBankAccount` | Połączone konto GoCardless (requisition, status, ostatnia sync) |
| `BankImport` | Historia importów CSV (plik, data, liczba rekordów) |

---

## Struktura projektu

```
projekt/
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── finance_project/
│   ├── settings.py
│   └── urls.py
└── finance/
    ├── models.py          # modele danych
    ├── repositories.py    # wzorzec Repository
    ├── services.py        # logika biznesowa
    ├── views.py           # widoki HTTP
    ├── forms.py           # formularze z walidacją
    ├── banking_api.py     # klienty API: GoCardless, Plaid, OBP
    ├── urls.py            # routing URL
    ├── tests.py           # testy jednostkowe i integracyjne (89 testów)
    ├── admin.py
    ├── migrations/
    ├── management/commands/seed_data.py
    └── templates/finance/
        ├── base.html
        ├── dashboard.html
        ├── transactions.html
        ├── transaction_form.html
        ├── categories.html
        ├── category_form.html
        ├── accounts.html
        ├── reports.html
        ├── banking.html
        └── banking_demo_auth.html
```

---

## Autorzy

- **Bohdan** — architektura aplikacji, modele, serwisy, repozytoria, widoki, formularze, testy
- **Mateusz** — integracja API bankowych (Plaid, GoCardless, OBP), Docker, dokumentacja