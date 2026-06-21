"""
Run: python manage.py test finance
"""
import io
from datetime import date
from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse

from .models import Account, Category, Transaction
from .forms import (
    AccountForm, CategoryForm, TransactionForm,
    TransactionFilterForm, ReportFilterForm, BankImportForm,
)
from .services import FinanceService


def make_account(**kwargs):
    defaults = {'name': 'Test', 'account_type': 'checking', 'balance': Decimal('1000'), 'currency': 'PLN'}
    defaults.update(kwargs)
    return Account.objects.create(**defaults)


def make_category(name='Food', cat_type='expense'):
    return Category.objects.create(name=name, category_type=cat_type, color='#ff0000')


def make_transaction(account, amount='100', tx_type='expense', **kwargs):
    return Transaction.objects.create(
        amount=Decimal(amount), transaction_type=tx_type,
        account=account, date=date.today(), **kwargs
    )


# ── Model tests ───────────────────────────────────────────────────────────

class AccountModelTest(TestCase):
    def test_str(self):
        a = make_account(name='PKO', currency='PLN')
        self.assertIn('PKO', str(a))

    def test_default_balance(self):
        a = Account.objects.create(name='X', account_type='cash')
        self.assertEqual(a.balance, Decimal('0'))


class TransactionModelTest(TestCase):
    def setUp(self):
        self.account = make_account()

    def test_str_income(self):
        tx = make_transaction(self.account, '50', 'income', description='salary')
        self.assertIn('+', str(tx))

    def test_str_expense(self):
        tx = make_transaction(self.account, '30', 'expense')
        self.assertIn('-', str(tx))


# ── Form validation tests ─────────────────────────────────────────────────

