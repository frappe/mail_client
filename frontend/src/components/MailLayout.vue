<template>
	<header
		class="sticky top-0 z-10 flex items-center justify-between border-b bg-white px-3 py-2.5 sm:px-5"
	>
		<Breadcrumbs :items="[{ label: folder }]">
			<template #suffix>
				<div class="ml-2 self-end text-xs text-gray-600">
					{{
						__('{0} {1}', [
							formatNumber(count || 0),
							count == 1 ? singularize('messages') : 'messages',
						])
					}}
				</div>
			</template>
		</Breadcrumbs>
		<HeaderActions />
	</header>
	<div v-if="mails.data" class="flex h-[calc(100vh-3.2rem)]">
		<div
			ref="mailSidebar"
			class="sticky top-16 w-1/3 overflow-y-scroll overscroll-contain border-r p-3"
			@scroll="loadMoreEmails"
		>
			<div
				v-for="(mail, idx) in mails.data"
				:key="idx"
				class="flex cursor-pointer flex-col space-y-1"
				:class="{ 'rounded bg-gray-200': mail.name == currentMail[folder] }"
				@click="setCurrentMail(folder, mail.name)"
			>
				<SidebarDetail :mail="mail" />
				<div
					:class="{
						'mx-4 h-[0.25px] border-b border-gray-100': idx < mails.data.length - 1,
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
				:mail-i-d="currentMail[folder]"
				:type="folder === 'Inbox' ? 'Incoming Mail' : 'Outgoing Mail'"
			/>
		</div>
	</div>
</template>
<script setup lang="ts">
import { useDebounceFn } from '@vueuse/core'
import { Breadcrumbs } from 'frappe-ui'

import { formatNumber, singularize, startResizing } from '@/utils'
import { userStore } from '@/stores/user'
import HeaderActions from '@/components/HeaderActions.vue'
import MailDetails from '@/components/MailDetails.vue'
import SidebarDetail from '@/components/SidebarDetail.vue'

import type { Folder } from '@/types'

const { currentMail, setCurrentMail } = userStore()

const props = defineProps<{
	folder: Folder
	count?: number
	mails: object
}>()

const loadMoreEmails = useDebounceFn(() => {
	if (props.mails.hasNextPage) props.mails.next()
}, 500)
</script>
