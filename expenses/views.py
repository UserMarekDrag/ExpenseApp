from django.views.generic.list import ListView

from .forms import ExpenseSearchForm
from .models import Expense, Category
from .reports import summary_per_category
from django.utils import timezone
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.paginator import Page
from django.db.models import Sum
from django.db.models.functions import TruncMonth, TruncYear


class ExpenseListView(ListView):
    model = Expense
    paginate_by = 5
    ordering = '-date'

    def get_context_data(self, *, object_list=None, **kwargs):
        queryset = object_list if object_list is not None else self.object_list

        form = ExpenseSearchForm(self.request.GET)
        if form.is_valid():
            name = form.cleaned_data.get('name', '').strip()
            if name:
                queryset = queryset.filter(name__icontains=name)

        categories = Category.objects.all()

        total_amount = queryset.aggregate(total_amount=Sum('amount'))['total_amount']

        paginator = Paginator(queryset, self.paginate_by)
        page = self.request.GET.get('page')
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        # QuerySet to calculate total amount per year and month
        summary_per_year_month = queryset.\
            annotate(year=TruncYear('date'), month=TruncMonth('date')).\
            values('year', 'month').\
            annotate(total_amount=Sum('amount')).\
            order_by('year', 'month')

        context = super().get_context_data(
            form=form,
            object_list=queryset,
            summary_per_category=summary_per_category(queryset),
            categories=categories,
            page_obj=page_obj,
            total_amount=total_amount,
            summary_per_year_month=summary_per_year_month,
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

        # Get sort parameters from query parameters
        sort_by = self.request.GET.get('sort_by', 'date')  # Default to sort by date
        sort_order = self.request.GET.get('sort_order', 'asc')  # Default to ascending order

        # Apply sorting based on sort_by parameter
        if sort_by == 'category':
            queryset = queryset.order_by('category__name')
        elif sort_by == 'date':
            queryset = queryset.order_by('date')

        # Apply sorting order based on sort_order parameter
        if sort_order == 'desc':
            queryset = queryset.reverse()

        return queryset


class CategoryListView(ListView):
    model = Category
    paginate_by = 5
