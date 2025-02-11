<template>
	<div class="">
		<header
			class="sticky top-0 z-10 flex items-center justify-between border-b bg-white px-3 py-2.5 sm:px-5"
		>
			<Breadcrumbs :items="[{ label: 'Inbox' }]">
				<template #suffix>
					<div v-if="incomingMailCount.data" class="ml-2 self-end text-xs text-gray-600">
						{{
							__('{0} {1}').format(
								formatNumber(incomingMailCount.data),
								incomingMailCount.data == 1 ? singularize('messages') : 'messages',
							)
						}}
					</div>
				</template>
			</Breadcrumbs>
			<HeaderActions />
		</header>
		<div v-if="incomingMails.data" class="flex h-[calc(100vh-3.2rem)]">
			<div
				ref="mailSidebar"
				class="mailSidebar sticky top-16 w-1/3 overflow-y-scroll overscroll-contain border-r p-3"
				@scroll="loadMoreEmails"
			>
				<div
					v-for="(mail, idx) in incomingMails.data"
					:key="idx"
					class="flex cursor-pointer flex-col space-y-1"
					:class="{ 'rounded bg-gray-200': mail.name == currentMail.incoming }"
					@click="setCurrentMail('incoming', mail.name)"
				>
					<SidebarDetail :mail="mail" />
					<div
						:class="{
							'mx-4 h-[0.25px] border-b border-gray-100':
								idx < incomingMails.data.length - 1,
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
				<MailDetails :mail-i-d="currentMail.incoming" type="Incoming Mail" />
			</div>
		</div>
	</div>
</template>
<script setup lang="ts">
import { Breadcrumbs, createListResource, createResource } from 'frappe-ui'
import { inject, onMounted } from 'vue'
import { formatNumber, startResizing, singularize } from '@/utils'
import HeaderActions from '@/components/HeaderActions.vue'
import MailDetails from '@/components/MailDetails.vue'
import { useDebounceFn } from '@vueuse/core'
import SidebarDetail from '@/components/SidebarDetail.vue'
import { userStore } from '@/stores/user'

const socket = inject('$socket')
const user = inject('$user')
const { currentMail, setCurrentMail } = userStore()

onMounted(() => {
	socket.on('incoming_mail_received', () => {
		incomingMails.reload()
		incomingMailCount.reload()
	})
})

const incomingMails = createListResource({
	url: 'mail.api.mail.get_incoming_mails',
	doctype: 'Incoming Mail',
	auto: true,
	pageLength: 50,
	cache: ['incoming', user.data?.name],
	onSuccess(data) {
		if (!currentMail.incoming && data.length) setCurrentMail('incoming', data[0].name)
	},
})

const incomingMailCount = createResource({
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

const loadMoreEmails = useDebounceFn(() => {
	if (incomingMails.hasNextPage) incomingMails.next()
}, 500)
</script>
