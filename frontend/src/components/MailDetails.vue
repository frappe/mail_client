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
						<div class="text-base font-semibold">
							{{ mail.display_name || mail.sender }}
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
					<div
						v-if="mail.folder === 'Drafts'"
						class="flex items-center space-x-2 self-start"
					>
						<MailDate :datetime="mail.modified" />
						<Tooltip :text="__('Edit')">
							<Button
								icon="edit"
								variant="ghost"
								@click="openModal('editDraft', mail.name)"
							>
							</Button>
						</Tooltip>
					</div>
					<div v-else class="flex items-center space-x-2 self-start">
						<MailDate :datetime="mail.creation" />
						<Tooltip :text="__('Reply')">
							<Button variant="ghost" @click="openModal('reply', mail)">
								<template #icon>
									<Reply class="h-4 w-4 text-gray-600" />
								</template>
							</Button>
						</Tooltip>
						<Tooltip :text="__('Reply All')">
							<Button variant="ghost" @click="openModal('replyAll', mail)">
								<template #icon>
									<ReplyAll class="h-4 w-4 text-gray-600" />
								</template>
							</Button>
						</Tooltip>
						<Tooltip :text="__('Forward')">
							<Button variant="ghost" @click="openModal('forward', mail)">
								<template #icon>
									<Forward class="h-4 w-4 text-gray-600" />
								</template>
							</Button>
						</Tooltip>
					</div>
				</div>
			</div>
			<div
				v-if="mail.body_html"
				class="ProseMirror prose prose-table:table-fixed prose-td:p-2 prose-th:p-2 prose-td:border prose-th:border prose-td:border-gray-300 prose-th:border-gray-300 prose-td:relative prose-th:relative prose-th:bg-gray-100 prose-sm max-w-none pt-4 text-sm leading-5"
				v-html="mailBody(mail.body_html)"
			></div>
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
import { Forward, Reply, ReplyAll } from 'lucide-vue-next'
import { Avatar, Button, Tooltip, createResource } from 'frappe-ui'

import MailDate from '@/components/MailDate.vue'
import SendMailModal from '@/components/Modals/SendMailModal.vue'

const showSendModal = ref(false)
const draftMailID = ref(null)
const dayjs = inject('$dayjs')

const props = defineProps({
	mailID: {
		type: [String, null],
		required: true,
	},
	type: {
		type: String,
		required: true,
	},
})

const emit = defineEmits(['reloadMails'])

const replyDetails = reactive({
	to: '',
	cc: '',
	bcc: '',
	subject: '',
	in_reply_to_mail_type: props.type,
	in_reply_to_mail_name: '',
})

const mailThread = createResource({
	url: 'mail.api.mail.get_mail_thread',
	makeParams() {
		return {
			name: props.mailID,
			mail_type: props.type,
		}
	},
	auto: !!props.mailID,
})

const reloadThread = () => {
	if (props.mailID) mailThread.reload()
}
defineExpose({ reloadThread })

const mailBody = (bodyHTML) => {
	bodyHTML = bodyHTML.replace(/<br\s*\/?>/, '')
	bodyHTML = bodyHTML.replace(
		/<blockquote>/g,
		'<div class="blockquote-container"><a href="#" class="font-medium text-gray-900 text-xs no-underline" onclick="this.nextElementSibling.style.display=\'block\'; this.style.display=\'none\'; return false;">Show more from this thread</a><blockquote style="display:none;">',
	)
	bodyHTML = bodyHTML.replace(/<\/blockquote>/g, '</blockquote></div>')
	return bodyHTML
}

const openModal = (type, mail) => {
	if (type === 'editDraft') {
		draftMailID.value = mail
		showSendModal.value = true
		return
	}
	if (props.type == 'Incoming Mail') {
		replyDetails.to = mail.sender
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
