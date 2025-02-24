<template>
  <div style="height: 100%; position: relative; display: flex">
    <!-- 折叠按钮移到外层 -->
    <div
      class="collapse-btn"
      :style="{ left: isCollapse ? '10px' : '410px', top: '50%' }"
      @click="toggleCollapse"
    >
      <el-icon :size="20">
        <component :is="isCollapse ? 'Expand' : 'Fold'" />
      </el-icon>
    </div>

    <div
      :style="{
        width: isCollapse ? '0' : '400px', // 添加显式宽度控制
        maxWidth: isCollapse ? '0' : '400px',
        borderRight: '1px solid #dfdfdf',
        position: !upBreakPoint ? 'relative' : 'absolute',
        left: 0,
        top: 0,
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)', // 添加贝塞尔曲线
        overflow: 'hidden', // 防止内容溢出
        height: '100%',
        zIndex: 1000,
        backgroundColor: '#fff'
      }"
    >
      <div class="chat-pc__left">
        <div class="p-24 pb-0">
          <el-button class="add-button w-full primary" plain type="primary" @click="newChat">
            <el-icon>
              <Plus />
            </el-icon>
            <span class="ml-4">{{ $t('chat.createChat') }}</span>
          </el-button>
        </div>
        <div class="chat-pc__left-tab">
          <el-radio-group v-model="leftTabActive" style="margin-bottom: 20px; width: 100%">
            <el-radio-button value="qaTexts" style="flex: 1">常用问答</el-radio-button>
            <el-radio-button value="historyLog" style="flex: 1">历史对话</el-radio-button>
          </el-radio-group>
          <div
            v-if="leftTabActive === 'qaTexts'"
            style="flex: 1; display: flex; flex-direction: column"
          >
            <div style="flex: 1; overflow: hidden; margin-bottom: 10px">
              <el-scrollbar style="height: 100%">
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
              </el-scrollbar>
            </div>
            <el-popover :width="300" :visible-arrow="false" placement="top" trigger="click">
              <template #reference>
                <el-button type="primary" style="width: fit-content; margin: 0 auto"
                  >新增问答</el-button
                >
              </template>
              <el-input v-model="qaText" placeholder="请输入问答文本" />
              <el-button
                type="primary"
                size="small"
                style="width: fit-content; margin: 10px auto 0"
                @click="addQaText"
              >
                新增
              </el-button>
            </el-popover>
          </div>
          <div v-else>
            <el-scrollbar>
              <div class="p-8 pt-0">
                <common-list
                  :style="{
                    '--el-color-primary': applicationDetail?.custom_theme?.theme_color,
                    '--el-color-primary-light-9': hexToRgba(
                      applicationDetail?.custom_theme?.theme_color,
                      0.1
                    )
                  }"
                  :data="chatLogData"
                  class="mt-8"
                  v-loading="left_loading"
                  :defaultActive="currentChatId"
                  @click="clickListHandle"
                  @mouseenter="mouseenter"
                  @mouseleave="mouseId = ''"
                >
                  <template #default="{ row }">
                    <div class="flex-between">
                      <auto-tooltip :content="row.abstract">
                        {{ row.abstract }}
                      </auto-tooltip>
                      <div @click.stop v-if="mouseId === row.id && row.id !== 'new'">
                        <el-button style="padding: 0" link @click.stop="deleteLog(row)">
                          <el-icon><Delete /></el-icon>
                        </el-button>
                      </div>
                    </div>
                  </template>
                  <template #empty>
                    <div class="text-center">
                      <el-text type="info">{{ $t('chat.noHistory') }}</el-text>
                    </div>
                  </template>
                </common-list>
              </div>
              <div v-if="chatLogData?.length" class="gradient-divider lighter mt-8">
                <span>{{ $t('chat.only20history') }}</span>
              </div>
            </el-scrollbar>
          </div>
        </div>
      </div>
    </div>
    <div
      :style="{
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        width: isCollapse || upBreakPoint ? '100%' : 'calc(100% - 400px - 16px)',
        backgroundColor: '#f3f7f9'
      }"
    >
      <div class="right-height chat-width">
        <AiChat
          ref="AiChatRef"
          v-model:applicationDetails="applicationDetail"
          :available="applicationAvailable"
          type="ai-chat"
          :appId="applicationDetail?.id"
          :record="currentRecordList"
          :chatId="currentChatId"
          @refresh="refresh"
          @scroll="handleScroll"
        >
        </AiChat>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, onBeforeUnmount, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Delete } from '@element-plus/icons-vue'
import useStore from '@/stores'
import { hexToRgba } from '@/utils/theme'
import { MsgSuccess } from '@/utils/message'
const { user, log, application } = useStore()
const { t } = useI18n()
const props = defineProps({
  application_profile: {
    type: Object,
    required: true
  },
  qa_subject_identifier: {
    type: String,
    required: true
  },
  applicationAvailable: Boolean
})

const chatLogData = ref<any[]>([])
const paginationConfig = ref({
  current_page: 1,
  page_size: 20,
  total: 0
})
const currentRecordList = ref<any>([])
const currentChatId = ref('new') // 当前历史记录Id 默认为'new'
const currentChatName = ref(t('chat.createChat'))
const applicationDetail = computed({
  get: () => {
    return props.application_profile
  },
  set: (v) => {}
})
const newObj = {
  id: 'new',
  abstract: t('chat.createChat')
}
const left_loading = ref(false)
const leftTabActive = ref('qaTexts')
const qaTexts = ref(applicationDetail.value.qa_texts || [])
const loading = ref(false)
const mouseId = ref('')
const AiChatRef = ref()

