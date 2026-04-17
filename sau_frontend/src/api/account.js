import { http } from '@/utils/request'

// 账号管理相关API
export const accountApi = {
  // 获取有效账号列表（带验证）
  getValidAccounts() {
    return http.get('/getValidAccounts')
  },

  // 获取账号列表（不带验证，快速加载）
  getAccounts() {
    return http.get('/getAccounts')
  },

  // 添加账号
  addAccount(data) {
    return http.post('/account', data)
  },

  // 更新账号
  updateAccount(data) {
    return http.post('/updateUserinfo', data)
  },

  // 删除账号
  deleteAccount(id) {
    return http.get(`/deleteAccount?id=${id}`)
  },

  // 获取运营者分组列表
  getGroups() {
    return http.get('/getGroups')
  },

  // 更新账号分组
  updateGroup(data) {
    return http.post('/updateAccountGroup', data)
  },

  // 更新帖子的账号选择
  updatePostAccounts(data) {
    return http.post('/updatePostAccounts', data)
  },

  // 运营者管理
  addOperator(data) {
    return http.post('/addOperator', data)
  },
  deleteOperator(data) {
    return http.post('/deleteOperator', data)
  },
  renameOperator(data) {
    return http.post('/renameOperator', data)
  }
}