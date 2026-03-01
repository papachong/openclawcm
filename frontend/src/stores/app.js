import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)
  const currentInstance = ref(null)

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function setCurrentInstance(instance) {
    currentInstance.value = instance
  }

  return {
    sidebarCollapsed,
    currentInstance,
    toggleSidebar,
    setCurrentInstance,
  }
})
