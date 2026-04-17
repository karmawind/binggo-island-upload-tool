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
          <el-select v-model="filterGroup" placeholder="运营者" clearable filterable style="width: 130px; margin-left: 8px">
            <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.name" />
          </el-select>
        </div>
        <div class="toolbar-right">
          <el-button @click="fetchPosts" :icon="Refresh">刷新</el-button>
          <el-button @click="triggerImport">导入 CSV</el-button>
          <el-button @click="articleApi.downloadTemplate()">下载模板</el-button>
          <el-button type="primary" @click="goToPublish">新建帖子</el-button>
          <input ref="csvInput" type="file" accept=".csv" style="display:none" @change="handleImport" />
        </div>
      </div>

      <!-- 帖子列表 -->
      <el-table :data="filteredPosts" style="width: 100%" @selection-change="handleSelection" row-key="id">
        <el-table-column type="selection" width="50" />
        <el-table-column type="expand">
          <template #default="scope">
            <div class="expand-account-select" v-if="getPostPlatforms(scope.row).length">
              <p class="expand-label">选择账号：</p>
              <div v-for="pt in getPostPlatforms(scope.row)" :key="pt" class="expand-platform-row">
                <el-tag size="small" effect="plain" style="margin-right: 8px; min-width: 70px">{{ formatPlatformId(pt) }}</el-tag>
                <el-select
                  :model-value="getPostAccounts(scope.row.id, pt)"
                  @update:model-value="val => setPostAccounts(scope.row.id, pt, val)"
                  multiple
                  placeholder="选择账号"
                  size="small"
                  style="flex: 1"
                  @change="handlePostAccountChange(scope.row)"
                >
                  <el-option
                    v-for="acc in getAccountsForPlatform(pt)"
                    :key="acc.id"
                    :label="(acc.group ? `[${acc.group}] ` : '') + acc.name"
                    :value="acc.id"
                  />
                </el-select>
              </div>
              <div v-if="!getPostPlatforms(scope.row).length" style="color: #a1a1aa">未关联平台</div>
            </div>
            <div v-else class="expand-account-select" style="color: #a1a1aa">未关联平台，请先编辑帖子选择平台</div>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column label="平台" width="140">
          <template #default="scope">
            <span v-if="scope.row.platforms && scope.row.platforms !== '[]'">
              {{ formatPlatforms(scope.row.platforms) }}
            </span>
            <span v-else-if="scope.row.platform" style="color:#a1a1aa">{{ formatPlatformId(scope.row.platform) }}</span>
            <span v-else style="color:#a1a1aa">未设置</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)" effect="plain">{{ statusLabel(scope.row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="scheduled_at" label="计划时间" width="170">
          <template #default="scope">
            <span v-if="scope.row.scheduled_at">{{ scope.row.scheduled_at }}</span>
            <span v-else style="color:#a1a1aa">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="250">
          <template #default="scope">
            <el-button size="small" @click="editPost(scope.row)">编辑</el-button>
            <el-button size="small" type="primary" @click="publishWithAccounts(scope.row)">发布</el-button>
            <el-button size="small" type="danger" @click="deletePost(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 批量操作 -->
      <div class="batch-bar" v-if="selectedPosts.length > 0">
        <span>已选 {{ selectedPosts.length }} 篇</span>
        <div class="batch-actions">
          <el-button type="primary" @click="openBatchPublishDialog">选择账号并发布</el-button>
          <el-button type="warning" @click="showScheduleDialog">排期发布</el-button>
          <el-button type="danger" @click="batchDelete">批量删除</el-button>
        </div>
      </div>
    </div>

    <!-- 批量选择账号发布对话框 -->
    <el-dialog v-model="batchPublishDialogVisible" title="选择账号并发布" width="600px" :close-on-click-modal="false">
      <p style="color: #909399; margin-bottom: 16px">为 {{ selectedPosts.length }} 篇帖子选择发布账号：</p>
      <div class="batch-platform-row" v-for="pt in batchPlatforms" :key="pt">
        <el-tag effect="plain" style="min-width: 80px">{{ formatPlatformId(pt) }}</el-tag>
        <el-select v-model="batchAccountMap[pt]" multiple placeholder="选择账号" style="flex: 1">
          <el-option
            v-for="acc in getAccountsForPlatform(pt)"
            :key="acc.id"
            :label="(acc.group ? `[${acc.group}] ` : '') + acc.name"
            :value="acc.id"
          />
        </el-select>
      </div>
      <div v-if="!batchPlatforms.length" style="color: #a1a1aa; text-align: center; padding: 20px">选中的帖子未关联平台</div>
      <template #footer>
        <el-button @click="batchPublishDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmBatchPublish" :loading="batchPublishing">确认发布</el-button>
      </template>
    </el-dialog>

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
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { articleApi } from '@/api/article'
import { accountApi } from '@/api/account'

