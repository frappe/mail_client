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
						type="text"
						:label="__('Username')"
						placeholder="johndoe"
						v-model="accountRequest.username"
						class="w-full"
					/>
					<FeatherIcon
						class="text-gray-400 h-4 w-4 mt-auto mb-1.5 mx-2.5"
						name="at-sign"
					/>
					<Link
						:label="__('Domain')"
						placeholder="yourdomain.com"
						v-model="accountRequest.domain"
						doctype="Mail Domain"
						:filters="{ tenant: user.data.tenant }"
						class="w-full"
					/>
				</div>
				<FormControl
					type="select"
					:label="__('Member Role')"
					:options="[
						{ label: __('Mail User'), value: 'Mail User' },
						{ label: __('Mail Admin'), value: 'Mail Admin' },
					]"
					v-model="accountRequest.role"
				/>
				<hr />
				<FormControl
					type="checkbox"
					:label="__('Send Invite')"
					v-model="accountRequest.send_invite"
				/>
				<FormControl
					v-if="accountRequest.send_invite"
					type="email"
					:label="__('Email')"
					placeholder="johndoe@personal.com"
					v-model="accountRequest.email"
				/>
				<template v-else>
					<FormControl
						type="text"
						:label="__('First Name')"
						placeholder="John"
						v-model="accountRequest.first_name"
					/>
					<FormControl
						type="text"
						:label="__('Last Name')"
						placeholder="Doe"
						v-model="accountRequest.last_name"
					/>
					<FormControl
						type="password"
						:label="__('Password')"
						placeholder="••••••••"
						v-model="accountRequest.password"
					/>
				</template>
				<ErrorMessage :message="addMember.error?.messages[0]" />
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { reactive, inject, watch } from 'vue'
import { Dialog, FeatherIcon, FormControl, ErrorMessage, createResource } from 'frappe-ui'
import Link from '@/components/Controls/Link.vue'
import { raiseToast } from '@/utils'

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
					: 'Member added successfully'
			)
		)
		if (!accountRequest.send_invite) emit('reloadMembers')
		show.value = false
	},
})
</script>
