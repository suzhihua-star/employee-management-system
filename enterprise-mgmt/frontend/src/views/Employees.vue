<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px">
      <h2>👥 人员管理</h2>
      <el-button type="primary" @click="openCreate">新增员工</el-button>
    </div>

    <!-- Search bar -->
    <el-card style="margin-bottom: 20px">
      <el-row :gutter="16" style="width: 100%">
        <el-col :span="6">
          <el-tree-select
            v-model="filters.department_id"
            :data="deptTree"
            :props="{ label: 'name', value: 'id', children: 'children' }"
            placeholder="按部门筛选"
            clearable
            check-strictly
            style="width: 100%"
            @change="fetchData"
          />
        </el-col>
        <el-col :span="6">
          <el-input v-model="filters.keyword" placeholder="搜索姓名或工号" clearable @input="onSearchInput" @clear="onSearchClear">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-button @click="fetchData">搜索</el-button>
          <el-button @click="filters.department_id = null; filters.keyword = ''; fetchData()">重置</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- Table -->
    <el-card>
      <el-table :data="employees" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="employee_no" label="工号" width="100" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="department_name" label="所属部门" width="130" />
        <el-table-column prop="position" label="职位" width="110" />
        <el-table-column prop="phone" label="电话" width="130" />
        <el-table-column prop="email" label="邮箱" min-width="160" show-overflow-tooltip />
        <el-table-column prop="hire_date" label="入职" width="110" />
        <el-table-column label="账号" width="130" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.has_account" type="success" size="small">{{ row.username }}</el-tag>
            <el-tag v-else type="info" size="small">未开通</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right" v-if="canManage">
          <template #default="{ row }">
            <el-button size="small" link type="warning" @click="openEdit(row)">编辑</el-button>
            <template v-if="isSuperAdmin">
              <el-button v-if="!row.has_account" size="small" link type="success" @click="openCreateAccount(row)">开通账号</el-button>
              <el-button v-else size="small" link type="primary" @click="openResetPassword(row)">重置密码</el-button>
              <el-button size="small" link type="danger" @click="handleDelete(row)">删除</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
      <div style="margin-top: 16px; display: flex; justify-content: flex-end" v-if="total > pageSize">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next, total"
          @current-change="fetchData"
        />
      </div>
    </el-card>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑员工' : '新增员工'"
      width="560px"
      @closed="resetMainForm"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="工号" prop="employee_no">
          <el-input v-model="form.employee_no" placeholder="请输入工号" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="所属部门" prop="department_id">
          <el-tree-select
            v-model="form.department_id"
            :data="deptTree"
            :props="{ label: 'name', value: 'id', children: 'children' }"
            placeholder="请选择部门"
            check-strictly
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="职位" prop="position">
          <el-input v-model="form.position" placeholder="如：前端工程师" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" placeholder="手机号（可选）" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" placeholder="邮箱（可选）" />
        </el-form-item>
        <el-form-item label="入职日期" prop="hire_date">
          <el-date-picker v-model="form.hire_date" type="date" placeholder="选择日期" style="width: 100%" value-format="YYYY-MM-DD" />
        </el-form-item>

        <!-- Login account section -->
        <el-divider content-position="left">登录账号</el-divider>
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="留空则不创建账号" :disabled="isEdit && editingEmp?.has_account" />
          <div v-if="isEdit && editingEmp?.has_account" style="font-size: 12px; color: #999; margin-top: 4px">
            已有账号，不可修改用户名
          </div>
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" placeholder="留空则不修改" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- Create Account Dialog -->
    <el-dialog v-model="accountDialogVisible" title="开通登录账号" width="420px">
      <el-form ref="accountFormRef" :model="accountForm" label-width="80px">
        <el-form-item label="员工">
          <span style="font-weight: 500">{{ accountTarget?.name }}（{{ accountTarget?.employee_no }}）</span>
        </el-form-item>
        <el-form-item label="用户名" prop="username" :rules="[{ required: true, message: '请输入用户名' }]">
          <el-input v-model="accountForm.username" placeholder="建议用工号" />
        </el-form-item>
        <el-form-item label="密码" prop="password" :rules="[{ required: true, message: '请输入密码' }]">
          <el-input v-model="accountForm.password" type="password" placeholder="至少6位" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="accountDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleCreateAccount">开通</el-button>
      </template>
    </el-dialog>

    <!-- Reset Password Dialog -->
    <el-dialog v-model="resetDialogVisible" title="重置密码" width="400px">
      <el-form ref="resetFormRef" :model="resetPwdForm" label-width="80px">
        <el-form-item label="员工">
          <span style="font-weight: 500">{{ resetTarget?.name }}（{{ resetTarget?.employee_no }}）</span>
        </el-form-item>
        <el-form-item label="新密码" prop="password" :rules="[{ required: true, message: '请输入新密码' }]">
          <el-input v-model="resetPwdForm.password" type="password" placeholder="至少6位" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleResetPassword">确认重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getEmployees, createEmployee, updateEmployee, deleteEmployee,
  getDepartments, createEmployeeAccount, resetEmployeePassword,
} from '../api'

