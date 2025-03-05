from django.core.files import File
from urllib.request import urlopen
from tempfile import NamedTemporaryFile

def save_profile_picture(strategy, details, backend, user=None, *args, **kwargs):
    avatar_url = None

    if backend.name == "github":
        avatar_url = kwargs["response"].get("avatar_url")
    elif backend.name == "google-oauth2":
        avatar_url = kwargs["response"].get("picture")

    if avatar_url:
        img_temp = NamedTemporaryFile(delete=True)
        img_temp.write(urlopen(avatar_url).read())
        img_temp.flush()

        user.profile_picture.save(f"avatar_{user.id}.jpg", File(img_temp))
        user.save()

    return {"user": user}