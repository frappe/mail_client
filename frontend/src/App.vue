<template>
	<Layout>
		<router-view />
	</Layout>
	<Dialogs />
	<Toasts />
</template>
<script setup>
import { Toasts } from 'frappe-ui'
import { Dialogs } from '@/utils/dialogs'
import { computed } from 'vue'
import { useScreenSize } from './utils/composables'
import LoginLayout from './components/LoginLayout.vue'
import DesktopLayout from './components/DesktopLayout.vue'
import MobileLayout from './components/MobileLayout.vue'
import { sessionStore } from '@/stores/session'

const { isLoggedIn } = sessionStore()
const screenSize = useScreenSize()

const Layout = computed(() => {
	if (!isLoggedIn) return LoginLayout
	if (screenSize.width < 640) return MobileLayout
	return DesktopLayout
})
</script>
