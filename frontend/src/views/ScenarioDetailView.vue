<template>
  <div class="scenario-detail-view">
    <div v-if="loading" class="loading-section">
      <el-icon class="is-loading" :size="32"><Loading /></el-icon>
      <p class="loading-text">正在加载场景详情...</p>
    </div>

    <div v-if="!loading && scenario">
      <!-- 场景基本信息 -->
      <el-card shadow="never" class="info-card">
        <template #header>
          <div class="info-header">
            <span class="card-title">{{ scenario.title }}</span>
            <div class="info-tags">
              <el-tag size="small">{{ scenario.relationship_type }}</el-tag>
              <el-tag :type="urgencyTagType(scenario.urgency)" size="small">{{ scenario.urgency }}</el-tag>
            </div>
          </div>
        </template>
        <p class="description">{{ scenario.description }}</p>
        <p v-if="scenario.context" class="context">
          <span class="label">补充背景：</span>{{ scenario.context }}
        </p>
      </el-card>

      <!-- 策略建议 -->
      <h3 class="section-title">策略建议</h3>
      <el-row :gutter="20" class="strategy-cards">
        <el-col :span="8">
          <el-card shadow="hover" class="strategy-card strategy-green">
            <template #header>
              <div class="strategy-header">
                <el-icon><ChatDotRound /></el-icon>
                <span>委婉策略</span>
              </div>
            </template>
            <p class="approach-text">{{ advice.strategies?.tactful?.approach }}</p>
            <div class="scripts-list">
              <div
                v-for="(script, idx) in advice.strategies?.tactful?.scripts || []"
                :key="idx"
                class="script-item"
              >
                <el-tag type="success" effect="plain" class="script-tag">
                  {{ script }}
                </el-tag>
                <el-button size="small" text @click="copyText(script)">
                  <el-icon><CopyDocument /></el-icon>
                </el-button>
              </div>
            </div>
            <div class="when-to-use">
              <span class="label">适用场景：</span>
              <span>{{ advice.strategies?.tactful?.when_to_use }}</span>
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
            <p class="approach-text">{{ advice.strategies?.direct?.approach }}</p>
            <div class="scripts-list">
              <div
                v-for="(script, idx) in advice.strategies?.direct?.scripts || []"
                :key="idx"
                class="script-item"
              >
                <el-tag type="primary" effect="plain" class="script-tag">
                  {{ script }}
                </el-tag>
                <el-button size="small" text @click="copyText(script)">
                  <el-icon><CopyDocument /></el-icon>
                </el-button>
              </div>
            </div>
            <div class="when-to-use">
              <span class="label">适用场景：</span>
              <span>{{ advice.strategies?.direct?.when_to_use }}</span>
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
            <p class="approach-text">{{ advice.strategies?.strategic?.approach }}</p>
            <div class="scripts-list">
              <div
                v-for="(script, idx) in advice.strategies?.strategic?.scripts || []"
                :key="idx"
                class="script-item"
              >
                <el-tag type="warning" effect="plain" class="script-tag">
                  {{ script }}
                </el-tag>
                <el-button size="small" text @click="copyText(script)">
                  <el-icon><CopyDocument /></el-icon>
                </el-button>
              </div>
            </div>
            <div class="when-to-use">
              <span class="label">适用场景：</span>
              <span>{{ advice.strategies?.strategic?.when_to_use }}</span>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 常见陷阱 -->
      <h3 class="section-title">常见陷阱</h3>
      <div class="pitfalls-section">
        <el-alert
          v-for="(pitfall, idx) in advice.pitfalls || []"
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
          v-for="(reaction, idx) in advice.predicted_reactions || []"
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

    <el-empty v-if="!loading && !scenario" description="未找到该场景" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getScenario } from '../api/scenarios'
import { ElMessage } from 'element-plus'
import { Loading, ChatDotRound, Promotion, SetUp, CopyDocument } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const scenario = ref(null)
const advice = ref({})

const fetchScenario = async () => {
  try {
    const { data } = await getScenario(route.params.id)
    scenario.value = data
    advice.value = data.advice || {}
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '加载场景详情失败')
    scenario.value = null
  } finally {
    loading.value = false
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

onMounted(() => {
  fetchScenario()
})
</script>

<style scoped>
.scenario-detail-view {
  max-width: 1200px;
  margin: 0 auto;
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

.info-card {
  margin-bottom: 24px;
}

.info-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
}

.info-tags {
  display: flex;
  gap: 8px;
}

.description {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  margin: 0 0 8px;
}

.context {
  font-size: 13px;
  color: #909399;
  margin: 0;
}

.context .label {
  font-weight: 600;
  color: #606266;
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