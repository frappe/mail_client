<template>
	<div>
		<Button variant="subtle" @click="openSendModal()">
			<template #prefix>
				<SquarePen class="h-4 w-4 text-gray-600" />
			</template>
			{{ __('Compose an email') }}
		</Button>
	</div>
	<SendMailModal v-model="showSendModal" @reload-mails="emit('reloadMails')" />
</template>
<script setup>
import { Button } from 'frappe-ui'
import { SquarePen } from 'lucide-vue-next'
import SendMailModal from '@/components/Modals/SendMailModal.vue'
import { ref } from 'vue'

const emit = defineEmits(['reloadMails'])

const showSendModal = ref(false)

const openSendModal = () => {
	showSendModal.value = true
}
</script>
