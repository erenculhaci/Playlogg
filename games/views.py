from .models import Game
import json
import boto3
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from accounts.views import verification_required
from django.contrib import messages
from django.db.models import Avg


@verification_required
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
    return render(request, 'core/game/add_game.html')


@login_required
def edit_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)

    # Ensure the logged-in user is the one who added the game
    if game.added_by != request.user:
        messages.error(request, "You do not have permission to edit this game.")
        return redirect('game_detail', game_id=game.id)

    # Store the original image path for possible deletion
    old_image = None
    if game.image and game.image.name != 'game_images/default_game.jpg':
        old_image = game.image.name

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
            # If there's a new image, we'll delete the old one after saving the new one
            game.image = request.FILES['image']

        # Handle image removal if requested
        if request.POST.get('remove_image') == 'on':
            game.image = None

        # Save the game with potentially new image
        game.save()

        # Now handle the deletion of the old image if needed
        if (('image' in request.FILES or request.POST.get('remove_image') == 'on') and
                old_image and old_image != 'game_images/default_game.jpg'):
            # Initialize S3 client
            s3 = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )

            try:
                # Delete the old file from S3
                s3.delete_object(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Key=f"{settings.MEDIA_ROOT}{old_image}"
                )
            except Exception as e:
                # Log the error but don't raise it
                print(f"Error deleting old image from S3: {e}")

        messages.success(request, 'Game details updated successfully!')
        return redirect('game_detail', game_id=game.id)

    return render(request, 'core/game/edit_game.html', {'game': game})


@login_required
def delete_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)

    # Ensure that the logged-in user added the game
    if game.added_by == request.user:
        game.delete()  # This will trigger the post_delete signal
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

    return render(request, 'core/game/game_detail.html', {
        'game': game,
        'comments': comments,
        'logs_with_notes': logs_with_notes,
        'average_rating': average_rating,
        'rating_distribution': rating_distribution,
        'total_ratings': total_ratings
    })