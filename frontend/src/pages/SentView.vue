<template>
	<MailLayout v-if="sentMails" folder="Sent" :count="sentMailsCount?.data" :mails="sentMails" />
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
	socket.on('outgoing_mail_sent', () => {
		sentMails.reload()
		sentMailsCount.reload()
	})
})

const sentMails = createListResource({
	url: 'mail.api.mail.get_sent_mails',
	doctype: 'Outgoing Mail',
	auto: true,
	pageLength: 50,
	cache: ['sentMails', user.data?.name],
	onSuccess(data) {
		if (!currentMail.Sent && data.length) setCurrentMail('Sent', data[0].name)
	},
})

const sentMailsCount = createResource({
	url: 'frappe.client.get_count',
	makeParams() {
		return {
			doctype: 'Outgoing Mail',
			filters: {
				sender: user.data?.name,
				status: 'Sent',
			},
		}
	},
	cache: ['sentMailsCount', user.data?.name],
	auto: true,
})
</script>
