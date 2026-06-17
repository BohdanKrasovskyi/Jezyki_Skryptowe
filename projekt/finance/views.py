import csv
import io
import logging
import uuid
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import DatabaseError
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .banking_api import GoCardlessError, GoCardlessNetworkError, OBPError, OBPNetworkError, PlaidError, PlaidNetworkError
from .forms import (
    AccountForm, BankImportForm, BankLinkForm,
    CategoryForm, OBPImportForm, PlaidImportForm, ReportFilterForm, TransactionFilterForm, TransactionForm,
)
from .models import BankImport, LinkedBankAccount, Transaction
from .repositories import AccountRepository, CategoryRepository, TransactionRepository
from .services import FinanceService

logger = logging.getLogger(__name__)

tx_repo = TransactionRepository()
cat_repo = CategoryRepository()
acc_repo = AccountRepository()
service = FinanceService()


# ── dashboard ─────────────────────────────────────────────────────────────

def dashboard(request):
    data = service.get_dashboard_data()
    return render(request, 'finance/dashboard.html', data)


# ── transactions ──────────────────────────────────────────────────────────

def transaction_list(request):
    form = TransactionFilterForm(request.GET or None)
    filters = {}
    if form.is_valid():
        cd = form.cleaned_data
        if cd.get('transaction_type'):
            filters['transaction_type'] = cd['transaction_type']
        if cd.get('category'):
            filters['category_id'] = cd['category'].id
        if cd.get('account'):
            filters['account_id'] = cd['account'].id
        if cd.get('date_from'):
            filters['date_from'] = cd['date_from']
        if cd.get('date_to'):
            filters['date_to'] = cd['date_to']

    transactions_qs = tx_repo.filter(**filters)
    total_income = transactions_qs.filter(transaction_type='income').aggregate(t=Sum('amount'))['t'] or Decimal('0')
    total_expense = transactions_qs.filter(transaction_type='expense').aggregate(t=Sum('amount'))['t'] or Decimal('0')

    paginator = Paginator(transactions_qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'finance/transactions.html', {
        'transactions': page_obj,
        'page_obj': page_obj,
        'filter_form': form,
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': total_income - total_expense,
    })


def add_transaction(request):
    no_accounts = not acc_repo.get_all().exists()
    form = TransactionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        try:
            service.add_transaction({
                'amount': data['amount'],
                'transaction_type': data['transaction_type'],
                'category': data['category'],
                'account': data['account'],
                'description': data['description'],
                'date': data['date'],
            })
            messages.success(request, 'Transakcja została dodana.')
            return redirect('transaction_list')
        except Exception as exc:
            logger.exception('Error adding transaction')
            messages.error(request, f'Błąd zapisu transakcji: {exc}')
    return render(request, 'finance/transaction_form.html', {
        'form': form,
        'title': 'Dodaj transakcję',
        'no_accounts': no_accounts,
    })


def edit_transaction(request, pk):
    tx = get_object_or_404(Transaction, pk=pk)
    form = TransactionForm(request.POST or None, instance=tx)
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        try:
            service.update_transaction(pk, {
                'amount': data['amount'],
                'transaction_type': data['transaction_type'],
                'category': data['category'],
                'account': data['account'],
                'description': data['description'],
                'date': data['date'],
            })
            messages.success(request, 'Transakcja została zaktualizowana.')
            return redirect('transaction_list')
        except Transaction.DoesNotExist:
            messages.error(request, 'Transakcja nie istnieje.')
            return redirect('transaction_list')
        except Exception as exc:
            logger.exception('Error updating transaction')
            messages.error(request, f'Błąd aktualizacji: {exc}')
    return render(request, 'finance/transaction_form.html', {
        'form': form,
        'title': 'Edytuj transakcję',
        'tx': tx,
    })


@require_POST
def delete_transaction(request, pk):
    try:
        service.delete_transaction(pk)
        messages.success(request, 'Transakcja została usunięta.')
    except Exception as exc:
        logger.exception('Error deleting transaction')
        messages.error(request, f'Nie można usunąć transakcji: {exc}')
    return redirect('transaction_list')


# ── export CSV ────────────────────────────────────────────────────────────