const router = useRouter()
const posts = ref([])
const selectedPosts = ref([])
const filterStatus = ref(null)
const filterGroup = ref('')
const batchPublishing = ref(false)
const allAccounts = ref([])
const groups = ref([])
const csvInput = ref(null)

// 帖子账号选择映射：{ postId: { platformType: [accountId, ...] } }
const postAccountMap = reactive({})

// 批量发布
const batchPublishDialogVisible = ref(false)
const batchAccountMap = reactive({})
const batchPlatforms = ref([])

// 排期
const scheduleDialogVisible = ref(false)
const scheduleForm = reactive({ startTime: '', interval: 60 })

const getStatusType = (status) => ({ draft: 'info', scheduled: '', publishing: 'warning', published: 'success', failed: 'danger' }[status] || 'info')
const statusLabel = (status) => ({ draft: '草稿', scheduled: '已排期', publishing: '发布中', published: '已发布', failed: '失败' }[status] || status)

const PLATFORM_ID_TO_NAME = { 1: '小红书', 2: '视频号', 3: '抖音', 4: '快手', 5: '百家号', 6: '什么值得买', 7: '头条号', 8: '携程', 9: '搜狐号', 10: '微博' }
const formatPlatformId = (id) => PLATFORM_ID_TO_NAME[id] || `平台${id}`
const formatPlatforms = (jsonStr) => {
  try { return (JSON.parse(jsonStr) || []).map(id => PLATFORM_ID_TO_NAME[id] || `平台${id}`).join(', ') } catch { return jsonStr }
}

const VIDEO_PLATFORMS = new Set([1, 2, 3, 4])

const filteredPosts = computed(() => {
  return posts.value.filter(p => {
    if (filterStatus.value && p.status !== filterStatus.value) return false
    // 运营者筛选：根据帖子关联平台的账号分组过滤
    if (filterGroup.value) {
      const platforms = getPostPlatforms(p)
      const hasGroupAccount = platforms.some(pt => {
        return getAccountsForPlatform(pt).some(a => a.group === filterGroup.value)
      })
      if (!hasGroupAccount) return false
    }
    return true
  })
})

// 获取帖子关联的平台列表
const getPostPlatforms = (post) => {
  const platforms = JSON.parse(post.platforms || '[]')
  const singlePlatform = post.platform || 0
  return platforms.length ? platforms : (singlePlatform ? [singlePlatform] : [])
}

// 获取某平台的可用账号（status === 1）
const getAccountsForPlatform = (platformType) => {
  return allAccounts.value.filter(a => a.type === platformType && a.status === 1)
}

// 帖子账号辅助：getter/setter（避免 v-model 用 ?. 赋值报错）
const getPostAccounts = (postId, platformType) => {
  return postAccountMap[postId]?.[platformType] || []
}
const setPostAccounts = (postId, platformType, val) => {
  if (!postAccountMap[postId]) postAccountMap[postId] = {}
  postAccountMap[postId][platformType] = val
}

// 帖子账号选择变更 → 保存到后端
const handlePostAccountChange = async (post) => {
  const selected = postAccountMap[post.id]
  if (!selected) return
  try {
    await accountApi.updatePostAccounts({
      id: post.id,
      selected_accounts: JSON.stringify(selected)
    })
  } catch (error) {
    console.error('保存账号选择失败:', error)
  }
}

// 加载帖子已有的账号选择
const loadPostAccounts = (post) => {
  if (postAccountMap[post.id]) return
  try {
    const saved = JSON.parse(post.selected_accounts || '{}')
    postAccountMap[post.id] = saved
  } catch {
    postAccountMap[post.id] = {}
  }
}

const fetchPosts = async () => {
  try {
    const res = await articleApi.getPosts()
    if (res.code === 200) {
      posts.value = res.data || []
      // 初始化每篇帖子的账号选择
      posts.value.forEach(p => loadPostAccounts(p))
    }
  } catch (error) { console.error('获取帖子失败:', error) }
}

