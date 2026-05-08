<template>
  <div class="simulation-view">
    <!-- 新建模式：设置表单 -->
    <div v-if="mode === 'new' && !sessionStarted" class="setup-section">
      <el-card shadow="never" class="setup-card">
        <template #header>
          <span class="card-title">开始新演练</span>
          <span class="card-subtitle">设置场景参数，与AI进行沟通模拟</span>
        </template>

        <el-form
          ref="setupFormRef"
          :model="setupForm"
          :rules="setupRules"
          label-position="top"
          size="default"
        >
          <el-form-item label="场景描述" prop="scenario_description">
            <el-input
              v-model="setupForm.scenario_description"
              type="textarea"
              :rows="4"
              placeholder="描述你要练习的沟通场景，例如：你需要向领导申请加薪，但你不确定如何开口..."
            />
          </el-form-item>

          <el-form-item label="角色描述（选填）">
            <el-input
              v-model="setupForm.role_description"
              type="textarea"
              :rows="2"
              placeholder="AI扮演的角色，如：你的领导，性格强势，注重结果"
            />
          </el-form-item>

          <el-form-item label="难度选择" prop="difficulty">
            <el-radio-group v-model="setupForm.difficulty">
              <el-radio-button label="easy">温和</el-radio-button>
              <el-radio-button label="medium">中等</el-radio-button>
              <el-radio-button label="hard">困难</el-radio-button>
            </el-radio-group>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" size="large" :loading="creating" @click="handleStart">
              开始演练
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <!-- 演练中/已结束：聊天界面 -->
    <div v-if="mode === 'existing' || sessionStarted" class="chat-layout">
      <!-- 顶部栏 -->
      <div class="chat-topbar">
        <div class="topbar-info">
          <span class="scenario-text">{{ simulation?.scenario_description || '加载中...' }}</span>
          <el-tag v-if="simulation?.role_description" size="small" type="info" class="role-tag">
            {{ simulation.role_description }}
          </el-tag>
        </div>
        <div class="topbar-actions">
          <el-radio-group
            v-model="currentDifficulty"
            size="small"
            :disabled="simulation?.status === 'completed'"
            @change="handleDifficultyChange"
          >
            <el-radio-button label="easy">温和</el-radio-button>
            <el-radio-button label="medium">中等</el-radio-button>
            <el-radio-button label="hard">困难</el-radio-button>
          </el-radio-group>
          <el-button
            v-if="simulation?.status !== 'completed'"
            type="danger"
            size="small"
            @click="handleEnd"
          >
            结束演练
          </el-button>
        </div>
      </div>

      <div class="chat-body">
        <!-- 左侧聊天区 -->
        <div class="chat-main" :class="{ 'full-width': !showFeedbackPanel }">
          <!-- 消息列表 -->
          <div ref="messagesContainer" class="messages-area">
            <div
              v-for="(msg, idx) in messages"
              :key="idx"
              class="message-item"
              :class="msg.role === 'user' ? 'message-right' : 'message-left'"
            >
              <div class="message-bubble" :class="msg.role === 'user' ? 'bubble-user' : 'bubble-assistant'">
                <div class="message-content">{{ msg.content }}</div>
                <!-- 助手消息的反馈展开区 -->
                <div
                  v-if="msg.role === 'assistant' && msg.feedback"
                  class="feedback-toggle"
                  @click="toggleMessageFeedback(idx)"
                >
                  <el-icon v-if="expandedFeedback[idx]"><ArrowUp /></el-icon>
                  <el-icon v-else><ArrowDown /></el-icon>
                  <span>查看反馈</span>
                  <el-tag v-if="msg.feedback.score != null" size="small" type="warning" class="inline-score">
                    {{ msg.feedback.score }}分
                  </el-tag>
                </div>
                <div v-if="msg.role === 'assistant' && msg.feedback && expandedFeedback[idx]" class="message-feedback">
                  <div v-if="msg.feedback.score != null" class="feedback-score">
                    <span class="score-label">评分：</span>
                    <el-rate :model-value="msg.feedback.score / 2" disabled :max="5" allow-half />
                    <span class="score-num">{{ msg.feedback.score }}/10</span>
                  </div>
                  <div v-if="msg.feedback.positives?.length" class="feedback-section">
                    <span class="section-label text-green">亮点：</span>
                    <el-tag
                      v-for="(p, pi) in msg.feedback.positives"
                      :key="pi"
                      type="success"
                      effect="plain"
                      size="small"
                      class="feedback-tag"
                    >
                      {{ p }}
                    </el-tag>
                  </div>
                  <div v-if="msg.feedback.suggestions?.length" class="feedback-section">
                    <span class="section-label text-orange">建议：</span>
                    <el-tag
                      v-for="(s, si) in msg.feedback.suggestions"
                      :key="si"
                      type="warning"
                      effect="plain"
                      size="small"
                      class="feedback-tag"
                    >
                      {{ s }}
                    </el-tag>
                  </div>
                </div>
              </div>
            </div>

            <!-- AI加载中 -->
            <div v-if="sending" class="message-item message-left">
              <div class="message-bubble bubble-assistant">
                <div class="typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          </div>

          <!-- 输入区 -->
          <div class="input-area">
            <el-input
              v-model="inputText"
              type="textarea"
              :rows="2"
              :disabled="sending || simulation?.status === 'completed'"
              placeholder="输入你的回复..."
              resize="none"
              @keydown.enter.exact.prevent="handleSend"
            />
            <el-button
              type="primary"
              :loading="sending"
              :disabled="!inputText.trim() || simulation?.status === 'completed'"
              @click="handleSend"
            >
              发送
            </el-button>
          </div>
        </div>

        <!-- 右侧反馈面板 -->
        <div v-if="showFeedbackPanel" class="feedback-panel">
          <div class="panel-header">
            <span class="panel-title">实时反馈</span>
            <el-icon class="panel-close" @click="showFeedbackPanel = false"><Close /></el-icon>
          </div>

          <div v-if="latestFeedback" class="panel-content">
            <div class="feedback-score-large">
              <span class="score-number">{{ latestFeedback.score ?? '--' }}</span>
              <span class="score-unit">/10</span>
            </div>
            <el-rate
              v-if="latestFeedback.score != null"
              :model-value="latestFeedback.score / 2"
              disabled
              :max="5"
              allow-half
              class="panel-rate"
            />

            <div v-if="latestFeedback.positives?.length" class="panel-section">
              <h4 class="panel-section-title text-green">亮点</h4>
              <div class="tag-list">
                <el-tag
                  v-for="(p, pi) in latestFeedback.positives"
                  :key="pi"
                  type="success"
                  effect="plain"
                  size="small"
                >
                  {{ p }}
                </el-tag>
              </div>
            </div>

            <div v-if="latestFeedback.suggestions?.length" class="panel-section">
              <h4 class="panel-section-title text-orange">改进建议</h4>
              <div class="tag-list">
                <el-tag
                  v-for="(s, si) in latestFeedback.suggestions"
                  :key="si"
                  type="warning"
                  effect="plain"
                  size="small"
                >
                  {{ s }}
                </el-tag>
              </div>
            </div>
          </div>

          <div v-else class="panel-empty">
            <el-icon :size="40" color="#c0c4cc"><ChatLineSquare /></el-icon>
            <p>发送消息后将显示实时反馈</p>
          </div>
        </div>
      </div>

      <!-- 反馈面板折叠按钮 -->
      <div
        v-if="!showFeedbackPanel"
        class="panel-expand-btn"
        @click="showFeedbackPanel = true"
      >
        <el-icon><ArrowLeft /></el-icon>
        <span>反馈面板</span>
      </div>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="loading-section">
      <el-icon class="is-loading" :size="32"><Loading /></el-icon>
      <p class="loading-text">加载演练数据中...</p>
    </div>

    <!-- 总结报告弹窗 -->
    <el-dialog
      v-model="showDebrief"
      title="演练报告"
      width="640px"
      :close-on-click-modal="false"
      class="debrief-dialog"
    >
      <div v-if="debrief" class="debrief-content">
        <div class="debrief-score-section">
          <div class="overall-score">
            <span class="overall-number">{{ debrief.overall_score ?? '--' }}</span>
            <span class="overall-unit">/10</span>
          </div>
          <p class="overall-label">综合评分</p>
        </div>

        <div class="debrief-summary">
          <h4>总结</h4>
          <p>{{ debrief.summary }}</p>
        </div>

        <el-row :gutter="20">
          <el-col :span="12">
            <div class="debrief-list strengths-list">
              <h4 class="text-green">优势</h4>
              <ul>
                <li v-for="(s, i) in debrief.strengths || []" :key="i">{{ s }}</li>
              </ul>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="debrief-list improvements-list">
              <h4 class="text-orange">待改进</h4>
              <ul>
                <li v-for="(s, i) in debrief.improvements || []" :key="i">{{ s }}</li>
              </ul>
            </div>
          </el-col>
        </el-row>

        <div v-if="debrief.dimension_scores" class="debrief-dimensions">
          <h4>维度评分</h4>
          <div
            v-for="(val, key) in debrief.dimension_scores"
            :key="key"
            class="dimension-bar"
          >
            <span class="dim-label">{{ dimensionLabel(key) }}</span>
            <el-progress
              :percentage="(val / 10) * 100"
              :stroke-width="12"
              :format="() => val + '/10'"
              :color="progressColor(val)"
            />
          </div>
        </div>

        <div v-if="debrief.recommended_practice" class="debrief-practice">
          <h4>推荐练习</h4>
          <p>{{ debrief.recommended_practice }}</p>
        </div>
      </div>

      <template #footer>
        <el-button @click="showDebrief = false">关闭</el-button>
        <el-button type="primary" @click="goNewSimulation">开始新演练</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createSimulation, getSimulation, sendMessage, updateDifficulty, endSimulation, getDebrief } from '../api/simulations'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, ArrowUp, ArrowDown, ArrowLeft, Close, ChatLineSquare } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const creating = ref(false)
