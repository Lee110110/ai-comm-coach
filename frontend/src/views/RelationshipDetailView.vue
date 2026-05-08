<template>
  <div class="relationship-detail-view">
    <div v-if="loading" class="loading-section">
      <el-icon class="is-loading" :size="32"><Loading /></el-icon>
      <p class="loading-text">加载中...</p>
    </div>

    <template v-if="profile">
      <!-- 返回 + 标题 -->
      <div class="top-bar">
        <el-button text @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
      </div>

      <!-- 个人信息卡 -->
      <el-card shadow="never" class="profile-info-card">
        <div class="info-layout">
          <span class="avatar-large">{{ profile.avatar_emoji || '👤' }}</span>
          <div class="info-main">
            <h2 class="profile-name">{{ profile.name }}</h2>
            <el-tag size="default">{{ profile.relation_type }}</el-tag>
            <div v-if="profile.communication_style?.length" class="info-tags">
              <span class="info-label">沟通风格：</span>
              <el-tag
                v-for="(s, i) in profile.communication_style"
                :key="i"
                size="small"
                effect="plain"
              >
                {{ s }}
              </el-tag>
            </div>
            <div v-if="profile.preferences?.length" class="info-tags">
              <span class="info-label">偏好：</span>
              <el-tag
                v-for="(p, i) in profile.preferences"
                :key="i"
                size="small"
                type="success"
                effect="plain"
              >
                {{ p }}
              </el-tag>
            </div>
            <div v-if="profile.avoid_topics?.length" class="info-tags">
              <span class="info-label">避免话题：</span>
              <el-tag
                v-for="(a, i) in profile.avoid_topics"
                :key="i"
                size="small"
                type="danger"
                effect="plain"
              >
                {{ a }}
              </el-tag>
            </div>
            <p v-if="profile.notes" class="info-notes">{{ profile.notes }}</p>
          </div>
          <div class="info-actions">
            <el-button type="primary" :loading="strategyLoading" @click="handleGetStrategy">
              <el-icon><MagicStick /></el-icon>
              获取沟通策略
            </el-button>
            <el-button @click="goEdit">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
          </div>
        </div>
      </el-card>

      <el-row :gutter="20">
        <!-- 互动时间线 -->
        <el-col :span="14">
          <el-card shadow="never" class="timeline-card">
            <template #header>
              <span class="card-title">最近互动</span>
            </template>

            <div v-if="!profile.recent_interactions?.length" class="empty-timeline">
              <el-empty description="暂无互动记录" :image-size="80" />
            </div>

            <el-timeline v-else>
              <el-timeline-item
                v-for="(interaction, idx) in profile.recent_interactions"
                :key="idx"
                :timestamp="formatDate(interaction.date || interaction.created_at)"
                placement="top"
              >
                <el-card shadow="never" class="timeline-item-card">
                  <h4 v-if="interaction.title" class="interaction-title">{{ interaction.title }}</h4>
                  <p class="interaction-desc">{{ interaction.description || interaction.summary || '' }}</p>
                  <div v-if="interaction.tags?.length" class="interaction-tags">
                    <el-tag
                      v-for="(t, ti) in interaction.tags"
                      :key="ti"
                      size="small"
                      effect="plain"
                      type="info"
                    >
                      {{ t }}
                    </el-tag>
                  </div>
                </el-card>
              </el-timeline-item>
            </el-timeline>
          </el-card>
        </el-col>

        <!-- 沟通策略 -->
        <el-col :span="10">
          <el-card shadow="never" class="strategy-card">
            <template #header>
              <span class="card-title">沟通策略</span>
            </template>

            <div v-if="!strategy" class="empty-strategy">
              <el-icon :size="40" color="#c0c4cc"><MagicStick /></el-icon>
              <p>点击"获取沟通策略"按钮，AI将根据关系档案生成个性化建议</p>
            </div>

            <div v-else class="strategy-content">
              <div v-if="strategy.overall_approach" class="strategy-section">
                <h4 class="section-heading">整体策略</h4>
                <p>{{ strategy.overall_approach }}</p>
              </div>

              <div v-if="strategy.do_list?.length" class="strategy-section">
                <h4 class="section-heading text-green">推荐做法</h4>
                <ul class="do-list">
                  <li v-for="(item, i) in strategy.do_list" :key="i">
                    <el-icon color="#67c23a"><Check /></el-icon>
                    <span>{{ item }}</span>
                  </li>
                </ul>
              </div>

              <div v-if="strategy.dont_list?.length" class="strategy-section">
                <h4 class="section-heading text-red">避免做法</h4>
                <ul class="dont-list">
                  <li v-for="(item, i) in strategy.dont_list" :key="i">
                    <el-icon color="#f56c6c"><Close /></el-icon>
                    <span>{{ item }}</span>
                  </li>
                </ul>
              </div>

              <div v-if="strategy.opening_style" class="strategy-section">
                <h4 class="section-heading text-blue">开场方式</h4>
                <p>{{ strategy.opening_style }}</p>
              </div>

              <div v-if="strategy.conflict_approach" class="strategy-section">
                <h4 class="section-heading text-orange">冲突处理</h4>
                <p>{{ strategy.conflict_approach }}</p>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getRelationship, getStrategy } from '../api/relationships'
