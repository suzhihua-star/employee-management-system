# 企业管理系统 — 技术文档

> 版本 1.0 | 2026-05

---

## 1. 项目概况

企业管理系统是一套面向 50–200 人中小型企业的 Web 应用，提供部门管理、人员管理、考勤签到和组织架构可视化功能。系统采用前后端分离架构，内置三级权限体系（超级管理员 / 部门主管 / 普通员工）。

| 属性 | 值 |
|------|-----|
| 架构 | 前后端分离 (REST API + SPA) |
| 后端 | Python 3.11+ / FastAPI |
| 前端 | Vue 3 / Element Plus / Vite |
| 数据库 | SQLite (SQLAlchemy ORM) |
| 认证 | JWT (python-jose + bcrypt) |
| 端口 | 后端 8000，前端 5173 |

---

## 2. 项目结构

```
enterprise-mgmt/
├── backend/                        # Python FastAPI 后端
│   ├── main.py                     # 应用入口 + CORS + 路由注册
│   ├── database.py                 # SQLAlchemy 引擎 + 会话管理
│   ├── models.py                   # ORM 模型 (5 张表)
│   ├── schemas.py                  # Pydantic 请求/响应模型
│   ├── utils.py                    # 共享工具函数
│   ├── seed.py                     # 种子数据 (8 员工 + 7 部门)
│   ├── requirements.txt            # Python 依赖
│   └── routers/
│       ├── auth.py                 # 登录 + JWT + 权限中间件 + 修改密码
│       ├── departments.py          # 部门树形 CRUD
│       ├── employees.py            # 员工 CRUD + 账号管理 + 分页
│       ├── checkin.py              # 签到/签退 + 记录查询 + 统计 + 状态修改
│       └── settings.py             # 系统设置 (企业名称 + 考勤时间)
├── frontend/                       # Vue 3 + Vite 前端
│   ├── index.html                  # HTML 入口
│   ├── vite.config.js              # Vite 配置 + API 代理
│   ├── package.json                # Node 依赖
│   └── src/
│       ├── main.js                 # Vue 应用入口 (Element Plus + Router)
│       ├── App.vue                 # 主布局 (侧边栏 + 顶栏 + 修改密码)
│       ├── api/index.js            # Axios 封装 (拦截器 + 所有 API 函数)
│       ├── router/index.js         # 路由定义 + 导航守卫
│       └── views/
│           ├── Login.vue           # 登录页
│           ├── Dashboard.vue       # 仪表盘 (角色自适应)
│           ├── Departments.vue     # 部门管理 (树形表格)
│           ├── Employees.vue       # 人员管理 (分页 + 搜索防抖 + 账号管理)
│           ├── Checkin.vue         # 签到系统 (签到/签退 + 设置 + 状态修改)
│           ├── OrgChart.vue        # 组织架构 (树形 + 部门明细)
│           └── Settings.vue        # 系统设置 (企业名称 + 考勤时间)
└── enterprise.db                   # SQLite 数据库文件 (运行时生成)
```

---

## 3. 技术栈详情

### 3.1 后端

| 组件 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.115.0 | REST API 框架 |
| Uvicorn | 0.30.0 | ASGI 服务器 (热重载) |
| SQLAlchemy | 2.0.35 | ORM + 数据库抽象 |
| python-jose | 3.3.0 | JWT 令牌签发与验证 |
| passlib | 1.7.4 | bcrypt 密码哈希 |
| bcrypt | 4.0.1 | 密码哈希底层库 |

### 3.2 前端

| 组件 | 版本 | 用途 |
|------|------|------|
| Vue | 3.4+ | 渐进式框架 (Composition API) |
| Vue Router | 4.3+ | SPA 路由 + 导航守卫 |
| Element Plus | 2.7+ | 企业级 UI 组件库 (中文) |
| Axios | 1.7+ | HTTP 客户端 (拦截器 + 代理) |
| Vite | 5.4+ | 构建工具 + 开发服务器 |

---

## 4. 数据模型

### 4.1 ER 关系

```
User ────1:1──── Employee ────1:N──── CheckIn
 │                  │
 │                  │ N:1
 │                  ▼
 │              Department (自引用树)
 │                  ▲
 └──── N:1 ────────┘ (dept_manager 关联)
```

### 4.2 表结构

**users** — 登录账号

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| username | VARCHAR(50) UNIQUE | 登录名 |
| password_hash | VARCHAR(128) | bcrypt 哈希 |
| role | ENUM | super_admin / dept_manager / employee |
| employee_id | INTEGER FK→employees | 关联员工 (普通员工必填) |
| department_id | INTEGER FK→departments | 主管管辖部门 |

**departments** — 部门树

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| name | VARCHAR(100) | 部门名称 |
| parent_id | INTEGER FK→departments | 上级部门 (NULL=根) |
| description | VARCHAR(255) | 描述 |
| created_at | DATETIME | 创建时间 |

