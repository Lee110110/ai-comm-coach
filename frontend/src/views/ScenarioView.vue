<template>
  <div class="scenario-view">
    <!-- 输入表单 -->
    <el-card shadow="never" class="form-card">
      <template #header>
        <span class="card-title">急救话术</span>
        <span class="card-subtitle">描述你的沟通场景，获取即时建议</span>
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
            <el-form-item label="场景标题" prop="title">
              <el-input v-model="form.title" placeholder="例如：拒绝加班请求" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="场景描述" prop="description">
              <el-input
                v-model="form.description"
                type="textarea"
                :rows="3"
                placeholder="详细描述你面临的沟通场景..."
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="补充背景（选填）">
              <el-input
                v-model="form.context"
                type="textarea"
                :rows="2"
                placeholder="补充任何有助于理解场景的背景信息..."
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="关系类型" prop="relationship_type">
              <el-select v-model="form.relationship_type" placeholder="请选择" style="width: 100%">
                <el-option label="上司" value="上司" />
                <el-option label="同事" value="同事" />
                <el-option label="伴侣" value="伴侣" />
                <el-option label="家人" value="家人" />
                <el-option label="朋友" value="朋友" />
                <el-option label="客户" value="客户" />
                <el-option label="其他" value="其他" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="紧急程度" prop="urgency">
              <el-radio-group v-model="form.urgency">
                <el-radio label="低">低</el-radio>
                <el-radio label="中">中</el-radio>
                <el-radio label="高">高</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleSubmit">
            获取建议
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-section">
      <el-icon class="is-loading" :size="32"><Loading /></el-icon>
      <p class="loading-text">AI 正在分析你的场景，生成建议中...</p>
    </div>

    <!-- 结果区域 -->
    <div v-if="result" class="result-section">
      <h3 class="section-title">策略建议</h3>

      <!-- 三个策略卡片 -->
      <el-row :gutter="20" class="strategy-cards">
        <el-col :span="8">
          <el-card shadow="hover" class="strategy-card strategy-green">
            <template #header>
              <div class="strategy-header">
                <el-icon><ChatDotRound /></el-icon>
                <span>委婉策略</span>
              </div>
            </template>
            <p class="approach-text">{{ result.strategies?.tactful?.approach }}</p>
            <div class="scripts-list">
              <div
                v-for="(script, idx) in result.strategies?.tactful?.scripts || []"
                :key="idx"
                class="script-item"
              >
                <el-tag type="success" effect="plain" class="script-tag">
                  {{ script }}
                </el-tag>
                <el-button
                  size="small"
                  text
                  @click="copyText(script)"
                >
                  <el-icon><CopyDocument /></el-icon>
                </el-button>
              </div>
            </div>
            <div class="when-to-use">
              <span class="label">适用场景：</span>
              <span>{{ result.strategies?.tactful?.when_to_use }}</span>
            </div>
          </el-card>
        </el-col>

        <el-col :span="8">
          <el-card shadow="hover" class="strategy-card strategy-blue">
            <template #header>
              <div class="strategy-header">
                <el-icon><Promotion /></el-icon>
                <span>直接策略</span>
              </div>
            </template>
            <p class="approach-text">{{ result.strategies?.direct?.approach }}</p>
            <div class="scripts-list">
              <div
                v-for="(script, idx) in result.strategies?.direct?.scripts || []"
                :key="idx"
                class="script-item"
              >
                <el-tag type="primary" effect="plain" class="script-tag">
                  {{ script }}
                </el-tag>
                <el-button
                  size="small"
                  text
                  @click="copyText(script)"
                >
                  <el-icon><CopyDocument /></el-icon>
                </el-button>
              </div>
            </div>
            <div class="when-to-use">
              <span class="label">适用场景：</span>
              <span>{{ result.strategies?.direct?.when_to_use }}</span>
            </div>
          </el-card>
        </el-col>

        <el-col :span="8">
          <el-card shadow="hover" class="strategy-card strategy-orange">
            <template #header>
              <div class="strategy-header">
                <el-icon><SetUp /></el-icon>
                <span>策略性方案</span>
              </div>
            </template>
            <p class="approach-text">{{ result.strategies?.strategic?.approach }}</p>
            <div class="scripts-list">
              <div
                v-for="(script, idx) in result.strategies?.strategic?.scripts || []"
                :key="idx"
                class="script-item"
              >
                <el-tag type="warning" effect="plain" class="script-tag">
                  {{ script }}
                </el-tag>
                <el-button
                  size="small"
                  text
                  @click="copyText(script)"
                >
                  <el-icon><CopyDocument /></el-icon>
                </el-button>
              </div>
            </div>
            <div class="when-to-use">
              <span class="label">适用场景：</span>
              <span>{{ result.strategies?.strategic?.when_to_use }}</span>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 常见陷阱 -->
      <h3 class="section-title">常见陷阱</h3>
      <div class="pitfalls-section">
        <el-alert
          v-for="(pitfall, idx) in result.pitfalls || []"
          :key="idx"
          type="warning"
          :closable="false"
          class="pitfall-alert"
        >
          <template #title>
            <strong>{{ pitfall.warning }}</strong>
          </template>
          <p class="pitfall-why">原因：{{ pitfall.why }}</p>
          <p class="pitfall-alt">建议替代：{{ pitfall.alternative }}</p>
        </el-alert>
      </div>

      <!-- 预测反应 -->
      <h3 class="section-title">预测反应</h3>
      <el-row :gutter="16" class="reactions-section">
        <el-col
          v-for="(reaction, idx) in result.predicted_reactions || []"
          :key="idx"
          :span="8"
        >
          <el-card shadow="hover" class="reaction-card">
            <div class="reaction-header">
              <span class="reaction-label">{{ reaction.reaction }}</span>
              <el-tag
                :type="probabilityTagType(reaction.probability)"
                size="small"
                round
              >
                {{ reaction.probability }}
              </el-tag>
            </div>
            <p class="reaction-handle">{{ reaction.how_to_handle }}</p>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 历史记录 -->
    <el-card shadow="never" class="history-card">
      <template #header>
        <span class="card-title">历史记录</span>
      </template>
      <el-table :data="scenarios" stripe style="width: 100%">
        <el-table-column prop="title" label="场景标题" min-width="160" />
        <el-table-column prop="relationship_type" label="关系类型" width="100" />
        <el-table-column prop="urgency" label="紧急程度" width="100">
          <template #default="{ row }">
            <el-tag
              :type="urgencyTagType(row.urgency)"
              size="small"
            >
              {{ row.urgency }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="viewScenario(row.id)">
              查看
            </el-button>
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
import { useRouter } from 'vue-router'
import { createScenario, listScenarios, deleteScenario } from '../api/scenarios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, ChatDotRound, Promotion, SetUp, CopyDocument } from '@element-plus/icons-vue'

const router = useRouter()

const formRef = ref(null)
const loading = ref(false)
const result = ref(null)
const scenarios = ref([])

const form = reactive({
  title: '',
  description: '',
  context: '',
  relationship_type: '',
  urgency: '中',
})

const rules = {
  title: [{ required: true, message: '请输入场景标题', trigger: 'blur' }],
  description: [{ required: true, message: '请输入场景描述', trigger: 'blur' }],
  relationship_type: [{ required: true, message: '请选择关系类型', trigger: 'change' }],
  urgency: [{ required: true, message: '请选择紧急程度', trigger: 'change' }],
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    result.value = null
    try {
      const { data } = await createScenario({
        title: form.title,
        description: form.description,
        context: form.context || undefined,
        relationship_type: form.relationship_type,
        urgency: form.urgency,
      })
      result.value = data.advice || data
      ElMessage.success('建议生成成功')
      fetchScenarios()
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || '生成建议失败')
    } finally {
      loading.value = false
    }
  })
}

