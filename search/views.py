from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.template.response import TemplateResponse

from wagtail.models import Page

# To enable logging of search queries for use with the "Promoted search results" module
# <https://docs.wagtail.org/en/stable/reference/contrib/searchpromotions.html>
# uncomment the following line and the lines indicated in the search function
# (after adding wagtail.contrib.search_promotions to INSTALLED_APPS):

# from wagtail.contrib.search_promotions.models import Query


def faq_matches(query, limit=5):
    """Ответы FAQ по словам запроса (docs/dop-stranicy/21): короткий путь к ответу."""
    from django.db.models import Q

    from core.models import FaqItem

    words = [word for word in (query or "").replace("ё", "е").split() if len(word) > 2][:5]
    if not words:
        return []
    condition = Q()
    for word in words:
        condition |= Q(question__icontains=word) | Q(answer__icontains=word)
    return list(FaqItem.objects.filter(is_published=True).filter(condition)[:limit])


def search(request):
    search_query = request.GET.get("query", None)
    page = request.GET.get("page", 1)

    # Search
    if search_query:
        search_results = Page.objects.live().search(search_query)

        # To log this query for use with the "Promoted search results" module:

        # query = Query.get(search_query)
        # query.add_hit()

    else:
        search_results = Page.objects.none()

    # Pagination
    paginator = Paginator(search_results, 10)
    try:
        search_results = paginator.page(page)
    except PageNotAnInteger:
        search_results = paginator.page(1)
    except EmptyPage:
        search_results = paginator.page(paginator.num_pages)

    return TemplateResponse(
        request,
        "search/search.html",
        {
            "search_query": search_query,
            "search_results": search_results,
            "faq_results": faq_matches(search_query),
            "faq_page": Page.objects.live().filter(slug="voprosy").first(),
        },
    )
