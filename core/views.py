from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.db.models import Count, F, Q, Avg
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Game, Comment, Profile, GameLog, User
from .forms import GameLogForm, ProfileEditForm, UserEditForm
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import os
from django.contrib.auth.hashers import check_password
from django.core.paginator import Paginator
import json

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

def login_redirect(request):
    return HttpResponseRedirect(reverse('login') + '?next=' + request.path)

# Register view
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'core/register.html', {'form': form})
# Login view
def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')  # Make sure 'home' is a valid URL in your URLs
        else:
            messages.error(request, 'Invalid login credentials. Please try again.')
    else:
        form = AuthenticationForm()

    return render(request, 'core/login.html', {'form': form})


@login_required
def edit_profile(request):
    # Make sure the profile exists
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=request.user)
        profile_form = ProfileEditForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_obj = profile_form.save(commit=False)

            # Handle profile picture
            if 'profile_picture' in request.FILES:
                profile_obj.profile_picture = request.FILES['profile_picture']
            elif 'profile_picture-clear' in request.POST:
                # This handles the case when user clears the image
                profile_obj.profile_picture = 'profile_pictures/default_profile.jpg'

            profile_obj.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=profile)

    return render(request, 'core/edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

@login_required
def delete_profile(request):
    if request.method == 'POST':
        password = request.POST.get('password')

        # Verify the password
        if check_password(password, request.user.password):
            # Delete the user account
            request.user.delete()
            messages.success(request, 'Your account has been deleted.')
            return redirect('register')
        else:
            messages.error(request, 'Incorrect password. Please try again.')

    return render(request, 'core/delete_profile.html')

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
@login_required()
def user_profile(request):
    user_profile, created = Profile.objects.get_or_create(user=request.user)
    liked_games = get_liked_games(request.user)

    # Loglar ve status filtreleme
    status_filter = request.GET.get('status', None)  # URL üzerinden status parametresini alıyoruz
    if status_filter:
        logs = get_games_by_status(request.user, status=status_filter)
    else:
        logs = GameLog.objects.filter(user=request.user).order_by('-created_at')[:4]  # Son 4 logu al

    # Tüm logları görmek için link
    all_logs_url = reverse('all_logs', kwargs={'user_id': request.user.id})

    return render(request, 'core/profile.html', {
        'profile': user_profile,
        'liked_games': liked_games,
        'logs': logs,
        'all_logs_url': all_logs_url
    })

#view another user's profile
def view_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user_profile, created = Profile.objects.get_or_create(user=user)
    liked_games = get_liked_games(user)
    logs = GameLog.objects.filter(user=user).order_by('-created_at')[:4]
    all_logs_url = reverse('all_logs', kwargs={'user_id': user.id})

    return render(request, 'core/profile.html', {
        'profile': user_profile,
        'liked_games': liked_games,
        'logs': logs,
        'all_logs_url': all_logs_url
    })

def all_logs(request, user_id):
    user = get_object_or_404(User, id=user_id)
    status_filter = request.GET.get('status', None)

    # Get logs using the existing function
    if status_filter:
        logs = get_games_by_status(user, status=status_filter).order_by('-created_at')
    else:
        logs = GameLog.objects.filter(user=user).order_by('-created_at')

    # Get status choices from model
    status_choices = GameLog.STATUS_CHOICES

    return render(request, 'core/all_logs.html', {
        'logs': logs,
        'user': user,
        'status_choices': status_choices
    })


@login_required
def add_game(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        release_date = request.POST.get('release_date')
        studio = request.POST.get('studio')

        # Parse JSON strings to Python lists
        genres = json.loads(request.POST.get('genres', '[]'))
        platforms = json.loads(request.POST.get('platforms', '[]'))

        # Create the game and assign the logged-in user to 'added_by'
        game = Game.objects.create(
            name=name,
            description=description,
            release_date=release_date,
            studio=studio,
            genres=genres,
            platforms=platforms,
            added_by=request.user
        )

        # Handle the image upload
        if 'image' in request.FILES:
            game.image = request.FILES['image']
            game.save()

        return redirect('home')
    return render(request, 'core/add_game.html')


@login_required
def edit_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)

    # Ensure the logged-in user is the one who added the game
    if game.added_by != request.user:
        messages.error(request, "You do not have permission to edit this game.")
        return redirect('game_detail', game_id=game.id)

    if request.method == 'POST':
        # Get the updated game details from the form
        game.name = request.POST.get('name')
        game.description = request.POST.get('description')
        game.release_date = request.POST.get('release_date')
        game.studio = request.POST.get('studio')

        # Parse JSON strings to Python lists
        genres = request.POST.get('genres', '[]')
        platforms = request.POST.get('platforms', '[]')

        if genres:
            game.genres = json.loads(genres)
        if platforms:
            game.platforms = json.loads(platforms)

        # Handle image updates
        if 'image' in request.FILES:
            # If there's an existing image, delete it
            if game.image and game.image.name != 'game_images/default_game.jpg':
                if os.path.isfile(game.image.path):
                    os.remove(game.image.path)

            # Save the new image
            game.image = request.FILES['image']

        # Handle image removal if requested
        if request.POST.get(
                'remove_image') == 'on' and game.image and game.image.name != 'game_images/default_game.jpg':
            if os.path.isfile(game.image.path):
                os.remove(game.image.path)
            game.image = None

        game.save()
        messages.success(request, 'Game details updated successfully!')
        return redirect('game_detail', game_id=game.id)

    return render(request, 'core/edit_game.html', {'game': game})

@login_required
def delete_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)

    # Ensure that the logged-in user added the game
    if game.added_by == request.user:
        game.delete()
        messages.success(request, 'Game deleted successfully.')
    else:
        messages.error(request, 'You do not have permission to delete this game.')

    return redirect('home')

