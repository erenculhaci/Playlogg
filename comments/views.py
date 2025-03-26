from .models import Game, Comment
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

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

    return render(request, 'core/game/edit_comment.html', {'comment': comment})


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