import './index.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { frappeRequest, pageMetaPlugin, setConfig } from 'frappe-ui'

import App from '@/App.vue'
import router from '@/router'
import { initSocket } from '@/socket'
import translationPlugin from '@/translation'
import dayjs from '@/utils/dayjs'
import { userStore } from '@/stores/user'

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
