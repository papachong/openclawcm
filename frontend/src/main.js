import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { pinia } from './stores'
import router from './router'
import i18n from './i18n'
import App from './App.vue'
import './assets/styles/global.css'

const app = createApp(App)

// Register all Element Plus icons
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(i18n)
app.use(ElementPlus)
app.use(pinia)
app.use(router)
app.mount('#app')
