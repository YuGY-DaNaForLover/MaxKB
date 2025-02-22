import os
import uuid
import pickle
from typing import Dict
from django.db import transaction
from django.db.models import QuerySet, Q
from rest_framework import serializers, status
from django.http import HttpResponse
import hashlib

from application.serializers.application_serializers import ApplicationSerializer, ApplicationSerializerModel
from function_lib.serializers.function_lib_serializer import FunctionLibModelSerializer
from application_ext.models.application_ext import ApplicationExt
from application_ext.models.application_ext import ApplicationQaText, ApplicationQaTextMapping
from application.models.application import Application
from application.models.api_key_model import ApplicationAccessToken
from function_lib.models.function import FunctionLib
from application.serializers.application_serializers import MKInstance
from common.util.field_message import ErrMessage
from common.response import result
from common.exception.app_exception import AppApiException
from django.utils.translation import gettext_lazy as _

from smartdoc.const import CONFIG


class Ext(serializers.Serializer):
    title = serializers.CharField(
        required=True, error_messages=ErrMessage.float(_("Reference segment number")))
    subject_identifier = serializers.CharField(
        required=False, allow_null=True, allow_blank=True)
    q_a_component = serializers.CharField(
        required=False, allow_null=True, allow_blank=True)


class QaText(serializers.Serializer):
    id = serializers.UUIDField(
        required=False, error_messages=ErrMessage.uuid(_("Application Qa Text ID")))
    subject_identifier = serializers.CharField(
        required=False, allow_null=True, allow_blank=True)
    q_a_text = serializers.CharField(
        required=False, allow_null=True, allow_blank=True)


class QaTextMapping(serializers.Serializer):
    application_qa_text_id = serializers.UUIDField(
        required=False, error_messages=ErrMessage.uuid(_("Application Qa Text ID")))


