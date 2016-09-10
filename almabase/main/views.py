from django.shortcuts import render, redirect
from .models import File

def index(request):
    if request.method == 'POST':
        fileObj = File()
        fileObj.name = request.POST['name']
        fileObj.desc = request.POST['desc']
        fileObj.file = request.FILES['file']
        fileObj.save()
        return redirect('/page1')
    if request.method == 'GET':
        return render(request,'main/fileUpload.html',None)
