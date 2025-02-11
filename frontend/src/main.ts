import './index.css'

import { createApp } from 'vue'
import router from './router'
import App from './App.vue'
import { createPinia } from 'pinia'
import dayjs from '@/utils/dayjs'
import { userStore } from './stores/user'
import translationPlugin from './translation'
import { initSocket } from './socket'
import { setConfig, frappeRequest, pageMetaPlugin } from 'frappe-ui'

const pinia = createPinia()
const app = createApp(App)
setConfig('resourceFetcher', frappeRequest)

app.use(pinia)
app.use(router)
app.use(translationPlugin)
app.use(pageMetaPlugin)
app.provide('$dayjs', dayjs)
app.provide('$socket', initSocket())
app.mount('#app')

const { userResource } = userStore()
app.provide('$user', userResource)
app.config.globalProperties.$user = userResource
