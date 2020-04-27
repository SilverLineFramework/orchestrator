from rest_framework import generics
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from rest_framework import permissions

from wasm_files.models import WASMFiles
from wasm_files.forms import WASMFilesForm
from wasm_files.serializers import FilesSerializer

class UploadedFilesView(generics.CreateAPIView):
    """
    GET wasm_files/
    """
    permission_classes = (permissions.AllowAny,)
    
    queryset = WASMFiles.objects.all()
    serializer_class = FilesSerializer
    
    def get(self, request, *args, **kwargs):
        wasm_files = WASMFiles.objects.all()
        return render(request, 'core/home.html', { 'wasm_files': wasm_files })
        
    def post(self, request, *args, **kwargs):
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('wasm_files_list')
        #else:
        #    form = DocumentForm()
        return render(request, 'core/file_upload.html', {
            'form': form
        })

def wasm_file_upload(request):
    if request.method == 'POST':
        form = WASMFilesForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('wasm_files_list')
    else:
        form = WASMFilesForm()
    return render(request, 'core/file_upload.html', {
        'form': form
    })            