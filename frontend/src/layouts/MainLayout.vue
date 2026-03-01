<template>
  <el-container class="main-layout">
    <!-- Sidebar -->
    <el-aside :width="sidebarCollapsed ? '64px' : '220px'" class="sidebar">
      <div class="logo">
        <img src="@/assets/logo.svg" alt="logo" class="logo-img" v-if="!sidebarCollapsed" />
        <span v-if="!sidebarCollapsed" class="logo-text">OpenClawCM</span>
        <span v-else class="logo-text-mini">OC</span>
      </div>
      <el-menu
        :default-active="currentRoute"
        :collapse="sidebarCollapsed"
        router
        class="sidebar-menu"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item
          v-for="item in menuItems"
          :key="item.path"
          :index="item.path"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.title }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- Main Content -->
    <el-container>
      <!-- Header -->
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="toggleSidebar" :size="20">
            <Fold v-if="!sidebarCollapsed" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">{{ $t('menu.home') }}</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <LanguageSwitch />
          <el-dropdown @command="handleUserCommand">
            <span class="user-info">
              <el-icon><UserFilled /></el-icon>
              <span>{{ displayName }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">{{ $t('layout.profile') }}</el-dropdown-item>
                <el-dropdown-item command="logout" divided>{{ $t('layout.logout') }}</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- Content Area -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'
import { ElMessage } from 'element-plus'
import {
  Odometer, Monitor, Cpu, UserFilled, MagicStick,
  Document, Connection, Setting, Fold, Expand, Coin
} from '@element-plus/icons-vue'
import LanguageSwitch from '@/components/common/LanguageSwitch.vue'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const appStore = useAppStore()

const sidebarCollapsed = computed(() => appStore.sidebarCollapsed)
const toggleSidebar = () => appStore.toggleSidebar()

const currentRoute = computed(() => route.path)
const currentTitle = computed(() => {
  const titleKey = route.meta?.titleKey
  if (titleKey) return t(titleKey)
  return route.meta?.title || ''
})

const displayName = computed(() => {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    return user.display_name || user.username || t('layout.user')
  } catch { return t('layout.user') }
})

const handleUserCommand = (command) => {
  if (command === 'logout') {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    ElMessage.success(t('layout.loggedOut'))
    router.push('/login')
  } else if (command === 'profile') {
    router.push('/settings')
  }
}

const menuItems = computed(() => [
  { path: '/dashboard', title: t('menu.dashboard'), icon: 'Odometer' },
  { path: '/instances', title: t('menu.instances'), icon: 'Monitor' },
  { path: '/models', title: t('menu.models'), icon: 'Cpu' },
  { path: '/agents', title: t('menu.agents'), icon: 'UserFilled' },
  { path: '/skills', title: t('menu.skills'), icon: 'MagicStick' },
  { path: '/outputs', title: t('menu.outputs'), icon: 'Document' },
  { path: '/memory-pools', title: t('menu.memoryPools'), icon: 'Coin' },
  { path: '/collaborations', title: t('menu.collaborations'), icon: 'Connection' },
  { path: '/settings', title: t('menu.settings'), icon: 'Setting' },
])
</script>

<style scoped>
.main-layout {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
  transition: width 0.3s;
  overflow: hidden;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 16px;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo-img {
  width: 32px;
  height: 32px;
  margin-right: 8px;
}

.logo-text-mini {
  font-size: 20px;
  font-weight: bold;
}

.sidebar-menu {
  border-right: none;
  height: calc(100vh - 60px);
  overflow-y: auto;
}

.sidebar-menu:not(.el-menu--collapse) {
  width: 220px;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e6e6e6;
  background: #fff;
  padding: 0 20px;
  height: 60px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-btn {
  cursor: pointer;
  color: #333;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: #333;
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}
</style>
