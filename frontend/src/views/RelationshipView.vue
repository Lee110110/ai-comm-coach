<template>
  <div class="relationship-view">
    <div class="top-bar">
      <h2 class="page-title">关系档案</h2>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        添加关系
      </el-button>
    </div>

    <!-- 卡片网格 -->
    <el-row :gutter="20" class="profile-grid">
      <el-col v-for="profile in relationships" :key="profile.id" :span="6">
        <el-card
          shadow="hover"
          class="profile-card"
          @click="goDetail(profile.id)"
        >
          <div class="card-top">
            <span class="avatar-emoji">{{ profile.avatar_emoji || '👤' }}</span>
            <el-dropdown trigger="click" @command="(cmd) => handleCommand(cmd, profile)" @click.stop>
              <el-icon class="more-btn" @click.stop><MoreFilled /></el-icon>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="edit">编辑</el-dropdown-item>
                  <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <h3 class="profile-name">{{ profile.name }}</h3>
          <el-tag size="small" class="relation-tag">{{ profile.relation_type }}</el-tag>
          <div v-if="profile.preferences?.length" class="pref-tags">
            <el-tag
              v-for="(p, pi) in profile.preferences.slice(0, 3)"
              :key="pi"
              size="small"
              effect="plain"
              type="info"
            >
              {{ p }}
            </el-tag>
            <el-tag v-if="profile.preferences.length > 3" size="small" effect="plain" type="info">
              +{{ profile.preferences.length - 3 }}
            </el-tag>
          </div>
          <div class="last-interaction">
            最近互动：{{ formatDate(profile.last_interaction) || '暂无' }}
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 空状态 -->
    <el-empty v-if="relationships.length === 0 && !loading" description="还没有关系档案，点击上方按钮添加" />

    <!-- 加载中 -->
    <div v-if="loading" class="loading-section">
      <el-icon class="is-loading" :size="32"><Loading /></el-icon>
      <p class="loading-text">加载中...</p>
    </div>

    <!-- 创建/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑关系' : '添加关系'"
      width="560px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        size="default"
      >
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="姓名" prop="name">
              <el-input v-model="form.name" placeholder="对方姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="关系类型" prop="relation_type">
              <el-select v-model="form.relation_type" placeholder="请选择" style="width: 100%">
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
        </el-row>

        <el-form-item label="Emoji头像">
          <el-input v-model="form.avatar_emoji" placeholder="选择一个emoji，如：👨‍💼">
            <template #prepend>
              <div class="emoji-suggestions">
                <span
                  v-for="emoji in emojiOptions"
                  :key="emoji"
                  class="emoji-option"
                  @click="form.avatar_emoji = emoji"
                >{{ emoji }}</span>
              </div>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="沟通风格">
          <div class="tags-input-area">
            <el-tag
              v-for="(tag, idx) in form.communication_style"
              :key="idx"
              closable
              size="small"
              @close="removeTag('communication_style', idx)"
              class="input-tag"
            >
              {{ tag }}
            </el-tag>
            <el-input
              v-model="styleInput"
              size="small"
              placeholder="输入后回车添加"
              style="width: 140px"
              @keydown.enter.prevent="addTag('communication_style')"
            />
          </div>
        </el-form-item>

        <el-form-item label="偏好">
          <div class="tags-input-area">
            <el-tag
              v-for="(tag, idx) in form.preferences"
              :key="idx"
              closable
              size="small"
              type="success"
              @close="removeTag('preferences', idx)"
              class="input-tag"
            >
              {{ tag }}
            </el-tag>
            <el-input
              v-model="prefInput"
              size="small"
              placeholder="输入后回车添加"
              style="width: 140px"
              @keydown.enter.prevent="addTag('preferences')"
            />
          </div>
        </el-form-item>

        <el-form-item label="避免话题">
          <div class="tags-input-area">
            <el-tag
              v-for="(tag, idx) in form.avoid_topics"
              :key="idx"
              closable
              size="small"
              type="danger"
              @close="removeTag('avoid_topics', idx)"
              class="input-tag"
            >
              {{ tag }}
            </el-tag>
            <el-input
              v-model="avoidInput"
              size="small"
              placeholder="输入后回车添加"
              style="width: 140px"
              @keydown.enter.prevent="addTag('avoid_topics')"
            />
          </div>
        </el-form-item>

        <el-form-item label="备注">
          <el-input
            v-model="form.notes"
            type="textarea"
            :rows="3"
            placeholder="补充备注信息..."
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ isEditing ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { createRelationship, listRelationships, updateRelationship, deleteRelationship } from '../api/relationships'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, MoreFilled, Loading } from '@element-plus/icons-vue'

