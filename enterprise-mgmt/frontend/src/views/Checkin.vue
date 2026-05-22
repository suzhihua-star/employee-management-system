<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px">
      <h2>⏰ 签到系统</h2>
      <div style="display: flex; gap: 12px">
        <el-button v-if="canManage" @click="openSettings">⚙ 签到设置</el-button>
        <template v-if="user.employee_id">
          <el-button v-if="!todayStatus?.check_in_time" type="success" size="large" @click="handleCheckIn" :loading="acting">
            签 到
          </el-button>
          <el-button v-else-if="!todayStatus?.check_out_time" type="warning" size="large" @click="handleCheckOut" :loading="acting">
            签 退
          </el-button>
          <el-tag v-else type="success" size="large">今日已完成 ✓</el-tag>
        </template>
      </div>
    </div>

    <!-- Today status -->
    <el-card style="margin-bottom: 20px" v-if="todayStatus">
      <template #header>今日签到状态</template>
      <el-descriptions :column="4" border>
        <el-descriptions-item label="签到时间">
          {{ todayStatus.check_in_time ? new Date(todayStatus.check_in_time).toLocaleTimeString('zh-CN') : '—' }}
        </el-descriptions-item>
        <el-descriptions-item label="签退时间">
          {{ todayStatus.check_out_time ? new Date(todayStatus.check_out_time).toLocaleTimeString('zh-CN') : '—' }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusType(todayStatus.status)">{{ statusLabel(todayStatus.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="日期">{{ todayStatus.check_date }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- Records -->
    <el-card>
      <template #header>
        <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap">
          <span>签到记录</span>
          <el-date-picker v-model="queryDate" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" @change="fetchRecords" style="width: 160px" />
          <el-tree-select
            v-if="isSuperAdmin"
            v-model="queryDept"
            :data="deptTree"
            :props="{ label: 'name', value: 'id', children: 'children' }"
            placeholder="按部门筛选"
            clearable
            check-strictly
            style="width: 180px"
            @change="fetchRecords"
          />
          <el-button @click="fetchRecords">查询</el-button>
        </div>
      </template>

      <el-table :data="records" stripe style="width: 100%" max-height="500" v-loading="loadingRecords">
        <el-table-column prop="employee_name" label="姓名" width="100" />
        <el-table-column prop="employee_no" label="工号" width="100" />
        <el-table-column prop="department_name" label="部门" width="130" v-if="canManage" />
        <el-table-column prop="check_date" label="日期" width="110" />
        <el-table-column prop="check_in_time" label="签到" width="90">
          <template #default="{ row }">
            {{ row.check_in_time ? new Date(row.check_in_time).toLocaleTimeString('zh-CN', {hour:'2-digit',minute:'2-digit'}) : '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="check_out_time" label="签退" width="90">
          <template #default="{ row }">
            {{ row.check_out_time ? new Date(row.check_out_time).toLocaleTimeString('zh-CN', {hour:'2-digit',minute:'2-digit'}) : '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <template v-if="canManage">
              <el-select
                :model-value="row.status"
                size="small"
                style="width: 90px"
                @change="(val) => handleStatusChange(row, val)"
              >
                <el-option label="正常" value="normal" />
                <el-option label="迟到" value="late" />
                <el-option label="早退" value="early" />
                <el-option label="缺勤" value="absent" />
              </el-select>
            </template>
            <el-tag v-else :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="!loadingRecords && records.length === 0" style="text-align: center; padding: 40px; color: #999">
        暂无签到记录
      </div>
      <div style="margin-top: 16px; display: flex; justify-content: flex-end" v-if="recordTotal > recordPageSize">
        <el-pagination
          v-model:current-page="recordPage"
          :page-size="recordPageSize"
          :total="recordTotal"
          layout="prev, pager, next, total"
          @current-change="fetchRecords"
        />
      </div>
    </el-card>

    <!-- Settings Dialog -->
    <el-dialog v-model="settingsVisible" title="签到时间设置" width="450px">
      <el-form :model="settingsForm" label-width="120px">
        <el-form-item label="上班时间">
          <el-row :gutter="8">
            <el-col :span="10">
              <el-input-number v-model="settingsForm.work_start_hour" :min="0" :max="23" controls-position="right" />
            </el-col>
            <el-col :span="2" style="text-align: center; line-height: 32px">:</el-col>
            <el-col :span="10">
              <el-input-number v-model="settingsForm.work_start_minute" :min="0" :max="59" controls-position="right" />
            </el-col>
          </el-row>
        </el-form-item>
        <el-form-item label="迟到阈值(分钟)">
          <el-input-number v-model="settingsForm.late_threshold_minutes" :min="0" :max="240" controls-position="right" style="width: 160px" />
          <span style="margin-left: 8px; color: #999; font-size: 13px">超过此时间算迟到</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="settingsVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingSettings" @click="handleSaveSettings">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  checkIn, checkOut, getTodayStatus, getCheckinRecords,
  getCheckinSettings, updateCheckinSettings, updateCheckinStatus,
  getDepartments,
} from '../api'

const user = computed(() => JSON.parse(localStorage.getItem('user') || '{}'))
const canManage = computed(() => ['super_admin', 'dept_manager'].includes(user.value.role))
const isSuperAdmin = computed(() => user.value.role === 'super_admin')

const acting = ref(false)
const todayStatus = ref(null)
const records = ref([])
const loadingRecords = ref(false)
const deptTree = ref([])
const queryDate = ref('')
const queryDept = ref(null)

// Pagination
const recordPage = ref(1)
const recordPageSize = ref(20)
const recordTotal = ref(0)

function statusType(s) {
  return { normal: 'success', late: 'danger', early: 'warning', absent: 'info' }[s] || 'info'
}
function statusLabel(s) {
  return { normal: '正常', late: '迟到', early: '早退', absent: '缺勤' }[s] || s
}

async function fetchTodayStatus() {
  try {
    const { data } = await getTodayStatus()
    todayStatus.value = data
  } catch { /* ignore */ }
}

async function fetchRecords() {
  loadingRecords.value = true
  try {
    const params = {
      page: recordPage.value,
      page_size: recordPageSize.value,
    }
    if (queryDate.value) params.check_date = queryDate.value
    if (isSuperAdmin.value && queryDept.value) params.department_id = queryDept.value
    const { data } = await getCheckinRecords(params)
    records.value = data
    if (data.length < recordPageSize.value) recordTotal.value = (recordPage.value - 1) * recordPageSize.value + data.length
    else recordTotal.value = recordPage.value * recordPageSize.value + 1
  } catch { /* ignore */ } finally {
    loadingRecords.value = false
  }
}

async function handleCheckIn() {
  acting.value = true
  try {
    const { data } = await checkIn()
    todayStatus.value = data
    ElMessage.success(`签到成功！${data.status === 'late' ? '（迟到）' : ''}`)
    fetchRecords()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '签到失败')
  } finally {
    acting.value = false
  }
}

async function handleCheckOut() {
  acting.value = true
  try {
    const { data } = await checkOut()
    todayStatus.value = data
    ElMessage.success('签退成功！')
    fetchRecords()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '签退失败')
  } finally {
    acting.value = false
  }
}

async function handleStatusChange(row, newStatus) {
  try {
    await updateCheckinStatus(row.id, newStatus)
    row.status = newStatus
    ElMessage.success(`状态已改为「${statusLabel(newStatus)}」`)
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '修改失败')
  }
}

// ── Settings ──────────────────────────────────────

const settingsVisible = ref(false)
const savingSettings = ref(false)
const settingsForm = reactive({
  work_start_hour: 9,
  work_start_minute: 0,
  late_threshold_minutes: 30,
})

async function openSettings() {
  try {
    const { data } = await getCheckinSettings()
    settingsForm.work_start_hour = data.work_start_hour
    settingsForm.work_start_minute = data.work_start_minute
    settingsForm.late_threshold_minutes = data.late_threshold_minutes
  } catch { /* use defaults */ }
  settingsVisible.value = true
}

async function handleSaveSettings() {
  savingSettings.value = true
  try {
    await updateCheckinSettings(settingsForm)
    ElMessage.success('签到时间设置已更新')
    settingsVisible.value = false
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '保存失败')
  } finally {
    savingSettings.value = false
  }
}

onMounted(async () => {
  await fetchTodayStatus()
  await fetchRecords()
  if (canManage.value) {
    const { data } = await getDepartments()
    deptTree.value = data
  }
})
</script>
