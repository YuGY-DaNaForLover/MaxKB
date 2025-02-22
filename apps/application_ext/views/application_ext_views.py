from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny


from application.views.application_views import Application
from application_ext.serializers.application_ext_serializers import ApplicationExtSerializer, ApplicationTemplateSerializer, WsdChatInfoSerializer, ApplicationQaTextSerializer
from common.response import result
from common.auth import has_permissions, TokenAuth
from common.constants.permission_constants import CompareConstants, PermissionConstants, ViewPermission, RoleConstants, Permission, Group, Operate
from common.exception.app_exception import AppAuthenticationFailed


class ApplicationExtView(Application):

    @action(methods=['POST'], detail=False)
    @has_permissions(PermissionConstants.APPLICATION_CREATE, compare=CompareConstants.AND)
    def post(self, request: Request):
        return result.success(ApplicationExtSerializer.Create(data={'user_id': request.user.id}).insert(request.data))

    class Operate(Application.Operate):

        @action(methods=['PUT'], detail=False)
        @has_permissions(ViewPermission(
            [RoleConstants.ADMIN, RoleConstants.USER],
            [lambda r, keywords: Permission(group=Group.APPLICATION, operate=Operate.MANAGE,
                                            dynamic_tag=keywords.get('application_id'))],
            compare=CompareConstants.AND))
        def put(self, request: Request, application_id: str):
            return result.success(
                ApplicationExtSerializer.Operate(
                    data={'application_id': application_id, 'user_id': request.user.id}).edit(
                    request.data))

        @action(methods=['GET'], detail=False)
        @has_permissions(ViewPermission(
            [RoleConstants.ADMIN, RoleConstants.USER, RoleConstants.APPLICATION_ACCESS_TOKEN,
             RoleConstants.APPLICATION_KEY],
            [lambda r, keywords: Permission(group=Group.APPLICATION, operate=Operate.USE,
                                            dynamic_tag=keywords.get('application_id'))],
            compare=CompareConstants.AND))
        def get(self, request: Request, application_id: str):
            return result.success(ApplicationExtSerializer.Operate(
                data={'application_id': application_id, 'user_id': request.user.id}).one())

    class Export(Application.Export):

        @action(methods="GET", detail=False)
        @has_permissions(lambda r, keywords: Permission(group=Group.APPLICATION, operate=Operate.MANAGE,
                                                        dynamic_tag=keywords.get('application_id')))
        def get(self, request: Request, application_id: str):
            return ApplicationExtSerializer.Operate(
                data={'application_id': application_id, 'user_id': request.user.id}).export()

    class Import(Application.Import):

        @action(methods="POST", detail=False)
        @has_permissions(RoleConstants.ADMIN, RoleConstants.USER)
        def post(self, request: Request):
            return result.success(ApplicationExtSerializer.Import(
                data={'user_id': request.user.id, 'file': request.FILES.get('file')}).import_())

    class Profile(APIView):
        authentication_classes = [TokenAuth]

        @action(methods=['GET'], detail=False)
        def get(self, request: Request):
            if 'application_id' in request.auth.keywords:
                return result.success(ApplicationExtSerializer.Operate(
                    data={'application_id': request.auth.keywords.get('application_id'),
                          'user_id': request.user.id}).profile(request.query_params.get('qa_subject_identifier')))
            raise AppAuthenticationFailed(401, "身份异常")


class ApplicationTemplateView(APIView):
    authentication_classes = [TokenAuth]

    @action(methods=['POST'], detail=False)
    @permission_classes((AllowAny,))
    def post(self, request: Request):
        return result.success(ApplicationTemplateSerializer(data={'user_id': request.user.id, 'system_name': request.data.get('system_name')}).save(request.data))


class ApplicationQaTextView(APIView):
    authentication_classes = [TokenAuth]

    class Operate(APIView):
        authentication_classes = [TokenAuth]

        @action(methods=['POST'], detail=False)
        @permission_classes((AllowAny,))
        def post(self, request: Request):
            if 'application_id' in request.auth.keywords:
                return result.success(ApplicationQaTextSerializer.Create(data={'user_id': request.user.id, **request.data}).save())
            raise AppAuthenticationFailed(401, "身份异常")

        @action(methods=['DELETE'], detail=False)
        @permission_classes((AllowAny,))
        def delete(self, request: Request, application_qa_text_id: str):
            if 'application_id' in request.auth.keywords:
                return result.success(ApplicationQaTextSerializer.Delete(data={'user_id': request.user.id, 'application_qa_text_id': application_qa_text_id}).delete())
            raise AppAuthenticationFailed(401, "身份异常")


class WsdChatInfoView(APIView):
    authentication_classes = [TokenAuth]

    @action(methods=['GET'], detail=False)
    def get(self, request: Request, app_subject_identifier: str):
        return result.success(WsdChatInfoSerializer(data={'user_id': request.user.id, 'app_subject_identifier': app_subject_identifier}).get())
