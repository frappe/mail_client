<template>
	<MailLayout
		v-if="incomingMails"
		folder="Inbox"
		:count="incomingMailsCount?.data"
		:mails="incomingMails"
	/>
</template>
<script setup lang="ts">
import { inject, onMounted } from 'vue'
import { createListResource, createResource } from 'frappe-ui'

import { userStore } from '@/stores/user'
import MailLayout from '@/components/MailLayout.vue'

import type { UserResource } from '@/types'

const socket = inject('$socket')
const user = inject('$user') as UserResource
const { currentMail, setCurrentMail } = userStore()

onMounted(() => {
	socket.on('incoming_mail_received', () => {
		incomingMails.reload()
		incomingMailsCount.reload()
	})
})

const incomingMails = createListResource({
	url: 'mail.api.mail.get_incoming_mails',
	doctype: 'Incoming Mail',
	auto: true,
	pageLength: 50,
	cache: ['incoming', user.data?.name],
	onSuccess(data) {
		if (!currentMail.Inbox && data.length) setCurrentMail('Inbox', data[0].name)
	},
})

const incomingMailsCount = createResource({
	url: 'frappe.client.get_count',
	makeParams() {
		return {
			doctype: 'Incoming Mail',
			filters: {
				receiver: user.data?.name,
			},
		}
	},
	cache: ['incomingMailCount', user.data?.name],
	auto: true,
})
</script>
