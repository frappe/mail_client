<template>
	<div>
		<div class="mb-6 text-center">
			<span class="text-center text-lg font-medium leading-5 tracking-tight text-gray-900">
				Set up mail tenant
			</span>
		</div>
		<form class="flex flex-col space-y-4" @submit.prevent="createTenant.submit()">
			<FormControl
				type="text"
				label="Tenant Name"
				placeholder="yourcompany.frappemail.com"
				v-model="tenantName"
				required
			/>
			<FormControl
				type="number"
				label="Maximum No. of Domains"
				v-model="maxDomains"
				required
			/>
			<FormControl
				type="number"
				label="Maximum No. of Accounts"
				v-model="maxAccounts"
				required
			/>
			<FormControl
				type="number"
				label="Maximum No. of Groups"
				v-model="maxGroups"
				required
			/>
			<ErrorMessage :message="errorMessage" />
			<Button variant="solid" :loading="createTenant.loading"> Create Tenant </Button>
		</form>
	</div>
</template>
<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { FormControl, Button, createResource, ErrorMessage } from 'frappe-ui'

const router = useRouter()

const tenantName = ref('')
const maxDomains = ref(10)
const maxAccounts = ref(1000)
const maxGroups = ref(100)
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
		router.replace({ name: 'Inbox' })
	},
	onError(error) {
		errorMessage.value = error.messages[0]
	},
})
</script>
