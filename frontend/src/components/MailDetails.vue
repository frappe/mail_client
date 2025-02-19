<template>
	<div v-if="props.mailID" class="p-3">
		<div
			v-for="mail in mailThread.data"
			:key="mail.name"
			class="mb-4 p-3"
			:class="{ 'rounded-md shadow': mailThread.data.length > 1 }"
		>
			<div class="flex space-x-3 border-b pb-2">
				<Avatar
					class="avatar border border-gray-300"
					:label="mail.display_name || mail.sender"
					:image="mail.user_image"
					size="lg"
				/>
				<div class="flex flex-1 justify-between text-xs">
					<div class="flex flex-col space-y-1">
						<div class="space-x-1">
							<span class="text-base font-semibold">
								{{ mail.display_name || mail.from_ || mail.sender }}
							</span>
							<span v-if="mail.display_name" class="text-sm text-gray-600">
								{{ `<${mail.from_ || mail.sender}>` }}
							</span>
						</div>
						<div class="leading-4">
							{{ mail.subject }}
						</div>
						<div class="space-x-2">
							<span v-if="mail.to.length">
								{{ __('To') }}:
								<span
									v-for="(recipient, idx) in mail.to"
									:key="idx"
									class="text-gray-700"
								>
									{{ recipient.display_name || recipient.email }}
								</span>
							</span>
							<span v-if="mail.cc.length">
								{{ __('Cc') }}:
								<span
									v-for="(recipient, idx) in mail.cc"
									:key="idx"
									class="text-gray-700"
								>
									{{ recipient.display_name || recipient.email }}
								</span>
							</span>
							<span v-if="mail.bcc.length">
								{{ __('Bcc') }}:
								<span
									v-for="(recipient, idx) in mail.bcc"
									:key="idx"
									class="text-gray-700"
								>
									{{ recipient.display_name || recipient.email }}
								</span>
							</span>
						</div>
					</div>
					<div class="flex items-center space-x-2 self-start">
						<MailDate
							:datetime="mail.folder === 'Drafts' ? mail.modified : mail.creation"
						/>
						<Tooltip
							v-for="action in mailActions(mail).filter(
								(d) => d.condition !== false,
							)"
							:key="action.label"
							:text="action.label"
						>
							<Button variant="ghost" @click="action.onClick()">
								<template #icon>
									<component :is="action.icon" class="h-4 w-4 text-gray-600" />
								</template>
							</Button>
						</Tooltip>
						<Tooltip v-if="mail.folder !== 'Drafts'" :text="__('More')">
							<Dropdown
								:options="moreActions(mail).filter((d) => d.condition !== false)"
							>
								<Button variant="ghost">
									<template #icon>
										<Ellipsis class="h-4 w-4 text-gray-600" />
									</template>
								</Button>
							</Dropdown>
						</Tooltip>
					</div>
				</div>
			</div>
			<div
				class="ProseMirror prose prose-table:table-fixed prose-td:p-2 prose-th:p-2 prose-td:border prose-th:border prose-td:border-gray-300 prose-th:border-gray-300 prose-td:relative prose-th:relative prose-th:bg-gray-100 max-w-none pt-4"
			>
				<div v-if="mail.body_html" class="prose-sm" v-html="mailBody(mail.body_html)" />
				<pre v-else-if="mail.body_plain" class="text-wrap bg-white text-gray-800">{{
					mail.body_plain
				}}</pre>
			</div>
		</div>
	</div>
	<div
		v-else
		class="my-auto flex h-full w-full flex-1 flex-col items-center justify-center space-y-2"
	>
		<div class="text-lg text-gray-500">
			{{ __('No emails to show') }}
		</div>
	</div>
	<SendMailModal
		v-model="showSendModal"
		:mail-i-d="draftMailID"
		:reply-details="replyDetails"
		@reload-mails="emit('reloadMails')"
	/>
</template>

<script setup lang="ts">
import { inject, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Ellipsis, Forward, Mail, Reply, ReplyAll, SquarePen } from 'lucide-vue-next'
import { Avatar, Button, Dropdown, Tooltip, createResource } from 'frappe-ui'

import { userStore } from '@/stores/user'
import MailDate from '@/components/MailDate.vue'
import SendMailModal from '@/components/Modals/SendMailModal.vue'

import type { Folder } from '@/types'

