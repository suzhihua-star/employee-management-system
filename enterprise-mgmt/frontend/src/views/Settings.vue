<template>
  <div>
    <h2 style="margin-bottom: 20px">⚙ 系统设置</h2>

    <el-card style="margin-bottom: 20px">
      <template #header>企业信息</template>
      <el-form :model="form" label-width="120px" style="max-width: 500px">
        <el-form-item label="企业名称">
          <el-input v-model="form.company_name" placeholder="请输入企业名称" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="saveCompanyName">保存企业名称</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <template #header>签到时间设置</template>
      <el-form :model="form" label-width="120px" style="max-width: 500px">
        <el-form-item label="上班时间">
          <el-row :gutter="8">
            <el-col :span="8">
              <el-input-number v-model="form.work_start_hour" :min="0" :max="23" controls-position="right" style="width: 100%" />
            </el-col>
            <el-col :span="2" style="text-align: center; line-height: 32px">时</el-col>
            <el-col :span="8">
              <el-input-number v-model="form.work_start_minute" :min="0" :max="59" controls-position="right" style="width: 100%" />
            </el-col>
            <el-col :span="2" style="text-align: center; line-height: 32px">分</el-col>
          </el-row>
        </el-form-item>
        <el-form-item label="迟到阈值">
          <el-input-number v-model="form.late_threshold_minutes" :min="0" :max="240" controls-position="right" style="width: 140px" />
          <span style="margin-left: 8px; color: #999">分钟（超过此时间算迟到）</span>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="saveCheckin">保存签到设置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSystemSettings, updateSystemSettings } from '../api'

const saving = ref(false)
const form = reactive({
  company_name: '企业管理系统',
  work_start_hour: 9,
  work_start_minute: 0,
  late_threshold_minutes: 30,
})

async function loadSettings() {
  try {
    const { data } = await getSystemSettings()
    form.company_name = data.company_name
    form.work_start_hour = data.work_start_hour
    form.work_start_minute = data.work_start_minute
    form.late_threshold_minutes = data.late_threshold_minutes
  } catch { /* use defaults */ }
}

async function saveCompanyName() {
  if (!form.company_name.trim()) {
    ElMessage.warning('企业名称不能为空')
    return
  }
  saving.value = true
  try {
    const { data } = await updateSystemSettings({ company_name: form.company_name.trim() })
    form.company_name = data.company_name
    ElMessage.success('企业名称已更新')
    // Trigger sidebar refresh
    window.dispatchEvent(new Event('settings-updated'))
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function saveCheckin() {
  saving.value = true
  try {
    await updateSystemSettings({
      work_start_hour: form.work_start_hour,
      work_start_minute: form.work_start_minute,
      late_threshold_minutes: form.late_threshold_minutes,
    })
    ElMessage.success('签到时间设置已更新')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(loadSettings)
</script>
