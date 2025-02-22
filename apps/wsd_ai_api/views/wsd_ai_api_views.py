from rest_framework.views import APIView
from rest_framework.views import Request
from rest_framework.decorators import action
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny

from common.auth import TokenAuth
from common.response import result
from wsd_ai_api.serializers.wsd_ai_api_serializers import WsdAiApiSerializers


class Dataset(APIView):
    authentication_classes = [TokenAuth]

    class Create(APIView):
        authentication_classes = [TokenAuth]

        @action(methods=['POST'], detail=False)
        @permission_classes((AllowAny,))
        def post(self, request: Request):
            print(str(request.user.id))
            return result.success(WsdAiApiSerializers.DatasetCreateSerializer(data={**request.data, 'user_id': str(request.user.id)}).save_web(request.data))

    class ReEmbedding(APIView):
        authentication_classes = [TokenAuth]

        @action(methods=['PUT'], detail=False)
        @permission_classes((AllowAny,))
        def put(self, request: Request, dataset_id: str):
            return result.success(
                WsdAiApiSerializers.DatasetReEmbeddingSerializer(data={'id': dataset_id, 'user_id': request.user.id}).re_embedding())

    class ReSync(APIView):
        authentication_classes = [TokenAuth]

        @action(methods=['PUT'], detail=False)
        @permission_classes((AllowAny,))
        def put(self, request: Request, dataset_id: str):
            return result.success(WsdAiApiSerializers.DatasetReSyncSerializer(data={'id': dataset_id, 'user_id': request.user.id}).sync())


class Application(APIView):
    authentication_classes = [TokenAuth]

    class CreateAndReturnUrl(APIView):
        authentication_classes = [TokenAuth]

        @action(methods=['POST'], detail=False)
        @permission_classes((AllowAny,))
        def post(self, request: Request):
            return result.success(WsdAiApiSerializers.ApplicationCreateSerializer(data={**request.data, 'user_id': request.user.id}).create())

    class ReturnUrl(APIView):
        authentication_classes = [TokenAuth]

        @action(methods=['GET'], detail=False)
        @permission_classes((AllowAny,))
        def get(self, request: Request, app_subject_identifier: str, qa_subject_identifier: str):
            return result.success(WsdAiApiSerializers.ApplicationUrlSerializer(data={'app_subject_identifier': app_subject_identifier, 'qa_subject_identifier': qa_subject_identifier}).get_url())