def export_csv(request):
    form = TransactionFilterForm(request.GET or None)
    filters = {}
    if form.is_valid():
        cd = form.cleaned_data
        if cd.get('transaction_type'):
            filters['transaction_type'] = cd['transaction_type']
        if cd.get('category'):
            filters['category_id'] = cd['category'].id
        if cd.get('account'):
            filters['account_id'] = cd['account'].id
        if cd.get('date_from'):
            filters['date_from'] = cd['date_from']
        if cd.get('date_to'):
            filters['date_to'] = cd['date_to']

    transactions_qs = tx_repo.filter(**filters)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="transakcje.csv"'
    response.write('﻿')  # UTF-8 BOM for Excel compatibility

    writer = csv.writer(response)
    writer.writerow(['Data', 'Typ', 'Kwota', 'Waluta', 'Kategoria', 'Konto', 'Opis'])
    for tx in transactions_qs:
        writer.writerow([
            tx.date.strftime('%Y-%m-%d'),
            'Przychód' if tx.transaction_type == 'income' else 'Wydatek',
            tx.amount,
            tx.account.currency,
            tx.category.name if tx.category else '',
            tx.account.name,
            tx.description,
        ])
    return response


# ── categories ────────────────────────────────────────────────────────────

def categories(request):
    form = CategoryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            cat_repo.save(form.save(commit=False))
            messages.success(request, 'Kategoria dodana.')
            return redirect('categories')
        except DatabaseError as exc:
            logger.exception('Error saving category')
            messages.error(request, f'Błąd zapisu kategorii: {exc}')
    return render(request, 'finance/categories.html', {
        'form': form,
        'categories': cat_repo.get_all(),
    })


def edit_category(request, pk):
    cat = get_object_or_404(cat_repo.get_all().model, pk=pk)
    form = CategoryForm(request.POST or None, instance=cat)
    if request.method == 'POST' and form.is_valid():
        try:
            cat_repo.save(form.save(commit=False))
            messages.success(request, 'Kategoria zaktualizowana.')
            return redirect('categories')
        except DatabaseError as exc:
            logger.exception('Error updating category')
            messages.error(request, f'Błąd aktualizacji kategorii: {exc}')
    return render(request, 'finance/category_form.html', {'form': form, 'cat': cat})


@require_POST
def delete_category(request, pk):
    try:
        cat_repo.delete(pk)
        messages.success(request, 'Kategoria usunięta.')
    except Exception as exc:
        logger.exception('Error deleting category')
        messages.error(request, f'Nie można usunąć kategorii: {exc}')
    return redirect('categories')


# ── accounts ──────────────────────────────────────────────────────────────

def accounts(request):
    form = AccountForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            acc_repo.save(form.save(commit=False))
            messages.success(request, 'Konto dodane.')
            return redirect('accounts')
        except DatabaseError as exc:
            logger.exception('Error saving account')
            messages.error(request, f'Błąd zapisu konta: {exc}')
    return render(request, 'finance/accounts.html', {
        'form': form,
        'accounts': acc_repo.get_all(),
    })


@require_POST
def delete_account(request, pk):
    try:
        acc_repo.delete(pk)
        messages.success(request, 'Konto usunięte.')
    except Exception as exc:
        logger.exception('Error deleting account')
        messages.error(request, f'Nie można usunąć konta: {exc}')
    return redirect('accounts')


# ── reports ───────────────────────────────────────────────────────────────

def reports(request):
    form = ReportFilterForm(request.GET or None)
    year = date.today().year
    month = None
    if form.is_valid():
        year = form.cleaned_data['year']
        raw_month = form.cleaned_data.get('month', '')
        month = int(raw_month) if raw_month else None

    data = service.get_report_data(year, month)
    return render(request, 'finance/reports.html', {
        'form': form,
        'year': year,
        'month': month,
        **data,
    })


def reports_chart_data(request):
    try:
        year = int(request.GET.get('year', date.today().year))
        if not (2000 <= year <= 2100):
            year = date.today().year
    except (ValueError, TypeError):
        year = date.today().year

    try:
        raw_month = request.GET.get('month', '')
        month = int(raw_month) if raw_month else None
        if month is not None and not (1 <= month <= 12):
            month = None
    except (ValueError, TypeError):
        month = None

    data = service.get_report_data(year, month)

    monthly = {}
    for row in data['monthly_summary']:
        m = row['month'].strftime('%Y-%m')
        monthly.setdefault(m, {'income': 0, 'expense': 0})
        monthly[m][row['transaction_type']] = float(row['total'])

    return JsonResponse({
        'income_by_category': [
            {
                'name': r['category__name'] or 'Brak kategorii',
                'total': float(r['total']),
                'color': r['category__color'] or '#6c757d',
            }
            for r in data['income_by_category']
        ],
        'expense_by_category': [
            {
                'name': r['category__name'] or 'Brak kategorii',
                'total': float(r['total']),
                'color': r['category__color'] or '#6c757d',
            }
            for r in data['expense_by_category']
        ],
        'monthly': monthly,
    })