class TransactionFormTest(TestCase):
    def setUp(self):
        self.account = make_account()

    def _base_data(self, **overrides):
        data = {
            'transaction_type': 'expense',
            'amount': '50.00',
            'account': self.account.pk,
            'description': 'lunch',
            'date': '2024-03-01',
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        form = TransactionForm(data=self._base_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_zero_amount_rejected(self):
        form = TransactionForm(data=self._base_data(amount='0'))
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_negative_amount_rejected(self):
        form = TransactionForm(data=self._base_data(amount='-10'))
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_missing_account_rejected(self):
        data = self._base_data()
        data.pop('account')
        form = TransactionForm(data=data)
        self.assertFalse(form.is_valid())

    def test_invalid_date_rejected(self):
        form = TransactionForm(data=self._base_data(date='not-a-date'))
        self.assertFalse(form.is_valid())

    def test_far_future_date_rejected(self):
        form = TransactionForm(data=self._base_data(date='3000-01-01'))
        self.assertFalse(form.is_valid())

    def test_no_category_allowed(self):
        form = TransactionForm(data=self._base_data())
        self.assertTrue(form.is_valid())


class AccountFormTest(TestCase):
    def _base(self, **kw):
        d = {'name': 'My Bank', 'account_type': 'checking',
             'balance': '0', 'currency': 'PLN'}
        d.update(kw)
        return d

    def test_valid(self):
        self.assertTrue(AccountForm(data=self._base()).is_valid())

    def test_currency_too_long(self):
        form = AccountForm(data=self._base(currency='EURO'))
        self.assertFalse(form.is_valid())
        self.assertIn('currency', form.errors)

    def test_currency_numeric_rejected(self):
        form = AccountForm(data=self._base(currency='123'))
        self.assertFalse(form.is_valid())

    def test_empty_name_rejected(self):
        form = AccountForm(data=self._base(name='   '))
        self.assertFalse(form.is_valid())

    def test_currency_normalised_to_upper(self):
        form = AccountForm(data=self._base(currency='pln'))
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['currency'], 'PLN')


class CategoryFormTest(TestCase):
    def test_valid(self):
        f = CategoryForm(data={'name': 'Food', 'category_type': 'expense', 'color': '#ff0000'})
        self.assertTrue(f.is_valid())

    def test_empty_name(self):
        f = CategoryForm(data={'name': '', 'category_type': 'expense', 'color': '#ff0000'})
        self.assertFalse(f.is_valid())


class TransactionFilterFormTest(TestCase):
    def test_date_from_after_date_to_rejected(self):
        f = TransactionFilterForm(data={'date_from': '2024-05-01', 'date_to': '2024-01-01'})
        self.assertFalse(f.is_valid())
        self.assertTrue(f.non_field_errors())

    def test_empty_filter_is_valid(self):
        f = TransactionFilterForm(data={})
        self.assertTrue(f.is_valid())

    def test_valid_date_range(self):
        f = TransactionFilterForm(data={'date_from': '2024-01-01', 'date_to': '2024-12-31'})
        self.assertTrue(f.is_valid())


class ReportFilterFormTest(TestCase):
    def test_year_out_of_range(self):
        f = ReportFilterForm(data={'year': '1800'})
        self.assertFalse(f.is_valid())

    def test_non_numeric_year(self):
        f = ReportFilterForm(data={'year': 'abc'})
        self.assertFalse(f.is_valid())

    def test_valid_year(self):
        f = ReportFilterForm(data={'year': '2024'})
        self.assertTrue(f.is_valid())


class BankImportFormTest(TestCase):
    def setUp(self):
        self.account = make_account()

    def test_non_csv_rejected(self):
        fake = io.BytesIO(b'fake data')
        fake.name = 'file.exe'
        from django.core.files.uploadedfile import InMemoryUploadedFile
        uploaded = InMemoryUploadedFile(fake, 'csv_file', 'file.exe', 'application/octet-stream', 9, None)
        f = BankImportForm(
            data={'account': self.account.pk},
            files={'csv_file': uploaded},
        )
        self.assertFalse(f.is_valid())
        self.assertIn('csv_file', f.errors)


# ── Service tests ─────────────────────────────────────────────────────────

class FinanceServiceTest(TestCase):
    def setUp(self):
        self.service = FinanceService()
        self.account = make_account(balance=Decimal('500'))
        self.cat = make_category()

    def test_add_income_updates_balance(self):
        self.service.add_transaction({
            'amount': Decimal('200'),
            'transaction_type': 'income',
            'category': self.cat,
            'account': self.account,
            'description': 'salary',
            'date': date.today(),
        })
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal('700'))

    def test_add_expense_updates_balance(self):
        self.service.add_transaction({
            'amount': Decimal('100'),
            'transaction_type': 'expense',
            'category': None,
            'account': self.account,
            'description': '',
            'date': date.today(),
        })
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal('400'))

    def test_delete_transaction_reverts_balance(self):
        tx = make_transaction(self.account, '150', 'expense')
        self.account.balance -= Decimal('150')
        self.account.save()
        self.service.delete_transaction(tx.pk)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal('500'))

    def test_delete_nonexistent_does_not_crash(self):
        self.service.delete_transaction(99999)

    def test_update_transaction_atomic(self):
        tx = make_transaction(self.account, '100', 'expense')
        self.account.balance -= Decimal('100')
        self.account.save()
        self.service.update_transaction(tx.pk, {
            'amount': Decimal('50'),
            'transaction_type': 'expense',
            'category': None,
            'account': self.account,
            'description': '',
            'date': date.today(),
        })
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal('450'))

    def test_import_csv_utf8(self):
        csv_content = 'Data,Kwota,Opis\n2024-01-01,100.00,Salary\n2024-01-02,-50.00,Food\n'
        f = io.BytesIO(csv_content.encode('utf-8'))
        f.name = 'test.csv'
        count = self.service.import_csv(f, self.account.pk, 'test.csv')
        self.assertEqual(count, 2)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal('550'))

    def test_import_csv_cp1250_encoding(self):
        csv_content = 'Data,Kwota,Opis\n2024-01-01,200.00,Wynagrodzenie\n'
        f = io.BytesIO(csv_content.encode('cp1250'))
        f.name = 'test.csv'
        count = self.service.import_csv(f, self.account.pk, 'test.csv')
        self.assertEqual(count, 1)

    def test_import_csv_empty_raises(self):
        f = io.BytesIO(b'')
        f.name = 'empty.csv'
        with self.assertRaises(ValueError):
            self.service.import_csv(f, self.account.pk, 'empty.csv')

    def test_import_csv_no_valid_rows_raises(self):
        csv_content = 'Data,Kwota,Opis\nnot-a-date,not-a-number,desc\n'
        f = io.BytesIO(csv_content.encode('utf-8'))
        f.name = 'bad.csv'
        with self.assertRaises(ValueError):
            self.service.import_csv(f, self.account.pk, 'bad.csv')

    def test_import_csv_comma_decimal(self):
        csv_content = 'Data,Kwota,Opis\n2024-01-01,"1 234,56",Test\n'
        f = io.BytesIO(csv_content.encode('utf-8'))
        f.name = 'test.csv'
        count = self.service.import_csv(f, self.account.pk, 'test.csv')
        self.assertEqual(count, 1)
        tx = Transaction.objects.filter(account=self.account, description='Test').first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.amount, Decimal('1234.56'))


