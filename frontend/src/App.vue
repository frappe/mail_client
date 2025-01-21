<template>
	<Layout>
		<router-view />
	</Layout>
	<Dialogs />
	<Toasts />
</template>
<script setup>
import { useRoute } from 'vue-router'
import { Toasts } from 'frappe-ui'
import { Dialogs } from '@/utils/dialogs'
import { computed } from 'vue'
import { useScreenSize } from './utils/composables'
import LoginLayout from './components/LoginLayout.vue'
import DesktopLayout from './components/DesktopLayout.vue'
import MobileLayout from './components/MobileLayout.vue'

const route = useRoute()
const screenSize = useScreenSize()

const Layout = computed(() => {
	if (route.meta.isLoginOrSetup) return LoginLayout
	if (screenSize.width < 640) return MobileLayout
	return DesktopLayout
})
</script>