const router = useRouter()
const relationships = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const submitting = ref(false)
const formRef = ref(null)

const styleInput = ref('')
const prefInput = ref('')
const avoidInput = ref('')

const emojiOptions = ['👨‍💼', '👩‍💼', '👴', '👵', '👨', '👩', '🧑‍💻', '👔', '💼', '🤝', '❤️', '🏠']

const defaultForm = () => ({
  name: '',
  relation_type: '',
  avatar_emoji: '👤',
  communication_style: [],
  preferences: [],
  avoid_topics: [],
  notes: '',
})

const form = reactive(defaultForm())

const rules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  relation_type: [{ required: true, message: '请选择关系类型', trigger: 'change' }],
}

const fetchRelationships = async () => {
  loading.value = true
  try {
    const { data } = await listRelationships()
    relationships.value = Array.isArray(data) ? data : data.items || []
  } catch {
    relationships.value = []
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  isEditing.value = false
  editingId.value = null
  Object.assign(form, defaultForm())
  styleInput.value = ''
  prefInput.value = ''
  avoidInput.value = ''
  dialogVisible.value = true
}

const openEditDialog = (profile) => {
  isEditing.value = true
  editingId.value = profile.id
  Object.assign(form, {
    name: profile.name || '',
    relation_type: profile.relation_type || '',
    avatar_emoji: profile.avatar_emoji || '👤',
    communication_style: [...(profile.communication_style || [])],
    preferences: [...(profile.preferences || [])],
    avoid_topics: [...(profile.avoid_topics || [])],
    notes: profile.notes || '',
  })
  styleInput.value = ''
  prefInput.value = ''
  avoidInput.value = ''
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      const payload = { ...form }
      if (isEditing.value) {
        await updateRelationship(editingId.value, payload)
        ElMessage.success('更新成功')
      } else {
        await createRelationship(payload)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      fetchRelationships()
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

const handleCommand = (cmd, profile) => {
  if (cmd === 'edit') {
    openEditDialog(profile)
  } else if (cmd === 'delete') {
    handleDelete(profile)
  }
}

const handleDelete = async (profile) => {
  try {
    await ElMessageBox.confirm(`确定删除与"${profile.name}"的关系档案？`, '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteRelationship(profile.id)
    ElMessage.success('删除成功')
    fetchRelationships()
  } catch {
    // cancelled
  }
}

const addTag = (field) => {
  const inputMap = {
    communication_style: styleInput,
    preferences: prefInput,
    avoid_topics: avoidInput,
  }
  const val = inputMap[field].value.trim()
  if (val && !form[field].includes(val)) {
    form[field].push(val)
  }
  inputMap[field].value = ''
}

const removeTag = (field, idx) => {
  form[field].splice(idx, 1)
}

const goDetail = (id) => {
  router.push({ name: 'relationship-detail', params: { id } })
}

const formatDate = (t) => {
  if (!t) return ''
  return new Date(t).toLocaleDateString('zh-CN')
}

onMounted(() => {
  fetchRelationships()
})
</script>

<style scoped>
.relationship-view {
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

.profile-grid {
  margin-bottom: 20px;
}

.profile-card {
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  height: 100%;
}

.profile-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 8px;
}

.avatar-emoji {
  font-size: 48px;
  line-height: 1;
}

.more-btn {
  cursor: pointer;
  color: #909399;
  font-size: 16px;
  padding: 4px;
  border-radius: 4px;
  transition: background 0.2s;
}

.more-btn:hover {
  background: #f0f0f0;
  color: #606266;
}

.profile-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 6px;
}

.relation-tag {
  margin-bottom: 8px;
}

.pref-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 8px;
}

.last-interaction {
  font-size: 12px;
  color: #c0c4cc;
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

/* Dialog form */
.emoji-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
}

.emoji-option {
  font-size: 16px;
  cursor: pointer;
  padding: 2px;
  border-radius: 4px;
  transition: background 0.2s;
}

.emoji-option:hover {
  background: #f0f0f0;
}

.tags-input-area {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  min-height: 40px;
  width: 100%;
}

.tags-input-area:focus-within {
  border-color: #409eff;
}

.input-tag {
  flex-shrink: 0;
}
</style>
