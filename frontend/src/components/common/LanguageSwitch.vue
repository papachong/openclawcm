<template>
  <el-dropdown trigger="click" @command="handleCommand">
    <span class="language-switch">
      <el-icon><i class="language-icon">🌐</i></el-icon>
      <span class="lang-text">{{ currentLabel }}</span>
    </span>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item
          v-for="lang in languages"
          :key="lang.value"
          :command="lang.value"
          :class="{ 'is-active': locale === lang.value }"
        >
          {{ lang.label }}
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { setLocale } from '@/i18n'

const { locale, t } = useI18n()

const languages = [
  { value: 'zh-CN', label: '简体中文' },
  { value: 'en-US', label: 'English' },
]

const currentLabel = computed(() => {
  return languages.find(l => l.value === locale.value)?.label || locale.value
})

function handleCommand(lang) {
  setLocale(lang)
}
</script>

<style scoped>
.language-switch {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  color: #333;
  font-size: 14px;
}

.language-icon {
  font-style: normal;
  font-size: 16px;
}

.lang-text {
  font-size: 13px;
}

:deep(.el-dropdown-menu__item.is-active) {
  color: #409EFF;
  font-weight: bold;
}
</style>