# ── banking ───────────────────────────────────────────────────────────────

def banking(request):
    csv_form = BankImportForm(request.POST or None, request.FILES or None)
    import_history = BankImport.objects.select_related('account').all()[:20]
    linked_accounts = LinkedBankAccount.objects.select_related('account').all()

    if request.method == 'POST' and csv_form.is_valid():
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            messages.error(request, 'Nie przesłano pliku.')
        else:
            account_id = csv_form.cleaned_data['account'].id
            try:
                count = service.import_csv(csv_file, account_id, csv_file.name)
                messages.success(request, f'Zaimportowano {count} transakcji z pliku CSV.')
                return redirect('banking')
            except ValueError as exc:
                messages.error(request, str(exc))
            except Exception as exc:
                logger.exception('CSV import failed')
                messages.error(request, f'Błąd importu: {exc}')

    return render(request, 'finance/banking.html', {
        'csv_form': csv_form,
        'plaid_form': PlaidImportForm(),
        'import_history': import_history,
        'linked_accounts': linked_accounts,
        'link_form': BankLinkForm(),
    })


def banking_institutions(request):
    country = request.GET.get('country', 'pl')
    if len(country) != 2 or not country.isalpha():
        country = 'pl'
    try:
        from .banking_api import get_client
        client = get_client()
        data = client.get_institutions(country)
        return JsonResponse({'institutions': data})
    except ValueError as exc:
        return JsonResponse({'error': str(exc)}, status=503)
    except GoCardlessNetworkError as exc:
        return JsonResponse({'error': str(exc)}, status=503)
    except GoCardlessError as exc:
        return JsonResponse({'error': str(exc)}, status=502)
    except Exception as exc:
        logger.exception('banking_institutions failed')
        return JsonResponse({'error': 'Wewnętrzny błąd serwera.'}, status=500)


def banking_link_start(request):
    if request.method != 'POST':
        return redirect('banking')
    form = BankLinkForm(request.POST)
    if not form.is_valid():
        for field_errors in form.errors.values():
            for error in field_errors:
                messages.error(request, error)
        return redirect('banking')
    try:
        from .banking_api import get_client
        client = get_client()
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect('banking')
    institution_id = form.cleaned_data['institution_id']
    institution_name = form.cleaned_data['institution_name']
    institution_logo = form.cleaned_data.get('institution_logo', '')
    local_account = form.cleaned_data['account']
    reference = str(uuid.uuid4())
    redirect_uri = request.build_absolute_uri('/banking/callback/')
    try:
        req_data = client.create_requisition(institution_id, redirect_uri, reference)
    except GoCardlessNetworkError as exc:
        messages.error(request, f'Brak połączenia z GoCardless: {exc.detail}')
        return redirect('banking')
    except GoCardlessError as exc:
        detail = exc.detail
        if isinstance(detail, dict):
            detail = detail.get('detail', str(detail))
        messages.error(request, f'Błąd GoCardless: {detail}')
        return redirect('banking')
    except Exception as exc:
        logger.exception('create_requisition failed')
        messages.error(request, 'Nieoczekiwany błąd podczas łączenia z bankiem.')
        return redirect('banking')
    LinkedBankAccount.objects.create(
        account=local_account,
        institution_id=institution_id,
        institution_name=institution_name[:200],
        institution_logo=institution_logo[:500],
        requisition_id=req_data['id'],
        reference=reference,
        status=LinkedBankAccount.PENDING,
    )
    return redirect(req_data['link'])