const fetchAccounts = async () => {
  try {
    const res = await accountApi.getAccounts()
    if (res.code === 200 && res.data) {
      allAccounts.value = res.data.map(item => ({
        id: item[0], type: item[1], filePath: item[2], name: item[3],
        status: item[4], group: item[5] || ''
      }))
    }
  } catch (error) { console.error('获取账号失败:', error) }
}

const fetchGroups = async () => {
  try {
    const res = await accountApi.getGroups()
    if (res.code === 200 && res.data) {
      groups.value = res.data
    }
  } catch (error) { console.error('获取分组失败:', error) }
}

onMounted(() => { fetchPosts(); fetchAccounts(); fetchGroups() })

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

// 根据帖子绑定的账号构建 platformAccounts（filePaths）
const buildPlatformAccounts = (post) => {
  const platforms = getPostPlatforms(post)
  const saved = postAccountMap[post.id] || {}
  const pa = {}

  for (const pt of platforms) {
    const accountIds = saved[pt] || []
    if (accountIds.length > 0) {
      // 使用绑定的账号
      const accs = allAccounts.value.filter(a => accountIds.includes(a.id) && a.status === 1)
      if (accs.length) {
        pa[pt] = accs.map(a => a.filePath)
        continue
      }
    }
    // 兜底：使用该平台所有有效账号
    const fallback = getAccountsForPlatform(pt)
    if (fallback.length) {
      pa[pt] = fallback.map(a => a.filePath)
    }
  }
  return pa
}

// 单篇发布（带账号选择）
const publishWithAccounts = async (post) => {
  const targetPlatforms = getPostPlatforms(post)
  if (!targetPlatforms.length) { ElMessage.warning('帖子未关联平台'); return }

  const imagePaths = JSON.parse(post.image_paths || '[]')
  const tags = JSON.parse(post.tags || '[]')
  const pa = buildPlatformAccounts(post)

  if (!Object.keys(pa).length) { ElMessage.warning('没有可用账号'); return }

  // 视频平台
  const videoPlatforms = targetPlatforms.filter(p => VIDEO_PLATFORMS.has(p))
  for (const pt of videoPlatforms) {
    if (!pa[pt] || !pa[pt].length) { ElMessage.warning(`${formatPlatformId(pt)} 没有可用账号`); return }
    if (!post.video_path) { ElMessage.warning(`${formatPlatformId(pt)} 需要视频文件路径`); return }
    try {
      const res = await articleApi.publishVideo({
        type: pt, title: post.title, fileList: [post.video_path],
        tags, accountList: pa[pt],
        category: 0, enableTimer: 0, videosPerDay: 1, dailyTimes: ['10:00'], startDays: 0,
        productLink: '', productTitle: '', isDraft: false, thumbnail: ''
      })
      if (res.code === 200) ElMessage.success(`${formatPlatformId(pt)} 发布任务已提交`)
      else ElMessage.error(res.msg || `${formatPlatformId(pt)} 发布失败`)
    } catch { ElMessage.error(`${formatPlatformId(pt)} 发布失败`) }
  }

  // 图文平台
  const articlePlatforms = targetPlatforms.filter(p => !VIDEO_PLATFORMS.has(p))
  if (articlePlatforms.length) {
    const articlePa = {}
    for (const pt of articlePlatforms) {
      if (pa[pt]) articlePa[pt] = pa[pt]
    }
    if (Object.keys(articlePa).length) {
      try {
        const res = await articleApi.publishArticle({
          title: post.title, content: post.content, imageList: imagePaths,
          tags, location: post.location || '', platformAccounts: articlePa
        })
        if (res.code === 200) ElMessage.success('图文发布任务已提交')
        else ElMessage.error(res.msg || '图文发布失败')
      } catch { ElMessage.error('图文发布失败') }
    }
  }
}

// 打开批量发布弹窗
const openBatchPublishDialog = () => {
  // 收集所有选中帖子涉及的平台
  const platformSet = new Set()
  selectedPosts.value.forEach(p => {
    getPostPlatforms(p).forEach(pt => platformSet.add(pt))
  })
  batchPlatforms.value = [...platformSet]

  // 初始化选择（保留之前的或默认空）
  Object.keys(batchAccountMap).forEach(k => delete batchAccountMap[k])
  batchPlatforms.value.forEach(pt => {
    batchAccountMap[pt] = []
  })

  batchPublishDialogVisible.value = true
}

