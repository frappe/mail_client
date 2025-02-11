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
							<LinkControl
								v-model="mail.from"
								doctype="Mail Account"
								:filters="{ user: user.data.name }"
							/>
						</div>
						<div class="flex items-center gap-2">
							<span class="text-xs text-gray-500">{{ __('To') }}:</span>
							<MultiselectInputControl
								v-model="mail.to"
								class="flex-1 text-sm"
								:validate="validateEmail"
								:error-message="
									(value) => __('{0} is an invalid email address', [value])
								"
							/>
							<div class="flex gap-1.5">
								<Button
									:label="__('Cc')"
									variant="ghost"
									:class="[
										cc ? '!bg-gray-300 hover:bg-gray-200' : '!text-gray-500',
									]"
									@click="toggleCC()"
								/>
								<Button
									:label="__('Bcc')"
									variant="ghost"
									:class="[
										bcc ? '!bg-gray-300 hover:bg-gray-200' : '!text-gray-500',
									]"
									@click="toggleBCC()"
								/>
							</div>
						</div>
						<div v-if="cc" class="flex items-center gap-2">
							<span class="text-xs text-gray-500">{{ __('Cc') }}:</span>
							<MultiselectInputControl
								ref="ccInput"
								v-model="mail.cc"
								class="flex-1 text-sm"
								:validate="validateEmail"
								:error-message="
									(value) => __('{0} is an invalid email address', [value])
								"
							/>
						</div>
						<div v-if="bcc" class="flex items-center gap-2">
							<span class="text-xs text-gray-500">{{ __('Bcc') }}:</span>
							<MultiselectInputControl
								ref="bccInput"
								v-model="mail.bcc"
								class="flex-1 text-sm"
								:validate="validateEmail"
								:error-message="
									(value) => __('{0} is an invalid email address', [value])
								"
							/>
						</div>
						<div class="flex items-center gap-2 pb-2.5">
							<span class="text-xs text-gray-500">{{ __('Subject') }}:</span>
							<TextInput
								v-model="mail.subject"
								class="flex-1 border-none bg-white text-sm hover:bg-white focus:border-none focus:!shadow-none focus-visible:!ring-0"
							/>
						</div>
					</div>
				</template>
				<template #editor="{ editor }">
					<EditorContent
						:class="['max-h-[35vh] overflow-y-auto border-t py-3 text-sm']"
						:editor="editor"
					/>
				</template>
				<template #bottom>
					<FileUploader
						:upload-args="{
							doctype: 'Outgoing Mail',
							docname: localMailID,
							private: true,
						}"
						:validate-file="
							async () => {
								if (!localMailID) await createDraftMail.submit()
							}
						"
						@success="attachments.fetch()"
					>
						<template #default="{ file, progress, uploading, openFileSelector }">
							<!-- Attachments -->
							<div
								v-if="localMailID"
								class="mb-2 flex flex-col gap-2 text-sm text-gray-700"
							>
								<div v-if="uploading" class="rounded bg-gray-100 p-2.5">
									<div class="mb-1.5 flex items-center">
										<span class="mr-1 font-medium">
											{{ file.name }}
										</span>
										<span class="font-extralight">
											({{ formatBytes(file.size) }})
										</span>
									</div>
									<Progress :value="progress" />
								</div>
								<div
									v-for="(file, index) in attachments.data"
									:key="index"
									class="flex cursor-pointer items-center rounded bg-gray-100 p-2.5"
								>
									<span class="mr-1 font-medium">
										{{ file.file_name || file.name }}
									</span>
									<span class="font-extralight">
										({{ formatBytes(file.file_size) }})
									</span>
									<FeatherIcon
										class="ml-auto h-3.5 w-3.5"
										name="x"
										@click="removeAttachment.submit({ name: file.name })"
									/>
								</div>
							</div>

							<div
								class="flex justify-between gap-2 overflow-hidden border-t py-2.5"
							>
								<!-- Text Editor Buttons -->
								<div class="flex items-center gap-1 overflow-x-auto">
									<TextEditorFixedMenu :buttons="textEditorMenuButtons" />
									<EmojiPicker
										v-slot="{ togglePopover }"
										v-model="emoji"
										@update:model-value="() => appendEmoji()"
									>
										<Button variant="ghost" @click="togglePopover()">
											<template #icon>
												<Laugh class="h-4 w-4" />
											</template>
										</Button>
									</EmojiPicker>
									<Button variant="ghost" @click="openFileSelector()">
										<template #icon>
											<Paperclip class="h-4" />
										</template>
									</Button>
								</div>

								<!-- Send & Discard -->
								<div class="flex items-center justify-end space-x-2 sm:mt-0">
									<Button :label="__('Discard')" @click="discardMail" />
									<Button variant="solid" :label="__('Send')" @click="send" />
								</div>
							</div>
						</template>
					</FileUploader>
				</template>
			</TextEditor>
		</template>
	</Dialog>
