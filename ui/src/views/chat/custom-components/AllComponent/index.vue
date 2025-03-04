<template>
  <div class="flex items-center">
    <NewChatButton :newChat="newChat" />
    <QaText :qaTexts="qaTexts" :click-qa-text="clickQaText" :delete-qa-text="deleteQaText" />
    <WordFileSelect :dataset_id_list="dataset_id_list" :onCallBack="onWordFileCallBack" />
  </div>
</template>

<script setup lang="ts">
import { type PropType } from 'vue'
import NewChatButton from '../NewChatButton/index.vue'
import QaText from '../QaText/index.vue'
import WordFileSelect from '../WordFileSelect/index.vue'

defineProps({
  newChat: {
    type: Function as PropType<() => any>,
    default: () => {}
  },
  qaTexts: {
    type: Array as PropType<any[]>,
    default: () => []
  },
  clickQaText: {
    type: Function as PropType<(item: any) => void>,
    default: () => () => {}
  },
  deleteQaText: {
    type: Function as PropType<(item: any) => void>,
    default: () => () => {}
  },
  dataset_id_list: { type: Array, required: true },
  onWordFileCallBack: Function as PropType<(list: string[]) => void>
})
</script>

<style scoped></style>