# ── View tests ────────────────────────────────────────────────────────────

class DashboardViewTest(TestCase):
    def test_dashboard_ok(self):
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_with_data(self):
        acc = make_account()
        make_transaction(acc, '100', 'expense')
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 200)


class TransactionViewTest(TestCase):
    def setUp(self):
        self.account = make_account()
        self.cat = make_category()

    def test_list_empty(self):
        resp = self.client.get(reverse('transaction_list'))
        self.assertEqual(resp.status_code, 200)

    def test_list_with_filters(self):
        resp = self.client.get(reverse('transaction_list'), {
            'transaction_type': 'income', 'date_from': '2024-01-01', 'date_to': '2024-12-31'
        })
        self.assertEqual(resp.status_code, 200)

    def test_filter_bad_dates_no_crash(self):
        resp = self.client.get(reverse('transaction_list'), {
            'date_from': '2024-12-31', 'date_to': '2024-01-01'
        })
        self.assertEqual(resp.status_code, 200)

    def test_add_transaction_get(self):
        resp = self.client.get(reverse('add_transaction'))
        self.assertEqual(resp.status_code, 200)

    def test_add_transaction_valid_post(self):
        resp = self.client.post(reverse('add_transaction'), {
            'transaction_type': 'expense',
            'amount': '50.00',
            'account': self.account.pk,
            'description': 'test',
            'date': '2024-03-01',
        })
        self.assertRedirects(resp, reverse('transaction_list'))
        self.assertEqual(Transaction.objects.count(), 1)

    def test_add_transaction_zero_amount(self):
        resp = self.client.post(reverse('add_transaction'), {
            'transaction_type': 'expense',
            'amount': '0',
            'account': self.account.pk,
            'date': '2024-03-01',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_add_transaction_no_account_no_crash(self):
        resp = self.client.post(reverse('add_transaction'), {
            'transaction_type': 'expense',
            'amount': '50.00',
            'account': '',
            'date': '2024-03-01',
        })
        self.assertEqual(resp.status_code, 200)

    def test_delete_nonexistent_transaction_no_crash(self):
        resp = self.client.post(reverse('delete_transaction', args=[99999]))
        self.assertRedirects(resp, reverse('transaction_list'))

    def test_edit_transaction_get(self):
        tx = make_transaction(self.account, '100', 'expense')
        resp = self.client.get(reverse('edit_transaction', args=[tx.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_edit_nonexistent_returns_404(self):
        resp = self.client.get(reverse('edit_transaction', args=[99999]))
        self.assertEqual(resp.status_code, 404)

    def test_edit_transaction_post_updates_balance(self):
        tx = make_transaction(self.account, '100', 'expense')
        self.account.balance -= Decimal('100')
        self.account.save()
        self.client.post(reverse('edit_transaction', args=[tx.pk]), {
            'transaction_type': 'expense',
            'amount': '200.00',
            'account': self.account.pk,
            'date': '2024-03-01',
        })
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal('800'))


class ReportsViewTest(TestCase):
    def test_reports_no_data(self):
        resp = self.client.get(reverse('reports'))
        self.assertEqual(resp.status_code, 200)

    def test_reports_with_year(self):
        resp = self.client.get(reverse('reports'), {'year': '2024'})
        self.assertEqual(resp.status_code, 200)

    def test_reports_bad_year_no_crash(self):
        resp = self.client.get(reverse('reports'), {'year': 'abc'})
        self.assertEqual(resp.status_code, 200)

    def test_chart_data_bad_year(self):
        resp = self.client.get(reverse('reports_chart_data'), {'year': 'xyz'})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('monthly', data)

    def test_chart_data_bad_month(self):
        resp = self.client.get(reverse('reports_chart_data'), {'year': '2024', 'month': 'abc'})
        self.assertEqual(resp.status_code, 200)

    def test_chart_data_month_out_of_range(self):
        resp = self.client.get(reverse('reports_chart_data'), {'year': '2024', 'month': '99'})
        self.assertEqual(resp.status_code, 200)


class AccountViewTest(TestCase):
    def test_accounts_get(self):
        resp = self.client.get(reverse('accounts'))
        self.assertEqual(resp.status_code, 200)

    def test_add_account_valid(self):
        resp = self.client.post(reverse('accounts'), {
            'name': 'Savings', 'account_type': 'savings',
            'balance': '5000', 'currency': 'PLN',
        })
        self.assertRedirects(resp, reverse('accounts'))
        self.assertEqual(Account.objects.count(), 1)

    def test_add_account_bad_currency(self):
        resp = self.client.post(reverse('accounts'), {
            'name': 'Test', 'account_type': 'checking',
            'balance': '0', 'currency': 'EURO',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Account.objects.count(), 0)

    def test_delete_nonexistent_account_no_crash(self):
        resp = self.client.post(reverse('delete_account', args=[99999]))
        self.assertRedirects(resp, reverse('accounts'))


class CategoryViewTest(TestCase):
    def test_categories_get(self):
        resp = self.client.get(reverse('categories'))
        self.assertEqual(resp.status_code, 200)

    def test_add_category_valid(self):
        resp = self.client.post(reverse('categories'), {
            'name': 'Transport', 'category_type': 'expense', 'color': '#0000ff',
        })
        self.assertRedirects(resp, reverse('categories'))

    def test_add_category_empty_name(self):
        resp = self.client.post(reverse('categories'), {
            'name': '', 'category_type': 'expense', 'color': '#0000ff',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Category.objects.count(), 0)

    def test_delete_nonexistent_category_no_crash(self):
        resp = self.client.post(reverse('delete_category', args=[99999]))
        self.assertRedirects(resp, reverse('categories'))

    def test_edit_category_get(self):
        cat = make_category('Food', 'expense')
        resp = self.client.get(reverse('edit_category', args=[cat.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_edit_category_post_updates(self):
        cat = make_category('Food', 'expense')
        resp = self.client.post(reverse('edit_category', args=[cat.pk]), {
            'name': 'Jedzenie', 'category_type': 'expense', 'color': '#ff0000',
        })
        self.assertRedirects(resp, reverse('categories'))
        cat.refresh_from_db()
        self.assertEqual(cat.name, 'Jedzenie')

    def test_edit_nonexistent_category_404(self):
        resp = self.client.get(reverse('edit_category', args=[99999]))
        self.assertEqual(resp.status_code, 404)


class ExportCsvTest(TestCase):
    def setUp(self):
        self.account = make_account()
        self.cat = make_category()

    def test_export_returns_csv(self):
        make_transaction(self.account, '100', 'expense')
        resp = self.client.get(reverse('export_csv'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('text/csv', resp['Content-Type'])

    def test_export_content(self):
        make_transaction(self.account, '200', 'income', description='salary')
        resp = self.client.get(reverse('export_csv'))
        content = resp.content.decode('utf-8-sig')
        self.assertIn('salary', content)
        self.assertIn('200', content)

    def test_export_with_filter(self):
        make_transaction(self.account, '100', 'expense', description='food')
        make_transaction(self.account, '200', 'income', description='salary')
        resp = self.client.get(reverse('export_csv'), {'transaction_type': 'income'})
        content = resp.content.decode('utf-8-sig')
        self.assertIn('salary', content)
        self.assertNotIn('food', content)

    def test_export_empty_db(self):
        resp = self.client.get(reverse('export_csv'))
        self.assertEqual(resp.status_code, 200)
        lines = resp.content.decode('utf-8-sig').strip().splitlines()
        self.assertEqual(len(lines), 1)  # only header


class PaginationTest(TestCase):
    def setUp(self):
        self.account = make_account()
        for i in range(25):
            make_transaction(self.account, '10', 'expense', description=f'tx {i}')

    def test_first_page_has_20_items(self):
        resp = self.client.get(reverse('transaction_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['transactions']), 20)

    def test_second_page_has_5_items(self):
        resp = self.client.get(reverse('transaction_list'), {'page': '2'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['transactions']), 5)

    def test_invalid_page_returns_last(self):
        resp = self.client.get(reverse('transaction_list'), {'page': '999'})
        self.assertEqual(resp.status_code, 200)