const sending = ref(false)
const sessionStarted = ref(false)
const simulation = ref(null)
const messages = ref([])
const inputText = ref('')
const currentDifficulty = ref('medium')
const showFeedbackPanel = ref(true)
const showDebrief = ref(false)
const debrief = ref(null)
const expandedFeedback = reactive({})
const messagesContainer = ref(null)

const mode = computed(() => {
  if (route.name === 'simulation-new') return 'new'
  return 'existing'
})

const setupFormRef = ref(null)
const setupForm = reactive({
  scenario_description: '',
  role_description: '',
  difficulty: 'medium',
})

const setupRules = {
  scenario_description: [{ required: true, message: '请输入场景描述', trigger: 'blur' }],
  difficulty: [{ required: true, message: '请选择难度', trigger: 'change' }],
}

const latestFeedback = computed(() => {
  for (let i = messages.value.length - 1; i >= 0; i--) {
    const msg = messages.value[i]
    if (msg.role === 'assistant' && msg.feedback) {
      return msg.feedback
    }
  }
  return null
})

const handleStart = async () => {
  if (!setupFormRef.value) return
  await setupFormRef.value.validate(async (valid) => {
    if (!valid) return

    creating.value = true
    try {
      const { data } = await createSimulation({
        scenario_description: setupForm.scenario_description,
        role_description: setupForm.role_description || undefined,
        difficulty: setupForm.difficulty,
      })
      simulation.value = data
      currentDifficulty.value = data.difficulty || setupForm.difficulty
      messages.value = data.messages || []
      sessionStarted.value = true
      // If the AI starts with an opening message, it will be in messages
      scrollToBottom()
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || '创建演练失败')
    } finally {
      creating.value = false
    }
  })
}

