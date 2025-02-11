<template>
	<div class="flex h-full flex-col">
		<header
			class="sticky top-0 z-10 flex items-center justify-between border-b bg-white px-3 py-2.5 sm:px-5"
		>
			<Breadcrumbs :items="[{ label: __('Members') }]" />
			<Button
				:label="__('Add Member')"
				icon-left="user-plus"
				@click="showAddMember = true"
			/>
		</header>
		<div class="m-6 flex flex-1 flex-col">
			<ListView
				v-if="members?.data"
				class="flex-1"
				:columns="[{ label: __('User'), key: 'user' }]"
				:rows="members.data"
				:options="{ selectable: false, showTooltip: false, rowHeight: 50 }"
				row-key="name"
			>
				<ListHeader />
				<ListRows>
					<ListRow v-for="row in members.data" :key="row.name" :row="row">
						<div class="grid grid-cols-3">
							<div class="flex items-center space-x-2">
								<Avatar :image="row.user_image" :label="row.full_name" size="lg" />
								<div class="text-sm">
									<p class="font-medium text-gray-900">{{ row.full_name }}</p>
									<p class="mt-0.5 text-gray-600">{{ row.name }}</p>
								</div>
							</div>
							<div class="mx-auto flex items-center">
								<Badge
									v-if="row.is_admin"
									:theme="row.name === tenantOwner.data ? 'orange' : 'blue'"
									:label="__(row.name === tenantOwner.data ? 'Owner' : 'Admin')"
								/>
							</div>
							<div class="ml-auto flex items-center">
								<Dropdown
									v-if="row.name !== tenantOwner.data"
									:options="dropdownOptions(row.name, row.is_admin)"
									:button="{ icon: 'more-horizontal', variant: 'ghost' }"
								/>
							</div>
						</div>
					</ListRow>
				</ListRows>
			</ListView>
		</div>
	</div>
	<AddMemberModal v-model="showAddMember" @reload-members="members.reload()" />
	<Dialog v-model="showRemoveMember" :options="removeMemberOptions" />
</template>
<script setup lang="ts">
import { ref, computed, inject } from 'vue'
import {
	Avatar,
	Badge,
	Button,
	Breadcrumbs,
	ListView,
	ListHeader,
	ListRows,
	ListRow,
	Dialog,
	Dropdown,
	createResource,
} from 'frappe-ui'
import AddMemberModal from '@/components/Modals/AddMemberModal.vue'
import { raiseToast } from '@/utils'

const user = inject('$user')

const showAddMember = ref(false)
const showRemoveMember = ref(false)
const memberToBeRemoved = ref('')

const tenantOwner = createResource({
	url: 'frappe.client.get_value',
	makeParams: () => ({
		doctype: 'Mail Tenant',
		fieldname: 'user',
		filters: user.data?.tenant,
		as_dict: false,
	}),
	auto: true,
	cache: ['mailTenantOwner', user.data?.tenant],
})

const members = createResource({
	url: 'mail.api.admin.get_tenant_members',
	makeParams: () => ({ tenant: user.data?.tenant }),
	auto: true,
	cache: ['mailTenantMembers', user.data?.tenant],
})

const editAdminRole = createResource({
	url: 'frappe.client.set_value',
	makeParams: (values) => ({
		doctype: 'Mail Tenant Member',
		name: values.name,
		fieldname: 'is_admin',
		value: values.is_admin,
	}),
	onSuccess: () => {
		raiseToast(__('Role updated successfully'))
		members.reload()
	},
	onError: (error) => raiseToast(error.messages[0], 'error'),
})

const removeMember = createResource({
	url: 'frappe.client.delete',
	makeParams: () => ({
		doctype: 'Mail Tenant Member',
		name: memberToBeRemoved.value,
	}),
	onSuccess: () => {
		raiseToast(__('Member removed successfully'))
		showRemoveMember.value = false
		members.reload()
	},
	onError: (error) => raiseToast(error.messages[0], 'error'),
})

const dropdownOptions = (name, isAdmin) => {
	return [
		{
			label: isAdmin ? __('Remove Admin') : __('Make Admin'),
			icon: isAdmin ? 'shield-off' : 'shield',
			onClick: () => editAdminRole.submit({ name, is_admin: !isAdmin }),
		},
		{
			label: __('Remove Member'),
			icon: 'user-x',
			onClick: () => {
				memberToBeRemoved.value = name
				showRemoveMember.value = true
			},
		},
	]
}

const removeMemberOptions = computed(() => ({
	title: __('Remove Member'),
	message: __(`Are you sure you want to remove member ${memberToBeRemoved.value}?`),
	icon: {
		name: 'alert-triangle',
		appearance: 'warning',
	},
	actions: [
		{
			label: __('Confirm'),
			variant: 'solid',
			onClick: removeMember.submit,
		},
	],
}))
</script>
