<template>
  <div class="dashboard-view">
    <!-- 欢迎区 -->
    <div class="welcome-section">
      <h1 class="welcome-text">欢迎回来，{{ authStore.user?.display_name || authStore.user?.username || '用户' }}</h1>
      <p class="welcome-sub">今天想练习什么？</p>
    </div>

    <!-- 快捷操作 -->
    <el-row :gutter="16" class="quick-actions">
      <el-col :span="6">
        <el-card shadow="hover" class="action-card" @click="goTo('/scenarios')">
          <div class="action-icon action-green">
            <el-icon :size="28"><FirstAidKit /></el-icon>
          </div>
          <h3 class="action-title">新建话术</h3>
          <p class="action-desc">描述场景，获取即时建议</p>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="action-card" @click="goTo({ name: 'simulation-new' })">
          <div class="action-icon action-blue">
            <el-icon :size="28"><ChatDotRound /></el-icon>
          </div>
          <h3 class="action-title">开始演练</h3>
          <p class="action-desc">与AI模拟真实沟通场景</p>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="action-card" @click="goTo('/messages')">
          <div class="action-icon action-orange">
            <el-icon :size="28"><EditPen /></el-icon>
          </div>
          <h3 class="action-title">润色消息</h3>
          <p class="action-desc">让表达更得体有效</p>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="action-card" @click="goTo('/patterns')">
          <div class="action-icon action-purple">
            <el-icon :size="28"><DataAnalysis /></el-icon>
          </div>
          <h3 class="action-title">查看画像</h3>
          <p class="action-desc">了解你的沟通风格</p>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <!-- 沟通画像概览 -->
      <el-col :span="12">
        <el-card shadow="never" class="overview-card">
          <template #header>
            <div class="card-header-row">
              <span class="card-title">沟通画像概览</span>
              <el-button text type="primary" @click="goTo('/patterns')">查看详情</el-button>
            </div>
          </template>
          <div v-if="patternLoading" class="chart-loading">
            <el-icon class="is-loading" :size="24"><Loading /></el-icon>
          </div>
          <div v-else-if="pattern" ref="radarChartRef" class="mini-radar"></div>
          <div v-else class="chart-empty">
            <el-empty description="完成演练后查看画像" :image-size="60" />
          </div>
        </el-card>
      </el-col>

      <!-- 最近洞察 -->
      <el-col :span="12">
        <el-card shadow="never" class="overview-card">
          <template #header>
            <div class="card-header-row">
              <span class="card-title">最近洞察</span>
              <el-button text type="primary" @click="goTo('/patterns')">查看全部</el-button>
            </div>
          </template>
          <div v-if="recentInsights.length === 0" class="chart-empty">
            <el-empty description="暂无洞察" :image-size="60" />
          </div>
          <div v-else class="insight-preview-list">
            <div
              v-for="insight in recentInsights"
              :key="insight.id"
              class="insight-preview"
              :class="insightClass(insight.type)"
            >
              <div class="insight-preview-left">
                <el-icon :size="16">
                  <WarnTriangleFilled v-if="insight.type === 'blind_spot'" />
                  <StarFilled v-else-if="insight.type === 'strength'" />
                  <TrendCharts v-else />
                </el-icon>
                <span class="insight-preview-title">{{ insight.title }}</span>
              </div>
              <el-tag size="small" :type="insightTagType(insight.type)">
                {{ insightTypeLabel(insight.type) }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近活动 -->
    <el-card shadow="never" class="activity-card">
      <template #header>
        <span class="card-title">最近活动</span>
      </template>
      <div v-if="recentActivities.length === 0" class="chart-empty">
        <el-empty description="暂无活动记录" :image-size="60" />
      </div>
      <el-table v-else :data="recentActivities" stripe style="width: 100%">
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="activityTagType(row.type)" size="small">
              {{ activityTypeLabel(row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="200">
          <template #default="{ row }">
            {{ truncate(row.title || row.scenario_description, 50) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.status" :type="row.status === 'completed' ? 'success' : 'primary'" size="small">
              {{ row.status === 'completed' ? '已完成' : '进行中' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="得分" width="80">
          <template #default="{ row }">
            <span v-if="row.score != null" class="score-value">{{ row.score }}</span>
            <span v-else class="score-empty">--</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="170">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="goToActivity(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { getCurrentPattern, getInsights } from '../api/patterns'
import { listSimulations } from '../api/simulations'
import { listScenarios } from '../api/scenarios'
import { ElMessage } from 'element-plus'
import {
  FirstAidKit,
  ChatDotRound,
  EditPen,
  DataAnalysis,
  Loading,
  WarnTriangleFilled,
  StarFilled,
  TrendCharts,
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const router = useRouter()
const authStore = useAuthStore()

const pattern = ref(null)
const patternLoading = ref(false)
const recentInsights = ref([])
const recentActivities = ref([])

const radarChartRef = ref(null)
let radarChart = null

const DIMENSION_KEYS = ['assertiveness', 'empathy', 'clarity', 'flexibility', 'conflict_handling', 'active_listening']
const DIMENSION_LABELS = {
  assertiveness: '坚定程度',
  empathy: '共情能力',
  clarity: '表达清晰度',
  flexibility: '灵活变通',
  conflict_handling: '冲突处理',
  active_listening: '积极倾听',
}

const goTo = (target) => {
  if (typeof target === 'string') {
    router.push(target)
  } else {
    router.push(target)
  }
}

const insightClass = (type) => {
  const map = {
    blind_spot: 'insight-blind',
    strength: 'insight-strength',
    trend: 'insight-trend',
  }
  return map[type] || ''
}

const insightTagType = (type) => {
  const map = {
    blind_spot: 'danger',
    strength: 'success',
    trend: 'primary',
  }
  return map[type] || 'info'
}

const insightTypeLabel = (type) => {
  const map = {
    blind_spot: '盲点',
    strength: '优势',
    trend: '趋势',
  }
  return map[type] || type
}

const activityTagType = (type) => {
  const map = { simulation: 'primary', scenario: 'success', message: 'warning' }
  return map[type] || 'info'
}

const activityTypeLabel = (type) => {
  const map = { simulation: '演练', scenario: '话术', message: '润色' }
  return map[type] || type
}

const goToActivity = (row) => {
  if (row.type === 'simulation') {
    router.push({ name: 'simulation', params: { id: row.id } })
  } else if (row.type === 'scenario') {
    router.push({ name: 'scenario-detail', params: { id: row.id } })
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

const fetchPattern = async () => {
  patternLoading.value = true
  try {
    const { data } = await getCurrentPattern()
    pattern.value = data
  } catch {
    pattern.value = null
  } finally {
    patternLoading.value = false
  }
}

const fetchInsights = async () => {
  try {
    const { data } = await getInsights()
    const all = Array.isArray(data) ? data : data.items || []
    recentInsights.value = all.slice(0, 3)
  } catch {
    recentInsights.value = []
  }
}

const fetchActivities = async () => {
  try {
    const [simRes, scenarioRes] = await Promise.allSettled([
      listSimulations(),
      listScenarios(),
    ])

    const activities = []

    if (simRes.status === 'fulfilled') {
      const sims = Array.isArray(simRes.value.data) ? simRes.value.data : simRes.value.data.items || []
      sims.forEach((s) => {
        activities.push({
          ...s,
          type: 'simulation',
          title: s.scenario_description,
        })
      })
    }

    if (scenarioRes.status === 'fulfilled') {
      const scenarios = Array.isArray(scenarioRes.value.data) ? scenarioRes.value.data : scenarioRes.value.data.items || []
      scenarios.forEach((s) => {
        activities.push({
          ...s,
          type: 'scenario',
        })
      })
    }

    // Sort by created_at desc and take top 5
    activities.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    recentActivities.value = activities.slice(0, 5)
  } catch {
    recentActivities.value = []
  }
}

const initRadarChart = () => {
  if (!radarChartRef.value || !pattern.value) return
  radarChart = echarts.init(radarChartRef.value)

  const scores = DIMENSION_KEYS.map((k) => pattern.value[k] ?? 0)
  const indicator = DIMENSION_KEYS.map((k) => ({
    name: DIMENSION_LABELS[k],
    max: 10,
  }))

  radarChart.setOption({
    tooltip: {},
    radar: {
      indicator,
      shape: 'circle',
      splitNumber: 5,
      radius: '70%',
      axisName: {
        color: '#606266',
        fontSize: 12,
      },
      splitArea: {
        areaStyle: {
          color: ['rgba(64,158,255,0.02)', 'rgba(64,158,255,0.05)', 'rgba(64,158,255,0.08)', 'rgba(64,158,255,0.11)', 'rgba(64,158,255,0.14)'],
        },
      },
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: scores,
            name: '当前评分',
            areaStyle: { color: 'rgba(64,158,255,0.2)' },
            lineStyle: { color: '#409eff', width: 2 },
            itemStyle: { color: '#409eff' },
          },
        ],
      },
    ],
  })
}

const handleResize = () => {
  radarChart?.resize()
}

watch(pattern, () => {
  nextTick(() => {
    initRadarChart()
  })
})

onMounted(async () => {
  await fetchPattern()
  fetchInsights()
  fetchActivities()
  nextTick(() => {
    initRadarChart()
  })
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  radarChart?.dispose()
})
</script>

<style scoped>
.dashboard-view {
  max-width: 1200px;
  margin: 0 auto;
}

.welcome-section {
  margin-bottom: 24px;
}

.welcome-text {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 4px;
}

.welcome-sub {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

/* Quick action cards */
.quick-actions {
  margin-bottom: 24px;
}

.action-card {
  cursor: pointer;
  text-align: center;
  padding: 8px 0;
  transition: transform 0.2s, box-shadow 0.2s;
}

.action-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.action-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 12px;
  margin-bottom: 12px;
}

.action-green {
  background: #f0f9eb;
  color: #67c23a;
}

.action-blue {
  background: #ecf5ff;
  color: #409eff;
}

.action-orange {
  background: #fdf6ec;
  color: #e6a23c;
}

.action-purple {
  background: #f3e8ff;
  color: #9b59b6;
}

.action-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 4px;
}

.action-desc {
  font-size: 12px;
  color: #909399;
  margin: 0;
}

/* Overview cards */
.overview-card {
  margin-bottom: 20px;
}

.card-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
}

.chart-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 260px;
}

.mini-radar {
  width: 100%;
  height: 280px;
}

.chart-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

/* Insight previews */
.insight-preview-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.insight-preview {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 8px;
  border-left: 3px solid #e4e7ed;
  background: #fafafa;
}

.insight-preview.insight-blind {
  border-left-color: #f56c6c;
  background: #fef0f0;
}

.insight-preview.insight-blind .el-icon {
  color: #f56c6c;
}

.insight-preview.insight-strength {
  border-left-color: #67c23a;
  background: #f0f9eb;
}

.insight-preview.insight-strength .el-icon {
  color: #67c23a;
}

.insight-preview.insight-trend {
  border-left-color: #409eff;
  background: #ecf5ff;
}

.insight-preview.insight-trend .el-icon {
  color: #409eff;
}

.insight-preview-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.insight-preview-title {
  font-size: 13px;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Activity */
.activity-card {
  margin-bottom: 20px;
}

.score-value {
  font-weight: 600;
  color: #409eff;
}

.score-empty {
  color: #c0c4cc;
}
</style>
