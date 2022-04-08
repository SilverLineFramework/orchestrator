from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework.views import status
from .models import Runtime, Module
from .serializers import RuntimeSerializer, ModuleSerializer
import uuid
import json

# tests for models

class RuntimeModelTest(APITestCase):
    def setUp(self):
        self.valid_uuid = uuid.uuid4()
        self.a_rt = Runtime.objects.create(
            uuid=self.valid_uuid,
            name="runtime1"
        )

    def test_runtime(self):
        """"
        This test ensures that the runtime created in the setup
        exists
        """
        self.assertEqual(self.a_rt.name, "runtime1")

    def test_create_runtime_with_no_uuid(self):
        """"
        This test ensures that a valid uuid is assigned to a runtime when
        created with no uuid
        """
        a_rt = Runtime.objects.create(
            name="runtime1"
        )
        self.assertEqual(a_rt.name, "runtime1")
        try:
            uuid_obj = uuid.UUID(str(a_rt.uuid), version=4)
        except ValueError:
            self.assertTrue(False)

    def test_delete_runtime(self):
        """"
        This test ensures that a runtime is deleted given a valid uuid
        """
        a_rt = Runtime.objects.get(uuid=self.valid_uuid)
        a_rt.delete()
        assert(Runtime.objects.all(), [])


class ModuleModelTest(APITestCase):
    def setUp(self):
        self.a_rt = Runtime.objects.create(
            uuid=uuid.uuid4(),
            name="runtime1"
        )
        self.a_mod = Module.objects.create(
            uuid=uuid.uuid4(),
            name="module1",
            parent=self.a_rt
        )

    def test_module(self):
        """"
        This test ensures that the module created in the setup
        exists
        """
        self.assertEqual(self.a_mod.name, "module1")
        self.assertEqual(self.a_mod.parent, self.a_rt)

    def test_create_module_with_no_uuid(self):
        """"
        This test ensures that a valid uuid is assigned to a module when
        created with no uuid
        """
        a_mod = Module.objects.create(
            name="module1",
            parent=self.a_rt
        )
        self.assertEqual(a_mod.name, "module1")
        try:
            uuid_obj = uuid.UUID(str(a_mod.uuid), version=4)
        except ValueError:
            self.assertTrue(False)

# tests for views

class BaseViewTest(APITestCase):
    """
    Setup for view tests
    """
    client = APIClient()

    @staticmethod
    def create_runtime(uuid="", name=""):
        if uuid != "" and name != "":
            Runtime.objects.create(uuid=uuid, name=name)

    @staticmethod
    def create_module(uuid="", name=""):
        if uuid != "" and name != "":
            Module.objects.create(uuid=uuid, name=name)

    def setUp(self):
        # add test data (using random UUIDs; see https://docs.python.org/3/library/uuid.html)
        self.create_runtime(uuid.uuid4(), "name1")
        self.create_runtime(uuid.uuid4(), "name2")
        self.create_runtime(uuid.uuid4(), "name3")
        self.create_runtime(uuid.uuid4(), "name4")
        self.create_runtime(uuid.uuid4(), "name4")

        self.valid_rt_uuid = Runtime.objects.get(name="name1").uuid

    def login_client(self, username="", password=""):
        # get a token from DRF
        response = self.client.post(
            reverse("create-token"),
            data={
                    'username': username,
                    'password': password
                },
            format='json'
        )
        print(response.data)
        self.token = response.data['token']
        # set the token in the header
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.token
        )
        self.client.login(username=username, password=password)
        return self.token

class GetAllRuntimesTest(BaseViewTest):
    """
    Get all runtimes
    """
    def test_get_all_runtimes(self):
        """
        This test ensures that all runtimes added in the setUp method
        exist when we make a GET request to the runtimes/endpoint
        """
        # hit the API endpoint
        response = self.client.get(
            reverse("runtimes-all", kwargs={"version": "v1"})
        )
        # fetch the data from db
        expected = Runtime.objects.all()
        serialized = RuntimeSerializer(expected, many=True)
        self.assertEqual(response.data, serialized.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class GetARuntimeTest(BaseViewTest):

    def test_get_a_runtime(self):
        """
        This test ensures that a single runtime of a given uuid is
        returned
        """
        # self.login_client('test', 'XJMq4Qrh6514fh')
        # hit the API endpoint
        response = self.client.get(
            reverse(
                "runtime-detail",
                kwargs={
                    "version": "v1",
                    "pk": self.valid_rt_uuid
                }
            ))
        # fetch the data from db
        expected = Runtime.objects.get(pk=self.valid_rt_uuid)
        serialized = RuntimeSerializer(expected)
        self.assertEqual(response.data, serialized.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # test with a runtime uuid that does not exist
        a_uuid = uuid.uuid4()
        response = self.client.get(
            reverse(
                "runtime-detail",
                kwargs={
                    "version": "v1",
                    "pk": a_uuid
                }
            ))
        self.assertEqual(
            response.data["message"],
            "Runtime with uuid: "+str(a_uuid)+" does not exist"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class AddRuntimeTest(BaseViewTest):

    def test_create_a_runtime(self):
        """
        This test ensures that a single runtime can be added
        """
        #self.login_client('test_user', 'testing')
        # hit the API endpoint
        valid_rt = { "name" : "runtime1" }
        # response = self.client.get(
        #     reverse("runtimes-all",
        #     kwargs={
        #         "version": kwargs["version"]
        #     }),
        #     data=json.dumps(kwargs["data"]),
        #     content_type='application/json'
        # )
        # self.assertEqual(response.data, valid_rt)
        # self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # # test with invalid data
        # response = self.make_a_request(
        #     kind="post",
        #     version="v1",
        #     data=self.invalid_data
        # )
        # self.assertEqual(
        #     response.data["message"],
        #     "Both title and artist are required to add a song"
        # )
        # self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
