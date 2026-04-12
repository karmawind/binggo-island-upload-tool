<template>
  <div class="article-management">
    <div class="page-header">
      <h1>帖子管理</h1>
    </div>

    <div class="content-card">
      <!-- 工具栏 -->
      <div class="toolbar">
        <div class="toolbar-left">
          <el-select v-model="filterStatus" placeholder="筛选状态" clearable style="width: 120px" @change="fetchPosts">
            <el-option label="草稿" value="draft" />
            <el-option label="已排期" value="scheduled" />
            <el-option label="发布中" value="publishing" />
            <el-option label="已发布" value="published" />
            <el-option label="失败" value="failed" />
          </el-select>
        </div>
        <div class="toolbar-right">
          <el-button @click="fetchPosts" :icon="Refresh">刷新</el-button>
          <el-button @click="triggerImport">导入 CSV</el-button>
          <el-button type="primary" @click="goToPublish">新建帖子</el-button>
          <input ref="csvInput" type="file" accept=".csv" style="display:none" @change="handleImport" />
        </div>
      </div>

      <!-- 帖子列表 -->
      <el-table :data="filteredPosts" style="width: 100%" @selection-change="handleSelection">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)" effect="plain">{{ statusLabel(scope.row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="scheduled_at" label="计划时间" width="170">
          <template #default="scope">
            <span v-if="scope.row.scheduled_at">{{ scope.row.scheduled_at }}</span>
            <span v-else style="color:#aaa">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="250">
          <template #default="scope">
            <el-button size="small" @click="editPost(scope.row)">编辑</el-button>
            <el-button size="small" type="primary" @click="publishSingle(scope.row)">发布</el-button>
            <el-button size="small" type="danger" @click="deletePost(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 批量操作 -->
      <div class="batch-bar" v-if="selectedPosts.length > 0">
        <span>已选 {{ selectedPosts.length }} 篇</span>
        <div class="batch-actions">
          <el-button type="primary" @click="batchPublish" :loading="batchPublishing">批量立即发布</el-button>
          <el-button type="warning" @click="showScheduleDialog">排期发布</el-button>
        </div>
      </div>
    </div>

    <!-- 排期对话框 -->
    <el-dialog v-model="scheduleDialogVisible" title="排期发布" width="450px">
      <el-form label-width="100px">
        <el-form-item label="起始时间">
          <el-date-picker v-model="scheduleForm.startTime" type="datetime" placeholder="选择开始时间" format="YYYY-MM-DD HH:mm" value-format="YYYY-MM-DD HH:mm" />
        </el-form-item>
        <el-form-item label="发布间隔">
          <el-input-number v-model="scheduleForm.interval" :min="10" :step="30" />
          <span style="margin-left: 8px">分钟</span>
        </el-form-item>
        <p style="color: #909399; font-size: 13px; margin-left: 100px">
          {{ selectedPosts.length }} 篇帖子将从 {{ scheduleForm.startTime || '...' }} 起，每隔 {{ scheduleForm.interval }} 分钟自动发布一篇。
        </p>
      </el-form>
      <template #footer>
        <el-button @click="scheduleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmSchedule">确认排期</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { articleApi } from '@/api/article'
import { accountApi } from '@/api/account'

const router = useRouter()
const posts = ref([])
const selectedPosts = ref([])
const filterStatus = ref(null)
const batchPublishing = ref(false)
const allAccounts = ref([])
const csvInput = ref(null)

// 排期
const scheduleDialogVisible = ref(false)
const scheduleForm = reactive({ startTime: '', interval: 60 })

const getStatusType = (status) => ({ draft: 'info', scheduled: '', publishing: 'warning', published: 'success', failed: 'danger' }[status] || 'info')
const statusLabel = (status) => ({ draft: '草稿', scheduled: '已排期', publishing: '发布中', published: '已发布', failed: '失败' }[status] || status)

const filteredPosts = computed(() => {
  return posts.value.filter(p => {
    if (filterStatus.value && p.status !== filterStatus.value) return false
    return true
  })
})

const fetchPosts = async () => {
  try {
    const res = await articleApi.getPosts()
    if (res.code === 200) posts.value = res.data || []
  } catch (error) { console.error('获取帖子失败:', error) }
}

