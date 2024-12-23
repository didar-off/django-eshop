from django.core.paginator import Paginator

def paginate_queryset(reqest, queryset, per_page):
    paginator = Paginator(queryset, per_page)
    page_number = reqest.GET.get('page')
    return paginator.get_page(page_number)