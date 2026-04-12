<template>
  <div class="article-publish">
    <div class="page-header">
      <h1>图文发布</h1>
    </div>

    <div class="publish-content">
      <!-- 平台选择（多选） -->
      <div class="section-card">
        <h3>选择平台 <span class="hint">（可多选，一键多平台分发）</span></h3>
        <el-checkbox-group v-model="selectedPlatforms">
          <el-checkbox :value="5">百家号</el-checkbox>
          <el-checkbox :value="6">什么值得买</el-checkbox>
          <el-checkbox :value="7">头条号</el-checkbox>
          <el-checkbox :value="8">携程</el-checkbox>
        </el-checkbox-group>
      </div>

      <!-- 每个平台的账号选择 -->
      <div v-for="pType in selectedPlatforms" :key="pType" class="section-card">
        <h3>{{ platformNames[pType] }} — 选择账号</h3>
        <div class="account-selector">
          <el-button type="primary" plain size="small" @click="openAccountDialog(pType)">
            选择账号 (已选 {{ (platformSelectedAccounts[pType] || []).length }})
          </el-button>
          <div class="selected-accounts" v-if="(platformSelectedAccounts[pType] || []).length">
            <el-tag
              v-for="acc in platformSelectedAccounts[pType]"
              :key="acc.id"
              closable
              @close="removeAccountFromPlatform(pType, acc)"
              style="margin: 4px"
            >
              {{ acc.name }}
            </el-tag>
          </div>
        </div>
      </div>

      <!-- 标题 -->
      <div class="section-card">
        <h3>标题 <span class="required">*</span></h3>
        <el-input v-model="form.title" placeholder="请输入标题" maxlength="80" show-word-limit />
      </div>

      <!-- 正文 -->
      <div class="section-card">
        <h3>正文内容</h3>
        <el-input v-model="form.content" type="textarea" placeholder="请输入正文内容（≥60字有机会评为优质）" :rows="8" maxlength="3000" show-word-limit />
      </div>

      <!-- 图片上传 -->
      <div class="section-card">
        <h3>上传图片 <span class="hint">（最多20张，推荐宽高比3:4~2:1）</span></h3>
        <el-upload :action="uploadUrl" list-type="picture-card" :file-list="fileList" :on-success="handleUploadSuccess" :on-remove="handleUploadRemove" :before-upload="beforeUpload" accept="image/*" :limit="20" name="file">
          <el-icon><Plus /></el-icon>
        </el-upload>
      </div>

      <!-- 标签 -->
      <div class="section-card">
        <h3>标签</h3>
        <div class="tags-input">
          <el-tag v-for="tag in form.tags" :key="tag" closable @close="removeTag(tag)" style="margin-right: 8px">{{ tag }}</el-tag>
          <el-input v-if="tagInputVisible" ref="tagInputRef" v-model="tagInputValue" size="small" style="width: 120px" @keyup.enter="addTag" @blur="addTag" />
          <el-button v-else size="small" @click="showTagInput">+ 添加标签</el-button>
        </div>
      </div>

      <!-- 携程专用：地点 -->
      <div class="section-card" v-if="selectedPlatforms.includes(8)">
        <h3>地点 <span class="required">（携程必填）</span></h3>
        <el-input v-model="form.location" placeholder="请输入地点，如：杭州" />
      </div>

      <!-- 操作按钮 -->
      <div class="action-bar">
        <el-button @click="saveDraft">保存草稿</el-button>
        <el-button type="primary" @click="publish" :loading="publishing">
          {{ publishing ? '发布中...' : '立即发布' }}
        </el-button>
      </div>
    </div>

    <!-- 账号选择对话框 -->
    <el-dialog v-model="showAccountDialog" :title="'选择 ' + platformNames[currentDialogPlatform] + ' 账号'" width="500px">
      <el-table :data="dialogAccounts" @selection-change="handleAccountSelection" ref="accountTableRef">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="status" label="状态">
          <template #default="scope">
            <el-tag :type="scope.row.status === '正常' ? 'success' : 'danger'" effect="plain">{{ scope.row.status }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="showAccountDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmAccountSelection">确定</el-button>
      </template>
    </el-dialog>

    <!-- 发布进度对话框 -->
    <el-dialog v-model="progressVisible" title="多平台发布进度" width="500px" :close-on-click-modal="false">
      <div class="progress-content">
        <el-progress :percentage="progressPercent" :status="progressStatus" />
        <div class="progress-detail">
          <p>已完成: {{ progressCompleted }} / {{ progressTotal }}</p>
          <div v-for="result in progressResults" :key="result.platform + result.account" class="progress-item">
            <el-tag :type="result.success ? 'success' : 'danger'" effect="plain">{{ result.success ? '成功' : '失败' }}</el-tag>
            <el-tag effect="plain" size="small">{{ result.platform }}</el-tag>
            <span>{{ result.account.split('\\').pop().split('/').pop() }}</span>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, nextTick, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { articleApi } from '@/api/article'
import { accountApi } from '@/api/account'
import { useArticleDraftStore } from '@/stores/articleDraft'

const platformNames = { 5: '百家号', 6: '什么值得买', 7: '头条号', 8: '携程' }
const draftStore = useArticleDraftStore()

// ref 类型的 store 属性必须用 storeToRefs 解构，否则 Pinia 会自动解包 ref 导致 .value 为 undefined
const { selectedPlatforms, fileList } = storeToRefs(draftStore)
// reactive 类型的 store 属性可以直接解构
const form = draftStore.form
const platformSelectedAccounts = draftStore.platformSelectedAccounts

// 账号相关
const allAccounts = ref([])
const showAccountDialog = ref(false)
const currentDialogPlatform = ref(5)
const accountTableRef = ref(null)
const tempSelectedAccounts = ref([])

// 图片相关 — fileList 已通过 storeToRefs 解构
const uploadUrl = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:5409') + '/uploadImage'

// 标签相关
const tagInputVisible = ref(false)
const tagInputValue = ref('')
const tagInputRef = ref(null)

// 发布状态
const publishing = ref(false)
const progressVisible = ref(false)
const progressPercent = ref(0)
const progressStatus = ref('')
const progressCompleted = ref(0)
const progressTotal = ref(0)
const progressResults = ref([])

// 对话框中显示的账号（按当前选中平台过滤）
const dialogAccounts = computed(() => {
  return allAccounts.value.filter(acc => acc.type === currentDialogPlatform.value)
})

// 获取所有账号
const fetchAccounts = async () => {
  try {
    const res = await accountApi.getAccounts()
    if (res.code === 200 && res.data) {
      allAccounts.value = res.data.map(item => ({
        id: item[0],
        type: item[1],
        filePath: item[2],
        name: item[3],
        status: item[4] === 1 ? '正常' : '异常',
      }))
    }
  } catch (error) {
    console.error('获取账号失败:', error)
  }
}

onMounted(() => { fetchAccounts() })

// 打开账号选择对话框
const openAccountDialog = (pType) => {
  currentDialogPlatform.value = pType
  tempSelectedAccounts.value = [...(platformSelectedAccounts[pType] || [])]
  showAccountDialog.value = true
  // 设置表格已选中状态
  nextTick(() => {
    if (accountTableRef.value) {
      dialogAccounts.value.forEach(row => {
        if (tempSelectedAccounts.value.some(s => s.id === row.id)) {
          accountTableRef.value.toggleRowSelection(row, true)
        }
      })
    }
  })
}

const handleAccountSelection = (selection) => {
  tempSelectedAccounts.value = selection
}

const confirmAccountSelection = () => {
  platformSelectedAccounts[currentDialogPlatform.value] = [...tempSelectedAccounts.value]
  showAccountDialog.value = false
}

const removeAccountFromPlatform = (pType, acc) => {
  platformSelectedAccounts[pType] = (platformSelectedAccounts[pType] || []).filter(a => a.id !== acc.id)
}

// 图片上传
const beforeUpload = (file) => {
  if (!file.type.startsWith('image/')) { ElMessage.error('只能上传图片文件'); return false }
  if (file.size / 1024 / 1024 > 10) { ElMessage.error('图片大小不能超过 10MB'); return false }
  return true
}

const handleUploadSuccess = (response, file) => {
  if (response.code === 200) {
    form.imagePaths.push(response.data.filepath)
    file.uploadedPath = response.data.filepath
  } else {
    ElMessage.error('上传失败: ' + response.msg)
  }
}

const handleUploadRemove = (file) => {
  if (file.uploadedPath) {
    form.imagePaths = form.imagePaths.filter(p => p !== file.uploadedPath)
  }
}

// 标签
const showTagInput = () => { tagInputVisible.value = true; nextTick(() => tagInputRef.value?.focus()) }
const addTag = () => {
  const val = tagInputValue.value.trim()
  if (val && !form.tags.includes(val)) form.tags.push(val)
  tagInputVisible.value = false; tagInputValue.value = ''
}
const removeTag = (tag) => { form.tags = form.tags.filter(t => t !== tag) }

// 保存草稿
const saveDraft = async () => {
  if (!form.title) { ElMessage.warning('请输入标题'); return }
  try {
    await articleApi.savePost({
      title: form.title,
      content: form.content,
      image_paths: JSON.stringify(form.imagePaths),
      tags: JSON.stringify(form.tags),
      location: form.location,
      platforms: JSON.stringify(selectedPlatforms.value),
      account_ids: JSON.stringify(
        Object.fromEntries(
          selectedPlatforms.value.map(p => [p, (platformSelectedAccounts[p] || []).map(a => a.id)])
        )
      )
    })
    ElMessage.success('草稿已保存')
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

// 发布
const publish = async () => {
  if (!form.title) { ElMessage.warning('请输入标题'); return }
  if (!selectedPlatforms.value.length) { ElMessage.warning('请选择至少一个平台'); return }

  // 构造每个平台的账号列表
  const platformAccounts = {}
  let totalAccounts = 0
  for (const pType of selectedPlatforms.value) {
    const accounts = platformSelectedAccounts[pType] || []
    if (!accounts.length) {
      ElMessage.warning(`请为${platformNames[pType]}选择至少一个账号`)
      return
    }
    platformAccounts[pType] = accounts.map(a => a.filePath)
    totalAccounts += accounts.length
  }

  if (selectedPlatforms.value.includes(8) && !form.location) {
    ElMessage.warning('携程发布必须填写地点')
    return
  }

  publishing.value = true
  progressVisible.value = true
  progressPercent.value = 0
  progressCompleted.value = 0
  progressTotal.value = totalAccounts
  progressResults.value = []
  progressStatus.value = ''

  try {
    const res = await articleApi.publishArticle({
      title: form.title,
      content: form.content,
      imageList: form.imagePaths,
      tags: form.tags,
      location: form.location,
      platformAccounts  // 多平台模式
    })

    if (res.code === 200 && res.data?.taskId) {
      pollTaskStatus(res.data.taskId)
    } else {
      ElMessage.error(res.msg || '发布失败')
      publishing.value = false
    }
  } catch (error) {
    ElMessage.error('发布请求失败')
    publishing.value = false
  }
}

const pollTaskStatus = (taskId) => {
  const timer = setInterval(async () => {
    try {
      const res = await articleApi.getTaskStatus(taskId)
      if (res.code === 200) {
        const { status, completed, total, results } = res.data
        progressCompleted.value = completed
        progressTotal.value = total
        progressResults.value = results
        progressPercent.value = total > 0 ? Math.round((completed / total) * 100) : 0
        if (status === 'completed') {
          clearInterval(timer)
          progressStatus.value = results.every(r => r.success) ? 'success' : 'warning'
          publishing.value = false
          ElMessage.success('发布任务完成')
          draftStore.reset()
        }
      }
    } catch (error) {
      clearInterval(timer)
      publishing.value = false
    }
  }, 2000)
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.article-publish {
  .page-header {
    margin-bottom: 24px;
    h1 { font-size: 24px; font-weight: 700; color: $text-primary; margin: 0; }
  }

  .section-card {
    background: $bg-color;
    border-radius: $border-radius-lg;
    box-shadow: $shadow-sm;
    padding: 24px;
    margin-bottom: 16px;
    position: relative;
    overflow: hidden;

    &::before {
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 3px;
      background: $card-accent-gradient;
    }

    h3 {
      margin: 0 0 14px;
      font-size: 16px;
      font-weight: 600;
      color: $text-primary;
      .required { color: $danger-color; }
      .hint { font-size: 12px; color: $text-secondary; font-weight: normal; }
    }
  }

  .account-selector { .selected-accounts { margin-top: 8px; } }
  .tags-input { display: flex; flex-wrap: wrap; align-items: center; gap: 4px; }

  .action-bar {
    background: $bg-color;
    border-radius: $border-radius-lg;
    box-shadow: $shadow-sm;
    padding: 16px 24px;
    display: flex;
    justify-content: flex-end;
    gap: 12px;
  }

  .progress-content {
    .progress-detail {
      margin-top: 16px;
      .progress-item { display: flex; align-items: center; gap: 8px; margin-top: 8px; }
    }
  }
}
</style>
