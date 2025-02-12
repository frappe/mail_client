<template>
	<Dialog
		v-model="show"
		:options="{
			title: __('Add Member'),
			actions: [
				{
					label: __(accountRequest.send_invite ? 'Invite Member' : 'Add Member'),
					variant: 'solid',
					onClick: addMember.submit,
				},
			],
		}"
	>
		<template #body-content>
			<div class="space-y-4">
				<div class="flex items-center justify-between">
					<FormControl
						v-model="accountRequest.username"
						type="text"
						:label="__('Username')"
						placeholder="johndoe"
						class="w-full"
					/>
					<FeatherIcon
						class="mx-2.5 mb-1.5 mt-auto h-4 w-4 text-gray-400"
						name="at-sign"
					/>
					<LinkControl
						v-model="accountRequest.domain"
						:label="__('Domain')"
						placeholder="yourdomain.com"
						doctype="Mail Domain"
						:filters="{ tenant: user.data.tenant, is_verified: 1 }"
						class="w-full"
					/>
				</div>
				<FormControl
					v-model="accountRequest.role"
					type="select"
					:label="__('Member Role')"
					:options="[
						{ label: __('Mail User'), value: 'Mail User' },
						{ label: __('Mail Admin'), value: 'Mail Admin' },
					]"
				/>
				<hr />
				<FormControl
					v-model="accountRequest.send_invite"
					type="checkbox"
					:label="__('Send Invite')"
				/>
				<FormControl
					v-if="accountRequest.send_invite"
					v-model="accountRequest.email"
					type="email"
					:label="__('Email')"
					placeholder="johndoe@personal.com"
				/>
				<template v-else>
					<FormControl
						v-model="accountRequest.first_name"
						type="text"
						:label="__('First Name')"
						placeholder="John"
					/>
					<FormControl
						v-model="accountRequest.last_name"
						type="text"
						:label="__('Last Name')"
						placeholder="Doe"
					/>
					<FormControl
						v-model="accountRequest.password"
						type="password"
						:label="__('Password')"
						placeholder="••••••••"
					/>
				</template>
				<ErrorMessage :message="addMember.error?.messages[0]" />
			</div>
		</template>
	</Dialog>
</template>

<script setup lang="ts">
import { inject, reactive, watch } from 'vue'
import { Dialog, ErrorMessage, FeatherIcon, FormControl, createResource } from 'frappe-ui'

import { raiseToast } from '@/utils'
import LinkControl from '@/components/Controls/LinkControl.vue'

const show = defineModel()
const user = inject('$user')

const defaultAccountRequest = {
	username: '',
	domain: '',
	role: 'Mail User',
	send_invite: true,
	email: '',
	first_name: '',
	last_name: '',
	password: '',
}

const accountRequest = reactive({ ...defaultAccountRequest })

const emit = defineEmits(['reloadMembers'])

watch(
	() => accountRequest.send_invite,
	() => addMember.reset(),
)

watch(show, () => {
	if (show.value) {
		Object.assign(accountRequest, defaultAccountRequest)
		addMember.reset()
	}
})

const addMember = createResource({
	url: 'mail.api.admin.add_member',
	makeParams() {
		return {
			tenant: user.data.tenant,
			...accountRequest,
		}
	},
	onSuccess() {
		raiseToast(
			__(
				accountRequest.send_invite
					? 'Member invited successfully'
					: 'Member added successfully',
			),
		)
		if (!accountRequest.send_invite) emit('reloadMembers')
		show.value = false
	},
})
</script>
