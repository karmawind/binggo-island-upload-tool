import { defineStore } from 'pinia'
import { ref } from 'vue'
import { accountApi } from '@/api/account'

export const useAccountStore = defineStore('account', () => {
  // 存储所有账号信息
  const accounts = ref([])
  // 运营者分组列表
  const groups = ref([])

  // 平台类型映射（1-4 视频，5-10 图文）
  const platformTypes = {
    1: '小红书',
    2: '视频号',
    3: '抖音',
    4: '快手',
    5: '百家号',
    6: '什么值得买',
    7: '头条号',
    8: '携程',
    9: '搜狐号',
    10: '微博'
  }

  // 设置账号列表
  const setAccounts = (accountsData) => {
    // 转换后端返回的数据格式为前端使用的格式
    accounts.value = accountsData.map(item => {
      return {
        id: item[0],
        type: item[1],
        filePath: item[2],
        name: item[3],
        status: item[4] === -1 ? '验证中' : (item[4] === 1 ? '正常' : '异常'),
        statusNum: item[4],
        platform: platformTypes[item[1]] || '未知',
        group: item[5] || ''
      }
    })
  }

  // 获取分组列表
  const fetchGroups = async () => {
    try {
      const res = await accountApi.getGroups()
      if (res.code === 200 && res.data) {
        groups.value = res.data
      }
    } catch (error) {
      console.error('获取分组失败:', error)
    }
  }

  // 添加账号
  const addAccount = (account) => {
    accounts.value.push(account)
  }

  // 更新账号
  const updateAccount = (id, updatedAccount) => {
    const index = accounts.value.findIndex(acc => acc.id === id)
    if (index !== -1) {
      accounts.value[index] = { ...accounts.value[index], ...updatedAccount }
    }
  }

  // 删除账号
  const deleteAccount = (id) => {
    accounts.value = accounts.value.filter(acc => acc.id !== id)
  }

  // 根据平台获取账号
  const getAccountsByPlatform = (platform) => {
    return accounts.value.filter(acc => acc.platform === platform)
  }

  return {
    accounts,
    groups,
    platformTypes,
    setAccounts,
    fetchGroups,
    addAccount,
    updateAccount,
    deleteAccount,
    getAccountsByPlatform
  }
})
