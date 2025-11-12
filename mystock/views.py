from django.shortcuts import render


def home_view(request):
    return render(request, 'home.html')


def legal_page(request):
    return render(request, 'legal_page.html')


def policy_cookies(request):
    return render(request, 'policy_cookies.html')


def locked_start(request):
    return render(request, 'locked_start.html')
