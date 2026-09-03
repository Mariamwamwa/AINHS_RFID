from django.shortcuts import render

def home(request):
    return render(request, 'Authentication/Home_Page.html')

def login_page(request):
    return render(request, 'Authentication/Login_Page.html')