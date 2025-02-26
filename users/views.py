from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.views import View

from .forms import RegisterForm, LoginForm

@login_required
def profile_view(request):
    request.session['from_profile'] = True
    return render(request, "registration/profile.html")

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
    