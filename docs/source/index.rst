.. StudySync documentation master file, created by
   sphinx-quickstart on Thu Feb 13 15:43:02 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.
===========
StudySync documentation!
===========

Welcome to StudySync documentation.

StudySync is a collaborative web application designed to transform the way students connect, study, and succeed together. Unlike traditional study groups or generic messaging platforms, StudySync provides a structured, scalable environment tailored specifically for academic collaboration. The platform makes it easy to find or create study groups based on courses, availability, and preferred study methods-removing the friction from group formation and scheduling.


===============================
Login and Accounts
===============================

.. module:: users.views

Overview
------------
This module provides user authentication (login, registration, account deletion).

Features:

- User registration and login (with "remember me" support)
- Profile management and secure account deletion


It leverages Django's authentication system, custom forms, and session management for secure and user-friendly workflows.

Usage
=====

Registration
=========

.. image:: register_page.jpg
   :width: 800
   :alt: Description

- Users register via the ``/register/`` page.
- Registration uses a custom form (``RegisterForm``). On success, the user is redirected to the home page.


.. code-block:: python

   # Code for Regirtering an Account
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

Login
=======

.. image:: sign_in_page.jpg
   :width: 800
   :alt: Description

Log In Options:
   * Log into Existing Account
   * Log in using GitHub
   * Log in using Google

- Users log in via a custom login page (``CustomLoginView``) with optional "remember me" functionality.

Remember Me Functionality
-------------------------

- The login view checks the "remember me" field. If not set, the session expires when the browser closes, improving security for shared devices.
- If "remember me" is not selected, the session expires when the browser closes.

Profile and Account Deletion
====================

.. image:: profile_page.jpg
   :width: 800
   :alt: Description

- Users can view their profile at ``/profile/``.
- Users can view their calender if thay have one linked.
- Users have access to "Create Session", "My Modules", "Upload" and "Log out". These allow for the user to navigate through the app.

.. code-block:: python

   # Code for Viewing Account

   @login_required
   def profile_view(request):
      request.session['from_profile'] = True
      return render(request, "users/profile.html")

.. image:: delete_account.jpg
   :width: 800
   :alt: Description

- Account deletion requires visiting the profile and confirmation pages in order.


.. code-block:: python

   # Code for Deleting Account

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

Troubleshooting
--------------

- If account deletion redirects unexpectedly, ensure session flags are being set correctly by visiting the profile and confirmation pages in order.
- If friend requests are not appearing, check for duplicate requests or incorrect user IDs.
- For login issues, verify that the custom login form inherits from Django's ``AuthenticationForm`` and includes the "remember me" field.


Troubleshooting
===============

- If account deletion redirects unexpectedly, ensure session flags are being set correctly by visiting the profile and confirmation pages in order.
- If friend requests are not appearing, check for duplicate requests or incorrect user IDs.
- For login issues, verify that the custom login form inherits from Django's ``AuthenticationForm`` and includes the "remember me" field.


=========
Social
=========


Friend Requests
-------------

- Users can send friend requests to others.
- Requests can be accepted or rejected.
- Accepted users are added to each other's friends lists.
- Friend request system (send, accept, reject)
- Friends list and user discovery

Sending a Friend Request
-----------------

.. code-block:: python

   # Sending Friend Request

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


Responding to Friend Request
----------------------

.. code-block:: python

   # Respodning to Friend Request

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

Friend Requests
---------------

.. code-block:: python

   #Friend Requests

   def friend_requests(request):
    requests = FriendRequest.objects.filter(
        to_user=request.user,
        status='pending'
    )
    return render(request, 'users/friend_requests.html', {'requests': requests})

Friends List
------------

.. code-block:: python

   # Friends List

   def friends_list(request):
    friends = request.user.friends.all()
    return render(request, 'users/friends.html', {'friends': friends})

Friend Request Integrity
-----------------------

- Duplicate friend requests are prevented by checking for existing requests before creation.
- Accepting a request updates both users' friends lists, ensuring bidirectional friendship.

User List
-----------

- yes

.. code-block:: python

   # User List
   
   def user_list(request):
    current_user = request.user
    friends = current_user.friends.all()
    sent_requests = FriendRequest.objects.filter(from_user=current_user).values_list('to_user', flat=True)
    received_requests = FriendRequest.objects.filter(to_user=current_user).values_list('from_user', flat=True)

    users = CustomUser.objects.exclude(id=current_user.id).exclude(id__in=friends).exclude(id__in=sent_requests).exclude(id__in=received_requests)
    
    return render(request, 'users/user_list.html', {'users': users})

==============
Additional Link
==============
- `GitHub Repository <https://github.com/UoP-1A>`_
- `Test Plans <https://docs.google.com/spreadsheets/d/16E_DPLyooj764T2RZqr4ZyrxSfrkw6ebbUSg-dzVfso/edit?gid=0#gid=0>`_
