<template>
	<div class="h-full flex flex-col">
		<header
			class="sticky top-0 z-10 flex items-center justify-between border-b bg-white px-3 py-2.5 sm:px-5"
		>
			<Breadcrumbs :items="[{ label: __('Members') }]" />
			<Button :label="__('Add Member')" iconLeft="user-plus" @click="showAddMember = true" />
		</header>
		<div class="m-6 flex-1 flex flex-col">
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
									<p class="text-gray-600 mt-0.5">{{ row.name }}</p>
								</div>
							</div>
							<div class="flex items-center mx-auto">
								<Badge v-if="row.is_admin" theme="orange" :label="__('Admin')" />
							</div>
							<div class="flex items-center ml-auto">
								<Dropdown
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
	<AddMember v-model="showAddMember" @reloadMembers="members.reload()" />
	<Dialog :options="removeMemberOptions" v-model="showRemoveMember" />
</template>
<script setup>
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
import AddMember from '@/components/Modals/AddMember.vue'
import { raiseToast } from '@/utils'

const user = inject('$user')

const showAddMember = ref(false)
const showRemoveMember = ref(false)
const memberToBeRemoved = ref('')

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
