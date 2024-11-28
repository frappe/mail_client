<template>
	<div class="h-full">
		<header
			class="sticky top-0 z-10 flex items-center justify-between border-b bg-white px-3 py-2.5 sm:px-5"
		>
			<Breadcrumbs :items="breadcrumbs">
				<template #suffix>
					<div v-if="sentMailsCount.data" class="self-end text-xs text-gray-600 ml-2">
						{{
							__('{0} {1}').format(
								formatNumber(sentMailsCount.data),
								sentMailsCount.data == 1 ? singularize('messages') : 'messages'
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
				class="mailSidebar border-r w-1/3 p-2 sticky top-16 overflow-y-scroll overscroll-contain"
			>
				<div
					v-for="(mail, idx) in sentMails.data"
					@click="setCurrentMail('sent', mail.name)"
					class="flex flex-col space-y-1 cursor-pointer"
					:class="{ 'bg-gray-200 rounded': mail.name == currentMail.sent }"
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
			<div class="flex-1 overflow-auto w-2/3">
				<MailDetails :mailID="currentMail.sent" type="Outgoing Mail" />
			</div>
		</div>
	</div>
</template>
<script setup>
import { Breadcrumbs, createResource, createListResource } from 'frappe-ui'
import { computed, inject, ref, onMounted } from 'vue'
import HeaderActions from '@/components/HeaderActions.vue'
import { formatNumber, startResizing, singularize } from '@/utils'
import MailDetails from '@/components/MailDetails.vue'
import { useDebounceFn } from '@vueuse/core'
import SidebarDetail from '@/components/SidebarDetail.vue'
import { userStore } from '@/stores/user'

const socket = inject('$socket')
const user = inject('$user')
const mailStart = ref(0)
const mailList = ref([])
const { currentMail, setCurrentMail } = userStore()

onMounted(() => {
	socket.on('outgoing_mail_sent', (data) => {
		sentMails.reload()
		sentMailsCount.reload()
	})
})

const sentMails = createListResource({
	url: 'mail_client.api.mail.get_sent_mails',
	doctype: 'Outgoing Mail',
	auto: true,
	start: mailStart.value,
	cache: ['sentMails', user.data?.name],
	onSuccess(data) {
		mailList.value = mailList.value.concat(data)
		mailStart.value = mailStart.value + data.length
		if (!currentMail.sent && mailList.value.length)
			setCurrentMail('sent', mailList.value[0].name)
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

const breadcrumbs = computed(() => {
	return [
		{
			label: 'Sent',
			route: { name: 'Sent' },
		},
	]
})
</script>
