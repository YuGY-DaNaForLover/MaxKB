<template>
  <el-button type="primary" link class="new-chat-button mb-8" @click="newChat">
    <el-icon><Plus /></el-icon><span class="ml-4">{{ $t('chat.createChat') }}</span>
  </el-button>
</template>

<script setup lang="ts">
import type { PropType } from 'vue'

defineProps({
  newChat: {
    type: Function as PropType<() => any>,
    required: true
  }
})
</script>

<style scoped></style>
