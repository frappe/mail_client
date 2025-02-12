<template>
	<FormControl type="text" label="User" :value="user.data?.name" readonly class="mb-4" />

	<form
		v-if="!user.data?.tenant"
		class="flex flex-col space-y-4"
		@submit.prevent="createTenant.submit()"
	>
		<FormControl
			v-model="tenantName"
			type="text"
			:label="__('Organization Name')"
			placeholder="Unico Plastics Inc."
			required
		/>
		<ErrorMessage :message="createTenant.error?.messages[0]" />
		<Button variant="solid" :loading="createTenant.loading"> Create Organization </Button>
	</form>
	<div class="mt-6 text-center">
		<button class="text-center text-base font-medium hover:underline" @click="logout.submit()">
			{{ __('Need to switch accounts? Log out.') }}
		</button>
	</div>
</template>
<script setup lang="ts">
import { inject, ref } from 'vue'
import { Button, ErrorMessage, FormControl, createResource } from 'frappe-ui'

import { sessionStore } from '@/stores/session'

const user = inject('$user')
const { logout } = sessionStore()

const tenantName = ref('')

const createTenant = createResource({
	url: 'mail.api.admin.create_tenant',
	makeParams() {
		return { tenant_name: tenantName.value }
	},
	onSuccess() {
		window.location.reload()
	},
})
</script>
