<template>
	<div class="">
		<header
			class="sticky top-0 z-10 flex items-center justify-between border-b bg-white px-3 py-2.5 sm:px-5"
		>
			<Breadcrumbs :items="breadcrumbs">
				<template #suffix>
					<div v-if="incomingMailCount.data" class="self-end text-xs text-gray-600 ml-2">
						{{
							__('{0} {1}').format(
								formatNumber(incomingMailCount.data),
								incomingMailCount.data == 1 ? singularize('messages') : 'messages'
							)
						}}
					</div>
				</template>
			</Breadcrumbs>
			<HeaderActions />
		</header>
		<div v-if="incomingMails.data" class="flex h-[calc(100vh-3.2rem)]">
			<div
				@scroll="loadMoreEmails"
				ref="mailSidebar"
				class="mailSidebar border-r w-1/3 p-3 sticky top-16 overflow-y-scroll overscroll-contain"
			>
				<div
					v-for="(mail, idx) in incomingMails.data"
					@click="openMail(mail)"
					class="flex flex-col space-y-1 cursor-pointer"
					:class="{ 'bg-gray-200 rounded': mail.name == currentMail }"
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
			<div class="flex-1 overflow-auto w-2/3">
				<MailDetails :mailID="currentMail" type="Incoming Mail" />
			</div>
		</div>
	</div>
</template>
<script setup>
import { Breadcrumbs, createListResource, createResource } from 'frappe-ui'
import { computed, inject, ref, onMounted } from 'vue'
import { formatNumber, startResizing, singularize } from '@/utils'
import HeaderActions from '@/components/HeaderActions.vue'
import MailDetails from '@/components/MailDetails.vue'
import { useDebounceFn } from '@vueuse/core'
import SidebarDetail from '@/components/SidebarDetail.vue'

const socket = inject('$socket')
const user = inject('$user')
const mailStart = ref(0)
const mailList = ref([])
const currentMail = ref(JSON.parse(sessionStorage.getItem('currentIncomingMail')))

onMounted(() => {
	socket.on('incoming_mail_received', (data) => {
		incomingMails.reload()
		incomingMailCount.reload()
	})
})

const setCurrentMail = (mail) => {
	sessionStorage.setItem('currentIncomingMail', JSON.stringify(mail))
}

const incomingMails = createListResource({
	url: 'mail_client.api.client.get_incoming_mails',
	doctype: 'Incoming Mail',
	auto: true,
	start: mailStart.value,
	pageLength: 50,
	cache: ['incoming', user.data?.name],
	onSuccess(data) {
		mailList.value = mailList.value.concat(data)
		mailStart.value = mailStart.value + data.length
		if (!currentMail.value && mailList.value.length) {
			currentMail.value = mailList.value[0].name
			setCurrentMail(mailList.value[0].name)
		}
	},
})

const incomingMailCount = createResource({
	url: 'frappe.client.get_count',
	makeParams(values) {
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

const openMail = (mail = null) => {
	currentMail.value = mail.name
	setCurrentMail(mail.name)
}

const breadcrumbs = computed(() => {
	return [
		{
			label: `Inbox`,
			route: { name: 'Inbox' },
		},
	]
})
</script>