const fetchScenarios = async () => {
  try {
    const { data } = await listScenarios()
    scenarios.value = Array.isArray(data) ? data : data.items || []
  } catch {
    scenarios.value = []
  }
}

const viewScenario = (id) => {
  router.push({ name: 'scenario-detail', params: { id } })
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定删除该场景记录？', '确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteScenario(id)
    ElMessage.success('删除成功')
    fetchScenarios()
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

const urgencyTagType = (urgency) => {
  const map = { '低': 'info', '中': 'warning', '高': 'danger' }
  return map[urgency] || 'info'
}

const probabilityTagType = (prob) => {
  if (!prob) return 'info'
  const p = prob.toLowerCase ? prob.toLowerCase() : ''
  if (p.includes('高') || p.includes('high')) return 'danger'
  if (p.includes('中') || p.includes('medium')) return 'warning'
  return 'info'
}

const formatTime = (t) => {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchScenarios()
})
</script>

<style scoped>
.scenario-view {
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

.strategy-cards {
  margin-bottom: 8px;
}

.strategy-card {
  height: 100%;
}

.strategy-green {
  border-top: 3px solid #67c23a;
}

.strategy-blue {
  border-top: 3px solid #409eff;
}

.strategy-orange {
  border-top: 3px solid #e6a23c;
}

.strategy-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
}

.approach-text {
  font-size: 14px;
  color: #606266;
  margin: 0 0 12px;
  line-height: 1.6;
}

.scripts-list {
  margin-bottom: 12px;
}

.script-item {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  margin-bottom: 8px;
}

.script-tag {
  flex: 1;
  white-space: normal;
  height: auto;
  line-height: 1.5;
  padding: 4px 10px;
}

.when-to-use {
  font-size: 13px;
  color: #909399;
  line-height: 1.5;
  padding-top: 8px;
  border-top: 1px dashed #ebeef5;
}

.when-to-use .label {
  font-weight: 600;
  color: #606266;
}

.pitfalls-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.pitfall-alert p {
  margin: 4px 0 0;
  font-size: 13px;
  line-height: 1.5;
}

.pitfall-why {
  color: #909399;
}

.pitfall-alt {
  color: #67c23a;
}

.reactions-section {
  margin-bottom: 8px;
}

.reaction-card {
  height: 100%;
}

.reaction-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.reaction-label {
  font-weight: 600;
  font-size: 14px;
}

.reaction-handle {
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
  margin: 0;
}
</style>
