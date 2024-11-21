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
								<Button :label="__('Discard')" @click="() => (show = false)" />
								<Button @click="send()" variant="solid" :label="__('Send')" />
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
	FileUploader,
	TextEditorFixedMenu,
	TextInput,
	Button,
} from 'frappe-ui'
import { reactive, watch, inject, ref, nextTick, computed } from 'vue'
import { Paperclip, Laugh } from 'lucide-vue-next'
import Link from '@/components/Controls/Link.vue'
import EmojiPicker from '@/components/EmojiPicker.vue'
import MultiselectInput from '@/components/Controls/MultiselectInput.vue'
import { EditorContent } from '@tiptap/vue-3'
import { validateEmail } from '@/utils'

const user = inject('$user')
const attachments = defineModel('attachments')
const show = defineModel()
const textEditor = ref(null)
const ccInput = ref(null)
const bccInput = ref(null)
const cc = ref(false)
const bcc = ref(false)
const emoji = ref()

const editor = computed(() => {
	return textEditor.value.editor
})

const props = defineProps({
	replyDetails: {
		type: Object,
		required: false,
	},
})

const mail = reactive({
	from: '',
	to: '',
	cc: '',
	bcc: '',
	subject: '',
	html: '',
})

watch(show, () => {
	if (show.value && props.replyDetails) {
		mail.to = props.replyDetails.to.split(',').filter((item) => item != '')
		mail.cc = props.replyDetails.cc.split(',').filter((item) => item != '')
		mail.bcc = props.replyDetails.bcc.split(',').filter((item) => item != '')
		cc.value = mail.cc.length > 0 ? true : false
		bcc.value = mail.bcc.length > 0 ? true : false
		mail.subject = props.replyDetails.subject
		mail.html = props.replyDetails.html
		mail.in_reply_to_mail_type = props.replyDetails.in_reply_to_mail_type
		mail.in_reply_to_mail_name = props.replyDetails.in_reply_to_mail_name
	}
})

const defaultOutgoing = createResource({
	url: 'mail_client.api.mail.get_default_outgoing',
	auto: true,
	onSuccess(data) {
		mail.from = data
	},
})

const sendMail = createResource({
	url: 'mail_client.api.outbound.send',
	method: 'POST',
	makeParams(values) {
		return {
			from_: `${user.data?.full_name} <${mail.from}>`,
			...mail,
		}
	},
})

const send = () => {
	sendMail.submit(
		{},
		{
			onSuccess() {
				show.value = false
			},
		}
	)
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