class ApplicationExtSerializer(ApplicationSerializer):

    class ExtEdit(serializers.Serializer):
        ext = Ext(required=True, error_messages=ErrMessage.json(
            _("application ext")))
        qa_texts = QaText(required=False, many=True, allow_null=True,
                          error_messages=ErrMessage.json(_("application qa texts")))

    class Create(ApplicationSerializer.Create):

        @transaction.atomic
        def insert(self, application: Dict):
            application_model_data = super().insert(application)
            application_ext_model = ApplicationExt(id=uuid.uuid1(
            ), application_id=application_model_data.get('id'), **application.get('ext', {}))
            application_ext_model.save()
            qa_texts = self.insert_qa_text(
                application, application_model_data.get('id'))
            return {**application_model_data, 'ext': Ext(application_ext_model).data, **qa_texts}

        def insert_qa_text(self, application: Dict, application_id: str):
            if 'qa_texts' in application and len(application.get('qa_texts', [])):
                records = [ApplicationQaText(
                    id=uuid.uuid1(), subject_identifier=qa_text.get('subject_identifier'), q_a_text=qa_text.get('q_a_text')) for qa_text in application.get('qa_texts', [])]
                QuerySet(ApplicationQaText).bulk_create(records)
                mapping_records = [ApplicationQaTextMapping(
                    id=uuid.uuid1(), application_id=application_id, application_qa_text_id=record.id) for record in records]
                QuerySet(ApplicationQaTextMapping).bulk_create(mapping_records)
            return {'qa_texts': [QaText(record).data for record in records]} if 'qa_texts' in application and len(application.get('qa_texts', [])) else {}

    class Operate(ApplicationSerializer.Operate):

        def one(self, with_valid=True):
            application_data = super().one(with_valid)
            if QuerySet(ApplicationExt).filter(application_id=self.data.get('application_id')).exists():
                ext_instance = QuerySet(ApplicationExt).filter(
                    application_id=self.data.get('application_id')).first()
                application_data['ext'] = Ext(
                    ext_instance).data if ext_instance else {}
            if QuerySet(ApplicationQaTextMapping).filter(application_id=self.data.get('application_id')).exists():
                application_data['qa_texts'] = [
                    QaText(qa_text).data
                    for qa_text in QuerySet(ApplicationQaText).filter(
                        id__in=QuerySet(ApplicationQaTextMapping).filter(application_id=self.data.get(
                            'application_id')).values_list('application_qa_text_id', flat=True)
                    )
                ]
            return application_data

        @transaction.atomic
        def edit(self, instance: Dict, with_valid=True):
            if with_valid:
                self.is_valid(raise_exception=True)
                ApplicationExtSerializer.ExtEdit(data=instance).is_valid(
                    raise_exception=True)
            if 'ext' in instance:
                if QuerySet(ApplicationExt).filter(application_id=self.data.get(
                        'application_id')).exists():
                    QuerySet(ApplicationExt).filter(application_id=self.data.get(
                        'application_id')).update(**instance.get('ext'))
                else:
                    ApplicationExt(id=uuid.uuid1(), application_id=self.data.get(
                        'application_id'), **instance.get('ext')).save()
            if 'qa_texts' in instance:
                QuerySet(ApplicationQaTextMapping).filter(
                    application_id=self.data.get('application_id')).delete()
                qa_text_models = []
                qa_text_mapping_models = []
                for qa_text in instance.get('qa_texts'):
                    qa_text_model = ApplicationQaText(
                        id=uuid.uuid1(), subject_identifier=qa_text.get('subject_identifier'), q_a_text=qa_text.get('q_a_text'))
                    qa_text_models.append(qa_text_model)
                    qa_text_mapping_models.append(ApplicationQaTextMapping(id=uuid.uuid1(), application_id=self.data.get(
                        'application_id'), application_qa_text_id=qa_text_model.id))
                QuerySet(ApplicationQaText).bulk_create(qa_text_models)
                QuerySet(ApplicationQaTextMapping).bulk_create(
                    qa_text_mapping_models)
            application_data = super().edit(instance, with_valid)
            return application_data

        @staticmethod
        def get_export_data(application: Application):
            function_lib_id_list = [node.get('properties', {}).get('node_data', {}).get('function_lib_id') for node
                                    in
                                    application.work_flow.get('nodes', []) if
                                    node.get('type') == 'function-lib-node']
            function_lib_list = []
            if len(function_lib_id_list) > 0:
                function_lib_list = QuerySet(FunctionLib).filter(
                    id__in=function_lib_id_list)
            application_dict = ApplicationSerializerModel(application).data
            application_ext_dict = Ext(QuerySet(ApplicationExt).filter(
                application_id=application.id).first()).data
            application_qa_text_mapping_list = QaTextMapping(
                instance=QuerySet(ApplicationQaTextMapping).filter(
                    application_id=application.id),
                many=True
            ).data
            mk_instance = MKInstance({**application_dict, 'ext': application_ext_dict, 'qa_text_mapping_list': application_qa_text_mapping_list},
                                     [FunctionLibModelSerializer(function_lib).data for function_lib in
                                         function_lib_list], 'v1')
            application_pickle = pickle.dumps(mk_instance)
            return application_pickle

        def export(self, with_valid=True):
            try:
                if with_valid:
                    self.is_valid()
                application_id = self.data.get('application_id')
                application = QuerySet(Application).filter(
                    id=application_id).first()
                application_pickle = self._get_export_data(
                    application=application)
                response = HttpResponse(
                    content_type='text/plain', content=application_pickle)
                response['Content-Disposition'] = f'attachment; filename="{application.name}.mk"'
                return response
            except Exception as e:
                return result.error(str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        def profile(self, qa_subject_identifier: str, with_valid=True):
            application_data = super().profile(with_valid)
            application_id = application_data.get('id')
            application_ext_model = QuerySet(ApplicationExt).filter(
                application_id=application_id).first()
            application_data['ext'] = Ext(
                application_ext_model).data if application_ext_model else {}
            application_qa_text_mapping_model_list = QuerySet(ApplicationQaTextMapping).filter(
                application_id=application_id).values_list('application_qa_text_id', flat=True)
            application_data['qa_texts'] = [
                QaText(qa_text).data
                for qa_text in QuerySet(ApplicationQaText).filter(Q(id__in=application_qa_text_mapping_model_list) &
                                                                  ((Q(subject_identifier__isnull=True) |
                                                                    Q(subject_identifier='')) |
                                                                  Q(subject_identifier=qa_subject_identifier)))
            ]
            return application_data

    class Import(ApplicationSerializer.Import):

        @transaction.atomic
        def import_(self, with_valid=True):
            if with_valid:
                self.is_valid()
            user_id = self.data.get('user_id')
            mk_instance_bytes = self.data.get('file').read()
            try:
                mk_instance = pickle.loads(mk_instance_bytes)
            except Exception as e:
                raise AppApiException(1001, _("Unsupported file format"))
            application = mk_instance.application
            application_ext = application.get('ext', {})
            application_qa_text_mapping_list = application.get(
                'qa_text_mapping_list', [])
            function_lib_list = mk_instance.function_lib_list
            if len(function_lib_list) > 0:
                function_lib_id_list = [function_lib.get(
                    'id') for function_lib in function_lib_list]
                exits_function_lib_id_list = [str(function_lib.id) for function_lib in
                                              QuerySet(FunctionLib).filter(id__in=function_lib_id_list)]
                # 获取到需要插入的函数
                function_lib_list = [function_lib for function_lib in function_lib_list if
                                     not exits_function_lib_id_list.__contains__(function_lib.get('id'))]
            application_model = self.to_application(application, user_id)
            function_lib_model_list = [self.to_function_lib(
                f, user_id) for f in function_lib_list]
            application_model.save()
            # 插入认证信息
            ApplicationAccessToken(application_id=application_model.id,
                                   access_token=hashlib.md5(str(uuid.uuid1()).encode()).hexdigest()[8:24]).save()
            QuerySet(FunctionLib).bulk_create(function_lib_model_list) if len(
                function_lib_model_list) > 0 else None
            # 插入应用扩展信息
            application_ext_model = self.to_application_ext(
                application_ext, application_model.id)
            application_ext_model.save()
            # 插入应用问答文本映射信息
            application_qa_text_mapping_model_list = self.to_application_qa_text(
                application_qa_text_mapping_list, application_model.id)
            QuerySet(ApplicationQaTextMapping).bulk_create(application_qa_text_mapping_model_list) if len(
                application_qa_text_mapping_model_list) > 0 else None
            return True

        @staticmethod
        def to_application_ext(application_ext: Dict, application_id: str):
            return ApplicationExt(id=uuid.uuid1(), application_id=application_id, **application_ext)

        @staticmethod
        def to_application_qa_text(application_qa_text_mapping_list: list, application_id: str):
            application_qa_text_mapping_model_list = []
            for application_qa_text_mapping in application_qa_text_mapping_list:
                application_qa_text_id = application_qa_text_mapping.get(
                    'application_qa_text_id')
                application_qa_text_mapping_model_list.append(ApplicationQaTextMapping(id=uuid.uuid1(
                ), application_id=application_id, application_qa_text_id=application_qa_text_id))
            return application_qa_text_mapping_model_list


class ApplicationTemplateSerializer(serializers.Serializer):
    user_id = serializers.UUIDField(
        required=True, error_messages=ErrMessage.uuid(_("User ID")))
    system_name = serializers.CharField(
        required=True, error_messages=ErrMessage.char(_("System Name")))

    @transaction.atomic
    def save(self, application: Dict):
        super().is_valid(raise_exception=True)
        user_id = self.data.get('user_id')
        system_name = self.data.get('system_name')
        application_dict = ApplicationExtSerializer.Create(
            data={'user_id': user_id}).insert(application)
        application_id = application_dict.get('id')
        application_model = QuerySet(Application).filter(
            id=application_id).first()
        application_pickle = ApplicationExtSerializer.Operate.get_export_data(
            application=application_model)
        folder_path = os.path.join(
            CONFIG.get_default_dataset_mk_instance(), system_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        file_path = os.path.join(
            folder_path, f'{application_dict.get("ext", {}).get("title", "")}.mk')
        if os.path.exists(file_path):
            os.remove(file_path)
        with open(file_path, 'wb') as f:
            f.write(application_pickle)
        QuerySet(Application).filter(id=application_id).delete()
        return True


class WsdChatInfoSerializer(serializers.Serializer):
    app_subject_identifier = serializers.CharField(
        required=True, error_messages=ErrMessage.char(_("Application Subject Identifier")))

    def get(self, with_valid=True):
        if with_valid:
            self.is_valid(raise_exception=True)
        app_subject_identifier = self.data.get('app_subject_identifier')
        application_ext_model_list = QuerySet(ApplicationExt).filter(
            subject_identifier=app_subject_identifier)
        if not application_ext_model_list.exists():
            raise AppApiException(1001, _("Application not found"))
        application_data_list = []
        for application_ext_model in application_ext_model_list:
            application_id = application_ext_model.application_id
            application_access_token_model = QuerySet(ApplicationAccessToken).filter(
                application_id=application_id)
            if not application_access_token_model.exists():
                raise AppApiException(
                    1001, _("Application access token not found"))
            application_access_token = application_access_token_model.first().access_token
            application_data_list.append({
                'application_id': application_id,
                'application_access_token': application_access_token,
                'application_ext': Ext(application_ext_model).data
            })
        return application_data_list


class ApplicationQaTextSerializer(serializers.Serializer):

    class Create(serializers.Serializer):
        user_id = serializers.UUIDField(
            required=True, error_messages=ErrMessage.uuid(_("User ID")))
        application_id = serializers.UUIDField(
            required=True, error_messages=ErrMessage.uuid(_("Application ID")))
        qa_subject_identifier = serializers.CharField(
            required=True, error_messages=ErrMessage.char(_("QA Subject Identifier")))
        qa_text = serializers.CharField(
            required=True, error_messages=ErrMessage.char(_("QA Text")))

        @transaction.atomic
        def save(self, with_valid=True):
            if with_valid:
                self.is_valid(raise_exception=True)
            application_id = self.data.get('application_id')
            qa_subject_identifier = self.data.get('qa_subject_identifier')
            qa_text = self.data.get('qa_text')
            qa_text_model = ApplicationQaText(
                id=uuid.uuid1(), subject_identifier=qa_subject_identifier, q_a_text=qa_text)
            qa_text_model.save()
            ApplicationQaTextMapping(id=uuid.uuid1(
            ), application_id=application_id, application_qa_text_id=qa_text_model.id).save()
            return QaText(qa_text_model).data

    class Delete(serializers.Serializer):
        user_id = serializers.UUIDField(
            required=True, error_messages=ErrMessage.uuid(_("User ID")))
        application_qa_text_id = serializers.UUIDField(
            required=True, error_messages=ErrMessage.uuid(_("Application Qa Text ID")))

        @transaction.atomic
        def delete(self, with_valid=True):
            if with_valid:
                self.is_valid(raise_exception=True)
            application_qa_text_id = self.data.get('application_qa_text_id')
            QuerySet(ApplicationQaText).filter(
                id=application_qa_text_id).delete()
            return True
