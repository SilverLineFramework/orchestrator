from django import forms

from wasm_files.models import WASMFiles

class WASMFilesForm(forms.ModelForm):
    class Meta:
        model = WASMFiles
        fields = ('description', 'wasm_file', )