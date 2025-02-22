import os
import hashlib
import uuid
import pickle
from typing import Dict
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.db.models import QuerySet
from django.db import transaction

from application.models.api_key_model import ApplicationAccessToken
from common.util.field_message import ErrMessage
from common.util.fork import Fork
from common.exception.app_exception import AppApiException
from dataset.models.data_set import DataSet, Type
from dataset.task import sync_web_dataset
from setting.models.model_management import Model
from common.util.file_util import get_mk_file_content
from function_lib.models.function import FunctionLib, PermissionType
from application.models import Application, ApplicationDatasetMapping
from dataset.serializers.dataset_serializers import DataSetSerializers
from application_ext.models.application_ext import ApplicationExt, ApplicationQaTextMapping
from application_ext.serializers.application_ext_serializers import ApplicationExtSerializer

from smartdoc.const import CONFIG


class WsdAiApiSerializers(serializers.Serializer):

    class ApplicationUrlSerializer(serializers.Serializer):
        app_subject_identifier = serializers.CharField(
            required=True, error_messages=ErrMessage.char(_("Application Subject Identifier")))
        qa_subject_identifier = serializers.CharField(
            required=True, error_messages=ErrMessage.char(_("QA Subject Identifier")))

        def get_url(self, with_valid=True):
            if with_valid:
                self.is_valid(raise_exception=True)
            app_subject_identifier = self.data.get('app_subject_identifier')
            qa_subject_identifier = self.data.get('qa_subject_identifier')
            if not QuerySet(ApplicationExt).filter(subject_identifier=app_subject_identifier).exists():
                raise AppApiException(500, _('Application does not exist'))

            return {
                'full_url': f'{CONFIG.get_frontend_url()}/ui/wsd-chat/{app_subject_identifier}/{qa_subject_identifier}',
                'float_url': f'{CONFIG.get_frontend_url()}/ui/wsd-chat/{app_subject_identifier}/{qa_subject_identifier}'''
            }

    class ApplicationCreateSerializer(serializers.Serializer):
        user_id = serializers.UUIDField(
            required=True, error_messages=ErrMessage.uuid(_("User ID")))
        dataset_id_list = serializers.ListField(
            required=True, error_messages=ErrMessage.uuid(_("Dataset ID")))
        dsr_name = serializers.CharField(
            required=True, error_messages=ErrMessage.char(_("Dsr Name")))
        app_subject_identifier = serializers.CharField(
            required=True, error_messages=ErrMessage.char(_("Application Subject Identifier")))
        system_name = serializers.CharField(
            required=True, error_messages=ErrMessage.char(_("System Name")))

        @transaction.atomic
        def create(self, with_valid=True):
            if with_valid:
                self.is_valid(raise_exception=True)
            user_id = self.data.get('user_id')
            dataset_id_list = self.data.get('dataset_id_list')
            dsr_name = self.data.get('dsr_name')
            app_subject_identifier = self.data.get('app_subject_identifier')
            system_name = self.data.get('system_name')
            # 读取默认信访智能体会话模版实例
            folder_path = os.path.join(
                CONFIG.get_default_dataset_mk_instance(), system_name)
            if not os.path.exists(folder_path):
                raise AppApiException(500, f'{system_name}智能体会话模版不存在')
            entries = os.listdir(folder_path)
            # 生成完整路径并过滤出文件
            files = [os.path.join(folder_path, entry)
                     for entry in entries
                     if os.path.isfile(os.path.join(folder_path, entry))]
            for file in files:
                try:
                    if not file.lower().endswith(('.mk')):
                        continue
                    mk_instance = pickle.loads(get_mk_file_content(file))
                except Exception as e:
                    raise AppApiException(1001, _("Unsupported file format"))
                application = mk_instance.application
                function_lib_list = mk_instance.function_lib_list
                application_ext = application.get('ext', {})
                if QuerySet(Application).filter(name=f'{dsr_name}-{application_ext.get("title")}').exists():
                    QuerySet(Application).filter(
                        name=f'{dsr_name}-{application_ext.get("title")}').delete()
                application_qa_text_mapping_list = application.get(
                    'qa_text_mapping_list', [])
                if len(function_lib_list) > 0:
                    function_lib_id_list = [function_lib.get(
                        'id') for function_lib in function_lib_list]
                    exits_function_lib_id_list = [str(function_lib.id) for function_lib in
                                                  QuerySet(FunctionLib).filter(id__in=function_lib_id_list)]
                    # 获取到需要插入的函数
                    function_lib_list = [function_lib for function_lib in function_lib_list if
                                         not exits_function_lib_id_list.__contains__(function_lib.get('id'))]
                application_model = self.to_application(
                    application, user_id, f'{dsr_name}-{application_ext.get("title")}')
                function_lib_model_list = [self.to_function_lib(
                    f, user_id) for f in function_lib_list]
                application_model.save()
                # 插入认证信息
                ApplicationAccessToken(application_id=application_model.id,
                                       access_token=hashlib.md5(str(uuid.uuid1()).encode()).hexdigest()[8:24]).save()
                QuerySet(FunctionLib).bulk_create(function_lib_model_list) if len(
                    function_lib_model_list) > 0 else None
                # 关联知识库
                application_dataset_mapping_list = []
                for dataset_id in dataset_id_list:
                    application_dataset_mapping_list.append(self.to_application_dataset_mapping(
                        application_model.id, dataset_id))
                QuerySet(ApplicationDatasetMapping).bulk_create(
                    application_dataset_mapping_list)
                # 插入应用扩展信息
                application_ext_model = self.to_application_ext(
                    {**application_ext, 'subject_identifier': app_subject_identifier}, application_model.id)
                application_ext_model.save()
                # 插入应用问答文本映射信息
                application_qa_text_mapping_model_list = self.to_application_qa_text(
                    application_qa_text_mapping_list, application_model.id)
                QuerySet(ApplicationQaTextMapping).bulk_create(application_qa_text_mapping_model_list) if len(
                    application_qa_text_mapping_model_list) > 0 else None

            return True

        @staticmethod
        def to_application(application, user_id, dsr_name):
            # 默认模型 todo
            model = QuerySet(Model).filter(
                model_name="deepseek-r1:32b").first()
            if model is None:
                raise AppApiException(500, _('Model does not exist'))
            llm_model_id = str(model.id)
            work_flow = application.get('work_flow')
            for node in work_flow.get('nodes', []):
                if node.get('type') == 'search-dataset-node':
                    node.get('properties', {}).get(
                        'node_data', {})['dataset_id_list'] = []
            return Application(id=uuid.uuid1(), user_id=user_id, name=dsr_name,
                               desc=application.get('desc'),
                               prologue=application.get('prologue'), dialogue_number=application.get('dialogue_number'),
                               dataset_setting=application.get(
                                   'dataset_setting'),
                               model_id=llm_model_id,
                               model_setting=application.get('model_setting'),
                               model_params_setting=application.get(
                                   'model_params_setting'),
                               tts_model_params_setting=application.get(
                                   'tts_model_params_setting'),
                               problem_optimization=application.get(
                                   'problem_optimization'),
                               icon="/ui/favicon.ico",
                               work_flow=work_flow,
                               type=application.get('type'),
                               problem_optimization_prompt=application.get(
                                   'problem_optimization_prompt'),
                               tts_model_enable=application.get(
                                   'tts_model_enable'),
                               stt_model_enable=application.get(
                                   'stt_model_enable'),
                               tts_type=application.get('tts_type'),
                               clean_time=application.get('clean_time'),
                               file_upload_enable=application.get(
                                   'file_upload_enable'),
                               file_upload_setting=application.get(
                                   'file_upload_setting'),
                               )

        @staticmethod
        def to_function_lib(function_lib, user_id):
            """

            @param user_id: 用户id
            @param function_lib: 函数库
            @return:
            """
            return FunctionLib(id=function_lib.get('id'), user_id=user_id, name=function_lib.get('name'),
                               code=function_lib.get('code'), input_field_list=function_lib.get('input_field_list'),
                               is_active=function_lib.get('is_active'),
                               permission_type=PermissionType.PRIVATE)

        @staticmethod
        def to_application_dataset_mapping(application_id, dataset_id):
            """

            @param user_id: 用户id
            @param function_lib: 函数库
            @return:
            """
            return ApplicationDatasetMapping(id=uuid.uuid1(), application_id=application_id, dataset_id=dataset_id)

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

    class DatasetCreateSerializer(serializers.Serializer):
        user_id = serializers.UUIDField(
            required=True, error_messages=ErrMessage.char(_('user id')), )
        name = serializers.CharField(required=True,
                                     error_messages=ErrMessage.char(
                                         _('dataset name')),
                                     max_length=64,
                                     min_length=1)
        desc = serializers.CharField(required=True,
                                     error_messages=ErrMessage.char(
                                         _('dataset description')),
                                     max_length=256,
                                     min_length=1)
        source_url = serializers.CharField(
            required=True, error_messages=ErrMessage.char(_('web source url list')), )

        def is_valid(self, *, raise_exception=False):
            super().is_valid(raise_exception=True)
            source_url = self.data.get('source_url')
            response = Fork(source_url, []).fork()
            if response.status == 500:
                raise AppApiException(500,
                                      _('URL error, cannot parse [{source_url}]').format(source_url=source_url))
            return True

        def save_web(self, instance: Dict, with_valid=True):
            if with_valid:
                self.is_valid(raise_exception=True)
            user_id = self.data.get('user_id')
            if QuerySet(DataSet).filter(user_id=user_id, name=instance.get('name')).exists():
                raise AppApiException(500, _('Knowledge base name duplicate!'))
            if not QuerySet(Model).filter(model_name="bge-m3").exists():
                raise AppApiException(500, "还未配置bge-m3模型")
            embedding_mode_id = str(QuerySet(Model).filter(
                model_name="bge-m3").first().id)
            dataset_id = uuid.uuid1()
            dataset = DataSet(
                **{'id': dataset_id, 'name': instance.get("name"), 'desc': instance.get('desc'), 'user_id': user_id,
                   'type': Type.web,
                   'embedding_mode_id': embedding_mode_id,
                   'meta': {'source_url': instance.get('source_url'), 'selector': ".markdown-body",
                            'embedding_mode_id': embedding_mode_id}})
            dataset.save()
            sync_web_dataset.delay(str(dataset_id), instance.get(
                'source_url'), ".markdown-body")
            return {'dataset_id': str(dataset_id)}

    class DatasetReEmbeddingSerializer(DataSetSerializers.Operate):

        @transaction.atomic
        def re_embedding(self, with_valid=True):
            super().re_embedding(with_valid=with_valid)

    class DatasetReSyncSerializer(serializers.Serializer):
        id = serializers.UUIDField(
            required=True, error_messages=ErrMessage.uuid(_("Dataset ID")))
        user_id = serializers.UUIDField(
            required=True, error_messages=ErrMessage.uuid(_("User ID")))

        def sync(self, with_valid=True):
            if with_valid:
                self.is_valid(raise_exception=True)
            dataset_id = self.data.get('id')
            user_id = self.data.get('user_id')
            DataSetSerializers.SyncWeb(data={'sync_type': 'complete', 'id': dataset_id,
                                             'user_id': user_id}).sync()
            return True
