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
<script setup lang="ts">
import { ref } from 'vue'
import { SquarePen } from 'lucide-vue-next'
import { Button } from 'frappe-ui'

import SendMailModal from '@/components/Modals/SendMailModal.vue'

const emit = defineEmits(['reloadMails'])

const showSendModal = ref(false)

const openSendModal = () => {
	showSendModal.value = true
}
</script>