// 确认批量发布
const confirmBatchPublish = async () => {
  // 检查是否每个平台都选了账号
  for (const pt of batchPlatforms.value) {
    if (!batchAccountMap[pt]?.length) {
      ElMessage.warning(`请为 ${formatPlatformId(pt)} 选择至少一个账号`)
      return
    }
  }

  batchPublishing.value = true
  let count = 0

  for (const post of selectedPosts.value) {
    const targetPlatforms = getPostPlatforms(post)
    const imagePaths = JSON.parse(post.image_paths || '[]')
    const tags = JSON.parse(post.tags || '[]')

    // 用弹窗中选择的账号
    const pa = {}
    for (const pt of targetPlatforms) {
      const accountIds = batchAccountMap[pt] || []
      const accs = allAccounts.value.filter(a => accountIds.includes(a.id) && a.status === 1)
      if (accs.length) pa[pt] = accs.map(a => a.filePath)
    }

    if (!Object.keys(pa).length) continue

    // 保存账号选择到帖子
    const saveMap = {}
    for (const pt of targetPlatforms) {
      if (batchAccountMap[pt]?.length) saveMap[pt] = batchAccountMap[pt]
    }
    try {
      await accountApi.updatePostAccounts({ id: post.id, selected_accounts: JSON.stringify(saveMap) })
    } catch { /* ignore */ }

    // 视频
    const videoPlatforms = targetPlatforms.filter(p => VIDEO_PLATFORMS.has(p))
    for (const pt of videoPlatforms) {
      if (!pa[pt]?.length || !post.video_path) continue
      try {
        await articleApi.publishVideo({
          type: pt, title: post.title, fileList: [post.video_path],
          tags, accountList: pa[pt],
          category: 0, enableTimer: 0, videosPerDay: 1, dailyTimes: ['10:00'], startDays: 0,
          productLink: '', productTitle: '', isDraft: false, thumbnail: ''
        })
      } catch { /* skip */ }
    }

    // 图文
    const articlePlatforms = targetPlatforms.filter(p => !VIDEO_PLATFORMS.has(p))
    if (articlePlatforms.length) {
      const articlePa = {}
      for (const pt of articlePlatforms) { if (pa[pt]) articlePa[pt] = pa[pt] }
      if (Object.keys(articlePa).length) {
        try {
          await articleApi.publishArticle({
            title: post.title, content: post.content, imageList: imagePaths,
            tags, location: post.location || '', platformAccounts: articlePa
          })
        } catch { /* skip */ }
      }
    }
    count++
  }

  batchPublishing.value = false
  batchPublishDialogVisible.value = false
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

const batchDelete = async () => {
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedPosts.value.length} 篇帖子吗？此操作不可撤销。`, '批量删除', { type: 'warning' })
    const res = await articleApi.batchDeletePosts(selectedPosts.value.map(p => p.id))
    if (res.code === 200) {
      ElMessage.success(res.msg)
      selectedPosts.value = []
      fetchPosts()
    } else {
      ElMessage.error(res.msg)
    }
  } catch { /* cancelled */ }
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
  .page-header {
    margin-bottom: 24px;
    h1 { font-size: 24px; font-weight: 700; color: $text-primary; margin: 0; }
  }

  .content-card {
    background: $bg-color;
    border-radius: $border-radius-lg;
    box-shadow: $shadow-sm;
    padding: 24px;
    position: relative;
    overflow: hidden;

    &::before {
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 3px;
      background: $card-accent-gradient;
    }
  }

  .toolbar {
    display: flex; justify-content: space-between; margin-bottom: 16px;
    .toolbar-left { display: flex; align-items: center; }
    .toolbar-right { display: flex; gap: 8px; }
  }

  .expand-account-select {
    padding: 12px 16px 12px 50px;

    .expand-label {
      font-size: 13px;
      color: $text-secondary;
      margin: 0 0 10px 0;
    }

    .expand-platform-row {
      display: flex;
      align-items: center;
      margin-bottom: 8px;
    }
  }

  .batch-bar {
    margin-top: 16px;
    padding: 12px 16px;
    background: linear-gradient(135deg, rgba(249, 115, 22, 0.08), rgba(99, 102, 241, 0.08));
    border-radius: $border-radius-sm;
    display: flex; align-items: center; justify-content: space-between;
    span { color: $primary-color; font-weight: 500; }
    .batch-actions { display: flex; gap: 8px; }
  }

  .batch-platform-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
  }
}
</style>
