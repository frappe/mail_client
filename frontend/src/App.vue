<template>
	<component :is="Layout">
		<router-view />
	</component>
	<Dialogs />
	<Toasts />
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Toasts } from 'frappe-ui'

import { useScreenSize } from '@/utils/composables'
import { Dialogs } from '@/utils/dialogs'
import DesktopLayout from '@/components/DesktopLayout.vue'
import LoginLayout from '@/components/LoginLayout.vue'
import MobileLayout from '@/components/MobileLayout.vue'

const route = useRoute()
const screenSize = useScreenSize()

const Layout = computed(() => {
	if (route.meta.isLogin || route.meta.isSetup) return LoginLayout
	if (route.meta.isMimeMessage) return 'div'
	if (screenSize.width < 640) return MobileLayout
	return DesktopLayout
})
</script>
