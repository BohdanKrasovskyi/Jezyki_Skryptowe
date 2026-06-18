from abc import ABC, abstractmethod
from django.db import transaction
from django.db.models import Sum
from decimal import Decimal
from .models import Transaction, Category, Account, BankImport


class BaseRepository(ABC):
    @abstractmethod
    def get_by_id(self, pk): ...
    @abstractmethod
    def get_all(self): ...
    @abstractmethod
    def save(self, entity): ...
    @abstractmethod
    def delete(self, pk): ...


class TransactionRepository(BaseRepository):
    def get_by_id(self, pk):
        return Transaction.objects.select_related('category', 'account').get(pk=pk)

    def get_all(self):
        return Transaction.objects.select_related('category', 'account').all()

    def save(self, entity):
        with transaction.atomic():
            entity.save()
        return entity

    def delete(self, pk):
        with transaction.atomic():
            Transaction.objects.filter(pk=pk).delete()

    def filter(self, transaction_type=None, category_id=None, account_id=None,
               date_from=None, date_to=None):
        qs = self.get_all()
        if transaction_type:
            qs = qs.filter(transaction_type=transaction_type)
        if category_id:
            qs = qs.filter(category_id=category_id)
        if account_id:
            qs = qs.filter(account_id=account_id)
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        return qs

    def total_income(self, date_from=None, date_to=None):
        qs = Transaction.objects.filter(transaction_type=Transaction.INCOME)
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        return qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    def total_expense(self, date_from=None, date_to=None):
        qs = Transaction.objects.filter(transaction_type=Transaction.EXPENSE)
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        return qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    def by_category(self, transaction_type, date_from=None, date_to=None):
        qs = Transaction.objects.filter(transaction_type=transaction_type)
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        return (
            qs.values('category__name', 'category__color')
            .annotate(total=Sum('amount'))
            .order_by('-total')
        )

    def monthly_summary(self, year):
        from django.db.models.functions import TruncMonth
        return (
            Transaction.objects.filter(date__year=year)
            .annotate(month=TruncMonth('date'))
            .values('month', 'transaction_type')
            .annotate(total=Sum('amount'))
            .order_by('month')
        )

    def bulk_create(self, transactions_list):
        with transaction.atomic():
            return Transaction.objects.bulk_create(transactions_list)


class CategoryRepository(BaseRepository):
    def get_by_id(self, pk):
        return Category.objects.get(pk=pk)

    def get_all(self):
        return Category.objects.all()

    def save(self, entity):
        entity.save()
        return entity

    def delete(self, pk):
        Category.objects.filter(pk=pk).delete()

    def get_by_type(self, category_type):
        return Category.objects.filter(category_type=category_type)


class AccountRepository(BaseRepository):
    def get_by_id(self, pk):
        return Account.objects.get(pk=pk)

    def get_all(self):
        return Account.objects.all()

    def save(self, entity):
        with transaction.atomic():
            entity.save()
        return entity

    def delete(self, pk):
        with transaction.atomic():
            Account.objects.filter(pk=pk).delete()

    def update_balance(self, account_id, delta: Decimal):
        from django.db.models import F
        with transaction.atomic():
            Account.objects.select_for_update().filter(pk=account_id).update(
                balance=F('balance') + delta
            )
            return Account.objects.get(pk=account_id)


class BankImportRepository:
    def save(self, entity):
        entity.save()
        return entity

    def get_all(self):
        return BankImport.objects.select_related('account').all()