**employees** — 员工档案

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| name | VARCHAR(50) | 姓名 |
| employee_no | VARCHAR(20) UNIQUE | 工号 |
| department_id | INTEGER FK→departments | 所属部门 |
| position | VARCHAR(50) | 职位 |
| phone | VARCHAR(20) | 手机号 |
| email | VARCHAR(100) | 邮箱 |
| hire_date | DATE | 入职日期 |
| created_at | DATETIME | 创建时间 |

**checkins** — 签到记录

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| employee_id | INTEGER FK→employees | 员工 |
| check_date | DATE | 签到日期 |
| check_in_time | DATETIME | 签到时间 (可空) |
| check_out_time | DATETIME | 签退时间 (可空) |
| status | ENUM | normal / late / early / absent |

**system_settings** — 系统配置 (单例)

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| id | INTEGER PK | — | 主键 (永远只有一行) |
| company_name | VARCHAR(100) | "企业管理系统" | 企业名称 |
| work_start_hour | INTEGER | 9 | 上班小时 |
| work_start_minute | INTEGER | 0 | 上班分钟 |
| late_threshold_minutes | INTEGER | 30 | 迟到阈值 |

---

## 5. API 接口

### 5.1 认证模块 `POST /api/auth`

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| POST | `/login` | 无 | 登录，返回 JWT + 用户信息 |
| GET | `/me` | 登录 | 获取当前用户信息 |
| POST | `/change-password` | 登录 | 自助修改密码 (old_password + new_password) |

请求示例：

```json
// POST /api/auth/login
{ "username": "admin", "password": "admin123" }

// 响应
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1, "username": "admin", "role": "super_admin",
    "employee_id": null, "department_id": null, "employee_name": null
  }
}
```

### 5.2 部门模块 `GET|POST|PUT|DELETE /api/departments`

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/` | 登录 | 获取部门树 (含累加员工数) |
| POST | `/` | 超管 | 新增部门 |
| PUT | `/{id}` | 超管 | 编辑部门 |
| DELETE | `/{id}` | 超管 | 删除 (有子部门/员工时拒绝) |

### 5.3 员工模块 `GET|POST|PUT|DELETE /api/employees`

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/` | 登录 | 列表 (role过滤 + 分页 + 搜索) |
| GET | `/{id}` | 登录 | 详情 |
| POST | `/` | 主管+ | 新增 (可同时创建账号) |
| PUT | `/{id}` | 主管+ | 编辑 (可修改密码) |
| DELETE | `/{id}` | 超管 | 删除 (级联删 User) |
| POST | `/{id}/create-account` | 超管 | 为已有员工开通账号 |
| POST | `/{id}/reset-password` | 超管 | 重置密码 |

查询参数：`?department_id=&keyword=&page=1&page_size=20`

### 5.4 签到模块 `GET|POST|PUT /api/checkin`

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| POST | `/in` | 登录 | 签到 (自动判定迟到) |
| POST | `/out` | 登录 | 签退 |
| GET | `/today` | 登录 | 今日签到状态 |
| GET | `/records` | 登录 | 记录查询 (分页) |
| GET | `/stats` | 主管+ | 今日统计 |
| GET | `/settings` | 主管+ | 考勤时间设置 |
| PUT | `/settings` | 主管+ | 修改考勤时间 |
| PUT | `/{id}/status` | 主管+ | 修改记录状态 |

### 5.5 系统设置 `GET|PUT /api/settings`

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/` | 登录 | 获取所有设置 |
| PUT | `/` | 超管 | 修改 (企业名称 + 考勤时间) |

---

## 6. 权限体系

### 6.1 角色定义

| 角色 | 标识 | 权限范围 |
|------|------|----------|
| 超级管理员 | `super_admin` | 全部功能：部门/员工/考勤管理 + 系统设置 |
| 部门主管 | `dept_manager` | 管辖本部门及子部门：员工管理(本部门) + 考勤查看/修改(本部门) + 考勤设置 |
| 普通员工 | `employee` | 个人考勤签到/签退 + 查看个人记录 + 组织架构查看 |

### 6.2 实现方式

- **后端**：FastAPI `Depends` 依赖注入链
  - `get_current_user` → 解码 JWT → 返回 User
  - `require_admin` → 仅 `super_admin`
  - `require_manager_or_above` → `super_admin` 或 `dept_manager`

- **前端**：Vue Router 导航守卫 + 菜单条件渲染
  - `meta.roles` 数组控制路由访问
  - `v-if` 按角色显示/隐藏菜单项和操作按钮

### 6.3 部门主管子树查询

部门主管查询员工和考勤时，使用递归获取管辖部门及其所有子孙部门 ID：

```python
# utils.py
def get_subtree_dept_ids(root_id: int, db: Session) -> list[int]:
    ids = [root_id]
    children = db.query(Department).filter(Department.parent_id == root_id).all()
    for child in children:
        ids.extend(get_subtree_dept_ids(child.id, db))
    return ids

