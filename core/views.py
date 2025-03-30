from django.db.models import Count, F, Q, Avg, Case, When, Value, FloatField
from games.models import Game
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.shortcuts import render
from django.contrib.auth.models import User
from django.db.models.functions import Lower
from django.core.cache import cache
from django.db import connection

def home(request):
    sort = request.GET.get('sort', 'recent')

    games_queryset = Game.objects.select_related(
    ).only(
        'id', 'name', 'release_date', 'studio', 'image', 'description',
        'genres', 'platforms'  # Only include fields needed for display
    )

    # Get filter parameters
    genres = request.GET.getlist('genres')
    platforms = request.GET.getlist('platforms')
    studio = request.GET.get('studio', '')
    year_from = request.GET.get('year_from', '')
    year_to = request.GET.get('year_to', '')
    rating_from = request.GET.get('rating_from', '')
    rating_to = request.GET.get('rating_to', '')

    # Apply filters
    if genres:
        # Use AND logic for multiple genres
        for genre in genres:
            games_queryset = games_queryset.filter(genres__contains=[genre])

    if platforms:
        # Use AND logic for multiple platforms
        for platform in platforms:
            games_queryset = games_queryset.filter(platforms__contains=[platform])

    if studio:
        games_queryset = games_queryset.filter(studio__icontains=studio)

    if year_from:
        games_queryset = games_queryset.filter(release_date__year__gte=year_from)
    if year_to:
        games_queryset = games_queryset.filter(release_date__year__lte=year_to)

    # Optimize rating filter with a single annotation
    if rating_from or rating_to:
        # Use COALESCE to convert NULL to 0 for games with no ratings
        games_queryset = games_queryset.annotate(
            avg_rating=Case(
                When(logs__rating__isnull=False, then=Avg('logs__rating')),
                default=Value(0.0),
                output_field=FloatField()
            )
        )

        if rating_from:
            games_queryset = games_queryset.filter(avg_rating__gte=float(rating_from))
        if rating_to:
            games_queryset = games_queryset.filter(avg_rating__lte=float(rating_to))

    # Optimize related counts and annotate in a single query
    games_queryset = games_queryset.annotate(
        log_count=Count('logs', distinct=True),
        comment_count=Count('comments', distinct=True),
        like_count=Count('liked_by', distinct=True)
    )

    # Sort logic - add indexes to the database for these fields
    if sort == 'recent':
        games_queryset = games_queryset.order_by('-id')
    elif sort == 'popular':
        games_queryset = games_queryset.annotate(
            popularity_score=F('log_count') + F('comment_count') + F('like_count')
        ).order_by('-popularity_score')
    elif sort == 'name':
        games_queryset = games_queryset.order_by(Lower('name'))  # Case-insensitive sorting

    # Add prefetch_related for many-to-many fields that are needed for display
    games_queryset = games_queryset.prefetch_related('liked_by')

    # Pagination
    paginator = Paginator(games_queryset, 12)  # Show 12 games per page
    page = request.GET.get('page')
    games = paginator.get_page(page)

    unique_genres = get_unique_genres()
    unique_platforms = get_unique_platforms()

    # Count active filters
    active_count = 0
    if genres: active_count += len(genres)
    if platforms: active_count += len(platforms)
    if studio: active_count += 1
    if year_from or year_to: active_count += 1
    if rating_from or rating_to: active_count += 1

    # Create current_filters dictionary with processed data
    current_filters = {
        'genres': genres,
        'platforms': platforms,
        'studio': studio,
        'year_from': year_from,
        'year_to': year_to,
        'rating_from': rating_from,
        'rating_to': rating_to,
        'active_count': active_count,
    }

    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')

    context = {
        'games': games,
        'genres': unique_genres,
        'platforms': unique_platforms,
        'current_filters': current_filters,
        'sort': sort,
        'query_params': query_params.urlencode()
    }

    return render(request, 'core/home.html', context)

# Search view
def search(request):
    query = request.GET.get('query', '').strip()

    # Use select_related to minimize database hits and only select needed fields
    games = Game.objects.filter(
        name__icontains=query
    ).only('id', 'name')[:20]  # Limit to 20 results for performance

    users = User.objects.filter(
        username__icontains=query
    ).only('id', 'username')[:20]  # Limit to 20 results for performance

    game_results = [{'id': game.id, 'name': game.name} for game in games]
    user_results = [{'id': user.id, 'username': user.username} for user in users]

    return JsonResponse({
        'games': game_results,
        'users': user_results
    })


def search_studios(request):
    term = request.GET.get('term', '').strip()

    if not term or len(term) < 2:
        return JsonResponse({'studios': []})

    # Try to get from cache first
    cache_key = f'studio_search_{term}'
    cached_result = cache.get(cache_key)

    if cached_result is not None:
        return JsonResponse({'studios': cached_result})

    # If not in cache, search in database
    # Using icontains for case-insensitive search
    studios = Game.objects.filter(studio__icontains=term) \
                  .values_list('studio', flat=True) \
                  .distinct() \
                  .order_by('studio')[:20]  # Limit to 20 results for performance

    result = list(studios)

    # Cache for 15 minutes
    cache.set(cache_key, result, 15 * 60)

    return JsonResponse({'studios': result})

def get_unique_genres():
    # Try to get from cache first
    cache_key = 'game_unique_genres'
    cached_result = cache.get(cache_key)

    if cached_result is not None:
        return cached_result

    # If not in cache, fetch from database
    query = """
        SELECT DISTINCT jsonb_array_elements_text(genres) as genre
        FROM games_game
        WHERE genres IS NOT NULL
        ORDER BY genre
    """

    with connection.cursor() as cursor:
        cursor.execute(query)
        result = [row[0] for row in cursor.fetchall()]

    # Cache for 1 hour
    cache.set(cache_key, result, 60 * 60)
    return result


def get_unique_platforms():
    # Try to get from cache first
    cache_key = 'game_unique_platforms'
    cached_result = cache.get(cache_key)

    if cached_result is not None:
        return cached_result

    # If not in cache, fetch from database
    query = """
        SELECT DISTINCT jsonb_array_elements_text(platforms) as platform
        FROM games_game
        WHERE platforms IS NOT NULL
        ORDER BY platform
    """

    with connection.cursor() as cursor:
        cursor.execute(query)
        result = [row[0] for row in cursor.fetchall()]

    # Cache for 1 hour
    cache.set(cache_key, result, 60 * 60)
    return result