import { ElMessage } from 'element-plus'
import { Loading, ArrowLeft, MagicStick, Edit, Check, Close } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const strategyLoading = ref(false)
const profile = ref(null)
const strategy = ref(null)

const fetchProfile = async (id) => {
  loading.value = true
  try {
    const { data } = await getRelationship(id)
    profile.value = data
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '加载关系档案失败')
  } finally {
    loading.value = false
  }
}

const handleGetStrategy = async () => {
  if (!profile.value) return
  strategyLoading.value = true
  try {
    const { data } = await getStrategy(profile.value.id)
    strategy.value = data
    ElMessage.success('策略生成成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '获取策略失败')
  } finally {
    strategyLoading.value = false
  }
}

const goBack = () => {
  router.push({ name: 'relationships' })
}

const goEdit = () => {
  // Navigate back to the list and open edit; or could open a dialog here
  router.push({ name: 'relationships' })
}

const formatDate = (t) => {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN')
}

onMounted(() => {
  if (route.params.id) {
    fetchProfile(route.params.id)
  }
})
</script>

<style scoped>
.relationship-detail-view {
  max-width: 1200px;
  margin: 0 auto;
}

.top-bar {
  margin-bottom: 16px;
}

/* Loading */
.loading-section {
  text-align: center;
  padding: 60px 0;
}

.loading-text {
  margin-top: 16px;
  color: #909399;
  font-size: 14px;
}

/* Profile info */
.profile-info-card {
  margin-bottom: 20px;
}

.info-layout {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.avatar-large {
  font-size: 64px;
  line-height: 1;
  flex-shrink: 0;
}

.info-main {
  flex: 1;
  min-width: 0;
}

.profile-name {
  font-size: 22px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px;
}

.info-tags {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 8px;
}

.info-label {
  font-size: 13px;
  color: #909399;
  margin-right: 4px;
  flex-shrink: 0;
}

.info-notes {
  font-size: 13px;
  color: #606266;
  margin: 8px 0 0;
  line-height: 1.6;
}

.info-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex-shrink: 0;
}

/* Timeline */
.timeline-card {
  min-height: 400px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
}

.empty-timeline {
  padding: 20px 0;
}

.timeline-item-card {
  margin-bottom: 0;
}

.interaction-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 4px;
}

.interaction-desc {
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
  margin: 0 0 6px;
}

.interaction-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

/* Strategy */
.strategy-card {
  min-height: 400px;
}

.empty-strategy {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  color: #c0c4cc;
}

.empty-strategy p {
  margin-top: 12px;
  font-size: 13px;
  line-height: 1.6;
}

.strategy-content {
  font-size: 14px;
  line-height: 1.7;
}

.strategy-section {
  margin-bottom: 18px;
}

.section-heading {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 8px;
  color: #303133;
}

.text-green {
  color: #67c23a;
}

.text-red {
  color: #f56c6c;
}

.text-blue {
  color: #409eff;
}

.text-orange {
  color: #e6a23c;
}

.strategy-section p {
  margin: 0;
  color: #606266;
}

.do-list,
.dont-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.do-list li,
.dont-list li {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-bottom: 6px;
  color: #606266;
}

.do-list li .el-icon,
.dont-list li .el-icon {
  margin-top: 3px;
  flex-shrink: 0;
}
</style>
