<template>
  <div class="wsd-chat-container">
    <div class="wsd-chat-header">
      <div class="wsd-chat-header-title">
        <img width="30" height="30" src="/logo.gif" alt="logo" style="margin-right: 10px" />
        {{ active_application_title }}
      </div>
      <el-tabs v-model="active_application_id" style="width: 50%">
        <el-tab-pane
          v-for="application in application_data_list"
          :key="application.application_id"
          :label="application.application_ext.title"
          :name="application.application_id"
        >
        </el-tab-pane>
      </el-tabs>
    </div>
    <div class="wsd-chat-content">
      <WsdPc
        v-if="application_access_token && chat_show && init_data_end"
        :key="application_access_token"
        :application_profile="application_profile"
        :applicationAvailable="applicationAvailable"
        :qa_subject_identifier="qa_subject_identifier"
        v-loading="loading"
      />
      <Auth
        v-else
        :application_profile="application_profile"
        :auth_type="application_profile.authentication_type"
        v-model="is_auth"
        :style="{
          '--el-color-primary': application_profile?.custom_theme?.theme_color,
          '--el-color-primary-light-9': hexToRgba(
            application_profile?.custom_theme?.theme_color,
            0.1
          )
        }"
      ></Auth>
    </div>
  </div>
</template>

<script setup lang="ts">
import WsdPc from './WsdPc/index.vue'
import Auth from '@/views/chat/auth/index.vue'
import { useRoute } from 'vue-router'
import useStore from '@/stores'
import { hexToRgba } from '@/utils/theme'
import { ref, onBeforeMount, computed, watch } from 'vue'

interface ApplicationData {
  application_id: string
  application_access_token: string
  application_ext: {
    title: string
    q_a_component: string
  }
}

const route = useRoute()
const { application, user } = useStore()
const {
  params: { app_subject_identifier, qa_subject_identifier }
} = route as any

const application_data_list = ref<ApplicationData[]>([])
const active_application_id = ref<string>('')
const loading = ref(false)
const is_auth = ref<boolean>(false)
const init_data_end = ref<boolean>(false)
const applicationAvailable = ref<boolean>(true)
const chat_show = computed(() => {
  if (init_data_end.value) {
    if (!applicationAvailable.value) {
      return true
    }
    if (application_profile.value) {
      if (application_profile.value.authentication && is_auth.value) {
        return true
      } else if (!application_profile.value.authentication) {
        return true
      }
    }
  }
  return false
})
const active_application_title = computed(() => {
  return application_data_list.value.find(
    (item) => item.application_id === active_application_id.value
  )?.application_ext.title
})
const application_access_token = computed(() => {
  return (
    application_data_list.value.find((item) => item.application_id === active_application_id.value)
      ?.application_access_token || ''
  )
})
watch(application_access_token, (newVal: string) => {
  if (newVal) {
    loading.value = true
    user.changeUserType(2)
    Promise.all([user.asyncGetProfile(), getAccessToken(newVal)])
      .catch(() => {
        applicationAvailable.value = false
      })
      .finally(() => {
        loading.value = false
        init_data_end.value = true
      })
  }
})
const application_profile = ref<any>({})
function getAppProfile() {
  return application.asyncGetAppExtProfile(qa_subject_identifier, loading).then((res: any) => {
    application_profile.value = res.data
  })
}
function getAccessToken(token: string) {
  return application.asyncAppAuthentication(token, loading).then(() => {
    return getAppProfile()
  })
}
onBeforeMount(async () => {
  const res = await application.asyncGetApplicationIdList(app_subject_identifier)
  application_data_list.value = res.data as ApplicationData[]
  if (application_data_list.value.length > 0) {
    active_application_id.value = application_data_list.value[0].application_id
  }
})
</script>

<style scoped>
.wsd-chat-container {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
}

.wsd-chat-header {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  background: linear-gradient(135deg, #f7f0ac, #acf7f0, #f0acf7);
  box-shadow: rgba(0, 0, 0, 0.24) 0px 3px 8px;
  z-index: 100;
}

.wsd-chat-header-title {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: bold;
  position: absolute;
  color: #333;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
}

.wsd-chat-content {
  flex: 1;
  min-height: 0;
}

:deep(.el-tabs__header) {
  margin-bottom: 5px;
}
:deep(.el-tabs__nav-wrap) {
  &::after {
    background-color: transparent;
  }
}
</style>
