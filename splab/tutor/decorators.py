from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .models import Tutor


def tutor_required(view_func):
    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not Tutor.objects.filter(user=request.user).exists():
            messages.error(request, 'Tutor access required.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)

    return _wrapped
