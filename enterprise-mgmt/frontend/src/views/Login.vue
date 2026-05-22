<template>
  <div style="height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)">
    <el-card style="width: 400px; border-radius: 8px">
      <template #header>
        <div style="text-align: center; font-size: 22px; font-weight: bold; color: #303133">
          企业管理系统
        </div>
      </template>

      <el-form :model="form" label-position="top" @keyup.enter="handleLogin">
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>

        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" style="width: 100%" :loading="loading" @click="handleLogin">
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div style="text-align: center; color: #999; font-size: 13px; margin-top: -8px">
        演示账号：admin / admin123
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login } from '../api'

const router = useRouter()
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

async function handleLogin() {
  // Simple validation without the form ref complexity
  if (!form.username.trim()) {
    ElMessage.warning('请输入用户名')
    return
  }
  if (!form.password) {
    ElMessage.warning('请输入密码')
    return
  }

  loading.value = true
  try {
    const { data } = await login({
      username: form.username.trim(),
      password: form.password,
    })
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user', JSON.stringify(data.user))
    ElMessage.success(`欢迎回来，${data.user.employee_name || data.user.username}`)
    router.push('/')
  } catch (err) {
    if (err.response) {
      ElMessage.error(err.response.data?.detail || '用户名或密码错误')
    } else if (err.code === 'ERR_NETWORK' || err.message?.includes('Network')) {
      ElMessage.error('无法连接服务器，请确认后端已启动（端口 8000）')
    } else {
      ElMessage.error('登录失败：' + (err.message || '未知错误'))
    }
  } finally {
    loading.value = false
  }
}
</script>
