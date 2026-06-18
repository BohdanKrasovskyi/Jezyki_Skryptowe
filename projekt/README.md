# FinanceTracker — Aplikacja do zarządzania finansami osobistymi

Projekt zaliczeniowy z przedmiotu **Języki Skryptowe**.  
Aplikacja webowa zbudowana w Django, umożliwiająca śledzenie przychodów i wydatków, zarządzanie kontami bankowymi oraz generowanie raportów finansowych z wykresami.

---

## Spis treści

1. [Opis projektu](#opis-projektu)
2. [Technologie](#technologie)
3. [Architektura](#architektura)
4. [Modele danych](#modele-danych)
5. [Funkcjonalności](#funkcjonalności)
6. [Integracja z API bankowym](#integracja-z-api-bankowym)
7. [Instalacja i uruchomienie](#instalacja-i-uruchomienie)
8. [Struktura projektu](#struktura-projektu)

---

## Opis projektu

FinanceTracker to aplikacja do zarządzania finansami osobistymi, która pozwala użytkownikowi:

- ręcznie rejestrować przychody i wydatki z przypisaniem do kategorii i konta,
- importować historię transakcji z pliku CSV (obsługa formatów polskich banków),
- łączyć się z prawdziwym (lub testowym) kontem bankowym przez otwarte API bankowe PSD2,
- przeglądać raporty i wykresy kołowe/słupkowe z podziałem na kategorie i miesiące,
- zarządzać wieloma kontami (konto bieżące, oszczędnościowe, karta kredytowa, gotówka).

---

## Technologie

| Warstwa | Technologia |
|---|---|
| Backend | Python 3.12, Django 6.0 |
| Baza danych | SQLite (przez Django ORM) |
| Frontend | Bootstrap 5, Chart.js, Bootstrap Icons |
| API bankowe | GoCardless Bank Account Data (dawniej Nordigen) |
| HTTP client | `urllib` (biblioteka standardowa Python) |
| Cache tokenów | Django cache framework |

Projekt **nie używa żadnych zewnętrznych bibliotek HTTP** (requests, httpx itp.) — cała komunikacja z API oparta jest na wbudowanym `urllib.request`.

---

## Architektura

Projekt stosuje warstwową architekturę z wyraźnym podziałem odpowiedzialności:

```
HTTP Request
    │
    ▼
┌─────────────┐
│   Views     │  ← warstwa prezentacji, obsługa żądań HTTP
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Services   │  ← logika biznesowa (FinanceService)
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│  Repositories    │  ← dostęp do danych (wzorzec Repository)
└──────┬───────────┘
       │
       ▼
┌─────────────┐
│  ORM / DB   │  ← Django ORM, SQLite
└─────────────┘
```

### Wzorzec Repository

Wszystkie repozytoria dziedziczą po klasie abstrakcyjnej `BaseRepository`:

```python
class BaseRepository(ABC):
    @abstractmethod
    def get_by_id(self, pk): ...
    @abstractmethod
    def get_all(self): ...
    @abstractmethod
    def save(self, entity): ...
    @abstractmethod
    def delete(self, pk): ...
```

Konkretne implementacje: `TransactionRepository`, `CategoryRepository`, `AccountRepository`, `BankImportRepository`.

### Warstwa serwisów

`FinanceService` zawiera całą logikę biznesową:

- **`add_transaction`** — dodaje transakcję i atomowo aktualizuje saldo konta (`select_for_update` zapobiega wyścigu)
- **`update_transaction`** — usuwa starą i tworzy nową transakcję w jednej atomowej operacji
- **`delete_transaction`** — usuwa transakcję i koryguje saldo konta
- **`import_csv`** — parsuje plik CSV z obsługą wielu kodowań i formatów dat
- **`sync_linked_account`** — pobiera nowe transakcje z GoCardless, deduplikuje po `external_id`
- **`get_dashboard_data`** / **`get_report_data`** — agregacje danych dla widoku

---

## Modele danych

### `Account` — Konto

| Pole | Typ | Opis |
|---|---|---|
| `name` | CharField | Nazwa konta |
| `account_type` | CharField | Typ: `checking`, `savings`, `credit`, `cash` |
| `balance` | DecimalField | Bieżące saldo (aktualizowane przy każdej transakcji) |
| `currency` | CharField | Kod waluty ISO 4217 (np. PLN, EUR) |
| `bank_name` | CharField | Nazwa banku (opcjonalnie) |
| `account_number` | CharField | Numer konta (opcjonalnie) |

### `Category` — Kategoria

| Pole | Typ | Opis |
|---|---|---|
| `name` | CharField | Nazwa kategorii |
| `category_type` | CharField | Typ: `income` (przychód) lub `expense` (wydatek) |
| `color` | CharField | Kolor HEX do wykresów (np. `#ef4444`) |
| `icon` | CharField | Klasa ikony Bootstrap Icons |

### `Transaction` — Transakcja

| Pole | Typ | Opis |
|---|---|---|
| `amount` | DecimalField | Kwota (zawsze dodatnia) |
| `transaction_type` | CharField | `income` lub `expense` |
| `category` | FK → Category | Kategoria (nullable — SET_NULL) |
| `account` | FK → Account | Konto (CASCADE) |
| `description` | CharField | Opis transakcji |
| `date` | DateField | Data operacji |
| `is_imported` | BooleanField | Czy zaimportowana (CSV lub API) |
| `external_id` | CharField | ID z banku (do deduplikacji przy syncronizacji) |

### `LinkedBankAccount` — Połączone konto bankowe

| Pole | Typ | Opis |
|---|---|---|
| `account` | FK → Account | Lokalne konto |
| `institution_id` | CharField | ID instytucji w GoCardless |
| `requisition_id` | CharField | ID sesji autoryzacyjnej |
| `reference` | CharField | UUID do identyfikacji callbacku OAuth |
| `gocardless_account_id` | CharField | ID konta w GoCardless (po autoryzacji) |
| `status` | CharField | `pending`, `linked`, `error` |
| `last_synced` | DateTimeField | Czas ostatniej synchronizacji |

### `BankImport` — Historia importów CSV

Rejestruje każdy import pliku CSV: nazwa pliku, data importu, liczba zaimportowanych rekordów.

---

## Funkcjonalności

### Dashboard (`/`)

Strona główna pokazuje podsumowanie bieżącego miesiąca:
- łączne przychody i wydatki w bieżącym miesiącu,
- wynikowe saldo,
- lista wszystkich kont z saldami,
- 10 ostatnich transakcji.

### Transakcje (`/transactions/`)

- Lista wszystkich transakcji z filtrowaniem po typie, kategorii, koncie i zakresie dat.
- Sumowanie przefiltrowanych wyników (przychody, wydatki, saldo).
- Dodawanie, edytowanie i usuwanie transakcji.
- Każda operacja **atomowo** koryguje saldo powiązanego konta.

### Kategorie (`/categories/`)

- Lista kategorii z podziałem na przychody i wydatki.
- Dodawanie nowych kategorii z kolorem (pikcer koloru).
- Usuwanie kategorii — transakcje zachowują się (`SET_NULL`).

### Konta (`/accounts/`)

- Zarządzanie kontami (konto bieżące, oszczędnościowe, karta kredytowa, gotówka).
- Waluta z walidacją kodu ISO 4217 (3 litery).

### Raporty (`/reports/`)

- Filtry: rok i opcjonalnie miesiąc.
- Wykresy kołowe przychodów i wydatków z podziałem na kategorie (Chart.js).
- Wykres słupkowy miesięcznego podsumowania.
- Dane do wykresów pobierane przez AJAX z endpointu `/reports/chart-data/`.

### Bankowość (`/banking/`)

Sekcja bankowości oferuje dwa sposoby importu danych:

#### Import CSV
- Obsługuje pliki `.csv` i `.txt` do 10 MB.
- Automatyczna detekcja kodowania: `UTF-8`, `UTF-8-BOM`, `CP1250`, `latin-1`.
- Rozpoznaje polskie i angielskie nagłówki kolumn: `Kwota`/`Amount`, `Data`/`Date`, `Opis`/`Description`.
- Obsługuje formaty dat: `YYYY-MM-DD`, `DD.MM.YYYY`, `DD/MM/YYYY`.

#### Integracja API (GoCardless)
- Łączenie konta bankowego przez Open Banking PSD2.
- Synchronizacja transakcji z deduplikacją po `external_id`.
- Pełna obsługa OAuth flow (start → redirect → callback).

---

## Integracja z API bankowym

### GoCardless Bank Account Data API

Projekt integruje się z **GoCardless Bank Account Data** (dawniej Nordigen) — bezpłatnym API PSD2 umożliwiającym dostęp do danych bankowych z ponad 2000 banków w Europie.

Dokumentacja sandbox: `https://developer.gocardless.com/bank-account-data/sandbox`

### Tryb sandbox (testowy)

Do testowania bez prawdziwego konta bankowego służy wbudowana instytucja sandbox:

```
Institution ID: SANDBOXFINANCE_SFIN0000
```

Sandbox zwraca realistyczne fikcyjne transakcje — nie wymaga żadnego prawdziwego konta bankowego ani certyfikatu eIDAS.

### Klient HTTP (`GoCardlessClient`)

Klasa `GoCardlessClient` w `banking_api.py` implementuje:

| Metoda | Endpoint | Opis |
|---|---|---|
| `_fetch_token()` | `POST /token/new/` | Pobiera token JWT, cachuje w Django cache |
| `get_institutions()` | `GET /institutions/?country=pl` | Lista banków w danym kraju |
| `create_requisition()` | `POST /requisitions/` | Tworzy sesję autoryzacyjną, zwraca link redirect |
| `get_requisition()` | `GET /requisitions/{id}/` | Sprawdza status i pobiera ID kont |
| `get_account_transactions()` | `GET /accounts/{id}/transactions/` | Pobiera transakcje (opcjonalnie od daty) |
| `delete_requisition()` | `DELETE /requisitions/{id}/` | Usuwa połączenie |

**Zarządzanie tokenem:** Token JWT jest automatycznie cachowany w Django cache z TTL odpowiadającym czasowi ważności zwróconym przez API (minus 60 sekund marginesu). Przy kolejnych żądaniach jest odczytywany z cache, a nowy token pobierany dopiero gdy stary wygaśnie.

### Flow autoryzacji banku

```
1. Użytkownik wybiera bank z listy instytucji (AJAX)
2. POST /banking/link/ → tworzy requisition w GoCardless
3. Zapis LinkedBankAccount(status=PENDING) do bazy
4. Redirect → strona banku (lub sandbox)
5. Użytkownik autoryzuje dostęp
6. Bank redirectuje z powrotem do /banking/callback/?ref=<uuid>
7. Callback odczytuje konto po reference (UUID), pobiera ID kont
8. Aktualizacja status=LINKED, zapis gocardless_account_id
9. POST /banking/{pk}/sync/ → pobiera transakcje, deduplikuje, zapisuje
```

### Hierarchia wyjątków

```
GoCardlessError(status_code, detail)
    └── GoCardlessNetworkError  ← brak sieci / timeout
```

### Konfiguracja

W `settings.py` należy uzupełnić:

```python
GOCARDLESS_SECRET_ID  = 'twój-secret-id'
GOCARDLESS_SECRET_KEY = 'twój-secret-key'
```

Klucze dostępne po bezpłatnej rejestracji na `https://bankaccountdata.gocardless.com/`.  
Do testów z sandbox klucze są wymagane, ale konto bankowe — nie.

---

## Instalacja i uruchomienie

### Wymagania

- Python 3.10+
- pip

### Kroki

```bash
# 1. Sklonuj repozytorium i przejdź do katalogu projektu
cd projekt

# 2. Utwórz i aktywuj wirtualne środowisko
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

# 3. Zainstaluj zależności
pip install django

# 4. Utwórz bazę danych
python manage.py migrate

# 5. (Opcjonalnie) Wypełnij bazę przykładowymi danymi
python manage.py seed_data

# 6. Utwórz konto administratora
python manage.py createsuperuser

# 7. Uruchom serwer deweloperski
python manage.py runserver
```

Aplikacja dostępna pod adresem: `http://127.0.0.1:8000/`  
Panel administracyjny: `http://127.0.0.1:8000/admin/`

### Testowe dane

Komenda `seed_data` tworzy:
- 10 kategorii (3 przychody, 7 wydatki) z kolorami do wykresów,
- 3 konta (PKO Konto Główne, mBank Oszczędnościowe, Gotówka),
- ~60 transakcji z ostatnich 90 dni (wynagrodzenie + losowe wydatki).

---

## Struktura projektu

```
projekt/
├── manage.py
├── finance_project/
│   ├── settings.py          # konfiguracja Django + klucze GoCardless
│   └── urls.py
└── finance/
    ├── models.py            # modele: Account, Category, Transaction,
    │                        #         BankImport, LinkedBankAccount
    ├── views.py             # widoki HTTP (dashboard, transactions, reports, banking)
    ├── services.py          # FinanceService — logika biznesowa
    ├── repositories.py      # BaseRepository + implementacje
    ├── forms.py             # formularze Django z walidacją
    ├── banking_api.py       # klient GoCardless (urllib, cache tokenów)
    ├── urls.py              # routing URL
    ├── admin.py             # rejestracja modeli w panelu admin
    ├── migrations/          # migracje bazy danych
    ├── management/
    │   └── commands/
    │       └── seed_data.py # komenda do wypełnienia bazy testowymi danymi
    └── templates/
        └── finance/
            ├── base.html           # szablon bazowy (Bootstrap 5, nawigacja)
            ├── dashboard.html      # strona główna z podsumowaniem
            ├── transactions.html   # lista transakcji z filtrowaniem
            ├── transaction_form.html
            ├── categories.html
            ├── accounts.html
            ├── reports.html        # raporty z wykresami Chart.js
            └── banking.html        # import CSV + integracja GoCardless
```

---

## Adresy URL

| URL | Widok | Opis |
|---|---|---|
| `/` | `dashboard` | Strona główna |
| `/transactions/` | `transaction_list` | Lista transakcji |
| `/transactions/add/` | `add_transaction` | Dodaj transakcję |
| `/transactions/<pk>/edit/` | `edit_transaction` | Edytuj transakcję |
| `/transactions/<pk>/delete/` | `delete_transaction` | Usuń transakcję (POST) |
| `/categories/` | `categories` | Zarządzanie kategoriami |
| `/accounts/` | `accounts` | Zarządzanie kontami |
| `/reports/` | `reports` | Raporty i wykresy |
| `/reports/chart-data/` | `reports_chart_data` | JSON dla Chart.js (AJAX) |
| `/banking/` | `banking` | Centrum bankowania (CSV + API) |
| `/banking/institutions/` | `banking_institutions` | JSON lista banków (AJAX) |
| `/banking/link/` | `banking_link_start` | Start autoryzacji OAuth |
| `/banking/callback/` | `banking_callback` | Callback po autoryzacji |
| `/banking/<pk>/sync/` | `banking_sync` | Synchronizuj transakcje (POST) |
| `/banking/<pk>/unlink/` | `banking_unlink` | Odłącz bank (POST) |