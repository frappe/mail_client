<template>
	<header
		class="sticky top-0 z-10 flex items-center justify-between border-b bg-white px-3 py-2.5 sm:px-5"
	>
		<Breadcrumbs :items="[{ label: currentFolder }]">
			<template #suffix>
				<div class="ml-2 self-end text-xs text-gray-600">
					{{
						__('{0} {1}', [
							formatNumber(mailCount?.data || 0),
							mailCount?.data == 1 ? singularize('messages') : 'messages',
						])
					}}
				</div>
			</template>
		</Breadcrumbs>
		<HeaderActions @reload-mails="reloadMails('Drafts')" />
	</header>
	<div v-if="mails[currentFolder].data" class="flex h-[calc(100vh-3.2rem)]">
		<div
			ref="mailSidebar"
			class="sticky top-16 w-1/3 overflow-y-scroll overscroll-contain border-r p-3"
			@scroll="loadMoreEmails"
		>
			<div
				v-for="(mail, idx) in mails[currentFolder].data"
				:key="idx"
				class="flex cursor-pointer flex-col space-y-1 rounded"
				:class="{ 'bg-gray-100': mail.name == currentMail[currentFolder] }"
				@click="setCurrentMail(currentFolder, mail.name)"
			>
				<SidebarDetail :mail="mail" @click="markAsRead(mail)" />
				<div
					:class="{
						'mx-4 h-[0.25px] border-b border-gray-100':
							idx < mails[currentFolder].data.length - 1,
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
			<MailDetails
				ref="mailDetails"
				:mail-i-d="currentMail[currentFolder]"
				:type="doctype"
				@reload-mails="reloadMails('Drafts')"
				@mark-as-unread="
					setSeen.submit({ mail_name: currentMail[currentFolder], seen_value: 0 })
				"
			/>
		</div>
	</div>
</template>
<script setup lang="ts">
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useDebounceFn } from '@vueuse/core'
import { Breadcrumbs, createListResource, createResource } from 'frappe-ui'

import { formatNumber, singularize, startResizing } from '@/utils'
import { userStore } from '@/stores/user'
import HeaderActions from '@/components/HeaderActions.vue'
import MailDetails from '@/components/MailDetails.vue'
import SidebarDetail from '@/components/SidebarDetail.vue'

import type { Folder, UserResource } from '@/types'

const socket = inject('$socket')
const user = inject('$user') as UserResource
const { currentMail, setCurrentMail } = userStore()
const route = useRoute()

const currentFolder = computed(() => String(route.name) as Folder)
const doctype = computed(() =>
	currentFolder.value === 'Inbox' ? 'Incoming Mail' : 'Outgoing Mail',
)

const mailDetails = ref<typeof MailDetails>()

const folders: Folder[] = ['Inbox', 'Sent', 'Outbox', 'Drafts']

const createMailResource = (folder: Folder) =>
	createListResource({
		url: `mail.api.mail.get_${folder.toLowerCase()}_mails`,
		doctype: doctype.value,
		pageLength: 50,
		cache: [`${folder}Mails`, user.data?.name],
		onSuccess: (data) => {
			if (!data.length) return
			if (!currentMail[folder] && folder !== 'Inbox') setCurrentMail(folder, data[0].name)
			mailDetails.value?.reloadThread()
		},
	})

const mails = Object.fromEntries(folders.map((folder) => [folder, createMailResource(folder)]))

const mailCountFilters = computed(() =>
	currentFolder.value === 'Inbox'
		? { receiver: user.data.name }
		: { sender: user.data.name, folder: currentFolder.value },
)

const mailCount = createResource({
	url: 'frappe.client.get_count',
	auto: true,
	makeParams: () => ({
		doctype: doctype.value,
		filters: mailCountFilters.value,
	}),
	cache: [`${currentFolder.value}MailCount`, user.data?.name],
})

interface SetSeenParams {
	mail_name: string
	seen_value: 1 | 0
}

const setSeen = createResource({
	url: 'mail.api.mail.set_seen',
	makeParams: (values: SetSeenParams) => ({ ...values }),
	onSuccess: (data: SetSeenParams) => {
		mails['Inbox'].data.find((m) => m.name === data.mail_name).seen = data.seen_value
		if (!data.seen_value) setCurrentMail('Inbox', null)
	},
})

const markAsRead = (mail) => {
	if (!mail.seen && currentFolder.value === 'Inbox')
		setSeen.submit({ mail_name: mail.name, seen_value: 1 })
}

const reloadMails = (folder?: Folder) => {
	if (folder && folder !== currentFolder.value) return
	mails[currentFolder.value].reload()
	mailCount.reload()
}

watch(() => currentFolder.value, reloadMails, { immediate: true })

onMounted(() => {
	socket.on('outgoing_mail_sent', () => reloadMails('Sent'))
	socket.on('incoming_mail_received', () => reloadMails('Inbox'))
})

const loadMoreEmails = useDebounceFn(() => {
	if (mails[currentFolder.value].hasNextPage) mails[currentFolder.value].next()
}, 500)
</script>