def banking_callback(request):
    reference = request.GET.get('ref', '').strip()
    if not reference:
        messages.error(request, 'Brakujący parametr autoryzacji.')
        return redirect('banking')
    linked = get_object_or_404(LinkedBankAccount, reference=reference)
    try:
        from .banking_api import get_client
        client = get_client()
        req_data = client.get_requisition(linked.requisition_id)
    except (GoCardlessError, GoCardlessNetworkError, ValueError) as exc:
        linked.status = LinkedBankAccount.ERROR
        linked.save(update_fields=['status'])
        messages.error(request, f'Błąd autoryzacji: {exc}')
        return redirect('banking')
    except Exception as exc:
        logger.exception('banking_callback failed')
        linked.status = LinkedBankAccount.ERROR
        linked.save(update_fields=['status'])
        messages.error(request, 'Nieoczekiwany błąd podczas autoryzacji.')
        return redirect('banking')
    gc_accounts = req_data.get('accounts', [])
    if not gc_accounts:
        linked.status = LinkedBankAccount.ERROR
        linked.save(update_fields=['status'])
        messages.warning(request, 'Bank nie zwrócił żadnych kont. Spróbuj ponownie.')
        return redirect('banking')
    linked.gocardless_account_id = gc_accounts[0]
    linked.status = LinkedBankAccount.LINKED
    linked.save(update_fields=['gocardless_account_id', 'status'])
    messages.success(request, f'Konto "{linked.institution_name}" zostało połączone!')
    return redirect('banking')


@require_POST
def banking_sync(request, pk):
    linked = get_object_or_404(LinkedBankAccount, pk=pk, status=LinkedBankAccount.LINKED)
    try:
        count = service.sync_linked_account(linked)
        messages.success(request, f'Zsynchronizowano {count} nowych transakcji z {linked.institution_name}.')
    except GoCardlessNetworkError as exc:
        messages.error(request, f'Brak połączenia z GoCardless: {exc.detail}')
    except (GoCardlessError, ValueError) as exc:
        messages.error(request, f'Błąd synchronizacji: {exc}')
    except Exception as exc:
        logger.exception('banking_sync failed')
        messages.error(request, f'Nieoczekiwany błąd synchronizacji: {exc}')
    return redirect('banking')


@require_POST
def banking_unlink(request, pk):
    linked = get_object_or_404(LinkedBankAccount, pk=pk)
    try:
        from .banking_api import get_client
        client = get_client()
        client.delete_requisition(linked.requisition_id)
    except Exception:
        pass
    linked.delete()
    messages.success(request, 'Połączenie bankowe zostało usunięte.')
    return redirect('banking')


def banking_demo_auth(request):
    reference = request.GET.get('ref', '').strip()
    if not reference:
        messages.error(request, 'Brakujący parametr demo.')
        return redirect('banking')
    return render(request, 'finance/banking_demo_auth.html', {'reference': reference})


@require_POST
def banking_plaid_import(request):
    form = PlaidImportForm(request.POST)
    if not form.is_valid():
        for errs in form.errors.values():
            for err in errs:
                messages.error(request, err)
        return redirect('banking')
    account_id = form.cleaned_data['account'].id
    try:
        count = service.import_from_plaid(account_id)
        if count:
            messages.success(request, f'Zaimportowano {count} transakcji z Plaid Sandbox (First Platypus Bank).')
        else:
            messages.info(request, 'Brak nowych transakcji — wszystkie już są w bazie.')
    except (PlaidError, PlaidNetworkError) as exc:
        messages.error(request, f'Błąd Plaid API: {exc}')
    except ValueError as exc:
        messages.error(request, str(exc))
    except Exception as exc:
        logger.exception('Plaid import failed')
        messages.error(request, f'Nieoczekiwany błąd: {exc}')
    return redirect('banking')


@require_POST
def banking_obp_import(request):
    form = OBPImportForm(request.POST)
    if not form.is_valid():
        for errs in form.errors.values():
            for err in errs:
                messages.error(request, err)
        return redirect('banking')
    account_id = form.cleaned_data['account'].id
    try:
        count, n_accounts = service.import_from_obp(account_id)
        if count:
            messages.success(request, f'Pobrano {count} nowych transakcji z Open Bank Project ({n_accounts} kont znalezionych).')
        elif n_accounts:
            messages.info(request, f'Połączono z OBP API ✓ — znaleziono {n_accounts} kont, brak transakcji historycznych.')
        else:
            messages.warning(request, 'Brak kont w OBP — sprawdź dane logowania.')
    except (OBPError, OBPNetworkError) as exc:
        messages.error(request, f'Błąd OBP API: {exc}')
    except ValueError as exc:
        messages.error(request, str(exc))
    except Exception as exc:
        logger.exception('OBP import failed')
        messages.error(request, f'Nieoczekiwany błąd: {exc}')
    return redirect('banking')