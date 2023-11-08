from django.shortcuts import render, redirect

from article.models import UserProfile
from .forms import SignupForm

# Create your views here.

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)

        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)

            return redirect('/login/')
    else:
        form = SignupForm()

    return render(request, 'core/signup.html', {
        'form': form
    })
