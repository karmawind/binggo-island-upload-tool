import { http } from '@/utils/request'

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

  // 从素材库复制图片到图文图片目录
  copyMaterialToImage(filePath) {
    return http.post('/copyMaterialToImage', { filePath })
  }
}
