<template>
  <el-popover :width="300" placement="top">
    <div style="height: 320px; display: flex; flex-direction: column">
      <span class="mb-8"
        >根据 <el-text type="primary" size="large" tag="b">{{ getTreeCount() }}</el-text
        > 份文档提问</span
      >
      <el-input
        v-model="filterText"
        style="width: 100%; margin-bottom: 3px"
        placeholder="筛选文书"
      />
      <div style="flex: 1; overflow: auto">
        <el-tree
          ref="treeRef"
          style="max-width: 600px"
          class="filter-tree"
          node-key="id"
          show-checkbox
          :data="treeData"
          :props="defaultProps"
          default-expand-all
          :filter-node-method="filterNode"
          @check="treeCheck"
        >
          <template #default="{ node }">
            <img :src="getImg(node.label)" style="width: 20px; height: 20px" />
            <span style="margin-left: 6px">{{ node.label }}</span>
          </template>
        </el-tree>
      </div>
    </div>
    <template #reference>
      <el-button type="primary" link class="new-chat-button mb-8">
        <el-icon><Document /></el-icon><span class="ml-4">文书检索</span>
      </el-button>
    </template>
  </el-popover>
</template>

<script setup lang="ts">
import type { ElTree } from 'element-plus'
import { watch, ref, type PropType, onMounted,  nextTick } from 'vue'
import useStore from '@/stores'
import paragraphApi from '@/api/paragraph'
import axios from 'axios'
import { useRoute } from 'vue-router'

const props = defineProps({
  dataset_id_list: { type: Array, required: true },
  onCallBack: Function as PropType<(list: string[]) => void>
})
const { document } = useStore()
const route = useRoute()
const {
  params: { app_subject_identifier }
} = route as any

interface TreeIter {
  [key: string]: any
}

const filterText = ref('')
const treeRef = ref<InstanceType<typeof ElTree>>()
const defaultProps = {
  children: 'children',
  label: 'label'
}
watch(filterText, (val) => {
  treeRef.value!.filter(val)
})
const filterNode = (value: string, data: TreeIter) => {
  if (!value) return true
  return data.label.includes(value)
}
const treeData = ref<TreeIter[]>([])
const exclude_paragraph_id_list = ref<string[]>([])
const getTreeCount = () => {
  return treeRef.value?.getCheckedNodes()?.filter((e) => e.label.includes('.')).length
}
const treeCheck = (data: TreeIter, { checkedNodes }: { checkedNodes: TreeIter[] }) => {
  exclude_paragraph_id_list.value = []
  const currentWordfile = checkedNodes.filter((e) => e.label.includes('.')).map((e) => e.id)
  const datasetList = props.dataset_id_list
  const documentReqs = datasetList.map((datasetId: any) => document.asyncGetAllDocument(datasetId))
  Promise.all(documentReqs).then((documentRes: any) => {
    let paragraphRes: any[] = []
    for (const d of documentRes) {
      paragraphRes = paragraphRes.concat(
        d.data.map((dres: any) => {
          return paragraphApi.getAllParagraph(dres.dataset_id, dres.id, {})
        })
      )
    }
    Promise.all(paragraphRes).then((pres) => {
      for (const p of pres) {
        for (const pdetail of p.data) {
          if (currentWordfile.some((e) => pdetail.title.includes(e))) {
            continue
          }
          exclude_paragraph_id_list.value.push(pdetail.id)
        }
      }
      if (props.onCallBack) props.onCallBack(exclude_paragraph_id_list.value)
    })
  })
}
const getImg = (fileName: string) => {
  if (fileName.split('.').length > 1) {
    const ext = fileName.split('.')[fileName.split('.').length - 1]
    if (ext === 'pdf') return new URL('@/assets/PDF.svg', import.meta.url).href
    else if (ext === 'doc' || ext === 'docx')
      return new URL('@/assets/word.svg', import.meta.url).href
    else if (ext === 'xls' || ext === 'xlsx')
      return new URL('@/assets/ECEL.svg', import.meta.url).href
    else return new URL('@/assets/TET.svg', import.meta.url).href
  } else return new URL('@/assets/floder.svg', import.meta.url).href
}
const getAllId = (list: TreeIter[]) => {
  const ids: any[] = []
  for (const item of list) {
    ids.push(item.id)
    if (item.children) {
      ids.push(...getAllId(item.children))
    }
  }
  return ids
}
const getTreeData = () => {
  axios
    .post('http://192.168.31.8:8089/admin/ai/fileList', {
      app_subject_identifier
    })
    .then((res) => {
      treeData.value = res.data.data
      nextTick(() => {
        treeRef.value?.setCheckedKeys(getAllId(treeData.value))
      })
    })
}

onMounted(() => {
  getTreeData()
})
</script>

<style scoped></style>
