import { http } from '@/utils/request'
import request from '@/utils/request'

export const articleApi = {
  // 上传图片
  uploadImage(formData, onUploadProgress) {
    return http.upload('/uploadImage', formData, onUploadProgress)
  },

  // 获取所有图片
  getImages() {
    return http.get('/getImages')
  },

  // 删除图片
  deleteImage(id) {
    return http.get(`/deleteImage?id=${id}`)
  },

  // 发布图文文章
  publishArticle(data) {
    return http.post('/postArticle', data)
  },

  // 发布视频
  publishVideo(data) {
    return http.post('/postVideo', data)
  },

  // 查询发布任务状态
  getTaskStatus(taskId) {
    return http.get(`/articleTaskStatus?taskId=${taskId}`)
  },

  // 获取所有帖子
  getPosts() {
    return http.get('/getArticlePosts')
  },

  // 保存帖子（新建草稿）
  savePost(data) {
    return http.post('/saveArticlePost', data)
  },

  // 更新帖子
  updatePost(data) {
    return http.post('/updateArticlePost', data)
  },

  // 删除帖子
  deletePost(id) {
    return http.get(`/deleteArticlePost?id=${id}`)
  },

  // 批量排期
  scheduleArticles(data) {
    return http.post('/scheduleArticles', data)
  },

  // 导入 CSV
  importArticles(formData) {
    return http.upload('/importArticles', formData)
  },

  // 下载 CSV 导入模板
  async downloadTemplate() {
    const res = await request.get('/downloadArticleTemplate', { responseType: 'blob' })
    const blob = new Blob([res], { type: 'text/csv;charset=utf-8-sig' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = 'article_template.csv'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(link.href)
  },

  // 从素材库复制图片到图文图片目录
  copyMaterialToImage(filePath) {
    return http.post('/copyMaterialToImage', { filePath })
  }
}
