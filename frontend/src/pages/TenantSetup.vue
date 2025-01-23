<template>
	<FormControl type="text" label="User" :value="user.data?.name" disabled class="mb-4" />

	<form
		v-if="!user.data?.tenant"
		class="flex flex-col space-y-4"
		@submit.prevent="createTenant.submit()"
	>
		<FormControl
			type="text"
			label="Tenant Name"
			placeholder="yourcompany.frappemail.com"
			v-model="tenantName"
			required
		/>
		<FormControl type="number" label="Maximum No. of Domains" v-model="maxDomains" required />
		<FormControl
			type="number"
			label="Maximum No. of Accounts"
			v-model="maxAccounts"
			required
		/>
		<FormControl type="number" label="Maximum No. of Groups" v-model="maxGroups" required />
		<ErrorMessage :message="createTenant.error?.messages[0]" />
		<Button variant="solid" :loading="createTenant.loading"> Create Tenant </Button>
	</form>

	<form v-else class="flex flex-col space-y-4" @submit.prevent="createDomainRequest.submit()">
		<FormControl
			type="text"
			label="Tenant Name"
			:value="user.data?.tenant_name"
			required
			disabled
		/>
		<FormControl
			type="text"
			label="Domain Name"
			placeholder="yourcompany.com"
			v-model="domainName"
			required
		/>
		<ErrorMessage :message="createDomainRequest.error?.messages[0]" />
		<Button variant="solid" :loading="createDomainRequest.loading"> Add Domain </Button>
	</form>

	<div class="mt-6 text-center">
		<button class="text-center text-base font-medium hover:underline" @click="logout.submit()">
			Need to switch accounts? Log out.
		</button>
	</div>
</template>
<script setup>
import { ref, inject } from 'vue'
import { FormControl, Button, createResource, ErrorMessage } from 'frappe-ui'
import { sessionStore } from '@/stores/session'

const user = inject('$user')
const { logout } = sessionStore()

const tenantName = ref('')
const maxDomains = ref(10)
const maxAccounts = ref(1000)
const maxGroups = ref(100)
const domainName = ref('')

const createTenant = createResource({
	url: 'mail.api.account.create_tenant',
	makeParams() {
		return {
			tenant_name: tenantName.value,
			max_domains: maxDomains.value,
			max_accounts: maxAccounts.value,
			max_groups: maxGroups.value,
		}
	},
	onSuccess() {
		window.location.reload()
	},
})

const createDomainRequest = createResource({
	url: 'mail.api.account.create_domain_request',
	makeParams() {
		return {
			domain_name: domainName.value,
			mail_tenant: user.data?.tenant,
		}
	},
	onSuccess() {
		window.location.reload()
	},
})
</script>
