<template>
  <div style="height: 100vh; display: flex">
    <!-- Sidebar -->
    <el-menu
      v-if="user"
      :default-active="currentRoute"
      router
      style="width: 220px; min-height: 100vh"
      background-color="#304156"
      text-color="#bfcbd9"
      active-text-color="#409EFF"
    >
      <div style="padding: 20px 16px; text-align: center; color: #fff; font-size: 18px; font-weight: bold; letter-spacing: 2px">
        🏢 {{ companyName }}
      </div>

      <el-menu-item index="/">
        <el-icon><DataAnalysis /></el-icon>
        <span>仪表盘</span>
      </el-menu-item>

      <el-menu-item v-if="user.role === 'super_admin'" index="/departments">
        <el-icon><OfficeBuilding /></el-icon>
        <span>部门管理</span>
      </el-menu-item>

      <el-menu-item v-if="['super_admin', 'dept_manager'].includes(user.role)" index="/employees">
        <el-icon><UserFilled /></el-icon>
        <span>人员管理</span>
      </el-menu-item>

      <el-menu-item index="/checkin">
        <el-icon><Clock /></el-icon>
        <span>签到系统</span>
      </el-menu-item>

      <el-menu-item index="/orgchart">
        <el-icon><Share /></el-icon>
        <span>组织架构</span>
      </el-menu-item>

      <el-menu-item v-if="user.role === 'super_admin'" index="/settings">
        <el-icon><Setting /></el-icon>
        <span>系统设置</span>
      </el-menu-item>
    </el-menu>

    <!-- Main area -->
    <div style="flex: 1; display: flex; flex-direction: column; overflow: hidden">
      <!-- Top bar -->
      <div v-if="user" style="height: 50px; background: #fff; border-bottom: 1px solid #e6e6e6; display: flex; align-items: center; justify-content: flex-end; padding: 0 20px; flex-shrink: 0">
        <span style="margin-right: 12px; color: #666">
          <el-icon><User /></el-icon>
          {{ user.employee_name || user.username }}
        </span>
        <el-tag size="small" :type="roleTagType">{{ roleLabel }}</el-tag>
        <el-button type="primary" link style="margin-left: 12px" @click="openChangePwd">修改密码</el-button>
        <el-button type="danger" link style="margin-left: 12px" @click="handleLogout">退出登录</el-button>
      </div>

      <!-- Content -->
      <div style="flex: 1; overflow-y: auto; background: #f0f2f5; padding: 20px">
        <router-view />
      </div>
    </div>

    <!-- Change Password Dialog -->
    <el-dialog v-model="pwdDialogVisible" title="修改密码" width="400px">
      <el-form ref="pwdFormRef" :model="pwdForm" label-width="80px">
        <el-form-item label="原密码" prop="old" :rules="[{ required: true, message: '请输入原密码' }]">
          <el-input v-model="pwdForm.old" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="new1" :rules="[{ required: true, min: 1, message: '请输入新密码' }]">
          <el-input v-model="pwdForm.new1" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="new2" :rules="[{ validator: validateNew2, trigger: 'blur' }]">
          <el-input v-model="pwdForm.new2" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="pwdSaving" @click="handleChangePwd">确认修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getSystemSettings, changePassword } from './api'

const router = useRouter()
const route = useRoute()

const user = ref(loadUser())
const companyName = ref('企业管理系统')

// Change password
const pwdDialogVisible = ref(false)
const pwdSaving = ref(false)
const pwdFormRef = ref(null)
const pwdForm = reactive({ old: '', new1: '', new2: '' })

function validateNew2(_rule, value, callback) {
  if (value !== pwdForm.new1) callback(new Error('两次密码不一致'))
  else callback()
}

function openChangePwd() {
  pwdForm.old = ''
  pwdForm.new1 = ''
  pwdForm.new2 = ''
  pwdDialogVisible.value = true
}

async function handleChangePwd() {
  const valid = await pwdFormRef.value.validate().catch(() => false)
  if (!valid) return
  pwdSaving.value = true
  try {
    await changePassword(pwdForm.old, pwdForm.new1)
    ElMessage.success('密码修改成功，请重新登录')
    pwdDialogVisible.value = false
    // Force re-login
    setTimeout(() => handleLogout(), 1000)
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '修改失败')
  } finally {
    pwdSaving.value = false
  }
}

function loadUser() {
  try {
    const raw = localStorage.getItem('user')
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

async function loadCompanyName() {
  try {
    const { data } = await getSystemSettings()
    companyName.value = data.company_name
  } catch { /* keep default */ }
}

// Listen for settings-updated event from Settings.vue
function onSettingsUpdated() {
  loadCompanyName()
}

onMounted(() => {
  loadCompanyName()
  window.addEventListener('settings-updated', onSettingsUpdated)
})

onUnmounted(() => {
  window.removeEventListener('settings-updated', onSettingsUpdated)
})

watch(() => route.path, () => {
  user.value = loadUser()
  loadCompanyName()  // Refresh company name on every navigation
})

const currentRoute = computed(() => route.path)

const roleLabel = computed(() => {
  const map = { super_admin: '超级管理员', dept_manager: '部门主管', employee: '普通员工' }
  return map[user.value?.role] || ''
})

const roleTagType = computed(() => {
  const map = { super_admin: 'danger', dept_manager: 'warning', employee: 'info' }
  return map[user.value?.role] || 'info'
})

function handleLogout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  user.value = null
  companyName.value = '企业管理系统'
  router.push('/login')
}
</script>
