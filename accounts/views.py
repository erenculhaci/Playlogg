from functools import wraps
from logs.models import GameLog
from common.utils import get_liked_games, get_games_by_status
from django.contrib.auth.forms import AuthenticationForm
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.hashers import check_password
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.models import User
from .forms import UserRegistrationForm, UserEditForm, ProfileEditForm, CustomPasswordChangeForm, PasswordResetForm, SetPasswordForm
from .models import Profile
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.utils.crypto import get_random_string


def login_redirect(request):
    return HttpResponseRedirect(reverse('login') + '?next=' + request.path)

# Register view with email verification
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Send verification email
            current_site = get_current_site(request)
            mail_subject = 'Activate your Playlogg account'
            message = render_to_string('core/email/verification_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': user.profile.verification_token,
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                mail_subject, message, to=[to_email]
            )
            email.content_subtype = "html"
            email.send()

            messages.success(request, 'Registration successful! Please check your email to verify your account.')
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")

    else:
        form = UserRegistrationForm()
    return render(request, 'core/user/register.html', {'form': form})


def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and user.profile.verification_token == token:
        user.profile.is_verified = True
        user.profile.verification_token = ''
        user.profile.save()
        login(request, user)
        messages.success(request, 'Your account has been verified! Welcome to Playlogg.')
        return redirect('home')
    else:
        messages.error(request, 'Activation link is invalid or has expired.')
        return redirect('login')


def verification_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        if not request.user.profile.is_verified:
            messages.warning(request, 'Email verification is required to access this feature.')
            return redirect('profile')

        return view_func(request, *args, **kwargs)

    return _wrapped_view


@login_required
def update_email(request):
    if request.method == 'POST':
        new_email = request.POST.get('new_email').strip()
        current_email = request.user.email

        # Check if new email is the same as current email
        if new_email.lower() == current_email.lower():
            messages.warning(request, 'The new email address is the same as your current email.')
            return render(request, 'core/user/update_email.html')

        # Check if email already exists
        if User.objects.filter(email=new_email).exists():
            messages.error(request, 'This email is already in use.')
            return render(request, 'core/user/update_email.html')

        # Generate a verification token
        user = request.user
        verification_token = user.profile.generate_verification_token()

        #update user's verification status to false when email is updated but not verified yet
        user.profile.is_verified = False
        user.profile.save()

        # Update user's email
        user.email = new_email
        user.save()

        # Send verification email
        current_site = get_current_site(request)
        mail_subject = 'Verify Your New Email on Playlogg'
        message = render_to_string('core/email/email_update_verification.html', {
            'user': user,
            'domain': current_site.domain,
            'new_email': new_email,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': verification_token,
        })

        email = EmailMessage(
            mail_subject,
            message,
            to=[new_email]
        )
        email.content_subtype = "html"
        email.send()

        # Store new email and verification token in session for verification
        request.session['new_email'] = new_email
        request.session['email_verification_token'] = verification_token

        messages.success(request, 'A verification email has been sent to your new email address.')
        return redirect('edit_profile')

    return render(request, 'core/user/update_email.html')


def confirm_email_update(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    # Check if user exists and token matches
    if user is not None and user.profile.verification_token == token:
        # Get the new email from the session
        new_email = request.session.get('new_email')

        if new_email:
            # Update user's email
            user.email = new_email
            user.save()

            # Update profile verification status
            user.profile.is_verified = True
            user.profile.verification_token = ''  # Clear the token after use
            user.profile.save()

            # Clear session data
            del request.session['new_email']
            del request.session['email_verification_token']

            messages.success(request, 'Your email has been successfully updated.')
            return redirect('profile')
        else:
            messages.error(request, 'No new email found in the session.')
            return redirect('update_email')
    else:
        messages.error(request, 'Invalid verification link.')
        return redirect('update_email')


def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Optional: Add a warning if not verified
            if not user.profile.is_verified:
                messages.warning(request, 'Your email is not verified. Some features may be limited.')

            return redirect('home')
        else:
            messages.error(request, 'Invalid login credentials. Please try again.')
    else:
        form = AuthenticationForm()

    return render(request, 'core/user/login.html', {'form': form})

# Password reset request view
def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                # Generate reset token
                reset_token = get_random_string(64)
                user.profile.verification_token = reset_token
                user.profile.save()

                # Send reset email
                current_site = get_current_site(request)
                mail_subject = 'Reset your Playlogg password'
                message = render_to_string('core/email/password_reset_email.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': reset_token,
                })
                to_email = email
                email_message = EmailMessage(
                    mail_subject, message, to=[to_email]
                )
                email_message.content_subtype = "html"
                email_message.send()

                messages.success(request, 'Password reset link has been sent to your email.')
                return redirect('login')
            except User.DoesNotExist:
                # Don't reveal that the user doesn't exist
                messages.success(request, 'Password reset link has been sent if the email exists.')
                return redirect('login')
    else:
        form = PasswordResetForm()

    return render(request, 'core/password/password_reset_form.html', {'form': form})


