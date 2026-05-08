<template>
  <div class="pattern-view">
    <div class="top-bar">
      <h2 class="page-title">沟通画像</h2>
      <el-button type="primary" :loading="recomputing" @click="handleRecompute">
        <el-icon><Refresh /></el-icon>
        重新计算
      </el-button>
    </div>

    <!-- 雷达图 -->
    <el-card shadow="never" class="radar-card">
      <div ref="radarChartRef" class="radar-chart"></div>
    </el-card>

    <!-- 维度详情卡片 -->
    <el-row :gutter="16" class="dimension-cards">
      <el-col v-for="dim in dimensions" :key="dim.key" :span="4">
        <el-card shadow="hover" class="dim-card" :class="dim.cardClass">
          <div class="dim-score">{{ pattern?.[dim.key] ?? '--' }}</div>
          <div class="dim-name">{{ dim.label }}</div>
          <div v-if="dim.trend != null" class="dim-trend" :class="dim.trend > 0 ? 'trend-up' : dim.trend < 0 ? 'trend-down' : ''">
            <el-icon v-if="dim.trend > 0"><Top /></el-icon>
            <el-icon v-else-if="dim.trend < 0"><Bottom /></el-icon>
            <span>{{ dim.trend > 0 ? '+' : '' }}{{ dim.trend }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <!-- 洞察列表 -->
      <el-col :span="14">
        <el-card shadow="never" class="insights-card">
          <template #header>
            <span class="card-title">沟通洞察</span>
          </template>

          <div v-if="insights.length === 0" class="empty-state">
            <el-empty description="暂无洞察数据，完成更多演练后将生成" />
          </div>

          <div v-for="insight in insights" :key="insight.id" class="insight-item" :class="insightClass(insight.type)">
            <div class="insight-header">
              <el-icon :size="18" class="insight-icon">
                <WarnTriangleFilled v-if="insight.type === 'blind_spot'" />
                <StarFilled v-else-if="insight.type === 'strength'" />
                <TrendCharts v-else />
              </el-icon>
              <span class="insight-type-label">{{ insightTypeLabel(insight.type) }}</span>
              <el-button
                size="small"
                text
                @click="handleMarkRead(insight.id)"
                :disabled="insight.is_read"
              >
                {{ insight.is_read ? '已读' : '标记已读' }}
              </el-button>
            </div>
            <h4 class="insight-title">{{ insight.title }}</h4>
            <p class="insight-desc">{{ insight.description }}</p>
            <div v-if="insight.evidence?.length" class="insight-evidence">
              <span class="evidence-label">证据：</span>
              <el-tag
                v-for="(e, ei) in insight.evidence"
                :key="ei"
                size="small"
                effect="plain"
                class="evidence-tag"
              >
                {{ e }}
              </el-tag>
            </div>
            <div v-if="insight.suggested_practice" class="insight-practice">
              <el-icon><EditPen /></el-icon>
              <span>建议练习：{{ insight.suggested_practice }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 趋势图 -->
      <el-col :span="10">
        <el-card shadow="never" class="trend-card">
          <template #header>
            <span class="card-title">维度趋势</span>
          </template>
          <div ref="trendChartRef" class="trend-chart"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { getCurrentPattern, getInsights, recomputePattern, getTrend, markInsightRead } from '../api/patterns'
import { ElMessage } from 'element-plus'
import { Refresh, Top, Bottom, WarnTriangleFilled, StarFilled, TrendCharts, EditPen } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const pattern = ref(null)
const insights = ref([])
const trendData = ref(null)
const recomputing = ref(false)

const radarChartRef = ref(null)
const trendChartRef = ref(null)
let radarChart = null
let trendChart = null

const DIMENSION_KEYS = ['assertiveness', 'empathy', 'clarity', 'flexibility', 'conflict_handling', 'active_listening']
const DIMENSION_LABELS = {
  assertiveness: '坚定程度',
  empathy: '共情能力',
  clarity: '表达清晰度',
  flexibility: '灵活变通',
  conflict_handling: '冲突处理',
  active_listening: '积极倾听',
}

const dimensions = computed(() => {
  if (!pattern.value) {
    return DIMENSION_KEYS.map((key) => ({
      key,
      label: DIMENSION_LABELS[key],
      trend: null,
      cardClass: '',
    }))
  }
  return DIMENSION_KEYS.map((key) => {
    const val = pattern.value[key] ?? 0
    const prev = pattern.value[`prev_${key}`]
    const trend = prev != null ? +(val - prev).toFixed(1) : null
    let cardClass = ''
    if (val >= 8) cardClass = 'dim-high'
    else if (val >= 6) cardClass = 'dim-mid'
    else if (val < 4) cardClass = 'dim-low'
    return { key, label: DIMENSION_LABELS[key], trend, cardClass }
  })
})

const insightClass = (type) => {
  const map = {
    blind_spot: 'insight-blind',
    strength: 'insight-strength',
    trend: 'insight-trend',
  }
  return map[type] || ''
}

const insightTypeLabel = (type) => {
  const map = {
    blind_spot: '盲点',
    strength: '优势',
    trend: '趋势',
  }
  return map[type] || type
}

const fetchPattern = async () => {
  try {
    const { data } = await getCurrentPattern()
    pattern.value = data
  } catch {
    pattern.value = null
  }
}

const fetchInsights = async () => {
  try {
    const { data } = await getInsights()
    insights.value = Array.isArray(data) ? data : data.items || []
  } catch {
    insights.value = []
  }
}

const fetchTrend = async () => {
  try {
    const { data } = await getTrend()
    trendData.value = data
  } catch {
    trendData.value = null
  }
}

const handleRecompute = async () => {
  recomputing.value = true
  try {
    await recomputePattern()
    ElMessage.success('画像已重新计算')
    await fetchPattern()
    await fetchInsights()
    await fetchTrend()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '重新计算失败')
  } finally {
    recomputing.value = false
  }
}

const handleMarkRead = async (id) => {
  try {
    await markInsightRead(id)
    const item = insights.value.find((i) => i.id === id)
    if (item) item.is_read = true
    ElMessage.success('已标记为已读')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const initRadarChart = () => {
  if (!radarChartRef.value) return
  radarChart = echarts.init(radarChartRef.value)

  const scores = DIMENSION_KEYS.map((k) => pattern.value?.[k] ?? 0)
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
      axisName: {
        color: '#606266',
        fontSize: 13,
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

const initTrendChart = () => {
  if (!trendChartRef.value || !trendData.value) return
  trendChart = echarts.init(trendChartRef.value)

  const dates = trendData.value.dates || []
  const series = DIMENSION_KEYS.map((key) => ({
    name: DIMENSION_LABELS[key],
    type: 'line',
    smooth: true,
    data: trendData.value[key] || [],
    symbolSize: 4,
  }))

  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: {
      data: DIMENSION_KEYS.map((k) => DIMENSION_LABELS[k]),
      bottom: 0,
      textStyle: { fontSize: 11 },
    },
    grid: { top: 10, right: 20, bottom: 50, left: 40 },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: { fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 10,
      axisLabel: { fontSize: 11 },
    },
    series,
  })
}

const handleResize = () => {
  radarChart?.resize()
  trendChart?.resize()
}

watch(pattern, () => {
  nextTick(() => {
    initRadarChart()
  })
})

watch(trendData, () => {
  nextTick(() => {
    initTrendChart()
  })
})

onMounted(async () => {
  await fetchPattern()
  await fetchInsights()
  await fetchTrend()
  nextTick(() => {
    initRadarChart()
    initTrendChart()
  })
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  radarChart?.dispose()
  trendChart?.dispose()
})
</script>

<style scoped>
.pattern-view {
  max-width: 1200px;
  margin: 0 auto;
}

.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.radar-card {
  margin-bottom: 20px;
}

.radar-chart {
  width: 100%;
  height: 380px;
}

.dimension-cards {
  margin-bottom: 20px;
}

.dim-card {
  text-align: center;
  transition: transform 0.2s;
}

.dim-card:hover {
  transform: translateY(-2px);
}

.dim-score {
  font-size: 28px;
  font-weight: 700;
  color: #409eff;
  margin-bottom: 4px;
}

.dim-high .dim-score {
  color: #67c23a;
}

.dim-mid .dim-score {
  color: #409eff;
}

.dim-low .dim-score {
  color: #f56c6c;
}

.dim-name {
  font-size: 13px;
  color: #909399;
  margin-bottom: 4px;
}

.dim-trend {
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
}

.trend-up {
  color: #67c23a;
}

.trend-down {
  color: #f56c6c;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
}

.insights-card {
  min-height: 400px;
}

.empty-state {
  padding: 40px 0;
}

.insight-item {
  padding: 14px 16px;
  margin-bottom: 12px;
  border-radius: 8px;
  border-left: 4px solid #e4e7ed;
  background: #fafafa;
  transition: background 0.2s;
}

.insight-item:hover {
  background: #f5f7fa;
}

.insight-blind {
  border-left-color: #f56c6c;
  background: #fef0f0;
}

.insight-blind:hover {
  background: #fde2e2;
}

.insight-blind .insight-icon {
  color: #f56c6c;
}

.insight-strength {
  border-left-color: #67c23a;
  background: #f0f9eb;
}

.insight-strength:hover {
  background: #e1f3d8;
}

.insight-strength .insight-icon {
  color: #67c23a;
}

.insight-trend {
  border-left-color: #409eff;
  background: #ecf5ff;
}

.insight-trend:hover {
  background: #d9ecff;
}

.insight-trend .insight-icon {
  color: #409eff;
}

.insight-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.insight-type-label {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.insight-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 4px;
}

.insight-desc {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  margin: 0 0 8px;
}

.insight-evidence {
  margin-bottom: 8px;
}

.evidence-label {
  font-size: 12px;
  color: #909399;
}

.evidence-tag {
  margin: 2px 4px 2px 0;
}

.insight-practice {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  font-size: 13px;
  color: #e6a23c;
  line-height: 1.5;
}

.trend-card {
  min-height: 400px;
}

.trend-chart {
  width: 100%;
  height: 350px;
}
</style>
