<template>
  <el-tree
    ref="treeRef"
    :data="data"
    show-checkbox
    default-expand-all
    node-key="id"
    :props="defaultProps"
  >
    <template #default="{ node }">
      <div class="custom-label">
        <MdPreview
          noIconfont
          ref="editorRef"
          editorId="preview-only"
          :modelValue="node.label"
          :key="node.id"
          class="maxkb-md"
        />
      </div>
    </template>
  </el-tree>
</template>
<script setup lang="ts">
import { v4 as uuidv4 } from 'uuid'
import { ElMessage, type TreeInstance } from 'element-plus'
import { ref, computed, onMounted, onBeforeMount } from 'vue'

interface dataType {
  id: string
  label: string
  children?: dataType[]
}

const props = withDefaults(
  defineProps<{
    source?: string
    chat_record_id?: string
  }>(),
  {
    source: '',
    chat_record_id: ''
  }
)
// 定义树节点的类型
type TreeNode = {
  id: string
  label: string
  children: TreeNode[]
}

// 检查是否为无意义元素（如分割线）
function isMeaninglessLine(line: string): boolean {
  const trimmedLine = line.trim()
  return /^([-*_])\1{2,}$/.test(trimmedLine)
}

// 将 Markdown 字符串转换为树结构的函数
function markdownToTree(markdown: string): TreeNode[] {
  // 将 Markdown 按行分割成数组
  const lines = markdown.split('\n')
  // 初始化栈，用于跟踪父节点
  const stack: { level: number; node: TreeNode }[] = []
  // 初始化根节点
  const root: TreeNode = { id: uuidv4(), label: '', children: [] }
  // 将根节点信息压入栈
  stack.push({ level: 0, node: root })

  // 遍历每一行
  lines.forEach((line) => {
    if (isMeaninglessLine(line)) {
      return // 跳过无意义的行
    }

    // 匹配标题行
    const match = line.match(/^(#+) (.*)$/)
    if (match) {
      // 获取标题的级别
      const level = match[1].length
      // 这里直接使用原文作为 label
      const label = line
      // 生成唯一 ID
      const id = uuidv4()
      // 创建新节点
      const newNode: TreeNode = { id, label, children: [] }

      // 找到合适的父节点
      while (stack.length > 0 && stack[stack.length - 1].level >= level) {
        stack.pop()
      }

      // 获取当前父节点
      const parent = stack[stack.length - 1].node
      // 将新节点添加到父节点的子节点列表中
      parent.children.push(newNode)
      // 将新节点信息压入栈
      stack.push({ level, node: newNode })
    } else if (line.trim() !== '') {
      // 非标题且非空行，直接使用原文作为 label
      const label = line
      // 生成唯一 ID
      const id = uuidv4()
      // 创建新节点
      const newNode: TreeNode = { id, label, children: [] }
      // 获取当前父节点
      const parent = stack[stack.length - 1].node
      // 将新节点添加到父节点的子节点列表中
      parent.children.push(newNode)
    }
  })

  // 返回根节点的子节点列表
  return root.children
}

const data = computed(() => {
  if (props.source) {
    console.log(markdownToTree(props.source))
    return markdownToTree(props.source) as dataType[]
  } else {
    return []
  }
})
const defaultProps = {
  children: 'children',
  label: 'label'
}
const treeRef = ref<TreeInstance>()

function filterKeyWithTree(keys: any[], data: dataType[]): dataType[] {
  const arr: dataType[] = []
  for (const item of data) {
    if (keys.includes(item.id)) {
      let children: dataType[] | undefined
      if (item.children) children = filterKeyWithTree(keys, item.children)
      arr.push({
        id: item.id,
        label: item.label,
        children
      })
    }
  }
  return arr
}
function introduceAnswer() {
  const keys = treeRef.value?.getHalfCheckedKeys()?.concat(treeRef.value?.getCheckedKeys())
  if (keys?.length) {
    const messageObj = filterKeyWithTree(keys, data.value)
    const messageStr = JSON.stringify(messageObj)
    console.log(messageObj)
    window.parent.postMessage(
      {
        type: 'wsd-ai',
        data: messageStr
      },
      '*'
    )
  } else {
    ElMessage.error('请先选择要引入的回答。')
  }
}

onMounted(() => {
  if (!(window as any).introduceAnswer) (window as any).introduceAnswer = {}
  ;(window as any).introduceAnswer[props.chat_record_id] = introduceAnswer
})
onBeforeMount(() => {
  ;(window as any).introduceAnswer = null
})
</script>
<style lang="scss" scoped>
p.is-checked {
  color: var(--el-color-primary);
}
:deep(.el-tree-node__content) {
  height: fit-content;
  &:hover {
    background-color: #fff;
  }
  .el-checkbox__inner {
    width: 20px;
    height: 20px;
    &:after {
      height: 9px;
      left: 6px;
      top: 2px;
      width: 5px;
    }
    &::before {
      top: 7px;
    }
  }
}
.custom-label {
  /* 设置最大宽度，超过宽度则换行 */
  max-width: 100%;
  /* 允许单词内换行 */
  word-break: break-all;
  /* 文本溢出时换行 */
  white-space: normal;
  display: inline-block;
}
:deep(.md-editor-preview) {
  h1,
  h2,
  h3,
  h4,
  h5,
  h6 {
    margin-top: 0.8em;
  }
  ul {
    padding-left: 0.25em;
  }
  ol {
    padding-left: 1.35em;
  }
}
</style>