</template>
<script setup lang="ts">
import {
	Dialog,
	FeatherIcon,
	TextEditor,
	createResource,
	createDocumentResource,
	FileUploader,
	TextEditorFixedMenu,
	TextInput,
	Button,
	Progress,
} from 'frappe-ui'
import { reactive, watch, inject, ref, nextTick, computed } from 'vue'
import { useDebounceFn } from '@vueuse/core'
import { Paperclip, Laugh } from 'lucide-vue-next'
import LinkControl from '@/components/Controls/LinkControl.vue'
import EmojiPicker from '@/components/EmojiPicker.vue'
import MultiselectInputControl from '@/components/Controls/MultiselectInputControl.vue'
import { EditorContent } from '@tiptap/vue-3'
import { validateEmail, formatBytes } from '@/utils'
import { userStore } from '@/stores/user'

const user = inject('$user')
const show = defineModel()
const localMailID = ref(null)
const textEditor = ref(null)
const ccInput = ref(null)
const bccInput = ref(null)
const cc = ref(false)
const bcc = ref(false)
const emoji = ref()
const isSend = ref(false)
const isMailWatcherActive = ref(true)
const { setCurrentMail } = userStore()

const SYNC_DEBOUNCE_TIME = 1500

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

const emit = defineEmits(['reloadMails'])

const discardMail = async () => {
	if (localMailID.value) await deleteDraftMail.submit()
	else if (!isMailEmpty.value) Object.assign(mail, emptyMail)
	show.value = false
}

const syncMail = useDebounceFn(() => {
	if (!isMailWatcherActive.value) return
	if (localMailID.value) updateDraftMail.submit()
	else if (!isMailEmpty.value) createDraftMail.submit()
}, SYNC_DEBOUNCE_TIME)

const emptyMail = {
	from: user.data?.default_outgoing,
	to: '',
	cc: '',
	bcc: '',
	subject: '',
	html: '',
}

const mail = reactive({ ...emptyMail })

watch(show, () => {
	if (!show.value) return
	if (props.mailID) getDraftMail(props.mailID)
	else {
		localMailID.value = null
		Object.assign(mail, emptyMail)
	}

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
	},
)

watch(mail, syncMail)

const createDraftMail = createResource({
	url: 'mail.api.outbound.send',
	method: 'POST',
	makeParams() {
		return {
			// TODO: use mail account display_name
			from_: `${user.data?.full_name} <${mail.from}>`,
			do_not_submit: !isSend.value,
			...mail,
		}
	},
	onSuccess(data) {
		if (isSend.value) Object.assign(mail, emptyMail)
		else {
			localMailID.value = data
			setCurrentMail('draft', data)
			emit('reloadMails')
		}
	},
})

const updateDraftMail = createResource({
	url: 'mail.api.mail.update_draft_mail',
	makeParams() {
		return {
			mail_id: localMailID.value,
			from_: `${user.data?.full_name} <${mail.from}>`,
			do_submit: isSend.value,
			...mail,
		}
	},
	onSuccess() {
		if (isSend.value) setCurrentMail('draft', null)
		emit('reloadMails')
	},
})

// TODO: delete using documentresource directly
const deleteDraftMail = createResource({
	url: 'frappe.client.delete',
	makeParams() {
		return {
			doctype: 'Outgoing Mail',
			name: localMailID.value,
		}
	},
	onSuccess() {
		setCurrentMail('draft', null)
		emit('reloadMails')
	},
})

const attachments = createResource({
	url: 'mail.api.mail.get_attachments',
	makeParams() {
		return {
			dt: 'Outgoing Mail',
			dn: localMailID.value,
		}
	},
})

const removeAttachment = createResource({
	url: 'frappe.client.delete',
	method: 'DELETE',
	makeParams(values) {
		return { doctype: 'File', name: values.name }
	},
	onSuccess() {
		attachments.fetch()
	},
})

const getDraftMail = (name) =>
	createDocumentResource({
		doctype: 'Outgoing Mail',
		name: name,
		onSuccess(data) {
			isMailWatcherActive.value = false
			const mailDetails = {
				from_: `${data.display_name} <${data.sender}>`,
				subject: data.subject,
				html: data.body_html,
				in_reply_to_mail_name: data.in_reply_to_mail_name,
				in_reply_to_mail_type: data.in_reply_to_mail_type,
			}
			for (const recipient of data.recipients) {
				const recipientType = recipient.type.toLowerCase()
				if (recipientType in mailDetails) mailDetails[recipientType].push(recipient.email)
				else mailDetails[recipientType] = [recipient.email]
			}
			localMailID.value = name
			attachments.fetch()
			Object.assign(mail, mailDetails)
			if (mailDetails.cc) cc.value = true
			if (mailDetails.bcc) bcc.value = true
			setTimeout(() => {
				isMailWatcherActive.value = true
			}, SYNC_DEBOUNCE_TIME + 1)
		},
	})

const send = async () => {
	isSend.value = true
	if (localMailID.value) await updateDraftMail.submit()
	else await createDraftMail.submit()
	isSend.value = false
	show.value = false
}

const toggleCC = () => {
	cc.value = !cc.value
	if (cc.value) nextTick(() => ccInput.value.setFocus())
}

const toggleBCC = () => {
	bcc.value = !bcc.value
	if (bcc.value) nextTick(() => bccInput.value.setFocus())
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
	'FontColor',
	'Separator',
	'Align Left',
	'Align Center',
	'Align Right',
	'Separator',
	'Bullet List',
	'Numbered List',
	'Separator',
	// todo: fix inline image upload
	// 'Image',
	'Link',
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
