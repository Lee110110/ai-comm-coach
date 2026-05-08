<template>
  <div class="message-polish-view">
    <!-- 输入表单 -->
    <el-card shadow="never" class="form-card">
      <template #header>
        <span class="card-title">消息润色</span>
        <span class="card-subtitle">让你的消息表达更得体、更有效</span>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        size="default"
      >
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="原始消息" prop="original_message">
              <el-input
                v-model="form.original_message"
                type="textarea"
                :rows="4"
                placeholder="输入你想要润色的消息内容..."
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="上下文/目的（选填）">
              <el-input
                v-model="form.context"
                placeholder="例如：回复客户投诉邮件"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="期望语气（选填）">
              <el-select v-model="form.desired_tone" placeholder="请选择" clearable style="width: 100%">
                <el-option label="正式" value="正式" />
                <el-option label="亲切" value="亲切" />
                <el-option label="坚定" value="坚定" />
                <el-option label="委婉" value="委婉" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handlePolish">
            润色消息
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-section">
      <el-icon class="is-loading" :size="32"><Loading /></el-icon>
      <p class="loading-text">AI 正在润色你的消息...</p>
    </div>

    <!-- 结果区域 -->
    <div v-if="result" class="result-section">
      <!-- 对比展示 -->
      <h3 class="section-title">润色对比</h3>
      <el-row :gutter="20" class="comparison-row">
        <el-col :span="12">
          <el-card shadow="never" class="compare-card original-card">
            <template #header>
              <span class="compare-label">原始消息</span>
            </template>
            <p class="compare-text">{{ result.original_message || form.original_message }}</p>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="never" class="compare-card polished-card">
            <template #header>
              <div class="polished-header">
                <span class="compare-label">润色结果</span>
                <el-button size="small" text @click="copyText(result.polished_message)">
                  <el-icon><CopyDocument /></el-icon> 复制
                </el-button>
              </div>
            </template>
            <p class="compare-text polished-text">{{ result.polished_message }}</p>
          </el-card>
        </el-col>
      </el-row>

      <!-- 修改详情 -->
      <h3 class="section-title">修改详情</h3>
      <el-table :data="result.changes || []" stripe class="changes-table">
        <el-table-column prop="original" label="原文片段" min-width="200" />
        <el-table-column prop="polished" label="润色后" min-width="200" />
        <el-table-column prop="reason" label="修改原因" min-width="200" />
      </el-table>

      <!-- 其他语气版本 -->
      <h3 v-if="result.alternative_versions && result.alternative_versions.length" class="section-title">
        其他语气版本
      </h3>
      <el-tabs v-if="result.alternative_versions && result.alternative_versions.length" type="border-card">
        <el-tab-pane
          v-for="(version, idx) in result.alternative_versions"
          :key="idx"
          :label="version.tone"
        >
          <div class="alt-version-content">
            <p class="alt-version-text">{{ version.message }}</p>
            <el-button size="small" text @click="copyText(version.message)">
              <el-icon><CopyDocument /></el-icon> 复制
            </el-button>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 历史记录 -->
    <el-card shadow="never" class="history-card">
      <template #header>
        <span class="card-title">润色历史</span>
      </template>
      <el-table :data="messages" stripe style="width: 100%">
        <el-table-column prop="original_message" label="原始消息" min-width="240">
          <template #default="{ row }">
            {{ truncate(row.original_message, 50) }}
          </template>
        </el-table-column>
        <el-table-column prop="desired_tone" label="期望语气" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button size="small" text type="danger" @click="handleDelete(row.id)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { polishMessage, listMessages, deleteMessage } from '../api/messages'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, CopyDocument } from '@element-plus/icons-vue'

const formRef = ref(null)
const loading = ref(false)
const result = ref(null)
const messages = ref([])

const form = reactive({
  original_message: '',
  context: '',
  desired_tone: '',
})

const rules = {
  original_message: [{ required: true, message: '请输入原始消息', trigger: 'blur' }],
}

const handlePolish = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    result.value = null
    try {
      const { data } = await polishMessage({
        original_message: form.original_message,
        context: form.context || undefined,
        desired_tone: form.desired_tone || undefined,
      })
      result.value = data
      ElMessage.success('润色完成')
      fetchMessages()
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || '润色失败')
    } finally {
      loading.value = false
    }
  })
}

const fetchMessages = async () => {
  try {
    const { data } = await listMessages()
    messages.value = Array.isArray(data) ? data : data.items || []
  } catch {
    messages.value = []
  }
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定删除该润色记录？', '确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteMessage(id)
    ElMessage.success('删除成功')
    fetchMessages()
  } catch {
    // cancelled
  }
}

const copyText = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}

const truncate = (str, len) => {
  if (!str) return ''
  return str.length > len ? str.slice(0, len) + '...' : str
}

const formatTime = (t) => {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchMessages()
})
</script>

<style scoped>
.message-polish-view {
  max-width: 1200px;
  margin: 0 auto;
}

.form-card,
.history-card {
  margin-bottom: 24px;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
}

.card-subtitle {
  display: block;
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.loading-section {
  text-align: center;
  padding: 60px 0;
}

.loading-text {
  margin-top: 16px;
  color: #909399;
  font-size: 14px;
}

.result-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 24px 0 16px;
}

.comparison-row {
  margin-bottom: 8px;
}

.compare-card {
  height: 100%;
}

.original-card {
  background: #fafafa;
}

.polished-card {
  background: #f0f9eb;
  border: 1px solid #e1f3d8;
}

.compare-label {
  font-weight: 600;
  font-size: 14px;
}

.polished-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.compare-text {
  font-size: 14px;
  color: #606266;
  line-height: 1.8;
  margin: 0;
  white-space: pre-wrap;
}

.polished-text {
  color: #303133;
}

.changes-table {
  margin-bottom: 8px;
}

.alt-version-content {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.alt-version-text {
  font-size: 14px;
  color: #606266;
  line-height: 1.8;
  margin: 0;
  white-space: pre-wrap;
}
</style>