const loadExisting = async (id) => {
  loading.value = true
  try {
    const { data } = await getSimulation(id)
    simulation.value = data
    currentDifficulty.value = data.difficulty || 'medium'
    messages.value = data.messages || []
    sessionStarted.value = true
    scrollToBottom()

    // If completed, auto-load debrief
    if (data.status === 'completed') {
      loadDebrief(id)
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '加载演练失败')
  } finally {
    loading.value = false
  }
}

const handleSend = async () => {
  const text = inputText.value.trim()
  if (!text || sending.value || simulation.value?.status === 'completed') return

  const simId = simulation.value.id
  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  sending.value = true
  scrollToBottom()

  try {
    const { data } = await sendMessage(simId, text)
    // data should contain the assistant's reply and feedback
    const assistantMsg = {
      role: 'assistant',
      content: data.content || data.message || '',
      feedback: data.feedback || null,
    }
    messages.value.push(assistantMsg)
    scrollToBottom()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '发送失败')
  } finally {
    sending.value = false
  }
}

const handleDifficultyChange = async (val) => {
  if (!simulation.value || simulation.value.status === 'completed') return
  try {
    await updateDifficulty(simulation.value.id, val)
    ElMessage.success('难度已更新')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '更新难度失败')
  }
}

const handleEnd = async () => {
  if (!simulation.value) return
  try {
    await ElMessageBox.confirm('确定要结束本次演练？结束后将生成报告。', '确认结束', {
      confirmButtonText: '结束',
      cancelButtonText: '继续演练',
      type: 'warning',
    })
    await endSimulation(simulation.value.id)
    simulation.value.status = 'completed'
    await loadDebrief(simulation.value.id)
    showDebrief.value = true
  } catch {
    // cancelled
  }
}

