<template>
  <div class="tree_box relative" :style="width && { width: width }">
    <el-select
      ref="treeSelect"
      v-model="value"
      clearable
      filterable
      :placeholder="placeholder || '请选择'"
      :filter-method="selectFilter"
      :teleported="teleported"
      @clear="clearSelected"
    >
      <template v-if="multiple && checkStrictly" #header>
        <div class="flex items-center">
          <div class="mr-2 text-[#606266]">是否选中子级</div>
          <el-switch v-model="isHaveSubTree" :active-value="true" :inactive-value="false" />
        </div>
      </template>
      <el-option :value="currentNodeKey" :label="currentNodeLabel">
        <el-tree-v2
          id="tree_v2"
          ref="treeV2"
          :data="options"
          :props="keyProps || TreeProps"
          :height="240"
          :style="{ width: '350px' }"
          :expand-on-click-node="false"
          :check-on-click-node="multiple ? false : true"
          :show-checkbox="multiple"
          :check-strictly="checkStrictly"
          :filter-method="treeFilter"
          :current-node-key="!multiple ? currentNodeKey : undefined"
          :default-checked-keys="
            multiple ? (currentNodeKey as string).split(',').map((e) => +e) : undefined
          "
          @node-click="nodeClick"
          @check-change="checkMethod"
        />
      </el-option>
    </el-select>
  </div>
</template>

<script lang="ts">
import {
  defineComponent,
  reactive,
  ref,
  nextTick,
  toRefs,
  watch,
  onMounted,
  type PropType
} from 'vue'
import type {
  FilterMethod,
  TreeData,
  TreeKey,
  TreeNode,
  TreeNodeData,
  TreeOptionProps
} from 'element-plus/es/components/tree-v2/src/types'
import type { ElTreeV2 } from 'element-plus'

const TreeProps: TreeOptionProps = {
  value: 'id',
  label: 'label',
  children: 'children'
}
interface TreeIter {
  id: number
  label: string
  children?: TreeIter[]
}
export default defineComponent({
  name: 'ComTreeSelect',
  props: {
    // 组件绑定的options
    options: {
      type: Array as PropType<TreeIter[]>,
      required: true
    },
    // 配置选项
    keyProps: Object as PropType<TreeOptionProps>,
    // 双向绑定值
    modelValue: { type: [String, Number, Array], default: () => [] },
    // 组件样式宽
    width: String,
    // 空占位字符
    placeholder: String,
    // 多选
    multiple: Boolean,
    checkStrictly: Boolean,
    teleported: { type: Boolean, default: false }
  },
  setup(props, { emit }) {
    // 解决 props道具变异
    const { modelValue } = toRefs(props)
    const select = reactive<{
      value: string | number
      currentNodeKey: string | number
      currentNodeLabel: string | number
    }>({
      value: props.multiple
        ? (modelValue.value as any[]).join(',')
        : (modelValue.value as string | number),
      currentNodeKey: '',
      currentNodeLabel: ''
    })
    const isLocalHanlde = ref(false)
    const treeSelect = ref<HTMLElement | null>(null)
    const isHaveSubTree = ref(false)
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const nodeClick = (data: TreeNodeData, node: TreeNode) => {
      if (props.multiple) return
      select.currentNodeKey = data.id
      select.currentNodeLabel = data.label
      nextTick(() => {
        select.value = select.currentNodeKey
        treeSelect.value?.blur()
        isLocalHanlde.value = true
        emit('update:modelValue', select.value)
      })
    }
    function setChecked(data: TreeNodeData) {
      data.children?.forEach((e: any) => {
        treeV2.value?.setChecked(e.id, true)
        if (e.children?.length) setChecked(e)
      })
    }
    const checkMethod = (data: TreeNodeData, checked: boolean) => {
      if (!props.multiple) return
      if (props.checkStrictly && isHaveSubTree.value && checked && data.children?.length) {
        setChecked(data)
      }
      // const { checkedKeys, checkedNodes } = info
      nextTick(() => {
        const checkedKeys = treeV2.value?.getCheckedKeys() as TreeKey[]
        const checkedNodes = treeV2.value?.getCheckedNodes() as TreeData
        select.currentNodeKey = checkedKeys.join(',')
        select.currentNodeLabel = checkedNodes.map((e) => e.label).join(',')
        nextTick(() => {
          select.value = select.currentNodeKey
          isLocalHanlde.value = true
          emit(
            'update:modelValue',
            (select.value as string).split(',').map((e) => +e)
          )
        })
      })
    }
    // select 筛选方法 treeV2 refs
    const treeV2 = ref<InstanceType<typeof ElTreeV2>>()
    const selectFilter = (query: string) => {
      treeV2.value?.filter(query)
    }
    // ztree-v2 筛选方法
    const treeFilter: FilterMethod = (query: string, node: TreeNodeData) => {
      return node.label?.indexOf(query) !== -1
    }
    // 直接清空选择数据
    const clearSelected = () => {
      select.currentNodeKey = ''
      select.currentNodeLabel = ''
      select.value = ''
      isLocalHanlde.value = true
      emit('update:modelValue', undefined)
    }
    // setCurrent通过select.value 设置下拉选择tree 显示绑定的v-model值
    // 可能存在问题：当动态v-model赋值时 options的数据还没有加载完成就会失效，下拉选择时会警告 placeholder
    const setCurrent = () => {
      select.currentNodeKey = select.value
      if (!props.multiple) {
        treeV2.value?.setCurrentKey(select.value)
        const data = treeV2.value?.getCurrentNode()
        select.currentNodeLabel = data?.label
      } else {
        treeV2.value?.setCheckedKeys((select.value as string).split(',').map((e) => +e))
        setTimeout(() => {
          const data = treeV2.value?.getCheckedNodes()
          select.currentNodeLabel = data?.map((e) => e.label).join(',') || ''
        }, 1000)
      }
    }
    // 监听外部清空数据源 清空组件数据
    watch(modelValue, (v) => {
      if (isLocalHanlde.value) {
        isLocalHanlde.value = false
        return
      }
      if (!v && select.currentNodeKey !== '') {
        clearSelected()
      }
      // 动态赋值
      if (v) {
        ;(select.value = props.multiple ? (v as any[]).join(',') : (v as string | number)),
          setCurrent()
      }
    })
    // 回显数据
    onMounted(async () => {
      await nextTick()
      if (select.value) {
        setCurrent()
      }
    })
    return {
      treeSelect,
      treeV2,
      TreeProps,
      isHaveSubTree,
      nodeClick,
      selectFilter,
      treeFilter,
      clearSelected,
      checkMethod,
      ...toRefs(select)
    }
  }
})
</script>

<style lang="scss" scoped>
.tree_box {
  width: 214px;
}
.el-scrollbar .el-scrollbar__view .el-select-dropdown__item {
  height: auto;
  max-height: 274px;
  padding: 0;
  overflow: hidden;
  overflow-y: auto;
}

.el-select-dropdown__item.selected {
  font-weight: normal;
}

ul li :deep(.el-tree .el-tree-node__content) {
  height: auto;
  padding: 0 20px;
}

.el-tree-node__label {
  font-weight: normal;
}

.el-tree :deep(.is-current .el-tree-node__label) {
  color: #409eff;
  font-weight: 700;
}

.el-tree :deep(.is-current .el-tree-node__children .el-tree-node__label) {
  color: #606266;
  font-weight: normal;
}
.selectInput {
  padding: 0 5px;
  box-sizing: border-box;
}
.el-select {
  width: 100% !important;
}
</style>
