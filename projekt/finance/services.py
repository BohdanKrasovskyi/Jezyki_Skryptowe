import csv
import io
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.db import transaction as db_transaction
from django.utils import timezone

from .models import Transaction, Account, BankImport, LinkedBankAccount
from .repositories import TransactionRepository, AccountRepository, BankImportRepository

_CSV_ENCODINGS = ('utf-8-sig', 'utf-8', 'cp1250', 'latin-1')


class FinanceService:
    def __init__(self):
        self.tx_repo = TransactionRepository()
        self.acc_repo = AccountRepository()
        self.import_repo = BankImportRepository()

    # ── transactions ──────────────────────────────────────────────────

    def add_transaction(self, form_data: dict) -> Transaction:
        with db_transaction.atomic():
            tx = Transaction(**form_data)
            self.tx_repo.save(tx)
            delta = tx.amount if tx.transaction_type == Transaction.INCOME else -tx.amount
            account = Account.objects.select_for_update().get(pk=tx.account_id)
            account.balance += delta
            account.save(update_fields=['balance'])
        return tx

    def update_transaction(self, pk: int, form_data: dict) -> Transaction:
        """Delete old transaction and create new one atomically — balance stays consistent."""
        with db_transaction.atomic():
            old = Transaction.objects.select_related('account').select_for_update().get(pk=pk)
            old_delta = -old.amount if old.transaction_type == Transaction.INCOME else old.amount
            old_account = Account.objects.select_for_update().get(pk=old.account_id)
            old_account.balance += old_delta
            old_account.save(update_fields=['balance'])
            old.delete()

            new_tx = Transaction(**form_data)
            new_tx.save()
            new_delta = new_tx.amount if new_tx.transaction_type == Transaction.INCOME else -new_tx.amount
            new_account = Account.objects.select_for_update().get(pk=new_tx.account_id)
            new_account.balance += new_delta
            new_account.save(update_fields=['balance'])
        return new_tx

    def delete_transaction(self, pk: int):
        with db_transaction.atomic():
            try:
                tx = Transaction.objects.select_related('account').select_for_update().get(pk=pk)
            except Transaction.DoesNotExist:
                return
            delta = -tx.amount if tx.transaction_type == Transaction.INCOME else tx.amount
            account = Account.objects.select_for_update().get(pk=tx.account_id)
            account.balance += delta
            account.save(update_fields=['balance'])
            tx.delete()

    # ── CSV import ────────────────────────────────────────────────────

    def import_csv(self, file, account_id: int, file_name: str) -> int:
        try:
            account = self.acc_repo.get_by_id(account_id)
        except Account.DoesNotExist:
            raise ValueError('Wybrane konto nie istnieje.')

        raw_bytes = file.read()
        text = self._decode(raw_bytes)
        if text is None:
            raise ValueError('Nie można odczytać pliku. Sprawdź kodowanie (UTF-8, CP1250).')

        reader = csv.DictReader(io.StringIO(text))
        if reader.fieldnames is None:
            raise ValueError('Plik CSV jest pusty lub nie zawiera nagłówków.')

        transactions = []
        balance_delta = Decimal('0.00')
        skipped = 0

        for row in reader:
            try:
                tx_type, amount = self._parse_csv_row(row)
                if amount == Decimal('0'):
                    skipped += 1
                    continue
                tx_date = self._parse_date(row)
                description = self._get_description(row)
                transactions.append(Transaction(
                    amount=amount,
                    transaction_type=tx_type,
                    account=account,
                    description=description,
                    date=tx_date,
                    is_imported=True,
                ))
                balance_delta += amount if tx_type == Transaction.INCOME else -amount
            except (KeyError, ValueError, InvalidOperation):
                skipped += 1

        if not transactions:
            if skipped:
                raise ValueError(f'Plik zawiera {skipped} wierszy, ale żaden nie mógł zostać zaimportowany. '
                                 f'Sprawdź format pliku.')
            raise ValueError('Plik CSV nie zawiera żadnych transakcji.')

        with db_transaction.atomic():
            self.tx_repo.bulk_create(transactions)
            account.balance += balance_delta
            account.save(update_fields=['balance'])
            self.import_repo.save(BankImport(
                account=account,
                file_name=file_name[:255],
                records_count=len(transactions),
            ))

        return len(transactions)

    def _decode(self, raw: bytes):
        for enc in _CSV_ENCODINGS:
            try:
                return raw.decode(enc)
            except (UnicodeDecodeError, LookupError):
                continue
        return None

    def _parse_csv_row(self, row: dict):
        raw = (
            row.get('Kwota') or row.get('Amount') or row.get('Wartość')
            or row.get('kwota') or row.get('amount') or '0'
        )
        raw = str(raw).strip().replace('\xa0', '').replace(' ', '').replace(',', '.')
        amount = Decimal(raw)
        tx_type = Transaction.INCOME if amount >= 0 else Transaction.EXPENSE
        return tx_type, abs(amount)

    def _parse_date(self, row: dict):
        raw = (
            row.get('Data') or row.get('Date') or row.get('Data operacji')
            or row.get('data') or ''
        )
        raw = str(raw).strip()
        for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d'):
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                continue
        return date.today()

    def _get_description(self, row: dict) -> str:
        val = (
            row.get('Opis') or row.get('Description') or row.get('Tytuł')
            or row.get('opis') or row.get('Nadawca/Odbiorca') or ''
        )
        return str(val).strip()[:255]

    # ── dashboard / reports ───────────────────────────────────────────

    def get_dashboard_data(self):
        today = date.today()
        month_start = today.replace(day=1)
        income = self.tx_repo.total_income(date_from=month_start)
        expense = self.tx_repo.total_expense(date_from=month_start)
        recent = self.tx_repo.filter()[:10]
        accounts = list(self.acc_repo.get_all())
        total_assets = sum(a.balance for a in accounts)
        return {
            'monthly_income': income,
            'monthly_expense': expense,
            'monthly_balance': income - expense,
            'recent_transactions': recent,
            'accounts': accounts,
            'total_assets': total_assets,
        }

    def get_report_data(self, year: int, month: int = None):
        from django.db.models import Sum
        filters = {'date__year': year}
        if month:
            filters['date__month'] = month

        income_by_cat = list(
            Transaction.objects.filter(transaction_type=Transaction.INCOME, **filters)
            .values('category__name', 'category__color')
            .annotate(total=Sum('amount'))
            .order_by('-total')
        )
        expense_by_cat = list(
            Transaction.objects.filter(transaction_type=Transaction.EXPENSE, **filters)
            .values('category__name', 'category__color')
            .annotate(total=Sum('amount'))
            .order_by('-total')
        )
        return {
            'income_by_category': income_by_cat,
            'expense_by_category': expense_by_cat,
            'monthly_summary': list(self.tx_repo.monthly_summary(year)),
            'total_income': self.tx_repo.total_income(),
            'total_expense': self.tx_repo.total_expense(),
        }

    # ── GoCardless sync ───────────────────────────────────────────────

    def sync_linked_account(self, linked: LinkedBankAccount) -> int:
        from .banking_api import get_client

        client = get_client()
        date_from = (
            linked.last_synced.date() - timedelta(days=1)
            if linked.last_synced
            else date.today() - timedelta(days=90)
        )

        raw = client.get_account_transactions(linked.gocardless_account_id, date_from=date_from)
        booked = raw.get('transactions', {}).get('booked', [])
        if not isinstance(booked, list):
            booked = []

        candidate_ids = [t.get('transactionId', '') for t in booked if t.get('transactionId')]
        existing_ids = set(
            Transaction.objects.filter(
                account=linked.account,
                external_id__in=candidate_ids,
            ).values_list('external_id', flat=True)
        ) if candidate_ids else set()

        new_txs = []
        balance_delta = Decimal('0.00')

        for raw_tx in booked:
            if not isinstance(raw_tx, dict):
                continue
            ext_id = str(raw_tx.get('transactionId') or '')
            if ext_id and ext_id in existing_ids:
                continue
            try:
                raw_amount = Decimal(str(raw_tx['transactionAmount']['amount']))
            except (KeyError, InvalidOperation, TypeError):
                continue

            tx_type = Transaction.INCOME if raw_amount >= 0 else Transaction.EXPENSE
            amount = abs(raw_amount)
            description = (
                raw_tx.get('remittanceInformationUnstructured')
                or raw_tx.get('remittanceInformationStructured')
                or raw_tx.get('creditorName')
                or raw_tx.get('debtorName')
                or ''
            )
            tx_date_str = raw_tx.get('bookingDate') or raw_tx.get('valueDate') or ''
            try:
                tx_date = datetime.strptime(str(tx_date_str), '%Y-%m-%d').date()
            except ValueError:
                tx_date = date.today()

            new_txs.append(Transaction(
                amount=amount,
                transaction_type=tx_type,
                account=linked.account,
                description=str(description)[:255],
                date=tx_date,
                is_imported=True,
                external_id=ext_id,
            ))
            balance_delta += amount if tx_type == Transaction.INCOME else -amount

        if new_txs:
            with db_transaction.atomic():
                self.tx_repo.bulk_create(new_txs)
                account = Account.objects.select_for_update().get(pk=linked.account_id)
                account.balance += balance_delta
                account.save(update_fields=['balance'])

        linked.last_synced = timezone.now()
        linked.save(update_fields=['last_synced'])
        return len(new_txs)