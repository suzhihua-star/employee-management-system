<template>
  <div>
    <h2 style="margin-bottom: 20px">📊 {{ isEmployee ? '我的工作台' : '仪表盘' }}</h2>

    <!-- Manager stats cards -->
    <el-row v-if="showStats" :gutter="20" style="margin-bottom: 20px">
      <el-col :span="6">
        <el-card shadow="hover">
          <div style="display: flex; align-items: center; gap: 16px">
            <el-icon size="40" color="#409EFF"><OfficeBuilding /></el-icon>
            <div>
              <div style="font-size: 13px; color: #999">部门总数</div>
              <div style="font-size: 28px; font-weight: bold">{{ stats.department_count }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div style="display: flex; align-items: center; gap: 16px">
            <el-icon size="40" color="#67C23A"><UserFilled /></el-icon>
            <div>
              <div style="font-size: 13px; color: #999">{{ isDeptManager ? '部门人数' : '员工总数' }}</div>
              <div style="font-size: 28px; font-weight: bold">{{ stats.employee_count }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div style="display: flex; align-items: center; gap: 16px">
            <el-icon size="40" color="#E6A23C"><Clock /></el-icon>
            <div>
              <div style="font-size: 13px; color: #999">今日签到率</div>
              <div style="font-size: 28px; font-weight: bold">{{ stats.today_checkin?.check_in_rate ?? 0 }}%</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div style="display: flex; align-items: center; gap: 16px">
            <el-icon size="40" color="#F56C6C"><WarningFilled /></el-icon>
            <div>
              <div style="font-size: 13px; color: #999">今日迟到</div>
              <div style="font-size: 28px; font-weight: bold">{{ stats.today_checkin?.late_count ?? 0 }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Stats detail -->
    <el-card v-if="showStats" style="margin-bottom: 20px">
      <template #header>今日考勤概览</template>
      <el-row :gutter="20">
        <el-col :span="8"><el-statistic title="已签到" :value="stats.today_checkin?.checked_in_today ?? 0" /></el-col>
        <el-col :span="8"><el-statistic title="未签到" :value="stats.today_checkin?.not_checked_in ?? 0" /></el-col>
        <el-col :span="8"><el-statistic title="迟到人数" :value="stats.today_checkin?.late_count ?? 0" /></el-col>
      </el-row>
    </el-card>

    <!-- Employee: my info card -->
    <el-card v-if="isEmployee && myInfo" style="margin-bottom: 20px">
      <template #header>我的信息</template>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="姓名">{{ myInfo.name }}</el-descriptions-item>
        <el-descriptions-item label="工号">{{ myInfo.employee_no }}</el-descriptions-item>
        <el-descriptions-item label="部门">{{ myInfo.department_name }}</el-descriptions-item>
        <el-descriptions-item label="职位">{{ myInfo.position }}</el-descriptions-item>
        <el-descriptions-item label="入职日期">{{ myInfo.hire_date }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ myInfo.email || '—' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- Records table -->
    <el-card>
      <template #header>
        <span>{{ showStats ? '今日签到记录' : '我的签到记录' }}</span>
        <el-button style="float: right" size="small" @click="fetchTodayRecords" :loading="loading">刷新</el-button>
      </template>
      <el-table :data="todayRecords" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="employee_name" label="姓名" width="100" v-if="showStats" />
        <el-table-column prop="employee_no" label="工号" width="100" v-if="showStats" />
        <el-table-column prop="department_name" label="部门" width="140" v-if="showStats" />
        <el-table-column prop="check_in_time" label="签到时间" width="170">
          <template #default="{ row }">
            {{ row.check_in_time ? new Date(row.check_in_time).toLocaleTimeString('zh-CN') : '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="check_out_time" label="签退时间" width="170">
          <template #default="{ row }">
            {{ row.check_out_time ? new Date(row.check_out_time).toLocaleTimeString('zh-CN') : '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="!loading && todayRecords.length === 0" style="text-align: center; padding: 40px; color: #999">
        暂无今日签到记录
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { getDepartments, getEmployees, getCheckinRecords, getCheckinStats } from '../api'

const user = computed(() => JSON.parse(localStorage.getItem('user') || '{}'))
const isSuperAdmin = computed(() => user.value.role === 'super_admin')
const isDeptManager = computed(() => user.value.role === 'dept_manager')
const isEmployee = computed(() => user.value.role === 'employee')
const showStats = computed(() => ['super_admin', 'dept_manager'].includes(user.value.role))

const loading = ref(false)
const todayRecords = ref([])
const myInfo = ref(null)
const stats = reactive({
  department_count: 0,
  employee_count: 0,
  today_checkin: null,
})

function statusType(status) {
  const map = { normal: 'success', late: 'danger', early: 'warning', absent: 'info' }
  return map[status] || 'info'
}
function statusLabel(status) {
  const map = { normal: '正常', late: '迟到', early: '早退', absent: '缺勤' }
  return map[status] || status
}

async function fetchData() {
  try {
    const [deptRes, empRes] = await Promise.all([
      getDepartments(),
      getEmployees({ page_size: 100 }),
    ])
    function countDepts(nodes) {
      let count = 0
      for (const n of nodes) { count += 1; if (n.children) count += countDepts(n.children) }
      return count
    }
    stats.department_count = isSuperAdmin.value ? countDepts(deptRes.data) : 0
    stats.employee_count = empRes.data.length

    if (isEmployee.value && empRes.data.length > 0) {
      myInfo.value = empRes.data[0]
    }
  } catch { /* ignore */ }

  if (showStats.value) {
    try {
      const statsRes = await getCheckinStats()
      stats.today_checkin = statsRes.data
    } catch { /* ignore */ }
  }
}

async function fetchTodayRecords() {
  loading.value = true
  try {
    const today = new Date().toISOString().split('T')[0]
    const { data } = await getCheckinRecords({ check_date: today, page_size: 100 })
    todayRecords.value = data
  } catch { /* ignore */ } finally {
    loading.value = false
  }
}

onMounted(() => { fetchData(); fetchTodayRecords() })
</script>
