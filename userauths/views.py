from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login

from userauths import models as userauths_models
from userauths import forms as userauths_forms
from vendor import models as vendor_models

def register_view(request):
    if request.user.is_authenticated:
        messages.warning(request, 'You are already logged in')
        return redirect('store:index')
    
    form = userauths_forms.UserRegisterForm(request.POST or None)

    if form.is_valid():
        user = form.save()

        full_name = form.cleaned_data.get('full_name')
        email = form.cleaned_data.get('email')
        mobile = form.cleaned_data.get('mobile')
        password = form.cleaned_data.get('password1')
        user_type = form.cleaned_data.get('user_type')

        user = authenticate(email=email, password=password)
        login(request, user)

        messages.success(request, 'Account was created succesfully')
        profile = userauths_models.Profile.objects.create(full_name=full_name, mobile=mobile, user=user)

        if user_type == 'Vendor':
            vendor_models.Vendor.objects.create(user=user, store_name=full_name)
            profile.user_type = 'Vendor'
        else:
            profile.user_type = 'Customer'

        profile.save()

        next_url = request.GET.get('next', 'store:index')
        return redirect(next_url)
    
    context = {
        'form': form
    }

    return render(request, 'userauths/sign-up.html', context)