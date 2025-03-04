import AppIcon from './icons/AppIcon.vue'
import AppAvatar from './app-avatar/index.vue'
import LoginLayout from './login-layout/index.vue'
import LoginContainer from './login-container/index.vue'
import LayoutContainer from './layout-container/index.vue'
import TagsInput from './tags-input/index.vue'
import CardBox from './card-box/index.vue'
import CardAdd from './card-add/index.vue'
import BackButton from './back-button/index.vue'
import AppTable from './app-table/index.vue'
import ReadWrite from './read-write/index.vue'
import TagEllipsis from './tag-ellipsis/index.vue'
import CommonList from './common-list/index.vue'
import dynamicsForm from './dynamics-form'
import CardCheckbox from './card-checkbox/index.vue'
import AiChat from './ai-chat/index.vue'
import InfiniteScroll from './infinite-scroll/index.vue'
import AutoTooltip from './auto-tooltip/index.vue'
import MdEditor from './markdown/MdEditor.vue'
import MdPreview from './markdown/MdPreview.vue'
import MdEditorMagnify from './markdown/MdEditorMagnify.vue'
import LogoFull from './logo/LogoFull.vue'
import LogoIcon from './logo/LogoIcon.vue'
import SendIcon from './logo/SendIcon.vue'
import CodemirrorEditor from './codemirror-editor/index.vue'
import ModelSelect from './model-select/index.vue'
import ComTreeSelect from './tree-select/ComTreeSelect.vue'

declare module '@vue/runtime-core' {
  export interface GlobalComponents {
    AppIcon: typeof AppIcon
    AppAvatar: typeof AppAvatar
    LoginLayout: typeof LoginLayout
    LoginContainer: typeof LoginContainer
    LayoutContainer: typeof LayoutContainer
    TagsInput: typeof TagsInput
    CardBox: typeof CardBox
    CardAdd: typeof CardAdd
    BackButton: typeof BackButton
    AppTable: typeof AppTable
    ReadWrite: typeof ReadWrite
    TagEllipsis: typeof TagEllipsis
    CommonList: typeof CommonList
    dynamicsForm: typeof dynamicsForm
    CardCheckbox: typeof CardCheckbox
    AiChat: typeof AiChat
    InfiniteScroll: typeof InfiniteScroll
    AutoTooltip: typeof AutoTooltip
    MdEditor: typeof MdEditor
    MdPreview: typeof MdPreview
    MdEditorMagnify: typeof MdEditorMagnify
    LogoFull: typeof LogoFull
    LogoIcon: typeof LogoIcon
    SendIcon: typeof SendIcon
    CodemirrorEditor: typeof CodemirrorEditor
    ModelSelect: typeof ModelSelect
    ComTreeSelect: typeof ComTreeSelect
  }
}