<template>
	<h1 class="font-semibold mb-8">Mailbox</h1>
	<div class="flex items-center mb-2">
		<span class="font-medium leading-normal text-gray-800 text-base">Email Address</span>
		<Link
			v-model="email"
			doctype="Mailbox"
			:filters="{ user: userResource.data?.name }"
			class="ml-auto"
		/>
	</div>
	<div v-if="mailbox.doc">
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
	</div>
</template>
<script setup>
import { ref, watch } from 'vue'
import { Switch, createDocumentResource } from 'frappe-ui'
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