const user = computed(() => JSON.parse(localStorage.getItem('user') || '{}'))
const isSuperAdmin = computed(() => user.value.role === 'super_admin')
const canManage = computed(() => ['super_admin', 'dept_manager'].includes(user.value.role))

const employees = ref([])
const deptTree = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const editingEmp = ref(null)
const formRef = ref(null)

// Pagination
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// Debounce search
let searchTimer = null
function onSearchInput() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { currentPage.value = 1; fetchData() }, 300)
}
function onSearchClear() {
  currentPage.value = 1
  fetchData()
}

const filters = reactive({
  department_id: null,
  keyword: '',
})

const form = reactive({
  name: '',
  employee_no: '',
  department_id: null,
  position: '员工',
  phone: '',
  email: '',
  hire_date: '',
  username: '',
  password: '',
})

const rules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  employee_no: [{ required: true, message: '请输入工号', trigger: 'blur' }],
  department_id: [{ required: true, message: '请选择部门', trigger: 'change' }],
  position: [{ required: true, message: '请输入职位', trigger: 'blur' }],
  hire_date: [{ required: true, message: '请选择入职日期', trigger: 'change' }],
}

// ── Account dialogs ──────────────────────────────
const accountDialogVisible = ref(false)
const accountTarget = ref(null)
const accountForm = reactive({ username: '', password: '' })

const resetDialogVisible = ref(false)
const resetTarget = ref(null)
const resetPwdForm = reactive({ password: '' })

async function fetchDeptTree() {
  const { data } = await getDepartments()
  deptTree.value = data
}

async function fetchData() {
  loading.value = true
  try {
    const { data } = await getEmployees({
      department_id: filters.department_id || undefined,
      keyword: filters.keyword || undefined,
      page: currentPage.value,
      page_size: pageSize.value,
    })
    employees.value = data
    // Estimate total from response (backend doesn't return total header yet)
    if (data.length < pageSize.value) total.value = (currentPage.value - 1) * pageSize.value + data.length
    else total.value = currentPage.value * pageSize.value + 1  // there's probably more
  } catch { /* ignore */ } finally {
    loading.value = false
  }
}

function openCreate() {
  isEdit.value = false
  editingId.value = null
  editingEmp.value = null
  form.name = ''
  form.employee_no = ''
  form.department_id = user.value.role === 'dept_manager' ? user.value.department_id : null
  form.position = '员工'
  form.phone = ''
  form.email = ''
  form.hire_date = ''
  form.username = ''
  form.password = ''
  dialogVisible.value = true
}

function openEdit(row) {
  isEdit.value = true
  editingId.value = row.id
  editingEmp.value = row
  form.name = row.name
  form.employee_no = row.employee_no
  form.department_id = row.department_id
  form.position = row.position
  form.phone = row.phone
  form.email = row.email
  form.hire_date = row.hire_date
  form.username = row.username || ''
  form.password = ''
  dialogVisible.value = true
}

function resetMainForm() {
  formRef.value?.resetFields()
}

async function handleSave() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    const payload = { ...form }
    // Remove empty account fields
    if (!payload.username) payload.username = undefined
    if (!payload.password) payload.password = undefined

    if (isEdit.value) {
      await updateEmployee(editingId.value, payload)
      ElMessage.success('员工信息已更新')
    } else {
      await createEmployee(payload)
      ElMessage.success('员工已创建')
    }
    dialogVisible.value = false
    await fetchData()
  } catch (err) {
    const msg = err.response?.data?.detail || '操作失败'
    ElMessage.error(msg)
  } finally {
    saving.value = false
  }
}

// ── Account management ────────────────────────────

function openCreateAccount(row) {
  accountTarget.value = row
  accountForm.username = row.employee_no
  accountForm.password = ''
  accountDialogVisible.value = true
}

async function handleCreateAccount() {
  if (!accountForm.username || !accountForm.password) {
    ElMessage.warning('请填写用户名和密码')
    return
  }
  saving.value = true
  try {
    await createEmployeeAccount(accountTarget.value.id, accountForm.username, accountForm.password)
    ElMessage.success('账号已开通')
    accountDialogVisible.value = false
    await fetchData()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '开通失败')
  } finally {
    saving.value = false
  }
}

function openResetPassword(row) {
  resetTarget.value = row
  resetPwdForm.password = ''
  resetDialogVisible.value = true
}

async function handleResetPassword() {
  if (!resetPwdForm.password) {
    ElMessage.warning('请输入新密码')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定要重置「${resetTarget.value.name}」的密码吗？`,
      '确认重置密码',
      { type: 'warning' }
    )
  } catch { return }  // user cancelled

  saving.value = true
  try {
    await resetEmployeePassword(resetTarget.value.id, resetPwdForm.password)
    ElMessage.success('密码已重置')
    resetDialogVisible.value = false
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '重置失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除员工「${row.name}（${row.employee_no}）」吗？`, '确认删除', { type: 'warning' })
    await deleteEmployee(row.id)
    ElMessage.success('员工已删除')
    await fetchData()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err.response?.data?.detail || '删除失败')
    }
  }
}

onMounted(() => {
  fetchDeptTree()
  fetchData()
})
</script>
