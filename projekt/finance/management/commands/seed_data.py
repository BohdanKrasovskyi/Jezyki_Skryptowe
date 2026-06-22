import random
from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from finance.models import Category, Account, Transaction


CATEGORIES = [
    ('Wynagrodzenie', 'income', '#10b981'),
    ('Freelance', 'income', '#3b82f6'),
    ('Inwestycje', 'income', '#8b5cf6'),
    ('Zakupy spożywcze', 'expense', '#ef4444'),
    ('Transport', 'expense', '#f59e0b'),
    ('Rozrywka', 'expense', '#ec4899'),
    ('Rachunki', 'expense', '#6366f1'),
    ('Restauracje', 'expense', '#f97316'),
    ('Zdrowie', 'expense', '#14b8a6'),
    ('Odzież', 'expense', '#a855f7'),
]


class Command(BaseCommand):
    help = 'Wypełnia bazę danych przykładowymi danymi'

    def handle(self, *args, **options):
        self.stdout.write('Tworze kategorie...')
        cats = {}
        for name, cat_type, color in CATEGORIES:
            cat, _ = Category.objects.get_or_create(name=name, defaults={'category_type': cat_type, 'color': color})
            cats[name] = cat

        self.stdout.write('Tworze konta...')
        checking, _ = Account.objects.get_or_create(
            name='PKO Konto Główne',
            defaults={'account_type': 'checking', 'balance': Decimal('0'), 'currency': 'PLN', 'bank_name': 'PKO BP'}
        )
        savings, _ = Account.objects.get_or_create(
            name='mBank Oszczędnościowe',
            defaults={'account_type': 'savings', 'balance': Decimal('15000'), 'currency': 'PLN', 'bank_name': 'mBank'}
        )
        cash, _ = Account.objects.get_or_create(
            name='Gotówka',
            defaults={'account_type': 'cash', 'balance': Decimal('500'), 'currency': 'PLN'}
        )

        if Transaction.objects.filter(account=checking).exists():
            self.stdout.write(self.style.WARNING('Transakcje demo już istnieją — pomijam seedowanie.'))
            return

        self.stdout.write('Tworze transakcje...')
        today = date.today()
        balance_delta = Decimal('0')

        transactions = []
        for days_ago in range(90):
            tx_date = today - timedelta(days=days_ago)

            # Monthly salary
            if tx_date.day == 25:
                transactions.append(Transaction(
                    amount=Decimal('5500'),
                    transaction_type='income',
                    category=cats['Wynagrodzenie'],
                    account=checking,
                    description='Wynagrodzenie miesięczne',
                    date=tx_date,
                ))
                balance_delta += Decimal('5500')

            # Random expenses every 1-3 days
            if days_ago % random.randint(1, 3) == 0:
                amount = Decimal(str(round(random.uniform(15, 250), 2)))
                cat_name = random.choice(['Zakupy spożywcze', 'Transport', 'Restauracje', 'Rozrywka', 'Odzież'])
                transactions.append(Transaction(
                    amount=amount,
                    transaction_type='expense',
                    category=cats[cat_name],
                    account=checking,
                    description=cat_name,
                    date=tx_date,
                ))
                balance_delta -= amount

        Transaction.objects.bulk_create(transactions)

        # Set realistic balance
        checking.balance = Decimal('2800') + balance_delta
        checking.save()

        self.stdout.write(self.style.SUCCESS(f'Done! Added {len(transactions)} transactions.'))