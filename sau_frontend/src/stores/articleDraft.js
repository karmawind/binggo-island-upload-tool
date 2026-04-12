import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'

export const useArticleDraftStore = defineStore('articleDraft', () => {
  // 图文发布页表单
  const form = reactive({
    title: '',
    content: '',
    tags: [],
    location: '',
    imagePaths: []
  })

  const selectedPlatforms = ref([5])
  const platformSelectedAccounts = reactive({})  // { 5: [{...}], 7: [...] }
  const fileList = ref([])

  // 清空
  const reset = () => {
    form.title = ''
    form.content = ''
    form.tags = []
    form.location = ''
    form.imagePaths = []
    selectedPlatforms.value = [5]
    Object.keys(platformSelectedAccounts).forEach(k => delete platformSelectedAccounts[k])
    fileList.value = []
  }

  return {
    form, selectedPlatforms, platformSelectedAccounts, fileList, reset
  }
})