const { setCurrentMail } = userStore()
const dayjs = inject('$dayjs')

const showSendModal = ref(false)
const draftMailID = ref<string>()

const props = defineProps<{
	mailID: string | null
	type: string
}>()

const emit = defineEmits(['reloadMails'])

const replyDetails = reactive({
	to: '',
	cc: '',
	bcc: '',
	subject: '',
	in_reply_to_mail_type: props.type,
	in_reply_to_mail_name: '',
})

const route = useRoute()

const mailThread = createResource({
	url: 'mail.api.mail.get_mail_thread',
	makeParams: () => {
		return {
			name: props.mailID,
			mail_type: props.type,
		}
	},
	onError: (error) => {
		if (error.exc_type === 'DoesNotExistError')
			setCurrentMail(String(route.name) as Folder, null)
	},
})

const reloadThread = () => {
	if (props.mailID) mailThread.reload()
}

defineExpose({ reloadThread })

const mailBody = (bodyHTML: string) => {
	bodyHTML = bodyHTML.replace(/<br\s*\/?>/, '')
	bodyHTML = bodyHTML.replace(
		/<blockquote>/g,
		'<div class="blockquote-container"><a href="#" class="font-medium text-gray-900 text-xs no-underline" onclick="this.nextElementSibling.style.display=\'block\'; this.style.display=\'none\'; return false;">Show more from this thread</a><blockquote style="display:none;">',
	)
	bodyHTML = bodyHTML.replace(/<\/blockquote>/g, '</blockquote></div>')
	return bodyHTML
}

type ActionType = 'editDraft' | 'reply' | 'replyAll' | 'forward'

interface MailAction {
	label: string
	onClick: () => void | typeof openModal
	icon: typeof SquarePen
	condition?: boolean
}

const mailActions = (mail): MailAction[] => [
	{
		label: __('Edit Draft'),
		onClick: () => {
			draftMailID.value = mail.name
			showSendModal.value = true
		},
		icon: SquarePen,
		condition: mail.folder === 'Drafts',
	},
	{
		label: __('Reply'),
		onClick: () => openModal('reply', mail),
		icon: Reply,
		condition: mail.folder !== 'Drafts',
	},
	{
		label: __('Reply All'),
		onClick: () => openModal('replyAll', mail),
		icon: ReplyAll,
		condition: mail.folder !== 'Drafts',
	},
	{
		label: __('Forward'),
		onClick: () => openModal('forward', mail),
		icon: Forward,
		condition: mail.folder !== 'Drafts',
	},
]

const moreActions = (mail): MailAction[] => [
	{
		label: __('See MIME Message'),
		onClick: () => {
			window
				.open(
					`mime-message/${mail.mail_type.toLowerCase().split(' ').join('-')}/${mail.name}`,
					'_blank',
				)
				?.focus()
		},
		icon: Mail,
	},
]

const openModal = (type: ActionType, mail) => {
	if (props.type == 'Incoming Mail') {
		replyDetails.to = mail.reply_to || mail.sender
	} else {
		replyDetails.to = mail.to.map((to) => to.email).join(', ')
	}

	replyDetails.subject = mail.subject.startsWith('Re: ') ? mail.subject : `Re: ${mail.subject}`
	replyDetails.cc = ''
	replyDetails.bcc = ''
	replyDetails.in_reply_to_mail_name = mail.name

	if (type === 'replyAll') {
		replyDetails.cc = mail.cc.map((cc) => cc.email).join(', ')
		replyDetails.bcc = mail.bcc.map((bcc) => bcc.email).join(', ')
	}
	if (type === 'forward') {
		replyDetails.to = ''
		replyDetails.subject = `Fwd: ${mail.subject}`
	}
	replyDetails.html = getReplyHtml(mail.body_html, mail.creation)
	showSendModal.value = true
}

const getReplyHtml = (html, creation) => {
	const replyHeader = `
        On ${dayjs(creation).format('DD MMM YYYY')} at ${dayjs(creation).format('h:mm A')}, ${
			replyDetails.to
		} wrote:
    `
	return `<br><blockquote>${replyHeader} <br> ${html}</blockquote>`
}

watch(() => props.mailID, reloadThread)
</script>
<style>
.prose
	:where(blockquote p:first-of-type):not(
		:where([class~='not-prose'], [class~='not-prose'] *)
	)::before {
	content: '';
}
</style>