# 查询时
dept_ids = get_subtree_dept_ids(manager.department_id, db)
q.filter(Employee.department_id.in_(dept_ids))
```

---

## 7. 前端架构

### 7.1 路由表

| 路径 | 组件 | 权限 | 标题 |
|------|------|------|------|
| `/login` | Login.vue | 无 | 登录 |
| `/` | Dashboard.vue | 登录 | 仪表盘/我的工作台 |
| `/departments` | Departments.vue | 超管 | 部门管理 |
| `/employees` | Employees.vue | 主管+ | 人员管理 |
| `/checkin` | Checkin.vue | 登录 | 签到系统 |
| `/orgchart` | OrgChart.vue | 登录 | 组织架构 |
| `/settings` | Settings.vue | 超管 | 系统设置 |

### 7.2 导航守卫

```javascript
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  // 未登录 → 跳转登录页
  if (to.meta.requiresAuth && !token) return next('/login')
  // 已登录访问登录页 → 跳转首页
  if (to.path === '/login' && token) return next('/')
  // 角色权限不足 → 跳转首页
  if (to.meta.roles && !to.meta.roles.includes(user.role)) return next('/')
  next()
})
```

### 7.3 HTTP 拦截器

- **请求拦截**：自动附加 `Authorization: Bearer <token>`
- **响应拦截**：401 时清除 token + 提示"登录已过期" + 跳转登录页 (登录接口本身除外)

### 7.4 Dev 代理

Vite 开发服务器将 `/api/*` 代理到 `http://127.0.0.1:8000`，避免跨域问题：

```javascript
// vite.config.js
server: {
  proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true } }
}
```

---

## 8. 部署与运行

### 8.1 环境要求

- Python 3.11+
- Node.js 18+
- npm 9+

### 8.2 后端启动

```bash
cd enterprise-mgmt/backend

# 安装依赖
pip install -r requirements.txt

# 初始化数据库 (种子数据)
python seed.py

# 启动服务 (开发模式，热重载)
python -m uvicorn enterprise-mgmt.backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 8.3 前端启动

```bash
cd enterprise-mgmt/frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 8.4 访问

浏览器打开 `http://localhost:5173`

### 8.5 演示账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 超级管理员 | admin | admin123 |
| 部门主管 (技术) | zhangwei | 123456 |
| 部门主管 (市场) | chenming | 123456 |
| 普通员工 | lina | 123456 |
| 普通员工 | wangqiang | 123456 |

### 8.6 生产部署建议

1. 将 `SECRET_KEY` 改为环境变量：`os.environ.get("SECRET_KEY", "fallback")`
2. SQLite 替换为 PostgreSQL（修改 `database.py` 连接字符串）
3. 前端 `npm run build` 生成静态文件，由 Nginx 托管
4. 后端用 Gunicorn + Uvicorn workers：
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker enterprise-mgmt.backend.main:app
   ```
5. Nginx 配置反向代理，统一域名

---

## 9. 关键业务逻辑

### 9.1 签到迟到判定

```
if 签到时间 > (上班时间 + 迟到阈值):
    status = "late"
else:
    status = "normal"
```

上班时间和阈值从 `system_settings` 表读取，可在「系统设置」页面动态修改。

### 9.2 账号创建

- **新建员工时**：填写用户名 + 密码 → 同步创建 `User` 记录 (角色=employee)
- **已有员工开通**：超管点击「开通账号」→ 输入用户名密码
- **重置密码**：超管点击「重置密码」→ 输入新密码 (需二次确认)

### 9.3 部门删除保护

删除部门时检查：
- 是否有子部门 → 拒绝，提示先删除子部门
- 是否有员工 → 拒绝，提示先转移或删除员工

---

## 10. 设计决策与权衡

| 决策 | 理由 |
|------|------|
| SQLite 而非 PostgreSQL | 零配置，适合中小规模；SQLAlchemy 可平滑迁移 |
| JWT 而非 Session | 无状态，前后端分离友好 |
| bcrypt 密码哈希 | 行业标准，防彩虹表 |
| 部门主管递归子树查询 | 避免 N+1 问题；50-200 人规模性能足够 |
| Element Plus 而非 Ant Design | Vue 3 生态最成熟，中文支持好 |
| 前端分页 (每页 20) | 平衡加载速度与翻页频率 |
| 300ms 搜索防抖 | 减少无效 API 请求 |

---

## 11. 已知限制与改进方向

| 限制 | 建议改进 |
|------|----------|
| 无数据导出功能 | 增加 Excel/CSV 导出 |
| 无操作日志 | 增加审计日志表 |
| 无移动端适配 | 响应式布局或小程序 |
| 无批量导入 | Excel 批量导入员工 |
| 部门主管设置时间与超管入口不一致 | 统一为 `/api/settings` |
| SECRET_KEY 硬编码 | 改为环境变量 |
| 前端无自动化测试 | 增加 Vitest + Vue Test Utils |
