<template>
	<h1 class="font-semibold mb-8">Mailbox</h1>
	<div class="flex items-center mb-3">
		<span class="font-medium leading-normal text-gray-800 text-base">Email Address</span>
		<Link
			v-model="email"
			doctype="Mailbox"
			:filters="{ user: userResource.data?.name }"
			class="ml-auto"
		/>
	</div>
	<div v-if="mailbox.doc" class="space-y-1.5">
		<Switch
			label="Enabled"
			v-model="mailbox.doc.enabled"
			@update:modelValue="mailbox.setValue.submit({ enabled: mailbox.doc.enabled })"
		/>
		<Switch
			label="Incoming"
			v-model="mailbox.doc.incoming"
			@update:modelValue="mailbox.setValue.submit({ incoming: mailbox.doc.incoming })"
		/>
		<Switch
			label="Outgoing"
			v-model="mailbox.doc.outgoing"
			@update:modelValue="mailbox.setValue.submit({ outgoing: mailbox.doc.outgoing })"
		/>
		<Switch
			label="Default Outgoing"
			v-model="mailbox.doc.is_default"
			:disabled="!mailbox.doc.outgoing"
			@update:modelValue="mailbox.setValue.submit({ is_default: mailbox.doc.is_default })"
		/>
		<Switch
			label="Track Outgoing Mail"
			v-model="mailbox.doc.track_outgoing_mail"
			:disabled="!mailbox.doc.outgoing"
			@update:modelValue="
				mailbox.setValue.submit({ track_outgoing_mail: mailbox.doc.track_outgoing_mail })
			"
		/>
		<Switch
			label="Create Mail Contact"
			v-model="mailbox.doc.create_mail_contact"
			@update:modelValue="
				mailbox.setValue.submit({ create_mail_contact: mailbox.doc.create_mail_contact })
			"
		/>
		<div class="mx-2.5 space-y-2.5 pt-0.5">
			<div class="flex items-center justify-between">
				<span class="font-medium leading-normal text-gray-800 text-base">
					Display Name
				</span>
				<TextInput
					v-model="mailbox.doc.display_name"
					@input="
						mailbox.setValueDebounced.submit({
							display_name: mailbox.doc.display_name,
						})
					"
				/>
			</div>
			<div class="flex items-center justify-between">
				<span class="font-medium leading-normal text-gray-800 text-base">Reply To</span>
				<TextInput
					v-model="mailbox.doc.reply_to"
					@input="mailbox.setValueDebounced.submit({ reply_to: mailbox.doc.reply_to })"
				/>
			</div>
		</div>
	</div>
</template>
<script setup>
import { ref, watch } from 'vue'
import { Switch, TextInput, createDocumentResource } from 'frappe-ui'
import Link from '@/components/Controls/Link.vue'
import { userStore } from '@/stores/user'

const { userResource, defaultOutgoing } = userStore()
const email = ref(defaultOutgoing.data)

watch(email, () => {
	mailbox.name = email.value
	mailbox.reload()
})

const mailbox = createDocumentResource({
	doctype: 'Mailbox',
	name: email.value,
	transform(data) {
		for (const d of [
			'enabled',
			'incoming',
			'outgoing',
			'is_default',
			'track_outgoing_mail',
			'create_mail_contact',
		]) {
			data[d] = !!data[d]
		}
	},
})
</script>
