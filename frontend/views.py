from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, 'index.html', {})

def encrypt(request):
    return render(request, 'encrypt.html', {})