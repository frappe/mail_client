<template>
	<Dialog
		v-model="show"
		:options="{
			title: __('Add Domain'),
			actions: [
				{
					label: __(domainRequest?.data ? 'Verify DNS' : 'Add Domain'),
					variant: 'solid',
					onClick: domainRequest?.data ? verifyDNS.submit : domainRequest.submit,
				},
			],
		}"
	>
		<template #body-content>
			<div class="space-y-4">
				<p class="text-p-base">
					{{
						__(
							`To add a domain, you must already own it. If you don't have one, purchase one and return here.`,
						)
					}}
				</p>
				<FormControl
					type="text"
					:label="__('Domain Name')"
					placeholder="example.com"
					v-model="domainName"
					:readonly="!!domainRequest?.data"
					autocomplete="off"
				/>
				<ErrorMessage :message="domainRequest.error?.messages[0]" />
				<div v-if="domainRequest.data?.verification_key" class="space-y-4">
					<p class="text-p-base">
						{{
							__(
								`Add the following TXT record to your domain's DNS records to verify your ownership:`,
							)
						}}
					</p>
					<Copy
						:label="__('Verification Key')"
						:value="domainRequest.data.verification_key"
					/>
					<ErrorMessage :message="verifyDNS.error?.messages[0] || verificationError" />
				</div>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { ref, inject, watch } from 'vue'
import { Dialog, FormControl, ErrorMessage, createResource } from 'frappe-ui'
import Copy from '@/components/Controls/Copy.vue'
import { raiseToast } from '@/utils'

const show = defineModel()
const user = inject('$user')

const domainName = ref('')
const verificationError = ref('')

const emit = defineEmits(['reloadDomains'])

watch(show, () => {
	if (show.value) {
		domainName.value = ''
		verificationError.value = ''
		domainRequest.reset()
		verifyDNS.reset()
	}
})

const domainRequest = createResource({
	url: 'mail.api.admin.get_domain_request',
	makeParams() {
		return { domain_name: domainName.value, mail_tenant: user.data.tenant }
	},
})

const verifyDNS = createResource({
	url: 'mail.api.admin.verify_dns_record',
	makeParams() {
		return { domain_request: domainRequest?.data.name }
	},
	onSuccess(data) {
		if (data) {
			show.value = false
			emit('reloadDomains')
			raiseToast('Domain added successfully!')
		} else verificationError.value = __('Failed to verify DNS record.')
	},
})
</script>
