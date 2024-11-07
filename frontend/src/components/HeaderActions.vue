<template>
	<div>
		<Button variant="subtle" @click="openSendModal()">
			<template #prefix>
				<SquarePen class="h-4 w-4 text-gray-600" />
			</template>
			{{ __('Compose an email') }}
		</Button>
	</div>
	<SendMail v-model="showSendModal" />
</template>
<script setup>
import { Button } from 'frappe-ui'
import { SquarePen } from 'lucide-vue-next'
import SendMail from '@/components/Modals/SendMail.vue'
import { ref } from 'vue'

const showSendModal = ref(false)

const openSendModal = () => {
	showSendModal.value = true
}
</script>
