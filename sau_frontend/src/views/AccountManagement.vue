<template>
  <div class="account-management">
    <div class="page-header">
      <h1>账号管理</h1>
    </div>
    
    <div class="account-tabs">
      <el-tabs v-model="activeTab" class="account-tabs-nav">
        <el-tab-pane label="全部" name="all">
          <div class="account-list-container">
            <div class="account-search">
              <el-input
                v-model="searchKeyword"
                placeholder="输入名称或账号搜索"
                prefix-icon="Search"
                clearable
                @clear="handleSearch"
                @input="handleSearch"
              />
              <el-select v-model="filterGroup" placeholder="运营者" clearable filterable style="width: 130px">
                <el-option v-for="g in accountStore.groups" :key="g.id" :label="g.name" :value="g.name" />
              </el-select>
              <div class="action-buttons">
                <el-button plain @click="showOperatorDialog">运营者管理</el-button>
                <el-button type="primary" @click="handleAddAccount">添加账号</el-button>
                <el-button type="info" @click="fetchAccounts" :loading="false">
                  <el-icon :class="{ 'is-loading': appStore.isAccountRefreshing }"><Refresh /></el-icon>
                  <span v-if="appStore.isAccountRefreshing">刷新中</span>
                </el-button>
              </div>
            </div>
            
            <div v-if="filteredAccounts.length > 0" class="account-list">
              <el-table :data="filteredAccounts" style="width: 100%">
                <el-table-column label="头像" width="80">
                  <template #default="scope">
                    <el-avatar :src="getDefaultAvatar(scope.row.name)" :size="40" />
                  </template>
                </el-table-column>
                <el-table-column prop="name" label="名称" width="180" />
                <el-table-column prop="platform" label="平台">
                  <template #default="scope">
                    <el-tag
                      :type="getPlatformTagType(scope.row.platform)"
                      effect="plain"
                    >
                      {{ scope.row.platform }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="状态">
                  <template #default="scope">
                    <el-tag
                      :type="getStatusTagType(scope.row.status)"
                      effect="plain"
                      :class="{'clickable-status': isStatusClickable(scope.row.status)}"
                      @click="handleStatusClick(scope.row)"
                    >
                      <el-icon :class="scope.row.status === '验证中' ? 'is-loading' : ''" v-if="scope.row.status === '验证中'">
                        <Loading />
                      </el-icon>
                      {{ scope.row.status }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="运营者" width="140">
                  <template #default="scope">
                    <el-select
                      v-model="scope.row.group"
                      placeholder="未分组"
                      clearable
                      filterable
                      size="small"
                      style="width: 110px"
                      @change="handleGroupChange(scope.row)"
                    >
                      <el-option v-for="g in accountStore.groups" :key="g.id" :label="g.name" :value="g.name" />
                    </el-select>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="200">
                  <template #default="scope">
                    <div class="action-cell">
                      <el-button size="small" @click="handleEdit(scope.row)">编辑</el-button>
                      <el-button size="small" type="warning" plain @click="handleReLogin(scope.row)">重新认证</el-button>
                      <el-dropdown trigger="click">
                        <el-button size="small" :icon="More" circle />
                        <template #dropdown>
                          <el-dropdown-menu>
                            <el-dropdown-item @click="handleDownloadCookie(scope.row)">
                              <el-icon><Download /></el-icon>下载Cookie
                            </el-dropdown-item>
                            <el-dropdown-item @click="handleUploadCookie(scope.row)">
                              <el-icon><Upload /></el-icon>上传Cookie
                            </el-dropdown-item>
                            <el-dropdown-item divided @click="handleDelete(scope.row)" style="color: #ef4444">
                              删除
                            </el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <div v-else class="empty-data">
              <el-empty description="暂无账号数据" />
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="快手" name="kuaishou">
          <div class="account-list-container">
            <div class="account-search">
              <el-input
                v-model="searchKeyword"
                placeholder="输入名称或账号搜索"
                prefix-icon="Search"
                clearable
                @clear="handleSearch"
                @input="handleSearch"
              />
              <div class="action-buttons">
                <el-button type="primary" @click="handleAddAccount">添加账号</el-button>
                <el-button type="info" @click="fetchAccounts" :loading="false">
                  <el-icon :class="{ 'is-loading': appStore.isAccountRefreshing }"><Refresh /></el-icon>
                  <span v-if="appStore.isAccountRefreshing">刷新中</span>
                </el-button>
              </div>
            </div>
            
            <div v-if="filteredKuaishouAccounts.length > 0" class="account-list">
              <el-table :data="filteredKuaishouAccounts" style="width: 100%">
                <el-table-column label="头像" width="80">
                  <template #default="scope">
                    <el-avatar :src="getDefaultAvatar(scope.row.name)" :size="40" />
                  </template>
                </el-table-column>
                <el-table-column prop="name" label="名称" width="180" />
                <el-table-column prop="platform" label="平台">
                  <template #default="scope">
                    <el-tag
                      :type="getPlatformTagType(scope.row.platform)"
                      effect="plain"
                    >
                      {{ scope.row.platform }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="状态">
                  <template #default="scope">
                    <el-tag
                      :type="getStatusTagType(scope.row.status)"
                      effect="plain"
                      :class="{'clickable-status': isStatusClickable(scope.row.status)}"
                      @click="handleStatusClick(scope.row)"
                    >
                      <el-icon :class="scope.row.status === '验证中' ? 'is-loading' : ''" v-if="scope.row.status === '验证中'">
                        <Loading />
                      </el-icon>
                      {{ scope.row.status }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="200">
                  <template #default="scope">
                    <div class="action-cell">
                      <el-button size="small" @click="handleEdit(scope.row)">编辑</el-button>
                      <el-button size="small" type="warning" plain @click="handleReLogin(scope.row)">重新认证</el-button>
                      <el-dropdown trigger="click">
                        <el-button size="small" :icon="More" circle />
                        <template #dropdown>
                          <el-dropdown-menu>
                            <el-dropdown-item @click="handleDownloadCookie(scope.row)">
                              <el-icon><Download /></el-icon>下载Cookie
                            </el-dropdown-item>
                            <el-dropdown-item @click="handleUploadCookie(scope.row)">
                              <el-icon><Upload /></el-icon>上传Cookie
                            </el-dropdown-item>
                            <el-dropdown-item divided @click="handleDelete(scope.row)" style="color: #ef4444">
                              删除
                            </el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <div v-else class="empty-data">
              <el-empty description="暂无快手账号数据" />
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="抖音" name="douyin">
          <div class="account-list-container">
            <div class="account-search">
              <el-input
                v-model="searchKeyword"
                placeholder="输入名称或账号搜索"
                prefix-icon="Search"
                clearable
                @clear="handleSearch"
                @input="handleSearch"
              />
              <div class="action-buttons">
                <el-button type="primary" @click="handleAddAccount">添加账号</el-button>
                <el-button type="info" @click="fetchAccounts" :loading="false">
                  <el-icon :class="{ 'is-loading': appStore.isAccountRefreshing }"><Refresh /></el-icon>
                  <span v-if="appStore.isAccountRefreshing">刷新中</span>
                </el-button>
              </div>
            </div>
            
            <div v-if="filteredDouyinAccounts.length > 0" class="account-list">
              <el-table :data="filteredDouyinAccounts" style="width: 100%">
                <el-table-column label="头像" width="80">
                  <template #default="scope">
                    <el-avatar :src="getDefaultAvatar(scope.row.name)" :size="40" />
                  </template>
                </el-table-column>
                <el-table-column prop="name" label="名称" width="180" />
                <el-table-column prop="platform" label="平台">
                  <template #default="scope">
                    <el-tag
                      :type="getPlatformTagType(scope.row.platform)"
                      effect="plain"
                    >
                      {{ scope.row.platform }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="状态">
                  <template #default="scope">
                    <el-tag
                      :type="getStatusTagType(scope.row.status)"
                      effect="plain"
                      :class="{'clickable-status': isStatusClickable(scope.row.status)}"
                      @click="handleStatusClick(scope.row)"
                    >
                      <el-icon :class="scope.row.status === '验证中' ? 'is-loading' : ''" v-if="scope.row.status === '验证中'">
                        <Loading />
                      </el-icon>
                      {{ scope.row.status }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="200">
                  <template #default="scope">
                    <div class="action-cell">
                      <el-button size="small" @click="handleEdit(scope.row)">编辑</el-button>
                      <el-button size="small" type="warning" plain @click="handleReLogin(scope.row)">重新认证</el-button>
                      <el-dropdown trigger="click">
                        <el-button size="small" :icon="More" circle />
                        <template #dropdown>
                          <el-dropdown-menu>
                            <el-dropdown-item @click="handleDownloadCookie(scope.row)">
                              <el-icon><Download /></el-icon>下载Cookie
                            </el-dropdown-item>
                            <el-dropdown-item @click="handleUploadCookie(scope.row)">
                              <el-icon><Upload /></el-icon>上传Cookie
                            </el-dropdown-item>
                            <el-dropdown-item divided @click="handleDelete(scope.row)" style="color: #ef4444">
                              删除
                            </el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <div v-else class="empty-data">
              <el-empty description="暂无抖音账号数据" />
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="视频号" name="channels">
          <div class="account-list-container">
            <div class="account-search">
              <el-input
                v-model="searchKeyword"
                placeholder="输入名称或账号搜索"
                prefix-icon="Search"
                clearable
                @clear="handleSearch"
                @input="handleSearch"
              />
              <div class="action-buttons">
                <el-button type="primary" @click="handleAddAccount">添加账号</el-button>
                <el-button type="info" @click="fetchAccounts" :loading="false">
                  <el-icon :class="{ 'is-loading': appStore.isAccountRefreshing }"><Refresh /></el-icon>
                  <span v-if="appStore.isAccountRefreshing">刷新中</span>
                </el-button>
              </div>
            </div>
            
            <div v-if="filteredChannelsAccounts.length > 0" class="account-list">
              <el-table :data="filteredChannelsAccounts" style="width: 100%">
                <el-table-column label="头像" width="80">
                  <template #default="scope">
                    <el-avatar :src="getDefaultAvatar(scope.row.name)" :size="40" />
                  </template>
                </el-table-column>
                <el-table-column prop="name" label="名称" width="180" />
                <el-table-column prop="platform" label="平台">
                  <template #default="scope">
                    <el-tag
                      :type="getPlatformTagType(scope.row.platform)"
                      effect="plain"
                    >
                      {{ scope.row.platform }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="状态">
                  <template #default="scope">
                    <el-tag
                      :type="getStatusTagType(scope.row.status)"
                      effect="plain"
                      :class="{'clickable-status': isStatusClickable(scope.row.status)}"
                      @click="handleStatusClick(scope.row)"
                    >
                      <el-icon :class="scope.row.status === '验证中' ? 'is-loading' : ''" v-if="scope.row.status === '验证中'">
                        <Loading />
                      </el-icon>
                      {{ scope.row.status }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="200">
                  <template #default="scope">
                    <div class="action-cell">
                      <el-button size="small" @click="handleEdit(scope.row)">编辑</el-button>
                      <el-button size="small" type="warning" plain @click="handleReLogin(scope.row)">重新认证</el-button>
                      <el-dropdown trigger="click">
                        <el-button size="small" :icon="More" circle />
                        <template #dropdown>
                          <el-dropdown-menu>
                            <el-dropdown-item @click="handleDownloadCookie(scope.row)">
                              <el-icon><Download /></el-icon>下载Cookie
                            </el-dropdown-item>
                            <el-dropdown-item @click="handleUploadCookie(scope.row)">
                              <el-icon><Upload /></el-icon>上传Cookie
                            </el-dropdown-item>
                            <el-dropdown-item divided @click="handleDelete(scope.row)" style="color: #ef4444">
                              删除
                            </el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <div v-else class="empty-data">
              <el-empty description="暂无视频号账号数据" />
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="小红书" name="xiaohongshu">
          <div class="account-list-container">
            <div class="account-search">
              <el-input
                v-model="searchKeyword"
                placeholder="输入名称或账号搜索"
                prefix-icon="Search"
                clearable
                @clear="handleSearch"
                @input="handleSearch"
              />
              <div class="action-buttons">
                <el-button type="primary" @click="handleAddAccount">添加账号</el-button>
                <el-button type="info" @click="fetchAccounts" :loading="false">
                  <el-icon :class="{ 'is-loading': appStore.isAccountRefreshing }"><Refresh /></el-icon>
                  <span v-if="appStore.isAccountRefreshing">刷新中</span>
                </el-button>
              </div>
            </div>
            
            <div v-if="filteredXiaohongshuAccounts.length > 0" class="account-list">
              <el-table :data="filteredXiaohongshuAccounts" style="width: 100%">
                <el-table-column label="头像" width="80">
                  <template #default="scope">
                    <el-avatar :src="getDefaultAvatar(scope.row.name)" :size="40" />
                  </template>
                </el-table-column>
                <el-table-column prop="name" label="名称" width="180" />
                <el-table-column prop="platform" label="平台">
                  <template #default="scope">
                    <el-tag
                      :type="getPlatformTagType(scope.row.platform)"
                      effect="plain"
                    >
                      {{ scope.row.platform }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="状态">
                  <template #default="scope">
                    <el-tag
                      :type="getStatusTagType(scope.row.status)"
                      effect="plain"
                      :class="{'clickable-status': isStatusClickable(scope.row.status)}"
                      @click="handleStatusClick(scope.row)"
                    >
                      <el-icon :class="scope.row.status === '验证中' ? 'is-loading' : ''" v-if="scope.row.status === '验证中'">
                        <Loading />
                      </el-icon>
                      {{ scope.row.status }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="200">
                  <template #default="scope">
                    <div class="action-cell">
                      <el-button size="small" @click="handleEdit(scope.row)">编辑</el-button>
                      <el-button size="small" type="warning" plain @click="handleReLogin(scope.row)">重新认证</el-button>
                      <el-dropdown trigger="click">
                        <el-button size="small" :icon="More" circle />
                        <template #dropdown>
                          <el-dropdown-menu>
                            <el-dropdown-item @click="handleDownloadCookie(scope.row)">
                              <el-icon><Download /></el-icon>下载Cookie
                            </el-dropdown-item>
                            <el-dropdown-item @click="handleUploadCookie(scope.row)">
                              <el-icon><Upload /></el-icon>上传Cookie
                            </el-dropdown-item>
                            <el-dropdown-item divided @click="handleDelete(scope.row)" style="color: #ef4444">
                              删除
                            </el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <div v-else class="empty-data">
              <el-empty description="暂无小红书账号数据" />
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="百家号" name="baijiahao">
          <div class="account-list-container">
            <div class="account-search">
              <el-input v-model="searchKeyword" placeholder="输入名称或账号搜索" prefix-icon="Search" clearable @clear="handleSearch" @input="handleSearch" />
              <div class="action-buttons">
                <el-button type="primary" @click="handleAddAccount">添加账号</el-button>
                <el-button type="info" @click="fetchAccounts" :loading="false">
                  <el-icon :class="{ 'is-loading': appStore.isAccountRefreshing }"><Refresh /></el-icon>
                  <span v-if="appStore.isAccountRefreshing">刷新中</span>
                </el-button>
              </div>
            </div>
            <div v-if="filteredBaijiahaoAccounts.length > 0" class="account-list">
              <el-table :data="filteredBaijiahaoAccounts" style="width: 100%">
                <el-table-column label="头像" width="80"><template #default="scope"><el-avatar :src="getDefaultAvatar(scope.row.name)" :size="40" /></template></el-table-column>
                <el-table-column prop="name" label="名称" width="180" />
                <el-table-column prop="platform" label="平台"><template #default="scope"><el-tag :type="getPlatformTagType(scope.row.platform)" effect="plain">{{ scope.row.platform }}</el-tag></template></el-table-column>
                <el-table-column prop="status" label="状态"><template #default="scope"><el-tag :type="getStatusTagType(scope.row.status)" effect="plain" :class="{'clickable-status': isStatusClickable(scope.row.status)}" @click="handleStatusClick(scope.row)"><el-icon :class="scope.row.status === '验证中' ? 'is-loading' : ''" v-if="scope.row.status === '验证中'"><Loading /></el-icon>{{ scope.row.status }}</el-tag></template></el-table-column>
                <el-table-column label="操作" width="160"><template #default="scope">
                    <div class="action-cell">
                      <el-button size="small" @click="handleEdit(scope.row)">编辑</el-button>
                      <el-dropdown trigger="click">
                        <el-button size="small" :icon="More" circle />
                        <template #dropdown>
                          <el-dropdown-menu>
                            <el-dropdown-item @click="handleDownloadCookie(scope.row)">
                              <el-icon><Download /></el-icon>下载Cookie
                            </el-dropdown-item>
                            <el-dropdown-item @click="handleUploadCookie(scope.row)">
                              <el-icon><Upload /></el-icon>上传Cookie
                            </el-dropdown-item>
                            <el-dropdown-item divided @click="handleDelete(scope.row)" style="color: #ef4444">
                              删除
                            </el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                    </div>
                </template></el-table-column>
              </el-table>
            </div>
            <div v-else class="empty-data"><el-empty description="暂无百家号账号数据" /></div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="什么值得买" name="smzdm">
          <div class="account-list-container">
            <div class="account-search">
              <el-input v-model="searchKeyword" placeholder="输入名称或账号搜索" prefix-icon="Search" clearable @clear="handleSearch" @input="handleSearch" />
              <div class="action-buttons">
                <el-button type="primary" @click="handleAddAccount">添加账号</el-button>
                <el-button type="info" @click="fetchAccounts" :loading="false">
                  <el-icon :class="{ 'is-loading': appStore.isAccountRefreshing }"><Refresh /></el-icon>
                  <span v-if="appStore.isAccountRefreshing">刷新中</span>
                </el-button>
              </div>
            </div>
            <div v-if="filteredSmzdmAccounts.length > 0" class="account-list">
              <el-table :data="filteredSmzdmAccounts" style="width: 100%">
                <el-table-column label="头像" width="80"><template #default="scope"><el-avatar :src="getDefaultAvatar(scope.row.name)" :size="40" /></template></el-table-column>
                <el-table-column prop="name" label="名称" width="180" />
                <el-table-column prop="platform" label="平台"><template #default="scope"><el-tag :type="getPlatformTagType(scope.row.platform)" effect="plain">{{ scope.row.platform }}</el-tag></template></el-table-column>
                <el-table-column prop="status" label="状态"><template #default="scope"><el-tag :type="getStatusTagType(scope.row.status)" effect="plain" :class="{'clickable-status': isStatusClickable(scope.row.status)}" @click="handleStatusClick(scope.row)"><el-icon :class="scope.row.status === '验证中' ? 'is-loading' : ''" v-if="scope.row.status === '验证中'"><Loading /></el-icon>{{ scope.row.status }}</el-tag></template></el-table-column>
                <el-table-column label="操作" width="160"><template #default="scope">
                    <div class="action-cell">
                      <el-button size="small" @click="handleEdit(scope.row)">编辑</el-button>
                      <el-dropdown trigger="click">
                        <el-button size="small" :icon="More" circle />
                        <template #dropdown>
                          <el-dropdown-menu>
                            <el-dropdown-item @click="handleDownloadCookie(scope.row)">
                              <el-icon><Download /></el-icon>下载Cookie
                            </el-dropdown-item>
                            <el-dropdown-item @click="handleUploadCookie(scope.row)">
                              <el-icon><Upload /></el-icon>上传Cookie
                            </el-dropdown-item>
                            <el-dropdown-item divided @click="handleDelete(scope.row)" style="color: #ef4444">
                              删除
                            </el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                    </div>
                </template></el-table-column>
              </el-table>
            </div>
            <div v-else class="empty-data"><el-empty description="暂无什么值得买账号数据" /></div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="头条号" name="toutiao">
          <div class="account-list-container">
            <div class="account-search">
              <el-input v-model="searchKeyword" placeholder="输入名称或账号搜索" prefix-icon="Search" clearable @clear="handleSearch" @input="handleSearch" />
              <div class="action-buttons">
                <el-button type="primary" @click="handleAddAccount">添加账号</el-button>
                <el-button type="info" @click="fetchAccounts" :loading="false">
                  <el-icon :class="{ 'is-loading': appStore.isAccountRefreshing }"><Refresh /></el-icon>
                  <span v-if="appStore.isAccountRefreshing">刷新中</span>
                </el-button>
              </div>
            </div>
            <div v-if="filteredToutiaoAccounts.length > 0" class="account-list">
              <el-table :data="filteredToutiaoAccounts" style="width: 100%">
                <el-table-column label="头像" width="80"><template #default="scope"><el-avatar :src="getDefaultAvatar(scope.row.name)" :size="40" /></template></el-table-column>
                <el-table-column prop="name" label="名称" width="180" />
                <el-table-column prop="platform" label="平台"><template #default="scope"><el-tag :type="getPlatformTagType(scope.row.platform)" effect="plain">{{ scope.row.platform }}</el-tag></template></el-table-column>
                <el-table-column prop="status" label="状态"><template #default="scope"><el-tag :type="getStatusTagType(scope.row.status)" effect="plain" :class="{'clickable-status': isStatusClickable(scope.row.status)}" @click="handleStatusClick(scope.row)"><el-icon :class="scope.row.status === '验证中' ? 'is-loading' : ''" v-if="scope.row.status === '验证中'"><Loading /></el-icon>{{ scope.row.status }}</el-tag></template></el-table-column>
                <el-table-column label="操作" width="160"><template #default="scope">
                    <div class="action-cell">
                      <el-button size="small" @click="handleEdit(scope.row)">编辑</el-button>
                      <el-dropdown trigger="click">
                        <el-button size="small" :icon="More" circle />
                        <template #dropdown>
                          <el-dropdown-menu>
                            <el-dropdown-item @click="handleDownloadCookie(scope.row)">
                              <el-icon><Download /></el-icon>下载Cookie
                            </el-dropdown-item>
                            <el-dropdown-item @click="handleUploadCookie(scope.row)">
                              <el-icon><Upload /></el-icon>上传Cookie
                            </el-dropdown-item>
                            <el-dropdown-item divided @click="handleDelete(scope.row)" style="color: #ef4444">
                              删除
                            </el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                    </div>
                </template></el-table-column>
              </el-table>
            </div>
            <div v-else class="empty-data"><el-empty description="暂无头条号账号数据" /></div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="携程" name="ctrip">
          <div class="account-list-container">
            <div class="account-search">
              <el-input v-model="searchKeyword" placeholder="输入名称或账号搜索" prefix-icon="Search" clearable @clear="handleSearch" @input="handleSearch" />
              <div class="action-buttons">
                <el-button type="primary" @click="handleAddAccount">添加账号</el-button>
                <el-button type="info" @click="fetchAccounts" :loading="false">
                  <el-icon :class="{ 'is-loading': appStore.isAccountRefreshing }"><Refresh /></el-icon>
                  <span v-if="appStore.isAccountRefreshing">刷新中</span>
                </el-button>
              </div>
            </div>
            <div v-if="filteredCtripAccounts.length > 0" class="account-list">
              <el-table :data="filteredCtripAccounts" style="width: 100%">
                <el-table-column label="头像" width="80"><template #default="scope"><el-avatar :src="getDefaultAvatar(scope.row.name)" :size="40" /></template></el-table-column>
                <el-table-column prop="name" label="名称" width="180" />
                <el-table-column prop="platform" label="平台"><template #default="scope"><el-tag :type="getPlatformTagType(scope.row.platform)" effect="plain">{{ scope.row.platform }}</el-tag></template></el-table-column>
                <el-table-column prop="status" label="状态"><template #default="scope"><el-tag :type="getStatusTagType(scope.row.status)" effect="plain" :class="{'clickable-status': isStatusClickable(scope.row.status)}" @click="handleStatusClick(scope.row)"><el-icon :class="scope.row.status === '验证中' ? 'is-loading' : ''" v-if="scope.row.status === '验证中'"><Loading /></el-icon>{{ scope.row.status }}</el-tag></template></el-table-column>
                <el-table-column label="操作" width="160"><template #default="scope">
                    <div class="action-cell">
                      <el-button size="small" @click="handleEdit(scope.row)">编辑</el-button>
                      <el-dropdown trigger="click">
                        <el-button size="small" :icon="More" circle />
                        <template #dropdown>
                          <el-dropdown-menu>
                            <el-dropdown-item @click="handleDownloadCookie(scope.row)">
                              <el-icon><Download /></el-icon>下载Cookie
                            </el-dropdown-item>
                            <el-dropdown-item @click="handleUploadCookie(scope.row)">
                              <el-icon><Upload /></el-icon>上传Cookie
                            </el-dropdown-item>
                            <el-dropdown-item divided @click="handleDelete(scope.row)" style="color: #ef4444">
                              删除
                            </el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                    </div>
                </template></el-table-column>
              </el-table>
            </div>
            <div v-else class="empty-data"><el-empty description="暂无携程账号数据" /></div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="搜狐号" name="sohu">
          <div class="account-list-container">
            <div class="account-search">
              <el-input v-model="searchKeyword" placeholder="输入名称或账号搜索" prefix-icon="Search" clearable @clear="handleSearch" @input="handleSearch" />
              <div class="action-buttons">
                <el-button type="primary" @click="handleAddAccount">添加账号</el-button>
                <el-button type="info" @click="fetchAccounts" :loading="false">
                  <el-icon :class="{ 'is-loading': appStore.isAccountRefreshing }"><Refresh /></el-icon>
                  <span v-if="appStore.isAccountRefreshing">刷新中</span>
                </el-button>
              </div>
            </div>
            <div v-if="filteredSohuAccounts.length > 0" class="account-list">
              <el-table :data="filteredSohuAccounts" style="width: 100%">
                <el-table-column label="头像" width="80"><template #default="scope"><el-avatar :src="getDefaultAvatar(scope.row.name)" :size="40" /></template></el-table-column>
                <el-table-column prop="name" label="名称" width="180" />
                <el-table-column prop="platform" label="平台"><template #default="scope"><el-tag :type="getPlatformTagType(scope.row.platform)" effect="plain">{{ scope.row.platform }}</el-tag></template></el-table-column>
                <el-table-column prop="status" label="状态"><template #default="scope"><el-tag :type="getStatusTagType(scope.row.status)" effect="plain" :class="{'clickable-status': isStatusClickable(scope.row.status)}" @click="handleStatusClick(scope.row)"><el-icon :class="scope.row.status === '验证中' ? 'is-loading' : ''" v-if="scope.row.status === '验证中'"><Loading /></el-icon>{{ scope.row.status }}</el-tag></template></el-table-column>
                <el-table-column label="操作" width="160"><template #default="scope">
                    <div class="action-cell">
                      <el-button size="small" @click="handleEdit(scope.row)">编辑</el-button>
                      <el-dropdown trigger="click">
                        <el-button size="small" :icon="More" circle />
                        <template #dropdown>
                          <el-dropdown-menu>
                            <el-dropdown-item @click="handleDownloadCookie(scope.row)">
                              <el-icon><Download /></el-icon>下载Cookie
                            </el-dropdown-item>
                            <el-dropdown-item @click="handleUploadCookie(scope.row)">
                              <el-icon><Upload /></el-icon>上传Cookie
                            </el-dropdown-item>
                            <el-dropdown-item divided @click="handleDelete(scope.row)" style="color: #ef4444">
                              删除
                            </el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                    </div>
                </template></el-table-column>
              </el-table>
            </div>
            <div v-else class="empty-data"><el-empty description="暂无搜狐号账号数据" /></div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="微博" name="weibo">
          <div class="account-list-container">
            <div class="account-search">
              <el-input v-model="searchKeyword" placeholder="输入名称或账号搜索" prefix-icon="Search" clearable @clear="handleSearch" @input="handleSearch" />
              <div class="action-buttons">
                <el-button type="primary" @click="handleAddAccount">添加账号</el-button>
                <el-button type="info" @click="fetchAccounts" :loading="false">
                  <el-icon :class="{ 'is-loading': appStore.isAccountRefreshing }"><Refresh /></el-icon>
                  <span v-if="appStore.isAccountRefreshing">刷新中</span>
                </el-button>
              </div>
            </div>
            <div v-if="filteredWeiboAccounts.length > 0" class="account-list">
              <el-table :data="filteredWeiboAccounts" style="width: 100%">
                <el-table-column label="头像" width="80"><template #default="scope"><el-avatar :src="getDefaultAvatar(scope.row.name)" :size="40" /></template></el-table-column>
                <el-table-column prop="name" label="名称" width="180" />
                <el-table-column prop="platform" label="平台"><template #default="scope"><el-tag :type="getPlatformTagType(scope.row.platform)" effect="plain">{{ scope.row.platform }}</el-tag></template></el-table-column>
                <el-table-column prop="status" label="状态"><template #default="scope"><el-tag :type="getStatusTagType(scope.row.status)" effect="plain" :class="{'clickable-status': isStatusClickable(scope.row.status)}" @click="handleStatusClick(scope.row)"><el-icon :class="scope.row.status === '验证中' ? 'is-loading' : ''" v-if="scope.row.status === '验证中'"><Loading /></el-icon>{{ scope.row.status }}</el-tag></template></el-table-column>
                <el-table-column label="操作" width="160"><template #default="scope">
                    <div class="action-cell">
                      <el-button size="small" @click="handleEdit(scope.row)">编辑</el-button>
                      <el-dropdown trigger="click">
                        <el-button size="small" :icon="More" circle />
                        <template #dropdown>
                          <el-dropdown-menu>
                            <el-dropdown-item @click="handleDownloadCookie(scope.row)">
                              <el-icon><Download /></el-icon>下载Cookie
                            </el-dropdown-item>
                            <el-dropdown-item @click="handleUploadCookie(scope.row)">
                              <el-icon><Upload /></el-icon>上传Cookie
                            </el-dropdown-item>
                            <el-dropdown-item divided @click="handleDelete(scope.row)" style="color: #ef4444">
                              删除
                            </el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                    </div>
                </template></el-table-column>
              </el-table>
            </div>
            <div v-else class="empty-data"><el-empty description="暂无微博账号数据" /></div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
    
    <!-- 添加/编辑账号对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'add' ? '添加账号' : '编辑账号'"
      width="500px"
      :close-on-click-modal="false"
      :close-on-press-escape="!sseConnecting"
      :show-close="!sseConnecting"
    >
      <el-form :model="accountForm" label-width="80px" :rules="rules" ref="accountFormRef">
        <el-form-item label="平台" prop="platform">
          <el-select
            v-model="accountForm.platform"
            placeholder="请选择平台"
            style="width: 100%"
            :disabled="dialogType === 'edit' || sseConnecting"
            popper-class="account-platform-select"
          >
            <el-option label="快手" value="快手" />
            <el-option label="抖音" value="抖音" />
            <el-option label="视频号" value="视频号" />
            <el-option label="小红书" value="小红书" />
            <el-option label="百家号" value="百家号" />
            <el-option label="什么值得买" value="什么值得买" />
            <el-option label="头条号" value="头条号" />
            <el-option label="携程" value="携程" />
            <el-option label="搜狐号" value="搜狐号" />
            <el-option label="微博" value="微博" />
          </el-select>
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input
            v-model="accountForm.name"
            placeholder="请输入账号名称"
            :disabled="sseConnecting"
          />
        </el-form-item>
        <el-form-item label="运营者">
          <el-select
            v-model="accountForm.group"
            placeholder="选择运营者"
            clearable
            filterable
            style="width: 100%"
            :disabled="sseConnecting"
          >
            <el-option v-for="g in accountStore.groups" :key="g.id" :label="g.name" :value="g.name" />
          </el-select>
        </el-form-item>
        
        <!-- 二维码 / 登录引导显示区域 -->
        <div v-if="sseConnecting" class="qrcode-container">
          <!-- 视频平台：二维码 -->
          <div v-if="qrCodeData && !loginStatus" class="qrcode-wrapper">
            <p class="qrcode-tip">请使用对应平台APP扫描二维码登录</p>
            <img :src="qrCodeData" alt="登录二维码" class="qrcode-image" />
          </div>
          <!-- 图文平台：文字引导消息 -->
          <div v-else-if="loginMessages.length > 0 && !loginStatus" class="guide-wrapper">
            <el-icon class="is-loading" style="font-size: 32px; margin-bottom: 12px"><Refresh /></el-icon>
            <div class="guide-messages">
              <p v-for="(msg, idx) in loginMessages" :key="idx" class="guide-msg">{{ msg }}</p>
            </div>
            <p class="guide-tip">请在弹出的浏览器窗口中完成登录</p>
          </div>
          <!-- 等待中 -->
          <div v-else-if="!qrCodeData && !loginStatus && loginMessages.length === 0" class="loading-wrapper">
            <el-icon class="is-loading"><Refresh /></el-icon>
            <span>正在启动浏览器...</span>
          </div>
          <!-- 成功 -->
          <div v-else-if="loginStatus === '200'" class="success-wrapper">
            <el-icon><CircleCheckFilled /></el-icon>
            <span>{{ loginMessages.length ? '登录成功，账号已自动创建' : '添加成功' }}</span>
          </div>
          <!-- 失败 -->
          <div v-else-if="loginStatus === '500'" class="error-wrapper">
            <el-icon><CircleCloseFilled /></el-icon>
            <span>添加失败，请稍后再试</span>
          </div>
        </div>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="submitAccountForm" 
            :loading="sseConnecting" 
            :disabled="sseConnecting"
          >
            {{ sseConnecting ? '请求中' : '确认' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 运营者管理弹窗 -->
    <el-dialog v-model="operatorDialogVisible" title="运营者管理" width="450px">
      <div class="operator-add">
        <el-input v-model="newOperatorName" placeholder="输入运营者名称" style="flex: 1" @keyup.enter="addOperator" />
        <el-button type="primary" @click="addOperator" :disabled="!newOperatorName.trim()">添加</el-button>
      </div>
      <el-table :data="accountStore.groups" style="width: 100%; margin-top: 16px" max-height="400">
        <el-table-column prop="name" label="运营者名称" />
        <el-table-column label="关联账号" width="100">
          <template #default="scope">
            {{ accountStore.accounts.filter(a => a.group === scope.row.name).length }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140">
          <template #default="scope">
            <el-button size="small" @click="startRenameOperator(scope.row)">重命名</el-button>
            <el-button size="small" type="danger" @click="deleteOperator(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="!accountStore.groups.length" style="text-align: center; padding: 20px; color: #909399">
        暂无运营者，请在上方输入名称添加
      </div>
    </el-dialog>

    <!-- 重命名运营者弹窗 -->
    <el-dialog v-model="renameDialogVisible" title="重命名运营者" width="350px">
      <el-input v-model="renameNewName" placeholder="输入新名称" @keyup.enter="confirmRename" />
      <template #footer>
        <el-button @click="renameDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmRename">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { Refresh, CircleCheckFilled, CircleCloseFilled, Download, Upload, Loading, More } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { accountApi } from '@/api/account'
import { useAccountStore } from '@/stores/account'
import { useAppStore } from '@/stores/app'
import { http } from '@/utils/request'

// 获取账号状态管理
const accountStore = useAccountStore()
// 获取应用状态管理
const appStore = useAppStore()

// 当前激活的标签页
const activeTab = ref('all')

// 搜索关键词
const searchKeyword = ref('')
// 运营者分组筛选
const filterGroup = ref('')

// 运营者管理
const operatorDialogVisible = ref(false)
const newOperatorName = ref('')
const renameDialogVisible = ref(false)
const renameNewName = ref('')
const renamingOperator = ref(null)

const showOperatorDialog = () => {
  newOperatorName.value = ''
  operatorDialogVisible.value = true
}

const addOperator = async () => {
  const name = newOperatorName.value.trim()
  if (!name) return
  try {
    const res = await accountApi.addOperator({ name })
    if (res.code === 200) {
      ElMessage.success(`运营者「${name}」已添加`)
      newOperatorName.value = ''
      await accountStore.fetchGroups()
    } else {
      ElMessage.error(res.msg || '添加失败')
    }
  } catch { ElMessage.error('添加失败') }
}

const deleteOperator = async (op) => {
  const linkedCount = accountStore.accounts.filter(a => a.group === op.name).length
  try {
    const msg = linkedCount > 0
      ? `运营者「${op.name}」关联了 ${linkedCount} 个账号，删除后这些账号将变为未分组。确认删除？`
      : `确认删除运营者「${op.name}」？`
    await ElMessageBox.confirm(msg, '删除运营者', { type: 'warning' })
    const res = await accountApi.deleteOperator({ id: op.id, name: op.name })
    if (res.code === 200) {
      ElMessage.success('已删除')
      await accountStore.fetchGroups()
      fetchAccounts()
    } else {
      ElMessage.error(res.msg || '删除失败')
    }
  } catch { /* cancelled */ }
}

const startRenameOperator = (op) => {
  renamingOperator.value = op
  renameNewName.value = op.name
  renameDialogVisible.value = true
}

const confirmRename = async () => {
  const newName = renameNewName.value.trim()
  if (!newName || !renamingOperator.value) return
  try {
    const res = await accountApi.renameOperator({
      id: renamingOperator.value.id,
      old_name: renamingOperator.value.name,
      new_name: newName
    })
    if (res.code === 200) {
      ElMessage.success('重命名成功')
      renameDialogVisible.value = false
      await accountStore.fetchGroups()
      fetchAccounts()
    } else {
      ElMessage.error(res.msg || '重命名失败')
    }
  } catch { ElMessage.error('重命名失败') }
}

// 获取账号数据（快速，不验证）
const fetchAccountsQuick = async () => {
  try {
    const res = await accountApi.getAccounts()
    if (res.code === 200 && res.data) {
      // 将所有账号的状态暂时设为"验证中"
      const accountsWithPendingStatus = res.data.map(account => {
        const updatedAccount = [...account];
        updatedAccount[4] = -1; // -1 表示验证中的临时状态
        return updatedAccount;
      });
      accountStore.setAccounts(accountsWithPendingStatus);
    }
  } catch (error) {
    console.error('快速获取账号数据失败:', error)
  }
}

// 获取账号数据（带验证）
const fetchAccounts = async () => {
  if (appStore.isAccountRefreshing) return

  appStore.setAccountRefreshing(true)

  try {
    const res = await accountApi.getValidAccounts()
    if (res.code === 200 && res.data) {
      accountStore.setAccounts(res.data)
      ElMessage.success('账号数据获取成功')
      // 标记为已访问
      if (appStore.isFirstTimeAccountManagement) {
        appStore.setAccountManagementVisited()
      }
    } else {
      ElMessage.error('获取账号数据失败')
    }
  } catch (error) {
    console.error('获取账号数据失败:', error)
    ElMessage.error('获取账号数据失败')
  } finally {
    appStore.setAccountRefreshing(false)
  }
}

// 后台验证所有账号（优化版本，使用setTimeout避免阻塞UI）
const validateAllAccountsInBackground = async () => {
  // 使用setTimeout将验证过程放在下一个事件循环，避免阻塞UI
  setTimeout(async () => {
    try {
      const res = await accountApi.getValidAccounts()
      if (res.code === 200 && res.data) {
        accountStore.setAccounts(res.data)
      }
    } catch (error) {
      console.error('后台验证账号失败:', error)
    }
  }, 0)
}

// 页面加载时获取账号数据
onMounted(() => {
  // 快速获取账号列表（不验证），立即显示
  fetchAccountsQuick()

  // 获取运营者分组列表
  accountStore.fetchGroups()

  // 在后台验证所有账号
  setTimeout(() => {
    validateAllAccountsInBackground()
  }, 100) // 稍微延迟一下，让用户看到快速加载的效果
})

// 获取平台标签类型
const getPlatformTagType = (platform) => {
  const typeMap = {
    '快手': 'success',
    '抖音': 'danger',
    '视频号': 'warning',
    '小红书': 'info',
    '百家号': '',
    '什么值得买': 'danger',
    '头条号': 'warning',
    '携程': '',
    '搜狐号': 'info',
    '微博': 'warning'
  }
  return typeMap[platform] || 'info'
}

// 判断状态是否可点击（异常状态可点击）
const isStatusClickable = (status) => {
  return status === '异常'; // 只有异常状态可点击，验证中不可点击
}

// 获取状态标签类型
const getStatusTagType = (status) => {
  if (status === '验证中') {
    return 'info'; // 验证中使用灰色
  } else if (status === '正常') {
    return 'success'; // 正常使用绿色
  } else {
    return 'danger'; // 无效使用红色
  }
}

// 处理状态点击事件
const handleStatusClick = (row) => {
  if (isStatusClickable(row.status)) {
    // 触发重新登录流程
    handleReLogin(row)
  }
}

// 过滤后的账号列表
const filteredAccounts = computed(() => {
  let result = accountStore.accounts
  if (searchKeyword.value) {
    result = result.filter(account => account.name.includes(searchKeyword.value))
  }
  if (filterGroup.value) {
    result = result.filter(account => account.group === filterGroup.value)
  }
  return result
})

// 更新账号分组
const handleGroupChange = async (row) => {
  try {
    await accountApi.updateGroup({ id: row.id, group_name: row.group })
    // 刷新分组列表（可能新增了运营者名称）
    await accountStore.fetchGroups()
    ElMessage.success('分组已更新')
  } catch (error) {
    ElMessage.error('分组更新失败')
  }
}

// 按平台过滤的账号列表
const filteredKuaishouAccounts = computed(() => {
  return filteredAccounts.value.filter(account => account.platform === '快手')
})

const filteredDouyinAccounts = computed(() => {
  return filteredAccounts.value.filter(account => account.platform === '抖音')
})

const filteredChannelsAccounts = computed(() => {
  return filteredAccounts.value.filter(account => account.platform === '视频号')
})

const filteredXiaohongshuAccounts = computed(() => {
  return filteredAccounts.value.filter(account => account.platform === '小红书')
})

const filteredBaijiahaoAccounts = computed(() => {
  return filteredAccounts.value.filter(account => account.platform === '百家号')
})

const filteredSmzdmAccounts = computed(() => {
  return filteredAccounts.value.filter(account => account.platform === '什么值得买')
})

const filteredToutiaoAccounts = computed(() => {
  return filteredAccounts.value.filter(account => account.platform === '头条号')
})

const filteredCtripAccounts = computed(() => {
  return filteredAccounts.value.filter(account => account.platform === '携程')
})

const filteredSohuAccounts = computed(() => {
  return filteredAccounts.value.filter(account => account.platform === '搜狐号')
})

const filteredWeiboAccounts = computed(() => {
  return filteredAccounts.value.filter(account => account.platform === '微博')
})

// 搜索处理
const handleSearch = () => {
  // 搜索逻辑已通过计算属性实现
}

// 对话框相关
const dialogVisible = ref(false)
const dialogType = ref('add') // 'add' 或 'edit'
const accountFormRef = ref(null)

// 账号表单
const accountForm = reactive({
  id: null,
  name: '',
  platform: '',
  group: '',
  status: '正常'
})

// 表单验证规则
const rules = {
  platform: [{ required: true, message: '请选择平台', trigger: 'change' }],
  name: [{ required: true, message: '请输入账号名称', trigger: 'blur' }]
}

// SSE连接状态
const sseConnecting = ref(false)
const qrCodeData = ref('')
const loginStatus = ref('')
const loginMessages = ref([])  // 图文平台登录引导消息

// 添加账号
const handleAddAccount = () => {
  dialogType.value = 'add'
  Object.assign(accountForm, {
    id: null,
    name: '',
    platform: '',
    group: '',
    status: '正常'
  })
  // 重置SSE状态
  sseConnecting.value = false
  qrCodeData.value = ''
  loginStatus.value = ''
  loginMessages.value = []
  dialogVisible.value = true
}

// 编辑账号
const handleEdit = (row) => {
  dialogType.value = 'edit'
  Object.assign(accountForm, {
    id: row.id,
    name: row.name,
    platform: row.platform,
    group: row.group || '',
    status: row.status
  })
  dialogVisible.value = true
}

// 删除账号
const handleDelete = (row) => {
  ElMessageBox.confirm(
    `确定要删除账号 ${row.name} 吗？`,
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )
    .then(async () => {
      try {
        // 调用API删除账号
        const response = await accountApi.deleteAccount(row.id)

        if (response.code === 200) {
          // 从状态管理中删除账号
          accountStore.deleteAccount(row.id)
          ElMessage({
            type: 'success',
            message: '删除成功',
          })
        } else {
          ElMessage.error(response.msg || '删除失败')
        }
      } catch (error) {
        console.error('删除账号失败:', error)
        ElMessage.error('删除账号失败')
      }
    })
    .catch(() => {
      // 取消删除
    })
}

// 下载Cookie文件
const handleDownloadCookie = (row) => {
  // 从后端获取Cookie文件
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5409'
  const downloadUrl = `${baseUrl}/downloadCookie?filePath=${encodeURIComponent(row.filePath)}`

  // 创建一个隐藏的链接来触发下载
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = `${row.name}_cookie.json`
  link.target = '_blank'
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// 上传Cookie文件
const handleUploadCookie = (row) => {
  // 创建一个隐藏的文件输入框
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  input.style.display = 'none'
  document.body.appendChild(input)

  input.onchange = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    // 检查文件类型
    if (!file.name.endsWith('.json')) {
      ElMessage.error('请选择JSON格式的Cookie文件')
      document.body.removeChild(input)
      return
    }

    try {
      // 创建FormData对象
      const formData = new FormData()
      formData.append('file', file)
      formData.append('id', row.id)
      formData.append('platform', row.platform)

      // 使用统一的http封装发送上传请求
      const result = await http.upload('/uploadCookie', formData)

      ElMessage.success('Cookie文件上传成功')
      // 刷新账号列表以显示更新
      fetchAccounts()
    } catch (error) {
      ElMessage.error('Cookie文件上传失败')
    } finally {
      document.body.removeChild(input)
    }
  }

  input.click()
}

// 重新登录账号
const handleReLogin = (row) => {
  // 设置表单信息
  dialogType.value = 'edit'
  Object.assign(accountForm, {
    id: row.id,
    name: row.name,
    platform: row.platform,
    status: row.status
  })

  // 重置SSE状态
  sseConnecting.value = false
  qrCodeData.value = ''
  loginStatus.value = ''
  loginMessages.value = []

  // 显示对话框
  dialogVisible.value = true

  // 立即开始登录流程
  setTimeout(() => {
    connectSSE(row.platform, row.name)
  }, 300)
}

// 获取默认头像
const getDefaultAvatar = (name) => {
  // 使用简单的默认头像，可以基于用户名生成不同的颜色
  return `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=random`
}

// SSE事件源对象
let eventSource = null

// 关闭SSE连接
const closeSSEConnection = () => {
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
}

// 建立SSE连接
const connectSSE = (platform, name) => {
  // 关闭可能存在的连接
  closeSSEConnection()

  // 设置连接状态
  sseConnecting.value = true
  qrCodeData.value = ''
  loginStatus.value = ''

  // 获取平台类型编号
  const platformTypeMap = {
    '小红书': '1',
    '视频号': '2',
    '抖音': '3',
    '快手': '4',
    '百家号': '5',
    '什么值得买': '6',
    '头条号': '7',
    '携程': '8',
    '搜狐号': '9',
    '微博': '10'
  }

  const type = platformTypeMap[platform] || '1'

  // 图文平台（5-10）走新的 CLI 登录端点
  const isArticlePlatform = ['5', '6', '7', '8', '9', '10'].includes(type)

  // 创建SSE连接
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5409'
  let url
  if (isArticlePlatform) {
    // 图文平台：调用 CLI 登录，传递 group 参数
    let articleUrl = `${baseUrl}/loginArticleAccount?type=${type}&name=${encodeURIComponent(name)}`
    if (accountForm.group) {
      articleUrl += `&group=${encodeURIComponent(accountForm.group)}`
    }
    url = articleUrl
  } else {
    // 视频平台：原有 QR 码登录，传递 group 参数
    let videoUrl = `${baseUrl}/login?type=${type}&id=${encodeURIComponent(name)}`
    if (accountForm.group) {
      videoUrl += `&group=${encodeURIComponent(accountForm.group)}`
    }
    url = videoUrl
  }

  eventSource = new EventSource(url)

  // 监听消息
  eventSource.onmessage = (event) => {
    const data = event.data

    // 图文平台：显示文字引导消息
    if (isArticlePlatform) {
      // 收到状态码
      if (data === '200' || data === '500') {
        loginStatus.value = data
        if (data === '200') {
          setTimeout(() => {
            closeSSEConnection()
            setTimeout(() => {
              dialogVisible.value = false
              sseConnecting.value = false
              ElMessage.success('登录成功，账号已自动创建')
              fetchAccounts()
            }, 1000)
          }, 1000)
        } else {
          closeSSEConnection()
          setTimeout(() => {
            sseConnecting.value = false
            qrCodeData.value = ''
            loginStatus.value = ''
          }, 2000)
        }
      } else {
        // 文字引导消息，显示到二维码区域
        loginMessages.value.push(data)
      }
      return
    }

    // 视频平台：原有逻辑
    // 如果还没有二维码数据，且数据长度较长，认为是二维码
    if (!qrCodeData.value && data.length > 100) {
      try {
        if (data.startsWith('data:image')) {
          qrCodeData.value = data
        } else {
          qrCodeData.value = `data:image/png;base64,${data}`
        }
      } catch (error) {
        // 处理二维码数据出错
      }
    }
    // 如果收到状态码
    else if (data === '200' || data === '500') {
      loginStatus.value = data

      // 如果登录成功
      if (data === '200') {
        setTimeout(() => {
          // 关闭连接
          closeSSEConnection()

          // 1秒后关闭对话框并开始刷新
          setTimeout(() => {
            dialogVisible.value = false
            sseConnecting.value = false

            // 根据是否是重新登录显示不同提示
            ElMessage.success(dialogType.value === 'edit' ? '重新登录成功' : '账号添加成功')

            // 显示更新账号信息提示
            ElMessage({
              type: 'info',
              message: '正在同步账号信息...',
              duration: 0
            })

            // 触发刷新操作
            fetchAccounts().then(() => {
              // 如果添加账号时设置了运营者，保存到数据库
              if (accountForm.group) {
                const newAcc = accountStore.accounts.find(a => a.name === accountForm.name && a.platform === accountForm.platform)
                if (newAcc) {
                  accountApi.updateGroup({ id: newAcc.id, group_name: accountForm.group })
                }
              }
              // 刷新完成后关闭提示
              ElMessage.closeAll()
              ElMessage.success('账号信息已更新')
            })
          }, 1000)
        }, 1000)
      } else {
        // 登录失败，关闭连接
        closeSSEConnection()

        // 2秒后重置状态，允许重试
        setTimeout(() => {
          sseConnecting.value = false
          qrCodeData.value = ''
          loginStatus.value = ''
        }, 2000)
      }
    }
  }

  // 监听错误
  eventSource.onerror = (error) => {
    console.error('SSE连接错误:', error)
    ElMessage.error('连接服务器失败，请稍后再试')
    closeSSEConnection()
    sseConnecting.value = false
  }
}

// 提交账号表单
const submitAccountForm = () => {
  accountFormRef.value.validate(async (valid) => {
    if (valid) {
      if (dialogType.value === 'add') {
        // 建立SSE连接
        connectSSE(accountForm.platform, accountForm.name)
      } else {
        // 编辑账号逻辑
        try {
          // 将平台名称转换为类型数字
          const platformTypeMap = {
            '小红书': 1,
            '视频号': 2,
            '抖音': 3,
            '快手': 4,
            '百家号': 5,
            '什么值得买': 6,
            '头条号': 7,
            '携程': 8,
            '搜狐号': 9,
            '微博': 10
          };
          const type = platformTypeMap[accountForm.platform] || 1;

          const res = await accountApi.updateAccount({
            id: accountForm.id,
            type: type,
            userName: accountForm.name
          })
          if (res.code === 200) {
            // 同步更新运营者分组
            if (accountForm.group) {
              await accountApi.updateGroup({ id: accountForm.id, group_name: accountForm.group })
            }
            // 更新状态管理中的账号
            const updatedAccount = {
              id: accountForm.id,
              name: accountForm.name,
              platform: accountForm.platform,
              group: accountForm.group,
              status: accountForm.status // Keep the existing status
            };
            accountStore.updateAccount(accountForm.id, updatedAccount)
            ElMessage.success('更新成功')
            dialogVisible.value = false
            // 刷新账号列表
            fetchAccounts()
            accountStore.fetchGroups()
          } else {
            ElMessage.error(res.msg || '更新账号失败')
          }
        } catch (error) {
          console.error('更新账号失败:', error)
          ElMessage.error('更新账号失败')
        }
      }
    } else {
      return false
    }
  })
}

// 组件卸载前关闭SSE连接
onBeforeUnmount(() => {
  closeSSEConnection()
})
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.account-management {
  .page-header {
    margin-bottom: 24px;

    h1 {
      font-size: 24px;
      font-weight: 700;
      color: $text-primary;
      margin: 0;
    }
  }

  .account-tabs {
    background-color: $bg-color;
    border-radius: $border-radius-lg;
    box-shadow: $shadow-base;
    position: relative;
    overflow: hidden;

    &::before {
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 3px;
      background: $card-accent-gradient;
    }

    .account-tabs-nav {
      padding: 20px;
    }
  }

  .account-list-container {
    .account-search {
      display: flex;
      justify-content: space-between;
      margin-bottom: 20px;

      .el-input { width: 300px; }

      .action-buttons {
        display: flex;
        gap: 10px;

        .el-icon.is-loading {
          animation: rotate 1s linear infinite;
        }
      }
    }

    .account-list { margin-bottom: 20px; }
    .empty-data { padding: 40px 0; }
  }

  .action-cell {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: nowrap;
  }

  .clickable-status {
    cursor: pointer;
    transition: all 0.2s ease;

    &:hover {
      transform: scale(1.05);
      box-shadow: 0 0 8px rgba(249, 115, 22, 0.2);
    }
  }

  .qrcode-container {
    margin-top: 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 250px;

    .qrcode-wrapper {
      text-align: center;

      .qrcode-tip {
        margin-bottom: 15px;
        color: $text-regular;
      }

      .qrcode-image {
        max-width: 200px;
        max-height: 200px;
        border: 1px solid $border-base;
        border-radius: $border-radius-sm;
        background-color: black;
      }
    }

    .loading-wrapper, .success-wrapper, .error-wrapper {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 10px;

      .el-icon {
        font-size: 48px;

        &.is-loading {
          animation: rotate 1s linear infinite;
        }
      }

      span { font-size: 16px; }
    }

    .success-wrapper .el-icon { color: $success-color; }
    .error-wrapper .el-icon { color: $danger-color; }

    .guide-wrapper {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;

      .guide-messages {
        max-height: 200px;
        overflow-y: auto;
        width: 100%;
        max-width: 400px;

        .guide-msg {
          margin: 4px 0;
          font-size: 13px;
          color: $text-regular;
          line-height: 1.6;
        }
      }

      .guide-tip {
        margin-top: 12px;
        color: $primary-color;
        font-size: 14px;
        font-weight: 500;
      }
    }
  }
}
</style>

<style lang="scss">
.account-platform-select {
  .el-select-dropdown__wrap {
    max-height: none !important;
  }
  .el-scrollbar__wrap {
    max-height: none !important;
    overflow: visible !important;
  }
}

.operator-add {
  display: flex;
  gap: 8px;
}
</style>