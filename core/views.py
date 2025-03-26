from django.db.models import Count, F, Q
from games.models import Game
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.shortcuts import render
from django.contrib.auth.models import User

def home(request):
    # Get the sort parameter from the URL
    sort = request.GET.get('sort', 'recent')  # Default to 'recent' if not specified

    # Base queryset
    games_queryset = Game.objects.all()

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
        for genre in genres:
            games_queryset = games_queryset.filter(genres__contains=[genre])

    if platforms:
        for platform in platforms:
            games_queryset = games_queryset.filter(platforms__contains=[platform])

    if studio:
        games_queryset = games_queryset.filter(studio__icontains=studio)

    if year_from:
        games_queryset = games_queryset.filter(release_date__year__gte=year_from)
    if year_to:
        games_queryset = games_queryset.filter(release_date__year__lte=year_to)

    # Rating filter logic
    if rating_from or rating_to:
        from django.db.models import Avg
        games_queryset = games_queryset.annotate(avg_rating=Avg('logs__rating'))
        if rating_from:
            games_queryset = games_queryset.filter(avg_rating__gte=float(rating_from))
        if rating_to:
            games_queryset = games_queryset.filter(avg_rating__lte=float(rating_to))

    # Sort logic
    if sort == 'recent':
        games_queryset = games_queryset.order_by('-id')
    elif sort == 'popular':
        games_queryset = games_queryset.annotate(
            log_count=Count('logs', distinct=True),
            comment_count=Count('comments', distinct=True),
            like_count=Count('liked_by', distinct=True),
            popularity_score=F('log_count') + F('comment_count') + F('like_count')
        ).order_by('-popularity_score')
    elif sort == 'name':
        games_queryset = games_queryset.order_by('name')

    # Pagination
    paginator = Paginator(games_queryset, 12)  # Show 12 games per page
    page = request.GET.get('page')
    games = paginator.get_page(page)

    # Get filter options
    all_genres = Game.objects.values_list('genres', flat=True).distinct()
    unique_genres = set()
    for game_genres in all_genres:
        if game_genres:
            for genre in game_genres:
                unique_genres.add(genre)

    all_platforms = Game.objects.values_list('platforms', flat=True).distinct()
    unique_platforms = set()
    for game_platforms in all_platforms:
        if game_platforms:
            for platform in game_platforms:
                unique_platforms.add(platform)

    all_studios = Game.objects.values_list('studio', flat=True).distinct()

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

    context = {
        'games': games,
        'genres': sorted(unique_genres),
        'platforms': sorted(unique_platforms),
        'studios': sorted(all_studios),
        'current_filters': current_filters,
        'sort': sort
    }

    return render(request, 'core/home.html', context)

# Search view
def search(request):
    query = request.GET.get('query', '')
    games = Game.objects.filter(Q(name__icontains=query))
    users = User.objects.filter(Q(username__icontains=query))

    game_results = [{'id': game.id, 'name': game.name} for game in games]
    user_results = [{'id': user.id, 'username': user.username} for user in users]

    return JsonResponse({
        'games': game_results,
        'users': user_results
    })