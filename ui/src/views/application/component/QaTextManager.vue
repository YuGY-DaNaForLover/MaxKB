<template>
  <el-button type="primary" @click="handleAdd" class="mb-16">添加</el-button>
  <el-table :data="qaTexts" style="width: 100%; margin-bottom: 16px" show-overflow-tooltip>
    <el-table-column prop="subject_identifier" label="主体标识符" :formatter="formatterSubjectIdentifier" />
    <el-table-column prop="q_a_text" label="问答文本" />
    <el-table-column label="操作">
      <template #default="scope">
        <el-button type="danger" @click="handleDelete(scope.$index)">删除</el-button>
      </template>
    </el-table-column>
  </el-table>
  <el-dialog v-model="dialogVisible" title="添加问答文本" width="40%" destroy-on-close>
    <el-form ref="formRef" :model="form" label-width="120px" class="mb-16">
      <el-form-item label="主体标识符">
        <el-input
          v-model="form.subject_identifier"
          placeholder="用于关联业务系统的用户，保存为智能体模版时不用填"
        />
      </el-form-item>
      <el-form-item
        label="问答文本"
        prop="q_a_text"
        :rules="{ required: true, message: '请输入问答文本' }"
      >
        <el-input v-model="form.q_a_text" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleSubmit">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { type PropType, computed, defineProps, defineEmits, ref } from 'vue'
import type { FormInstance } from 'element-plus'
interface QaText {
  subject_identifier: string
  q_a_text: string
}

const props = defineProps({
  modelValue: {
    type: Array as PropType<QaText[]>,
    default: () => []
  }
})
const emit = defineEmits(['update:modelValue'])
const qaTexts = computed({
  get() {
    return props.modelValue
  },
  set(value: QaText[]) {
    emit('update:modelValue', value)
  }
})

const dialogVisible = ref(false)
const form = ref<QaText>({
  subject_identifier: '',
  q_a_text: ''
})
const formRef = ref<FormInstance>()

const formatterSubjectIdentifier = (row: QaText) => {
  return row.subject_identifier || '无'
}
const handleDelete = (index: number) => {
  qaTexts.value = qaTexts.value.filter((_, i) => i !== index)
}
const handleAdd = () => {
  dialogVisible.value = true
}
const handleSubmit = () => {
  formRef.value?.validate((valid) => {
    if (valid) {
      qaTexts.value = [...qaTexts.value, form.value]
      dialogVisible.value = false
      form.value = {
        subject_identifier: '',
        q_a_text: ''
      }
    }
  })
}
</script>

<style scoped></style>
