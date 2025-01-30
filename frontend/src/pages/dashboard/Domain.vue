<template>
	<div v-if="domain?.doc" class="h-full flex flex-col">
		<header
			class="sticky top-0 z-10 flex items-center justify-between border-b bg-white px-3 py-2.5 sm:px-5"
		>
			<Breadcrumbs :items="BREADCRUMBS" />
			<Dropdown :options="DROPDOWN_OPTIONS" :button="{ icon: 'more-horizontal' }" />
		</header>
		<div class="m-6 space-y-6">
			<div class="grid grid-cols-1 sm:grid-cols-2 border rounded-md">
				<div class="p-4 border-r">
					<Switch
						:label="__('Enabled')"
						v-model="domain.doc.enabled"
						@update:modelValue="
							domain.setValue.submit({ enabled: domain.doc.enabled })
						"
					/>
					<Switch
						:label="__('Verified')"
						v-model="domain.doc.is_verified"
						:disabled="true"
					/>
					<Switch
						:label="__('Subdomain')"
						v-model="domain.doc.is_subdomain"
						:disabled="true"
					/>
					<Switch
						:label="__('Root Domain')"
						v-model="domain.doc.is_root_domain"
						:disabled="true"
					/>
				</div>
				<div class="p-4">
					<div class="my-1.5 space-y-3">
						<HorizontalFormControl :label="__('Mail Tenant')" :disabled="true">
							<FormControl v-model="domain.doc.tenant_name" :disabled="true" />
						</HorizontalFormControl>
						<HorizontalFormControl :label="__('DKIM RSA Key Size')">
							<FormControl
								type="select"
								:options="[
									{ label: '2048', value: 2048 },
									{ label: '4096', value: 4096 },
								]"
								v-model="domain.doc.dkim_rsa_key_size"
								@update:modelValue="
									domain.setValue.submit({
										dkim_rsa_key_size: domain.doc.dkim_rsa_key_size,
									})
								"
							/>
						</HorizontalFormControl>
						<HorizontalFormControl :label="__('Newsletter Retention (Days)')">
							<FormControl
								type="number"
								min="1"
								max="7"
								v-model="domain.doc.newsletter_retention"
								@update:modelValue="
									domain.setValueDebounced.submit({
										newsletter_retention: Number(
											domain.doc.newsletter_retention
										),
									})
								"
							/>
						</HorizontalFormControl>
					</div>
				</div>
			</div>
			<div class="border rounded-md p-4">
				<ListView
					class="flex-1"
					:columns="LIST_COLUMNS"
					:rows="domain.doc.dns_records"
					:options="LIST_OPTIONS"
					row-key="name"
				/>
			</div>
		</div>
	</div>
</template>
<script setup>
import { useRouter } from 'vue-router'
import {
	Switch,
	FormControl,
	Dropdown,
	Breadcrumbs,
	ListView,
	createDocumentResource,
} from 'frappe-ui'
import { raiseToast } from '@/utils'
import HorizontalFormControl from '@/components/Controls/HorizontalFormControl.vue'

const router = useRouter()

const props = defineProps({
	domainName: {
		type: String,
		required: true,
	},
})

const domain = createDocumentResource({
	doctype: 'Mail Domain',
	name: props.domainName,
	transform(data) {
		for (const d of ['enabled', 'is_verified', 'is_subdomain', 'is_root_domain'])
			data[d] = !!data[d]

		data.dns_records.forEach((d) => {
			d.priority = d.priority.toString()
			d.ttl = d.ttl.toString()
		})
	},
	setValue: {
		onError(error) {
			raiseToast(error.messages[0], 'error')
		},
	},
	// whitelistedMethods: {
	// 	verifyDnsRecords: 'verify_dns_records',
	// },
	onError(error) {
		if (error.exc_type === 'DoesNotExistError') router.replace({ name: 'Domains' })
	},
})

const BREADCRUMBS = [
	{ label: 'Domains', route: '/dashboard/domains' },
	{ label: props.domainName },
]

const DROPDOWN_OPTIONS = [
	{
		label: 'View in Desk',
		icon: 'external-link',
		onClick: () => {
			window.open(`/app/mail-domain/${props.domainName}`, '_blank').focus()
		},
	},
	{
		label: 'Verify DNS Records',
		icon: 'check-square',
		onClick: () => {
			// domain.verifyDnsRecords.submit()
		},
	},
	{
		label: 'Refresh DNS Records',
		icon: 'refresh-cw',
		onClick: () => {},
	},
	{
		label: 'Rotate DKIM Keys',
		icon: 'rotate-cw',
		onClick: () => {},
	},
]

const LIST_COLUMNS = [
	{
		label: 'Type',
		key: 'type',
		width: 0.2,
	},
	{
		label: 'Host',
		key: 'host',
		width: 0.5,
	},
	{
		label: 'Priority',
		key: 'priority',
		width: 0.2,
	},
	{
		label: 'Value',
		key: 'value',
	},
	{
		label: 'TTL (Recommended)',
		key: 'ttl',
		width: 0.2,
	},
]

const LIST_OPTIONS = {
	selectable: false,
}
</script>
