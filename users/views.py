from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.views import View

from .models import CustomUser, FriendRequest
from .forms import RegisterForm, LoginForm

@login_required
def profile_view(request):
    request.session['from_profile'] = True
    return render(request, "users/profile.html")

@login_required
def delete_account_confirmation_view(request): 
    if not request.session.get('from_profile', False): # Requires you to visit profile screen first
        return redirect(to="/profile")
    
    request.session["can_delete_account"] = True 
    return render(request, "registration/delete_account_confirmation.html")

@login_required
def delete_account(request):
    if not request.session.get("can_delete_account", False): # Requires you to visit confirmation screen first
        return redirect(to="/profile")

    if request.method == "POST":
        request.session["can_delete_account"] = False 
        user = request.user
        user.delete()

        return redirect(to="/")
    
    return redirect(to="/profile")

class RegisterView(View):
    form_class = RegisterForm
    initial = {"key": "value"}
    template_name = "registration/register.html"

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            form.save()

            return redirect(to="/")

        return render(request, self.template_name, {"form": form})

class CustomLoginView(LoginView):
    form_class = LoginForm

    def form_valid(self, form):
        remember_me = form.cleaned_data.get("remember_me")

        if not remember_me:
            # set session expiry to 0 seconds. So it will automatically close the session after the browser is closed.
            self.request.session.set_expiry(0)

            # Set session as modified to force data updates/cookie to be saved.
            self.request.session.modified = True

        # else browser session will be as long as the session cookie time "SESSION_COOKIE_AGE" defined in settings.py
        return super(CustomLoginView, self).form_valid(form)

@login_required
def send_friend_request(request, user_id):
    to_user = get_object_or_404(CustomUser, id=user_id)
    from_user = request.user

    if FriendRequest.objects.filter(from_user=from_user, to_user=to_user).exists():
        return redirect('user_list')

    try:
        FriendRequest.objects.create(from_user=from_user, to_user=to_user, status='pending')
        print("Friend request created successfully!") 
    except Exception as e:
        print(f"Error creating friend request: {e}") 

    return redirect('user_list')

@login_required
def respond_request(request, request_id, action):
    friend_request = get_object_or_404(FriendRequest, id=request_id)
    
    if request.user != friend_request.to_user:
        return redirect('home')
    
    if action == 'accept':
        friend_request.status = 'accepted'
        friend_request.save()
        # Add to friends list
        request.user.friends.add(friend_request.from_user)
        friend_request.from_user.friends.add(request.user)
    elif action == 'reject':
        friend_request.status = 'rejected'
        friend_request.save()
    
    return redirect('friend_requests')

@login_required
def friend_requests(request):
    requests = FriendRequest.objects.filter(
        to_user=request.user,
        status='pending'
    )
    return render(request, 'users/friend_requests.html', {'requests': requests})

@login_required
def friends_list(request):
    friends = request.user.friends.all()
    return render(request, 'users/friends.html', {'friends': friends})

@login_required
def user_list(request):
    current_user = request.user
    friends = current_user.friends.all()
    sent_requests = FriendRequest.objects.filter(from_user=current_user).values_list('to_user', flat=True)
    received_requests = FriendRequest.objects.filter(to_user=current_user).values_list('from_user', flat=True)

    users = CustomUser.objects.exclude(id=current_user.id).exclude(id__in=friends).exclude(id__in=sent_requests).exclude(id__in=received_requests)
    
    return render(request, 'users/user_list.html', {'users': users})
