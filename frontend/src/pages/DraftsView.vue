<template>
	<MailLayout
		v-if="draftMails"
		folder="Drafts"
		:count="draftMailsCount?.data"
		:mails="draftMails"
	/>
</template>
<script setup lang="ts">
import { inject, ref } from 'vue'
import { createListResource, createResource } from 'frappe-ui'

import { userStore } from '@/stores/user'
import MailLayout from '@/components/MailLayout.vue'

import type { UserResource } from '@/types'

const mailDetails = ref(null)
const user = inject('$user') as UserResource
const { currentMail, setCurrentMail } = userStore()

// const reloadDrafts = () => {
// 	draftMails.reload()
// 	draftMailsCount.reload()
// }

const draftMails = createListResource({
	url: 'mail.api.mail.get_draft_mails',
	doctype: 'Outgoing Mail',
	auto: true,
	pageLength: 50,
	cache: ['draftMails', user.data?.name],
	onSuccess(data) {
		if (!data.length) return
		if (!currentMail.Drafts) setCurrentMail('Drafts', data[0].name)
		mailDetails.value?.reloadThread()
	},
})

const draftMailsCount = createResource({
	url: 'frappe.client.get_count',
	makeParams() {
		return {
			doctype: 'Outgoing Mail',
			filters: {
				sender: user.data?.name,
				status: 'Draft',
			},
		}
	},
	cache: ['draftMailsCount', user.data?.name],
	auto: true,
})
</script>
