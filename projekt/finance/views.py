import csv
import io
import logging
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import DatabaseError
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .forms import (
    AccountForm, BankImportForm,
    CategoryForm, ReportFilterForm, TransactionFilterForm, TransactionForm,
)
from .models import BankImport, Transaction
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


# ── banking (CSV import only — API integration added by Mateusz) ──────────

def banking(request):
    csv_form = BankImportForm(request.POST or None, request.FILES or None)
    import_history = BankImport.objects.select_related('account').all()[:20]

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
        'import_history': import_history,
    })