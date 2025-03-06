<template>
  <el-popover :width="300" placement="top">
    <el-scrollbar height="250px">
      <el-card
        v-for="(item, index) in qaTexts"
        :key="index"
        shadow="always"
        class="qa-text-item mb-8"
        @click.stop="clickQaText(item)"
      >
        <div class="qa-text-item-text">
          <span>{{ item.q_a_text }}</span>
          <el-button
            class="delete-button"
            :class="{ 'is-self-qa-text': item.subject_identifier !== '' }"
            text
            :icon="Delete"
            @click.stop="deleteQaText(item)"
          ></el-button>
        </div>
      </el-card>
      <el-empty v-if="qaTexts.length === 0" description="暂无常用问答" :image-size="100" />
    </el-scrollbar>
    <template #reference>
      <el-button type="primary" link class="new-chat-button mb-8">
        <el-icon><Comment /></el-icon><span class="ml-4">常用语</span>
      </el-button>
    </template>
  </el-popover>
</template>

<script setup lang="ts">
import { type PropType } from 'vue'
import { Delete } from '@element-plus/icons-vue'

defineProps({
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
  }
})
</script>

<style lang="scss" scoped>
.qa-text-item {
  cursor: pointer;
  &:hover {
    background-color: #3370ff;
    .qa-text-item-text {
      color: #fff;
      display: flex;
      .is-self-qa-text {
        display: block;
        color: #fff;
      }
    }
  }
  &:active {
    background-color: #fff;
    .qa-text-item-text {
      color: #000;
    }
  }
  .qa-text-item-text {
    display: flex;
    justify-content: space-between;
    align-items: center;
    .delete-button {
      display: none;
    }
  }
}
</style>
