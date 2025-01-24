<template>
	<FormControl type="text" label="User" :value="user.data?.name" disabled class="mb-4" />

	<form
		v-if="!user.data?.tenant"
		class="flex flex-col space-y-4"
		@submit.prevent="createTenant.submit()"
	>
		<FormControl
			type="text"
			:label="__('Tenant Name')"
			placeholder="yourcompany.frappemail.com"
			v-model="tenantName"
			required
		/>
		<FormControl type="number" label="Maximum No. of Domains" v-model="maxDomains" required />
		<FormControl
			type="number"
			:label="__('Maximum No. of Accounts')"
			v-model="maxAccounts"
			required
		/>
		<FormControl type="number" label="Maximum No. of Groups" v-model="maxGroups" required />
		<ErrorMessage :message="createTenant.error?.messages[0]" />
		<Button variant="solid" :loading="createTenant.loading"> Create Tenant </Button>
	</form>

	<form
		v-else
		class="flex flex-col space-y-4"
		@submit.prevent="verificationKey ? verifyKey.submit() : createDomainRequest.submit()"
	>
		<FormControl
			type="text"
			:label="__('Tenant Name')"
			:value="user.data?.tenant_name"
			required
			disabled
		/>
		<FormControl
			type="url"
			:label="__('Domain Name')"
			placeholder="https://example.com"
			v-model="domainName"
			required
			:disabled="!!verificationKey"
		/>

		<FormControl
			v-if="verificationKey"
			type="text"
			:label="__('Verification Key')"
			:value="verificationKey"
			:description="__('Paste this key in to the DNS records for your domain.')"
			required
			disabled
		/>
		<ErrorMessage
			:message="
				createDomainRequest.error?.messages[0] ||
				verifyKey.error?.messages[0] ||
				errorMessage
			"
		/>
		<Button variant="solid" :loading="createDomainRequest.loading || verifyKey.loading">
			{{ verificationKey ? __('Verify') : __('Add Domain') }}
		</Button>
	</form>

	<div class="mt-6 text-center">
		<button class="text-center text-base font-medium hover:underline" @click="logout.submit()">
			{{ __('Need to switch accounts? Log out.') }}
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
const verificationKey = ref('')
const errorMessage = ref('')

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
	onSuccess(data) {
		verificationKey.value = data
	},
})

const verifyKey = createResource({
	url: 'mail.api.account.verify_domain_key',
	makeParams() {
		return {
			domain_name: domainName.value,
			verification_key: verificationKey.value,
		}
	},
	onSuccess(data) {
		if (data) window.location.reload()
		else errorMessage.value = 'Failed to verify DNS records.'
	},
})
</script>
