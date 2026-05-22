<template>
  <div>
    <h2 style="margin-bottom: 20px">🌳 组织架构</h2>

    <el-card>
      <el-tree
        :data="treeData"
        :props="{ label: 'name', children: 'children' }"
        node-key="id"
        default-expand-all
        :expand-on-click-node="false"
      >
        <template #default="{ data }">
          <div style="display: flex; align-items: center; gap: 8px; padding: 4px 0">
            <el-icon color="#409EFF" size="18"><OfficeBuilding /></el-icon>
            <span style="font-weight: 500">{{ data.name }}</span>
            <el-tag size="small" type="info" v-if="data.employee_count !== undefined">
              {{ data.employee_count }} 人
            </el-tag>
            <span v-if="data.description" style="color: #999; font-size: 13px; margin-left: 8px">
              — {{ data.description }}
            </span>
          </div>
        </template>
      </el-tree>
    </el-card>

    <!-- Employee list by department -->
    <el-card style="margin-top: 20px">
      <template #header>部门人员明细</template>
      <el-collapse v-model="activeDepts">
        <el-collapse-item
          v-for="dept in flatDepts"
          :key="dept.id"
          :name="dept.id"
        >
          <template #title>
            <div style="display: flex; align-items: center; gap: 8px">
              <el-icon color="#409EFF"><Folder /></el-icon>
              <span style="font-weight: 500">{{ dept.name }}</span>
              <el-tag size="small">{{ dept.employee_count }} 人</el-tag>
            </div>
          </template>

          <el-table v-if="dept.employees?.length" :data="dept.employees" size="small" stripe>
            <el-table-column prop="employee_no" label="工号" width="100" />
            <el-table-column prop="name" label="姓名" width="100" />
            <el-table-column prop="position" label="职位" width="150" />
            <el-table-column prop="phone" label="电话" width="130" />
            <el-table-column prop="email" label="邮箱" min-width="180" />
          </el-table>
          <div v-else style="text-align: center; padding: 20px; color: #999">
            {{ dept.employee_count > 0 ? '暂无查看权限' : '该部门暂无员工' }}
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getDepartments, getEmployees } from '../api'

const treeData = ref([])
const flatDepts = ref([])
const activeDepts = ref([])

function flattenDepts(nodes) {
  const result = []
  for (const n of nodes) {
    result.push({ ...n, employees: [] })
    if (n.children) {
      result.push(...flattenDepts(n.children))
    }
  }
  return result
}

onMounted(async () => {
  const [deptRes, empRes] = await Promise.all([
    getDepartments(),
    getEmployees({}),
  ])

  treeData.value = deptRes.data
  flatDepts.value = flattenDepts(deptRes.data)
  activeDepts.value = flatDepts.value.map(d => d.id)

  // Map employees to departments
  const empMap = {}
  for (const emp of empRes.data) {
    if (!empMap[emp.department_id]) empMap[emp.department_id] = []
    empMap[emp.department_id].push(emp)
  }
  for (const dept of flatDepts.value) {
    dept.employees = empMap[dept.id] || []
  }
})
</script>
