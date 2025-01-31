<template>
	<div v-if="domain?.doc" class="h-full flex flex-col">
		<header
			class="sticky top-0 z-10 flex items-center justify-between border-b bg-white px-3 py-2.5 sm:px-5"
		>
			<Breadcrumbs :items="BREADCRUMBS" />
			<div class="flex space-x-2">
				<Dropdown :options="DROPDOWN_OPTIONS" :button="{ icon: 'more-horizontal' }" />
				<Button
					variant="solid"
					:loading="domain.save.loading"
					:disabled="!domain.isDirty"
					:label="__('Save')"
					@click="domain.save.submit()"
				/>
			</div>
		</header>
		<div class="m-6 space-y-6">
			<div class="grid grid-cols-1 sm:grid-cols-2 border rounded-md">
				<div class="p-4 border-r">
					<Switch :label="__('Enabled')" v-model="domain.doc.enabled" />
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
							/>
						</HorizontalFormControl>
						<HorizontalFormControl :label="__('Newsletter Retention (Days)')">
							<FormControl
								type="number"
								min="1"
								max="7"
								v-model="domain.doc.newsletter_retention"
								@update:modelValue="
									domain.doc.newsletter_retention =
										+domain.doc.newsletter_retention
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
					:options="{ selectable: false }"
					row-key="name"
				>
					<ListHeader />
					<ListRows>
						<ListRow
							v-for="row in domain.doc.dns_records"
							:key="row.name"
							v-slot="{ column, item }"
							:row="row"
						>
							{{ item }}
						</ListRow>
					</ListRows>
				</ListView>
			</div>
		</div>
	</div>
	<Dialog :options="confirmDialogOptions" v-model="showConfirmDialog" />
</template>
<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
	Button,
	Switch,
	FormControl,
	Dropdown,
	Breadcrumbs,
	ListView,
	ListHeader,
	ListRows,
	ListRow,
	Dialog,
	createDocumentResource,
} from 'frappe-ui'
import { raiseToast } from '@/utils'
import HorizontalFormControl from '@/components/Controls/HorizontalFormControl.vue'

const props = defineProps({
	domainName: {
		type: String,
		required: true,
	},
})

const router = useRouter()

const showConfirmDialog = ref(false)
const confirmDialogAction = ref('')

const confirmDialogOptions = computed(() => ({
	title: __('Confirm'),
	message: __(
		confirmDialogAction.value === 'refreshDnsRecords'
			? `Are you sure you want to refresh the DNS records? If there are any changes, you'll need to update the DNS settings with your DNS provider accordingly.`
			: `Are you sure you want to rotate the DKIM keys? This will generate new keys for email signing and may take up to 10 minutes to propagate across DNS servers. Emails sent during this period may fail DKIM verification.`
	),
	size: 'xl',
	icon: {
		name: 'alert-triangle',
		appearance: 'warning',
	},
	actions: [
		{
			label: __('Confirm'),
			variant: 'solid',
			onClick:
				confirmDialogAction.value === 'refreshDnsRecords'
					? domain.refreshDnsRecords.submit
					: domain.rotateDkimKeys.submit,
		},
	],
}))

const domain = createDocumentResource({
	doctype: 'Mail Domain',
	name: props.domainName,
	transform(data) {
		for (const d of ['enabled', 'is_verified', 'is_subdomain', 'is_root_domain'])
			data[d] = !!data[d]

		// todo: fix isDirty save randomly not working
	},
	setValue: {
		onSuccess() {
			raiseToast('Domain settings saved successfully')
		},
		onError(error) {
			raiseToast(error.messages[0], 'error')
			domain.reload()
		},
	},
	whitelistedMethods: {
		verifyDnsRecords: {
			method: 'verify_dns_records',
			makeParams() {
				return { do_not_save: false }
			},
			onSuccess(data) {
				raiseToast(
					data ? 'DNS records verified successfully.' : 'DNS verification failed.',
					data ? 'success' : 'error'
				)
				domain.reload()
			},
			onError(error) {
				raiseToast(error.messages[0], 'error')
				domain.reload()
			},
		},
		refreshDnsRecords: {
			method: 'refresh_dns_records',
			makeParams() {
				return { do_not_save: false }
			},
			onSuccess(data) {
				showConfirmDialog.value = false
				raiseToast('DNS Records refreshed successfully.')
				domain.reload()
			},
			onError(error) {
				raiseToast(error.messages[0], 'error')
				domain.reload()
			},
		},
		rotateDkimKeys: {
			method: 'rotate_dkim_keys',
			onSuccess(data) {
				showConfirmDialog.value = false
				raiseToast('DKIM Keys rotated successfully.')
				domain.reload()
			},
			onError(error) {
				raiseToast(error.messages[0], 'error')
				domain.reload()
			},
		},
	},
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
		onClick: domain.verifyDnsRecords.submit,
	},
	{
		label: 'Refresh DNS Records',
		icon: 'refresh-cw',
		onClick: () => {
			confirmDialogAction.value = 'refreshDnsRecords'
			showConfirmDialog.value = true
		},
	},
	{
		label: 'Rotate DKIM Keys',
		icon: 'rotate-cw',
		onClick: () => {
			confirmDialogAction.value = 'rotateDkimKeys'
			showConfirmDialog.value = true
		},
	},
]

const LIST_COLUMNS = [
	{
		label: 'Type',
		key: 'type',
		width: '10%',
	},
	{
		label: 'Host',
		key: 'host',
		width: '20%',
	},
	{
		label: 'Priority',
		key: 'priority',
		width: '10%',
	},
	{
		label: 'Value',
		key: 'value',
		width: '50%',
	},
	{
		label: 'TTL (Recommended)',
		key: 'ttl',
		width: '10%',
	},
]
</script>
