import factory
from django.contrib.auth import get_user_model

from ledgerflow.apps.accounts.models import Membership, Organization
from ledgerflow.apps.budgets.models import Budget
from ledgerflow.apps.expenses.models import Category, Expense

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    full_name = factory.Faker("name")
    password = factory.PostGenerationMethodCall("set_password", "password123")


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: f"Org {n}")


class MembershipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Membership

    user = factory.SubFactory(UserFactory)
    organization = factory.SubFactory(OrganizationFactory)
    role = Membership.Role.EMPLOYEE


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.Sequence(lambda n: f"Category {n}")


class ExpenseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Expense

    organization = factory.LazyAttribute(lambda o: o.category.organization)
    submitter = factory.SubFactory(UserFactory)
    category = factory.SubFactory(CategoryFactory)
    title = "Taxi"
    description = "Client visit"
    amount = "50.00"
    currency = "USD"
    incurred_on = factory.Faker("date_object")
    status = Expense.Status.DRAFT


class BudgetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Budget

    organization = factory.SubFactory(OrganizationFactory)
    category = None
    limit_amount = "100.00"
    currency = "USD"
    period_start = factory.Faker("date_object")
    period_end = factory.Faker("date_object")
