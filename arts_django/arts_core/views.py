
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login

from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import status
from rest_framework_jwt.settings import api_settings

from rest_framework import generics
from .models import Runtime, Module, Link
from .serializers import RuntimeSerializer, ModuleSerializer, LinkSerializer, TokenSerializer, UserSerializer #, RuntimeListSerializer

# Get the JWT settings
jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

# class ListRuntimesView(generics.ListAPIView):
#     """
#     Returns a list of Runtimes.
#     GET runtime/
#     """
#     queryset = Runtime.objects.all()
#     serializer_class = RuntimeSerializer

class ListRuntimesView(generics.ListCreateAPIView):
    """
    Returns a list of Runtimes.
    GET runtime/
    """
    #queryset = Runtime.objects.all()
    queryset = Runtime.objects.all()#.prefetch_related('parent')
    serializer_class = RuntimeSerializer

    #def get_serializer_class(self):
    #    if (self.request.GET.get('type') == 'tree'):

    # def get_context_data(self, **kwargs):
    #     # Call the base implementation first to get a context
    #     context = super().get_context_data(**kwargs)
    #     # Add in a QuerySet of all the books
    #     context['module_list'] = Module.objects.all()
    #     return context
    
    # def list(self, request, *args, **kwargs):
    #     # Note the use of `get_queryset()` instead of `self.queryset`
    #     #if (self.request.GET.get('type') == 'tree'):
            
    #     #else:
    #     list = []
    #     queryset = Runtime.objects.all().prefetch_related('parent')
    #     for rt in queryset:
    #         a_rt['name'] = rt.name
            
    #         print(rt.name)
    #         modules = rt.parent.all()
    #         for m in modules:
    #             print(m)
        
    #     #company.interviews.all()
    #     #print(str(queryset))
    #     serializer = RuntimeListSerializer(queryset, many=True)
        
    #     return Response(serializer.data)

        
class RuntimeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET runtime/:id/
    PUT runtime/:id/
    DELETE runtime/:id/
    """
    queryset = Runtime.objects.all()
    serializer_class = RuntimeSerializer

    def get(self, request, *args, **kwargs):
        try:
            a_rt = self.queryset.get(pk=kwargs["pk"])
            return Response(RuntimeSerializer(a_rt).data)
        except Runtime.DoesNotExist:
            return Response(
                data={
                    "message": "Runtime with uuid: {} does not exist".format(kwargs["pk"])
                },
                status=status.HTTP_404_NOT_FOUND
            )

    #@validate_request_data
    def put(self, request, *args, **kwargs):
        try:
            a_rt = self.queryset.get(pk=kwargs["pk"])
            serializer = RuntimeSerializer()
            updated_rt = serializer.update(a_rt, request.data)
            return Response(RuntimeSerializer(updated_song).data)
        except Runtime.DoesNotExist:
            return Response(
                data={
                    "message": "Runtime with uuid: {} does not exist".format(kwargs["pk"])
                },
                status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, *args, **kwargs):
        try:
            a_rt = self.queryset.get(pk=kwargs["pk"])
            a_rt.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Runtime.DoesNotExist:
            return Response(
                data={
                    "message": "Song with id: {} does not exist".format(kwargs["pk"])
                },
                status=status.HTTP_404_NOT_FOUND
            )

class ListModulesView(generics.ListCreateAPIView):
    """
    Returns a list of Modules.
    GET module/
    """
    #queryset = Runtime.objects.all()
    queryset = Module.objects.all()#.prefetch_related('parent')
    serializer_class = ModuleSerializer
    
class LoginView(generics.CreateAPIView):
    """
    POST auth/login/
    """

    # This permission class will over ride the global permission
    # class setting
    permission_classes = (permissions.AllowAny,)

    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def post(self, request, *args, **kwargs):
        username = request.data.get("username", "")
        password = request.data.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # login saves the user’s ID in the session,
            # using Django’s session framework.
            login(request, user)
            serializer = TokenSerializer(data={
                # using drf jwt utility functions to generate a token
                "token": jwt_encode_handler(
                    jwt_payload_handler(user)
                )})
            serializer.is_valid()
            return Response(serializer.data)
        return Response(status=status.HTTP_401_UNAUTHORIZED)


class RegisterUsers(generics.CreateAPIView):
    """
    POST auth/register/
    """
    permission_classes = (permissions.AllowAny,)

    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        username = request.data.get("username", "")
        password = request.data.get("password", "")
        email = request.data.get("email", "")
        if not username and not password and not email:
            return Response(
                data={
                    "message": "username, password and email is required to register a user"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        new_user = User.objects.create_user(
            username=username, password=password, email=email
        )
        return Response(
            data=UserSerializer(new_user).data,
            status=status.HTTP_201_CREATED
        )


def wasm_file_upload(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = DocumentForm()
    return render(request, 'core/model_form_upload.html', {
        'form': form
    })            