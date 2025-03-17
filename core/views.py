from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Game, Comment, Profile, GameLog, User
from .forms import GameLogForm
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q

# Home page view
def home(request):
    games = Game.objects.all()
    return render(request, 'core/home.html', {'games': games})

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

# Add a game view
@login_required
def add_game(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        release_date = request.POST.get('release_date')

        # Create the game and assign the logged-in user to 'added_by'
        game = Game.objects.create(
            name=name,
            description=description,
            release_date=release_date,
            added_by=request.user
        )
        return redirect('home')
    return render(request, 'core/add_game.html')


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
            return redirect('game_detail', game_id=log.game.id)
    else:
        form = GameLogForm(instance=log)

    status_choices = GameLog.STATUS_CHOICES

    return render(request, 'core/log_form.html', {'form': form, 'game': log.game, 'status_choices': status_choices})


@login_required
def delete_log(request, log_id):
    log = get_object_or_404(GameLog, id=log_id, user=request.user)
    game_id = log.game.id
    log.delete()
    return redirect('game_detail', game_id=game_id)

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
        return redirect('game_detail', game_id=game.id)

    return redirect('game_detail', game_id=game.id)


@login_required
def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if request.user in comment.likes.all():
        comment.likes.remove(request.user)
    else:
        comment.likes.add(request.user)

    return redirect('game_detail', game_id=comment.game.id)


# Edit comment view
@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user != comment.user:
        return redirect('home')

    if request.method == 'POST':
        comment.text = request.POST.get('comment')
        comment.save()
        return redirect('game_detail', game_id=comment.game.id)

    return render(request, 'core/edit_comment.html', {'comment': comment})


# Delete comment view
@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user != comment.user:
        return redirect('home')

    comment.delete()
    return redirect('game_detail', game_id=comment.game.id)


# Game detail view
def game_detail(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    comments = game.comments.filter(parent__isnull=True).order_by('-created_at')
    logs_with_notes = game.logs.filter(notes__isnull=False).exclude(notes="").order_by('-created_at')
    return render(request, 'core/game_detail.html', {'game': game, 'comments': comments, 'logs_with_notes': logs_with_notes})

def user_logout(request):
    logout(request)
    return redirect('login')