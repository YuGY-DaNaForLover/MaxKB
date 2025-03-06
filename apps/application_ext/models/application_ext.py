import uuid

from common.mixins.app_model_mixin import AppModelMixin
from django.db import models

from application.models.application import Application


class ApplicationExt(AppModelMixin):
    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid1, editable=False, verbose_name="主键id")
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    title = models.CharField(max_length=128, verbose_name="应用显示标题")
    subject_identifier = models.CharField(max_length=64, verbose_name="主体标识符", default='')
    q_a_component = models.CharField(max_length=64, verbose_name="问答组件", default='', blank=True)
    is_checkbox = models.BooleanField(verbose_name="回答是否可以被引入", default=False)
    is_public = models.BooleanField(verbose_name="是否公共应用", default=False)
    
    class Meta:
        db_table = "application_ext"

class ApplicationQaText(AppModelMixin):
    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid1, editable=False, verbose_name="主键id")
    subject_identifier = models.CharField(max_length=64, verbose_name="主体标识符", default='global')
    q_a_text = models.CharField(max_length=128, verbose_name="问答文本")
    
    class Meta:
        db_table = "application_qa_text"
        
class ApplicationQaTextMapping(AppModelMixin):
    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid1, editable=False, verbose_name="主键id")
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    application_qa_text = models.ForeignKey(ApplicationQaText, on_delete=models.CASCADE)
    
    class Meta:
        db_table = "application_ext_qa_text_mapping"