<template>
	<div class="h-full">
		<header
			class="sticky top-0 z-10 flex items-center justify-between border-b bg-white px-3 py-2.5 sm:px-5"
		>
			<Breadcrumbs :items="[{ label: 'Sent' }]">
				<template #suffix>
					<div v-if="sentMailsCount.data" class="ml-2 self-end text-xs text-gray-600">
						{{
							__('{0} {1}').format(
								formatNumber(sentMailsCount.data),
								sentMailsCount.data == 1 ? singularize('messages') : 'messages',
							)
						}}
					</div>
				</template>
			</Breadcrumbs>
			<HeaderActions />
		</header>
		<div v-if="sentMails.data" class="flex h-[calc(100vh-3.2rem)]">
			<div
				@scroll="loadMoreEmails"
				ref="mailSidebar"
				class="mailSidebar sticky top-16 w-1/3 overflow-y-scroll overscroll-contain border-r p-2"
			>
				<div
					v-for="(mail, idx) in sentMails.data"
					@click="setCurrentMail('sent', mail.name)"
					class="flex cursor-pointer flex-col space-y-1"
					:class="{ 'rounded bg-gray-200': mail.name == currentMail.sent }"
				>
					<SidebarDetail :mail="mail" />
					<div
						:class="{
							'mx-4 h-[0.25px] border-b border-gray-100':
								idx < sentMails.data.length - 1,
						}"
					></div>
				</div>
			</div>
			<div class="flex w-px cursor-col-resize justify-center" @mousedown="startResizing">
				<div
					ref="resizer"
					class="h-full w-[2px] rounded-full transition-all duration-300 ease-in-out group-hover:bg-gray-400"
				/>
			</div>
			<div class="w-2/3 flex-1 overflow-auto">
				<MailDetails :mailID="currentMail.sent" type="Outgoing Mail" />
			</div>
		</div>
	</div>
</template>
<script setup>
import { Breadcrumbs, createResource, createListResource } from 'frappe-ui'
import { inject, ref, onMounted } from 'vue'
import HeaderActions from '@/components/HeaderActions.vue'
import { formatNumber, startResizing, singularize } from '@/utils'
import MailDetails from '@/components/MailDetails.vue'
import { useDebounceFn } from '@vueuse/core'
import SidebarDetail from '@/components/SidebarDetail.vue'
import { userStore } from '@/stores/user'

const socket = inject('$socket')
const user = inject('$user')
const { currentMail, setCurrentMail } = userStore()

onMounted(() => {
	socket.on('outgoing_mail_sent', (data) => {
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
		if (!currentMail.sent && data.length) setCurrentMail('sent', data[0].name)
	},
})

const sentMailsCount = createResource({
	url: 'frappe.client.get_count',
	makeParams(values) {
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

const loadMoreEmails = useDebounceFn(() => {
	if (sentMails.hasNextPage) sentMails.next()
}, 500)
</script>
