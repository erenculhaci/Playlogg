from .models import Game
from logs.models import GameLog
from .forms import GameLogForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from common.utils import get_games_by_status

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

    return render(request, 'core/game/log_form.html', {'form': form, 'game': game, 'status_choices': status_choices})


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

    return render(request, 'core/game/log_form.html', {'form': form, 'game': log.game, 'status_choices': status_choices})


@login_required
def delete_log(request, log_id):
    log = get_object_or_404(GameLog, id=log_id, user=request.user)
    game_id = log.game.id
    referer_url = request.META.get('HTTP_REFERER')
    log.delete()
    return redirect(referer_url if referer_url else 'game_detail', game_id=game_id)

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

    return render(request, 'core/game/all_logs.html', {
        'logs': logs,
        'user': user,
        'status_choices': status_choices
    })