# Password reset confirm view
def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    # Check if token is valid
    if user is not None and user.profile.verification_token == token:
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                # Clear the token after successful reset
                user.profile.verification_token = ''
                user.profile.save()
                messages.success(request,
                                 'Your password has been reset successfully. You can now log in with your new password.')
                return redirect('login')
        else:
            form = SetPasswordForm(user)

        return render(request, 'core/password/password_reset_confirm.html', {'form': form})
    else:
        messages.error(request, 'The password reset link is invalid or has expired.')
        return redirect('password_reset_request')


# Change password view (for logged-in users)
@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Keep the user logged in
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('edit_profile')
    else:
        form = CustomPasswordChangeForm(request.user)

    return render(request, 'core/password/change_password.html', {'form': form})

# Resend verification email
def resend_verification(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            if not user.profile.is_verified:
                # Regenerate token
                token = user.profile.generate_verification_token()

                # Send verification email
                current_site = get_current_site(request)
                mail_subject = 'Activate your Playlogg account'
                message = render_to_string('core/email/verification_email.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': token,
                })
                to_email = user.email
                email = EmailMessage(
                    mail_subject, message, to=[to_email]
                )
                email.content_subtype = "html"
                email.send()

                messages.success(request, 'Verification email has been resent. Please check your inbox.')
            else:
                messages.info(request, 'This account is already verified. You can log in.')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')

    return render(request, 'core/user/resend_verification.html')

@login_required()
def resend_verification_from_profile(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            if not user.profile.is_verified:
                # Regenerate token
                token = user.profile.generate_verification_token()

                # Send verification email
                current_site = get_current_site(request)
                mail_subject = 'Activate your Playlogg account'
                message = render_to_string('core/email/verification_email.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': token,
                })
                to_email = user.email
                email = EmailMessage(
                    mail_subject, message, to=[to_email]
                )
                email.content_subtype = "html"
                email.send()

                messages.success(request, 'Verification email has been resent. Please check your inbox.')
            else:
                messages.info(request, 'This account is already verified. You can log in.')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')

    return redirect('profile')


@login_required
def edit_profile(request):
    # Make sure the profile exists
    profile, created = Profile.objects.get_or_create(user=request.user)

    # Store the original image path for possible deletion
    old_image = None
    if profile.profile_picture and profile.profile_picture.name != 'profile_pictures/default_profile.jpg':
        old_image = profile.profile_picture.name

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
                profile_obj.profile_picture = None  # Will be set to default in save() method

            # Save the profile with potentially new image
            profile_obj.save()

            # Now handle the deletion of the old image if needed
            if (('profile_picture' in request.FILES or 'profile_picture-clear' in request.POST) and
                    old_image and old_image != 'profile_pictures/default_profile.jpg'):
                from common.s3_utils import delete_s3_image
                delete_s3_image(old_image)

            messages.success(request, 'Your profile was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=profile)

    return render(request, 'core/user/edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


@login_required
def delete_profile(request):
    if request.method == 'POST':
        password = request.POST.get('password')

        # Verify the password
        if check_password(password, request.user.password):
            # Delete the profile picture from S3 if it exists and is not default
            profile = request.user.profile
            if profile.profile_picture and profile.profile_picture.name != 'profile_pictures/default_profile.jpg':
                from common.s3_utils import delete_s3_image
                delete_s3_image(profile.profile_picture.name)

            # Delete the user account (this will trigger the post_delete signal)
            request.user.delete()
            messages.success(request, 'Your account has been deleted.')
            return redirect('register')
        else:
            messages.error(request, 'Incorrect password. Please try again.')

    return render(request, 'core/user/delete_profile.html')


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

    return render(request, 'core/user/profile.html', {
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

    return render(request, 'core/user/profile.html', {
        'profile': user_profile,
        'liked_games': liked_games,
        'logs': logs,
        'all_logs_url': all_logs_url
    })

def user_logout(request):
    logout(request)
    return redirect('login')