// 添加响应式断点（示例为1500px，可根据需要调整）
const breakPoint = 1500
// 添加折叠状态
const isCollapse = ref(window.innerWidth < breakPoint)
const upBreakPoint = ref(window.innerWidth < breakPoint)
const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}
// 监听窗口变化
const handleResize = () => {
  isCollapse.value = window.innerWidth < breakPoint
  upBreakPoint.value = window.innerWidth < breakPoint
}

watch(
  () => props.application_profile,
  (newVal) => {
    qaTexts.value = newVal.qa_texts || []
  }
)
function mouseenter(row: any) {
  mouseId.value = row.id
}
function deleteLog(row: any) {
  log.asyncDelChatClientLog(applicationDetail.value.id, row.id, left_loading).then(() => {
    if (currentChatId.value === row.id) {
      currentChatId.value = 'new'
      currentChatName.value = t('chat.createChat')
      paginationConfig.value.current_page = 1
      paginationConfig.value.total = 0
      currentRecordList.value = []
    }
    getChatLog(applicationDetail.value.id)
  })
}
function newChat() {
  if (!chatLogData.value.some((v) => v.id === 'new')) {
    paginationConfig.value.current_page = 1
    paginationConfig.value.total = 0
    currentRecordList.value = []
    chatLogData.value.unshift(newObj)
  } else {
    paginationConfig.value.current_page = 1
    paginationConfig.value.total = 0
    currentRecordList.value = []
  }
  currentChatId.value = 'new'
  currentChatName.value = t('chat.createChat')
}
function getChatLog(id: string, refresh?: boolean) {
  const page = {
    current_page: 1,
    page_size: 20
  }

  log.asyncGetChatLogClient(id, page, left_loading).then((res: any) => {
    chatLogData.value = res.data.records
    if (refresh) {
      currentChatName.value = chatLogData.value?.[0].abstract
    }
  })
}
function getChatRecord() {
  return log
    .asyncChatRecordLog(
      applicationDetail.value.id,
      currentChatId.value,
      paginationConfig.value,
      loading,
      false
    )
    .then((res: any) => {
      paginationConfig.value.total = res.data.total
      const list = res.data.records
      list.map((v: any) => {
        v['write_ed'] = true
        v['record_id'] = v.id
      })
      currentRecordList.value = [...list, ...currentRecordList.value].sort((a, b) =>
        a.create_time.localeCompare(b.create_time)
      )
      if (paginationConfig.value.current_page === 1) {
        nextTick(() => {
          // 将滚动条滚动到最下面
          AiChatRef.value.setScrollBottom()
        })
      }
    })
}
const clickListHandle = (item: any) => {
  if (item.id !== currentChatId.value) {
    paginationConfig.value.current_page = 1
    paginationConfig.value.total = 0
    currentRecordList.value = []
    currentChatId.value = item.id
    currentChatName.value = item.abstract
    if (currentChatId.value !== 'new') {
      getChatRecord()
    }
  }
}
const deleteQaText = (item: any) => {
  if (item.subject_identifier !== '') {
    application.asyncDeleteApplicationQaText(item.id).then(() => {
      qaTexts.value = qaTexts.value.filter((v: any) => v.id !== item.id)
      MsgSuccess('删除成功')
    })
  }
}
const qaText = ref('')
const addQaText = () => {
  application
    .asyncCreateApplicationQaText(
      applicationDetail.value.id,
      props.qa_subject_identifier,
      qaText.value
    )
    .then((res: any) => {
      qaTexts.value = [
        ...qaTexts.value,
        {
          id: res.data.id,
          subject_identifier: props.qa_subject_identifier,
          q_a_text: res.data.q_a_text
        }
      ]
      qaText.value = ''
      MsgSuccess('新增成功')
    })
}
const clickQaText = (item: any) => {
  AiChatRef.value.sendMessage(item.q_a_text)
  if (upBreakPoint.value) {
    isCollapse.value = false
  }
}
function refresh(id: string) {
  getChatLog(applicationDetail.value.id, true)
  currentChatId.value = id
}
function handleScroll(event: any) {
  if (
    currentChatId.value !== 'new' &&
    event.scrollTop === 0 &&
    paginationConfig.value.total > currentRecordList.value.length
  ) {
    const history_height = event.dialogScrollbar.offsetHeight
    paginationConfig.value.current_page += 1
    getChatRecord().then(() => {
      event.scrollDiv.setScrollTop(event.dialogScrollbar.offsetHeight - history_height)
    })
  }
}

/**
 *初始化历史对话记录
 */
const init = () => {
  if (
    (applicationDetail.value.show_history || !user.isEnterprise()) &&
    props.applicationAvailable
  ) {
    getChatLog(applicationDetail.value.id)
  }
}
onMounted(() => {
  init()
  window.addEventListener('resize', handleResize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style lang="scss" scoped>
// 修改折叠按钮样式
.collapse-btn {
  position: absolute;
  top: 20px;
  z-index: 1000;
  cursor: pointer;
  padding: 8px;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s;

  &:hover {
    background: #f5f7fa;
    transform: scale(1.1);
  }

  // 根据状态显示不同图标颜色
  .el-icon {
    color: var(--el-color-primary);
  }
}

.chat-pc__left {
  width: 400px;
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 1000;
  background-color: #fff;
}
.chat-pc__left-tab {
  margin-top: 20px;
  padding: 0 24px 24px 24px;
  display: flex;
  flex-direction: column;
  height: 100%;
}
:deep(.el-radio-button__inner) {
  width: 100%;
}
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

.right-height {
  padding: 24px 0;
  height: calc(100% - 48px);
}
.chat-width {
  max-width: 80%;
  margin: 0 auto;
}
@media only screen and (max-width: 1000px) {
  .chat-width {
    max-width: 100% !important;
    margin: 0 auto;
  }
}
</style>
