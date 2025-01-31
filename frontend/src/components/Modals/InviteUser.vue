<template>
	<Dialog
		v-model="show"
		:options="{
			title: __('Invite User'),
			actions: [
				{
					label: __('Invite User'),
					variant: 'solid',
					onClick: inviteUser.submit,
				},
			],
		}"
	>
		<template #body-content>
			<div class="space-y-4">
				<div class="flex items-center justify-between">
					<FormControl
						type="text"
						:label="__('Username')"
						placeholder="johndoe"
						v-model="accountRequest.username"
						class="w-full"
					/>
					<FeatherIcon
						class="text-gray-400 h-4.5 w-4.5 mt-auto mb-1 mx-2.5"
						name="at-sign"
					/>
					<Link
						:label="__('Domain')"
						placeholder="example.com"
						v-model="accountRequest.domain"
						doctype="Mail Domain"
						:filters="{ tenant: user.data.tenant }"
						class="w-full"
					/>
				</div>
				<FormControl
					type="select"
					:label="__('User Role')"
					:options="[
						{ label: __('Mail User'), value: 'Mail User' },
						{ label: __('Mail Admin'), value: 'Mail Admin' },
					]"
					v-model="accountRequest.role"
				/>
				<FormControl
					type="email"
					:label="__('User Email')"
					placeholder="johndoe@personal.com"
					v-model="accountRequest.email"
				/>
				<ErrorMessage :message="inviteUser.error?.messages[0]" />
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { reactive, inject } from 'vue'
import { Dialog, FeatherIcon, FormControl, ErrorMessage, createResource } from 'frappe-ui'
import Link from '@/components/Controls/Link.vue'
import { raiseToast } from '@/utils'

const show = defineModel()
const user = inject('$user')

const accountRequest = reactive({
	username: '',
	domain: '',
	role: 'Mail User',
	email: '',
})

const inviteUser = createResource({
	url: 'mail.api.account.create_account_request',
	makeParams() {
		return {
			account: `${accountRequest.username}@${accountRequest.domain}`,
			domain_name: accountRequest.domain,
			invited_by: user.data.name,
			tenant: user.data.tenant,
			email: accountRequest.email,
			role: accountRequest.role,
		}
	},
	onSuccess(data) {
		show.value = false
		raiseToast('User invited successfully!')
	},
})
</script>
