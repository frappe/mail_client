<template>
	<Dialog
		v-model="show"
		:options="{
			title: __('Send Mail'),
			size: '4xl',
		}"
	>
		<template #body-content>
			<TextEditor
				ref="textEditor"
				:editor-class="[
					'prose-sm max-w-none',
					'min-h-[15rem]',
					'[&_p.reply-to-content]:hidden',
				]"
				:content="mail.html"
				@change="(val) => (mail.html = val)"
			>
				<template #top>
					<div class="flex flex-col gap-3">
						<div class="flex items-center gap-2 border-t pt-2.5">
							<span class="text-xs text-gray-500">{{ __('From') }}:</span>
							<Link
								v-model="mail.from"
								doctype="Mailbox"
								:filters="{ user: user.data.name }"
							/>
						</div>
						<div class="flex items-center gap-2">
							<span class="text-xs text-gray-500">{{ __('To') }}:</span>
							<MultiselectInput
								class="flex-1 text-sm"
								v-model="mail.to"
								:validate="validateEmail"
								:error-message="
									(value) => __('{0} is an invalid email address', [value])
								"
							/>
							<div class="flex gap-1.5">
								<Button
									:label="__('Cc')"
									variant="ghost"
									@click="toggleCC()"
									:class="[
										cc ? '!bg-gray-300 hover:bg-gray-200' : '!text-gray-500',
									]"
								/>
								<Button
									:label="__('Bcc')"
									variant="ghost"
									@click="toggleBCC()"
									:class="[
										bcc ? '!bg-gray-300 hover:bg-gray-200' : '!text-gray-500',
									]"
								/>
							</div>
						</div>
						<div v-if="cc" class="flex items-center gap-2">
							<span class="text-xs text-gray-500">{{ __('Cc') }}:</span>
							<MultiselectInput
								ref="ccInput"
								class="flex-1 text-sm"
								v-model="mail.cc"
								:validate="validateEmail"
								:error-message="
									(value) => __('{0} is an invalid email address', [value])
								"
							/>
						</div>
						<div v-if="bcc" class="flex items-center gap-2">
							<span class="text-xs text-gray-500">{{ __('Bcc') }}:</span>
							<MultiselectInput
								ref="bccInput"
								class="flex-1 text-sm"
								v-model="mail.bcc"
								:validate="validateEmail"
								:error-message="
									(value) => __('{0} is an invalid email address', [value])
								"
							/>
						</div>
						<div class="flex items-center gap-2 pb-2.5">
							<span class="text-xs text-gray-500">{{ __('Subject') }}:</span>
							<TextInput
								class="flex-1 text-sm border-none bg-white hover:bg-white focus:border-none focus:!shadow-none focus-visible:!ring-0"
								v-model="mail.subject"
							/>
						</div>
					</div>
				</template>
				<template v-slot:editor="{ editor }">
					<EditorContent
						:class="['max-h-[35vh] overflow-y-auto border-t py-3 text-sm']"
						:editor="editor"
					/>
				</template>
				<template v-slot:bottom>
					<div class="flex flex-col gap-2">
						<div class="flex flex-wrap gap-2">
							<!-- <AttachmentItem
                                v-for="a in attachments"
                                :key="a.file_url"
                                :label="a.file_name"`
                            >
                                <template #suffix>
                                <FeatherIcon
                                    class="h-3.5"
                                    name="x"
                                    @click.stop="removeAttachment(a)"
                                />
                                </template>
                            </AttachmentItem> -->
						</div>
						<div class="flex justify-between gap-2 overflow-hidden border-t py-2.5">
							<div class="flex gap-1 items-center overflow-x-auto">
								<!--  <TextEditorFixedMenu :buttons="textEditorMenuButtons" /> -->
								<EmojiPicker
									v-model="emoji"
									v-slot="{ togglePopover }"
									@update:modelValue="() => appendEmoji()"
								>
									<Button variant="ghost" @click="togglePopover()">
										<template #icon>
											<Laugh class="h-4 w-4" />
										</template>
									</Button>
								</EmojiPicker>
								<FileUploader @success="(f) => attachments.push(f)">
									<template #default="{ openFileSelector }">
										<Button variant="ghost" @click="openFileSelector()">
											<template #icon>
												<Paperclip class="h-4" />
											</template>
										</Button>
									</template>
								</FileUploader>
							</div>
							<div class="mt-2 flex items-center justify-end space-x-2 sm:mt-0">
								<Button :label="__('Discard')" @click="discardMail" />
								<Button @click="send" variant="solid" :label="__('Send')" />
							</div>
						</div>
					</div>
				</template>
			</TextEditor>
		</template>
	</Dialog>
</template>
<script setup>
import {
	Dialog,
	TextEditor,
	createResource,
	createDocumentResource,
	FileUploader,
	TextEditorFixedMenu,
	TextInput,
	Button,
} from 'frappe-ui'
import { reactive, watch, inject, ref, nextTick, computed } from 'vue'
import { watchDebounced } from '@vueuse/core'
import { Paperclip, Laugh } from 'lucide-vue-next'
import Link from '@/components/Controls/Link.vue'
import EmojiPicker from '@/components/EmojiPicker.vue'
import MultiselectInput from '@/components/Controls/MultiselectInput.vue'
import { EditorContent } from '@tiptap/vue-3'
import { validateEmail } from '@/utils'
import { userStore } from '@/stores/user'

const user = inject('$user')
const attachments = defineModel('attachments')
const show = defineModel()
const mailID = ref(null)
const textEditor = ref(null)
const ccInput = ref(null)
const bccInput = ref(null)
const cc = ref(false)
const bcc = ref(false)
const emoji = ref()
const isSendMail = ref(false)
const { setCurrentMail } = userStore()

const editor = computed(() => {
	return textEditor.value.editor
})

const isMailEmpty = computed(() => {
	const isSubjectEmpty = !mail.subject.length
	let isHtmlEmpty = true
	if (mail.html) {
		const element = document.createElement('div')
		element.innerHTML = mail.html
		isHtmlEmpty = !element.textContent.trim()
		isHtmlEmpty = Array.from(element.children).some((d) => !d.textContent.trim())
	}
	const isRecipientsEmpty = [mail.to, mail.cc, mail.bcc].every((d) => !d.length)

	return isSubjectEmpty && isHtmlEmpty && isRecipientsEmpty
})

const props = defineProps({
	mailID: {
		type: String,
		required: false,
	},
	replyDetails: {
		type: Object,
		required: false,
	},
})

const emit = defineEmits(['reloadMailThread'])

const discardMail = async () => {
	if (mailID.value) await deleteDraftMail.submit()
	show.value = false
}

const emptyMail = {
	to: '',
	cc: '',
	bcc: '',
	subject: '',
	html: '',
}

const mail = reactive({ ...emptyMail })

watch(show, async () => {
	if (!show.value) {
		if (mailID.value) {
			if (isMailEmpty.value) await deleteDraftMail.submit()
			else await updateDraftMail.submit()
			emit('reloadMailThread')

			mailID.value = null
			Object.assign(mail, emptyMail)
		}
		return
	}

	if (props.mailID) getDraftMail(props.mailID)

	if (!props.replyDetails) return

	mail.to = props.replyDetails.to.split(',').filter((item) => item != '')
	mail.cc = props.replyDetails.cc.split(',').filter((item) => item != '')
	mail.bcc = props.replyDetails.bcc.split(',').filter((item) => item != '')
	cc.value = mail.cc.length > 0 ? true : false
	bcc.value = mail.bcc.length > 0 ? true : false
	mail.subject = props.replyDetails.subject
	mail.html = props.replyDetails.html
	mail.in_reply_to_mail_type = props.replyDetails.in_reply_to_mail_type
	mail.in_reply_to_mail_name = props.replyDetails.in_reply_to_mail_name
})

watch(
	() => props.mailID,
	(val) => {
		// TODO: use documentresource directly
		if (val) getDraftMail(val)
	}
)
watchDebounced(
	mail,
	() => {
		if (mailID.value) {
			if (isMailEmpty.value) deleteDraftMail.submit()
			else updateDraftMail.submit()
		} else if (!isMailEmpty.value) createDraftMail.submit()
	},
	{ debounce: 1500 }
)

const defaultOutgoing = createResource({
	url: 'mail_client.api.mail.get_default_outgoing',
	auto: true,
	onSuccess(data) {
		if (data) mail.from = data
	},
})

const createDraftMail = createResource({
	url: 'mail_client.api.outbound.send',
	method: 'POST',
	makeParams(values) {
		return {
			// TODO: use mailbox display_name
			from_: `${user.data?.full_name} <${mail.from}>`,
			do_not_submit: true,
			...mail,
		}
	},
	onSuccess(data) {
		mailID.value = data
		setCurrentMail('draft', data)
	},
})

const updateDraftMail = createResource({
	url: 'mail_client.api.mail.update_draft_mail',
	makeParams(values) {
		return {
			mail_id: mailID.value,
			from_: `${user.data?.full_name} <${mail.from}>`,
			do_submit: isSendMail.value,
			...mail,
		}
	},
	onSuccess() {
		if (!isSendMail.value) return
		isSendMail.value = false
		show.value = false
	},
})

// TODO: delete using documentresource directly
const deleteDraftMail = createResource({
	url: 'frappe.client.delete',
	makeParams(values) {
		return {
			doctype: 'Outgoing Mail',
			name: mailID.value,
		}
	},
	onSuccess() {
		mailID.value = null
		Object.assign(mail, emptyMail)
		setCurrentMail('draft', null)
	},
})

const getDraftMail = (name) =>
	createDocumentResource({
		doctype: 'Outgoing Mail',
		name: name,
		onSuccess(data) {
			const mailDetails = {
				from_: `${data.display_name} <${data.sender}>`,
				subject: data.subject,
				html: data.body_html,
				in_reply_to_mail_name: data.in_reply_to_mail_name,
				in_reply_to_mail_type: data.in_reply_to_mail_type,
			}
			for (const recipient of data.recipients) {
				const recipientType = recipient.type.toLowerCase()
				if (recipientType in mailDetails) {
					mailDetails[recipientType].push(recipient.email)
				} else {
					mailDetails[recipientType] = [recipient.email]
				}
			}
			mailID.value = name
			Object.assign(mail, mailDetails)
			if (mailDetails.cc) cc.value = true
			if (mailDetails.bcc) bcc.value = true
			// TODO: don't trigger updateDraftMail
		},
	})

const send = () => {
	isSendMail.value = true
	updateDraftMail.submit()
}

const toggleCC = () => {
	cc.value = !cc.value
	cc.value && nextTick(() => ccInput.value.setFocus())
}

const toggleBCC = () => {
	bcc.value = !bcc.value
	bcc.value && nextTick(() => bccInput.value.setFocus())
}

const appendEmoji = () => {
	editor.value.commands.insertContent(emoji.value)
	editor.value.commands.focus()
	emoji.value = ''
}

const textEditorMenuButtons = [
	'Paragraph',
	['Heading 2', 'Heading 3', 'Heading 4', 'Heading 5', 'Heading 6'],
	'Separator',
	'Bold',
	'Italic',
	'Separator',
	'Bullet List',
	'Numbered List',
	'Separator',
	'Align Left',
	'Align Center',
	'Align Right',
	'FontColor',
	'Separator',
	'Image',
	'Video',
	'Link',
	'Blockquote',
	'Code',
	'Horizontal Rule',
	[
		'InsertTable',
		'AddColumnBefore',
		'AddColumnAfter',
		'DeleteColumn',
		'AddRowBefore',
		'AddRowAfter',
		'DeleteRow',
		'MergeCells',
		'SplitCell',
		'ToggleHeaderColumn',
		'ToggleHeaderRow',
		'ToggleHeaderCell',
		'DeleteTable',
	],
]
</script>
