<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px">
      <h2>🏛️ 部门管理</h2>
      <el-button type="primary" @click="openCreate(null)">新增部门</el-button>
    </div>

    <el-card>
      <el-table :data="treeData" row-key="id" stripe default-expand-all style="width: 100%">
        <el-table-column prop="name" label="部门名称" min-width="200">
          <template #default="{ row }">
            <span :style="{ paddingLeft: (row._level || 0) * 24 + 'px' }">
              {{ row._level > 0 ? '├ ' : '' }}{{ row.name }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="250" show-overflow-tooltip />
        <el-table-column prop="employee_count" label="员工数" width="100" align="center" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" link type="primary" @click="openCreate(row)">添加子部门</el-button>
            <el-button size="small" link type="warning" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑部门' : '新增部门'"
      width="500px"
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="部门名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入部门名称" />
        </el-form-item>
        <el-form-item label="上级部门" prop="parent_id">
          <el-tree-select
            v-model="form.parent_id"
            :data="flatOptions"
            :props="{ label: 'name', value: 'id', children: 'children' }"
            placeholder="不选则为顶级部门"
            clearable
            check-strictly
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="部门描述（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getDepartments, createDepartment, updateDepartment, deleteDepartment } from '../api'

const treeData = ref([])
const flatOptions = ref([])
const dialogVisible = ref(false)
const saving = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const formRef = ref(null)

const form = reactive({
  name: '',
  parent_id: null,
  description: '',
})

const rules = {
  name: [{ required: true, message: '请输入部门名称', trigger: 'blur' }],
}

function flattenTree(nodes, level = 0) {
  const result = []
  for (const node of nodes) {
    result.push({ ...node, _level: level })
    if (node.children && node.children.length > 0) {
      result.push(...flattenTree(node.children, level + 1))
    }
  }
  return result
}

async function fetchData() {
  const { data } = await getDepartments()
  flatOptions.value = data
  treeData.value = flattenTree(data)
}

function openCreate(parent) {
  isEdit.value = false
  editingId.value = null
  form.name = ''
  form.description = ''
  form.parent_id = parent ? parent.id : null
  dialogVisible.value = true
}

function openEdit(row) {
  isEdit.value = true
  editingId.value = row.id
  form.name = row.name
  form.description = row.description
  form.parent_id = row.parent_id
  dialogVisible.value = true
}

function resetForm() {
  formRef.value?.resetFields()
}

async function handleSave() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    const payload = {
      name: form.name,
      parent_id: form.parent_id,
      description: form.description,
    }
    if (isEdit.value) {
      await updateDepartment(editingId.value, payload)
      ElMessage.success('部门已更新')
    } else {
      await createDepartment(payload)
      ElMessage.success('部门已创建')
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

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除部门「${row.name}」吗？如果该部门下有子部门或员工则无法删除。`, '确认删除', {
      type: 'warning',
    })
    await deleteDepartment(row.id)
    ElMessage.success('部门已删除')
    await fetchData()
  } catch (err) {
    if (err !== 'cancel') {
      const msg = err.response?.data?.detail || '删除失败'
      ElMessage.error(msg)
    }
  }
}

onMounted(fetchData)
</script>
