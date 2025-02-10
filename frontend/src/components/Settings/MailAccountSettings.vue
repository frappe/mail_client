<template>
	<h1 class="mb-8 font-semibold">Account</h1>
	<div class="mb-3 flex items-center">
		<span class="text-base font-medium leading-normal text-gray-800">Email Address</span>
		<Link
			v-model="email"
			doctype="Mail Account"
			:filters="{ user: user.data?.name }"
			class="ml-auto"
		/>
	</div>
	<div v-if="account.doc" class="space-y-1.5">
		<Switch
			label="Enabled"
			v-model="account.doc.enabled"
			@update:modelValue="account.setValue.submit({ enabled: account.doc.enabled })"
		/>
		<Switch
			label="Track Outgoing Mail"
			v-model="account.doc.track_outgoing_mail"
			@update:modelValue="
				account.setValue.submit({ track_outgoing_mail: account.doc.track_outgoing_mail })
			"
		/>
		<Switch
			label="Create Mail Contact"
			v-model="account.doc.create_mail_contact"
			@update:modelValue="
				account.setValue.submit({ create_mail_contact: account.doc.create_mail_contact })
			"
		/>
		<div class="mx-2.5 space-y-2.5 pt-0.5">
			<div class="flex items-center justify-between">
				<span class="text-base font-medium leading-normal text-gray-800">
					Display Name
				</span>
				<TextInput
					v-model="account.doc.display_name"
					@input="
						account.setValueDebounced.submit({
							display_name: account.doc.display_name,
						})
					"
				/>
			</div>
			<div class="flex items-center justify-between">
				<span class="text-base font-medium leading-normal text-gray-800">Reply To</span>
				<TextInput
					v-model="account.doc.reply_to"
					@input="account.setValueDebounced.submit({ reply_to: account.doc.reply_to })"
				/>
			</div>
		</div>
	</div>
</template>
<script setup>
import { ref, inject, watch, onMounted } from 'vue'
import { Switch, TextInput, createDocumentResource } from 'frappe-ui'
import Link from '@/components/Controls/Link.vue'

const user = inject('$user')

const email = ref(user.data?.default_outgoing)

const fetchMailAccount = () => {
	account.name = email.value
	account.reload()
}

onMounted(fetchMailAccount)
watch(email, fetchMailAccount)

const account = createDocumentResource({
	doctype: 'Mail Account',
	name: email.value,
	auto: false,
	transform(data) {
		for (const d of ['enabled', 'track_outgoing_mail', 'create_mail_contact']) {
			data[d] = !!data[d]
		}
	},
})
</script>
