from django.views.generic.list import ListView

from .forms import ExpenseSearchForm
from .models import Expense, Category
from .reports import summary_per_category
from django.utils import timezone


class ExpenseListView(ListView):
    model = Expense
    paginate_by = 5

    def get_context_data(self, *, object_list=None, **kwargs):
        queryset = object_list if object_list is not None else self.object_list

        form = ExpenseSearchForm(self.request.GET)
        if form.is_valid():
            name = form.cleaned_data.get('name', '').strip()
            if name:
                queryset = queryset.filter(name__icontains=name)

        categories = Category.objects.all()
        context = super().get_context_data(
            form=form,
            object_list=queryset,
            summary_per_category=summary_per_category(queryset),
            categories=categories,
            **kwargs)
        return context

    def get_queryset(self):
        queryset = super().get_queryset()

        date_from = self.request.GET.get('from')
        date_to = self.request.GET.get('to')

        if date_from and date_to:
            queryset = queryset.filter(date__range=(date_from, date_to))
        elif date_from:
            queryset = queryset.filter(date__gte=date_from)
        elif date_to:
            queryset = queryset.filter(date__lte=date_to)

        categories = self.request.GET.getlist('categories')

        if categories:
            queryset = queryset.filter(category__name__in=categories)

        return queryset


class CategoryListView(ListView):
    model = Category
    paginate_by = 5
