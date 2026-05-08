<template>
  <div class="simulation-list-view">
    <!-- 顶部操作栏 -->
    <div class="top-bar">
      <h2 class="page-title">沟通演练</h2>
      <router-link :to="{ name: 'simulation-new' }">
        <el-button type="primary">
          <el-icon><Plus /></el-icon>
          开始新演练
        </el-button>
      </router-link>
    </div>

    <!-- 演练列表 -->
    <el-card shadow="never">
      <el-table :data="simulations" stripe style="width: 100%">
        <el-table-column prop="scenario_description" label="场景描述" min-width="240">
          <template #default="{ row }">
            {{ truncate(row.scenario_description, 40) }}
          </template>
        </el-table-column>

        <el-table-column prop="difficulty" label="难度" width="100">
          <template #default="{ row }">
            <el-tag :type="difficultyTagType(row.difficulty)" size="small">
              {{ row.difficulty }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="row.status === 'completed' ? 'success' : 'primary'"
              size="small"
            >
              {{ row.status === 'completed' ? '已完成' : '进行中' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="turn_count" label="回合数" width="90" />

        <el-table-column prop="score" label="得分" width="90">
          <template #default="{ row }">
            <span v-if="row.score != null" class="score-value">{{ row.score }}</span>
            <span v-else class="score-empty">--</span>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'active'"
              size="small"
              text
              type="primary"
              @click="continueSimulation(row.id)"
            >
              继续
            </el-button>
            <el-button
              v-if="row.status === 'completed'"
              size="small"
              text
              type="success"
              @click="viewSimulation(row.id)"
            >
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listSimulations } from '../api/simulations'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const router = useRouter()
const simulations = ref([])

const fetchSimulations = async () => {
  try {
    const { data } = await listSimulations()
    simulations.value = Array.isArray(data) ? data : data.items || []
  } catch {
    simulations.value = []
  }
}

const continueSimulation = (id) => {
  router.push({ name: 'simulation', params: { id } })
}

const viewSimulation = (id) => {
  router.push({ name: 'simulation', params: { id } })
}

const difficultyTagType = (difficulty) => {
  const map = { '简单': 'success', '中等': 'warning', '困难': 'danger' }
  return map[difficulty] || 'info'
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
  fetchSimulations()
})
</script>

<style scoped>
.simulation-list-view {
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

.score-value {
  font-weight: 600;
  color: #409eff;
}

.score-empty {
  color: #c0c4cc;
}
</style>