const fetchAccounts = async () => {
  try {
    const res = await accountApi.getAccounts()
    if (res.code === 200 && res.data) {
      allAccounts.value = res.data.map(item => ({
        id: item[0], type: item[1], filePath: item[2], name: item[3], status: item[4]
      }))
    }
  } catch (error) { console.error('获取账号失败:', error) }
}

onMounted(() => { fetchPosts(); fetchAccounts() })

const handleSelection = (selection) => { selectedPosts.value = selection }
const goToPublish = () => { router.push('/article-publish') }
const editPost = (post) => { router.push({ path: '/article-publish', query: { id: post.id } }) }

const deletePost = async (post) => {
  try {
    await ElMessageBox.confirm(`确定要删除「${post.title}」吗？`, '确认删除', { type: 'warning' })
    const res = await articleApi.deletePost(post.id)
    if (res.code === 200) { ElMessage.success('删除成功'); fetchPosts() }
  } catch { /* cancelled */ }
}

const publishSingle = async (post) => {
  const platforms = JSON.parse(post.platforms || '[]')
  const singlePlatform = post.platform || 0
  const targetPlatforms = platforms.length ? platforms : (singlePlatform ? [singlePlatform] : [])

  if (!targetPlatforms.length) { ElMessage.warning('帖子未关联平台'); return }

  const pa = {}
  for (const pt of targetPlatforms) {
    const accs = allAccounts.value.filter(a => a.type === pt && a.status === 1)
    if (!accs.length) { ElMessage.warning(`${pt} 没有可用账号`); return }
    pa[pt] = accs.map(a => a.filePath)
  }

  try {
    const imagePaths = JSON.parse(post.image_paths || '[]')
    const tags = JSON.parse(post.tags || '[]')
    const res = await articleApi.publishArticle({
      title: post.title, content: post.content, imageList: imagePaths,
      tags, location: post.location || '', platformAccounts: pa
    })
    if (res.code === 200) ElMessage.success('发布任务已提交')
    else ElMessage.error(res.msg || '发布失败')
  } catch { ElMessage.error('发布失败') }
}

const batchPublish = async () => {
  batchPublishing.value = true
  let count = 0
  for (const post of selectedPosts.value) {
    try { await publishSingle(post); count++ } catch { /* skip */ }
  }
  batchPublishing.value = false
  ElMessage.success(`已提交 ${count} 篇`)
  fetchPosts()
}

// 排期
const showScheduleDialog = () => {
  scheduleForm.startTime = ''
  scheduleForm.interval = 60
  scheduleDialogVisible.value = true
}

const confirmSchedule = async () => {
  if (!scheduleForm.startTime) { ElMessage.warning('请选择起始时间'); return }
  try {
    const res = await articleApi.scheduleArticles({
      postIds: selectedPosts.value.map(p => p.id),
      startTime: scheduleForm.startTime,
      interval: scheduleForm.interval
    })
    if (res.code === 200) {
      ElMessage.success(res.msg)
      scheduleDialogVisible.value = false
      fetchPosts()
    } else {
      ElMessage.error(res.msg)
    }
  } catch { ElMessage.error('排期失败') }
}

// CSV 导入
const triggerImport = () => { csvInput.value?.click() }

const handleImport = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  try {
    const formData = new FormData()
    formData.append('file', file)
    const res = await articleApi.importArticles(formData)
    if (res.code === 200) {
      ElMessage.success(res.msg)
      fetchPosts()
    } else {
      ElMessage.error(res.msg)
    }
  } catch { ElMessage.error('导入失败') }
  event.target.value = ''
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.article-management {
  .page-header { margin-bottom: 20px; h1 { font-size: 24px; color: $text-primary; margin: 0; } }

  .content-card { background: #fff; border-radius: 4px; box-shadow: $box-shadow-light; padding: 20px; }

  .toolbar {
    display: flex; justify-content: space-between; margin-bottom: 16px;
    .toolbar-left { display: flex; align-items: center; }
    .toolbar-right { display: flex; gap: 8px; }
  }

  .batch-bar {
    margin-top: 16px; padding: 12px; background: #ecf5ff; border-radius: 4px;
    display: flex; align-items: center; justify-content: space-between;
    span { color: #409eff; }
    .batch-actions { display: flex; gap: 8px; }
  }
}
</style>