const loadDebrief = async (id) => {
  try {
    const { data } = await getDebrief(id)
    debrief.value = data
    showDebrief.value = true
  } catch (error) {
    // debrief might not be ready yet
    console.warn('Failed to load debrief:', error)
  }
}

const toggleMessageFeedback = (idx) => {
  expandedFeedback[idx] = !expandedFeedback[idx]
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const dimensionLabel = (key) => {
  const map = {
    assertiveness: '坚定程度',
    empathy: '共情能力',
    clarity: '表达清晰度',
    flexibility: '灵活变通',
    conflict_handling: '冲突处理',
    active_listening: '积极倾听',
  }
  return map[key] || key
}

const progressColor = (val) => {
  if (val >= 8) return '#67c23a'
  if (val >= 6) return '#409eff'
  if (val >= 4) return '#e6a23c'
  return '#f56c6c'
}

const goNewSimulation = () => {
  showDebrief.value = false
  router.push({ name: 'simulation-new' })
}

onMounted(() => {
  if (mode.value === 'existing' && route.params.id) {
    loadExisting(route.params.id)
  }
})

watch(() => route.params.id, (newId) => {
  if (mode.value === 'existing' && newId) {
    loadExisting(newId)
  }
})
</script>

<style scoped>
.simulation-view {
  height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
}

/* Setup section */
.setup-section {
  max-width: 700px;
  margin: 0 auto;
  padding: 20px 0;
}

.setup-card {
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

/* Chat layout */
.chat-layout {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
  border-radius: 8px 8px 0 0;
  flex-shrink: 0;
}

.topbar-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.scenario-text {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.role-tag {
  flex-shrink: 0;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.chat-body {
  flex: 1;
  display: flex;
  overflow: hidden;
  background: #f5f7fa;
  border-radius: 0 0 8px 8px;
}

/* Chat main area */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  transition: all 0.3s;
}

.chat-main.full-width {
  flex: 1;
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-item {
  display: flex;
}

.message-right {
  justify-content: flex-end;
}

.message-left {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  font-size: 14px;
  word-break: break-word;
}

.bubble-user {
  background: #409eff;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.bubble-assistant {
  background: #fff;
  color: #303133;
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.message-content {
  white-space: pre-wrap;
}

/* Feedback toggle in message */
.feedback-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #e4e7ed;
  font-size: 12px;
  color: #909399;
  cursor: pointer;
  user-select: none;
}

.feedback-toggle:hover {
  color: #409eff;
}

.inline-score {
  margin-left: auto;
}

.message-feedback {
  margin-top: 8px;
  padding: 10px;
  background: #fafafa;
  border-radius: 8px;
}

.feedback-score {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.score-label {
  font-size: 13px;
  color: #606266;
}

.score-num {
  font-size: 13px;
  font-weight: 600;
  color: #e6a23c;
}

.feedback-section {
  margin-bottom: 6px;
}

.section-label {
  font-size: 13px;
  font-weight: 600;
  margin-right: 4px;
}

.text-green {
  color: #67c23a;
}

.text-orange {
  color: #e6a23c;
}

.feedback-tag {
  margin: 2px 4px 2px 0;
}

/* Typing indicator */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #c0c4cc;
  animation: typing 1.2s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-6px); opacity: 1; }
}

/* Input area */
.input-area {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  padding: 16px 20px;
  background: #fff;
  border-top: 1px solid #e6e6e6;
  flex-shrink: 0;
}

.input-area .el-input {
  flex: 1;
}

.input-area .el-button {
  flex-shrink: 0;
  height: 40px;
}

/* Feedback panel */
.feedback-panel {
  width: 320px;
  background: #fff;
  border-left: 1px solid #e6e6e6;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow-y: auto;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid #e6e6e6;
}

.panel-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.panel-close {
  cursor: pointer;
  color: #909399;
  font-size: 16px;
}

.panel-close:hover {
  color: #606266;
}

.panel-content {
  padding: 16px;
}

.feedback-score-large {
  text-align: center;
  padding: 16px 0;
}

.score-number {
  font-size: 48px;
  font-weight: 700;
  color: #e6a23c;
}

.score-unit {
  font-size: 18px;
  color: #909399;
}

.panel-rate {
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}

.panel-section {
  margin-bottom: 16px;
}

.panel-section-title {
  font-size: 14px;
  margin: 0 0 8px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.panel-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #c0c4cc;
}

.panel-empty p {
  margin-top: 12px;
  font-size: 13px;
}

/* Panel expand button */
.panel-expand-btn {
  position: fixed;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  background: #fff;
  border: 1px solid #e6e6e6;
  border-right: none;
  border-radius: 8px 0 0 8px;
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  z-index: 10;
  color: #909399;
  font-size: 12px;
  writing-mode: vertical-rl;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.06);
}

.panel-expand-btn:hover {
  color: #409eff;
  background: #f0f7ff;
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

/* Debrief dialog */
.debrief-content {
  text-align: left;
}

.debrief-score-section {
  text-align: center;
  padding: 20px 0;
  margin-bottom: 20px;
  background: linear-gradient(135deg, #f0f9eb 0%, #fdf6ec 100%);
  border-radius: 12px;
}

.overall-score {
  margin-bottom: 4px;
}

.overall-number {
  font-size: 56px;
  font-weight: 700;
  color: #e6a23c;
}

.overall-unit {
  font-size: 20px;
  color: #909399;
}

.overall-label {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.debrief-summary {
  margin-bottom: 20px;
}

.debrief-summary h4 {
  font-size: 15px;
  margin: 0 0 8px;
}

.debrief-summary p {
  font-size: 14px;
  color: #606266;
  line-height: 1.7;
  margin: 0;
}

.debrief-list {
  margin-bottom: 16px;
}

.debrief-list h4 {
  font-size: 15px;
  margin: 0 0 8px;
}

.debrief-list ul {
  padding-left: 18px;
  margin: 0;
}

.debrief-list li {
  font-size: 14px;
  color: #606266;
  line-height: 1.7;
  margin-bottom: 4px;
}

.debrief-dimensions {
  margin-bottom: 20px;
}

.debrief-dimensions h4 {
  font-size: 15px;
  margin: 0 0 12px;
}

.dimension-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.dim-label {
  font-size: 13px;
  color: #606266;
  width: 80px;
  flex-shrink: 0;
}

.dimension-bar .el-progress {
  flex: 1;
}

.debrief-practice {
  padding: 16px;
  background: #f0f9eb;
  border-radius: 8px;
  border: 1px solid #e1f3d8;
}

.debrief-practice h4 {
  font-size: 15px;
  margin: 0 0 8px;
  color: #67c23a;
}

.debrief-practice p {
  font-size: 14px;
  color: #606266;
  line-height: 1.7;
  margin: 0;
}
</style>