@login_required
def like_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)

    # Check if the user already liked the game
    if request.user in game.liked_by.all():
        # If the user already liked the game, remove their like (unlike it)
        game.liked_by.remove(request.user)
        game.likes -= 1
    else:
        # If the user hasn't liked the game yet, add their like
        game.liked_by.add(request.user)
        game.likes += 1

    game.save()
    return redirect('game_detail', game_id=game.id)


@login_required
def unfavorite_game(request, game_id):
    # Get the game object
    game = get_object_or_404(Game, id=game_id)

    # Check if the game is in the user's liked list
    if game.liked_by.filter(id=request.user.id).exists():
        # Remove the user from the liked_by field
        game.liked_by.remove(request.user)

    # Redirect back to the profile page
    return redirect('profile')


def get_liked_games(user):
    return Game.objects.filter(liked_by=user)


@login_required
def add_log(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    log, created = GameLog.objects.get_or_create(user=request.user, game=game)

    if request.method == 'POST':
        form = GameLogForm(request.POST, instance=log)
        if form.is_valid():
            form.save()
            return redirect('game_detail', game_id=game.id)
    else:
        form = GameLogForm(instance=log)

    status_choices = GameLog.STATUS_CHOICES

    return render(request, 'core/log_form.html', {'form': form, 'game': game, 'status_choices': status_choices})


@login_required
def edit_log(request, log_id):
    log = get_object_or_404(GameLog, id=log_id, user=request.user)

    if request.method == 'POST':
        form = GameLogForm(request.POST, instance=log)
        if form.is_valid():
            form.save()
            referer_url = request.META.get('HTTP_REFERER')
            return redirect (referer_url if referer_url else 'game_detail', game_id=log.game.id)
    else:
        form = GameLogForm(instance=log)

    status_choices = GameLog.STATUS_CHOICES

    return render(request, 'core/log_form.html', {'form': form, 'game': log.game, 'status_choices': status_choices})


@login_required
def delete_log(request, log_id):
    log = get_object_or_404(GameLog, id=log_id, user=request.user)
    game_id = log.game.id
    referer_url = request.META.get('HTTP_REFERER')
    log.delete()
    return redirect(referer_url if referer_url else 'game_detail', game_id=game_id)

def get_games_by_status(user, status=None):
    if status:
        return GameLog.objects.filter(user=user, status=status)
    return GameLog.objects.filter(user=user)

@login_required
def add_comment(request, game_id):
    game = get_object_or_404(Game, id=game_id)

    user_comments_count = Comment.objects.filter(user=request.user, game=game).count()
    if user_comments_count >= 5:
        messages.error(request, "You can only have up to 5 comments. Delete one to add another.")
        return redirect('game_detail', game_id=game.id)

    if request.method == 'POST':
        text = request.POST.get('comment')
        parent_id = request.POST.get('parent_id')
        parent_comment = Comment.objects.get(id=parent_id) if parent_id else None

        Comment.objects.create(game=game, user=request.user, text=text, parent=parent_comment)
        messages.success(request, "Comment added successfully!")
        # Changed redirect to include fragment
        return HttpResponseRedirect(reverse('game_detail', kwargs={'game_id': game.id}) + '#comments')

    return redirect('game_detail', game_id=game.id)


@login_required
def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if request.user in comment.likes.all():
        comment.likes.remove(request.user)
    else:
        comment.likes.add(request.user)

    # Changed redirect to include fragment
    return HttpResponseRedirect(reverse('game_detail', kwargs={'game_id': comment.game.id}) + '#comments')


# Edit comment view
@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user != comment.user:
        return redirect('home')

    if request.method == 'POST':
        comment.text = request.POST.get('comment')
        comment.save()
        # Changed redirect to include fragment
        return HttpResponseRedirect(reverse('game_detail', kwargs={'game_id': comment.game.id}) + '#comments')

    return render(request, 'core/edit_comment.html', {'comment': comment})


# Delete comment view
@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user != comment.user:
        return redirect('home')

    game_id = comment.game.id
    comment.delete()
    # Changed redirect to include fragment
    return HttpResponseRedirect(reverse('game_detail', kwargs={'game_id': game_id}) + '#comments')


# Game detail view
def game_detail(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    comments = game.comments.filter(parent__isnull=True).order_by('-created_at')
    logs_with_notes = game.logs.filter(notes__isnull=False).exclude(notes="").order_by('-created_at')

    # Get average rating
    average_rating = game.logs.filter(rating__isnull=False).aggregate(avg_rating=Avg('rating'))['avg_rating']

    # Get rating distribution
    ratings = [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]
    rating_distribution = []

    # Count logs for each rating value
    for rating in ratings:
        count = game.logs.filter(rating=rating).count()
        rating_distribution.append({
            'rating': rating,
            'count': count
        })

    # Get total number of ratings
    total_ratings = game.logs.filter(rating__isnull=False).count()

    return render(request, 'core/game_detail.html', {
        'game': game,
        'comments': comments,
        'logs_with_notes': logs_with_notes,
        'average_rating': average_rating,
        'rating_distribution': rating_distribution,
        'total_ratings': total_ratings
    })
def user_logout(request):
    logout(request)
    return redirect('login')