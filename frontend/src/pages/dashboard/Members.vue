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
				:columns="[{ label: __('User') }]"
				:rows="members.data"
				:options="{ selectable: false, showTooltip: false }"
				row-key="name"
			>
				<ListHeader />
				<ListRows>
					<ListRow v-for="row in members.data" :key="row.name" :row="row">
						<!-- todo: fix vertical spacing -->
						<div class="flex items-center space-x-2">
							<Avatar :image="row.user_image" :label="row.full_name" size="lg" />
							<div class="text-sm">
								<p class="font-medium text-gray-900">{{ row.full_name }}</p>
								<p class="text-gray-600 mt-0.5">{{ row.name }}</p>
							</div>
						</div>
					</ListRow>
				</ListRows>
			</ListView>
		</div>
	</div>
	<AddMember v-model="showAddMember" />
</template>
<script setup>
import { ref, inject } from 'vue'
import {
	Avatar,
	Button,
	Breadcrumbs,
	ListView,
	ListHeader,
	ListRows,
	ListRow,
	createResource,
} from 'frappe-ui'
import AddMember from '@/components/Modals/AddMember.vue'

const user = inject('$user')

const showAddMember = ref(false)

const members = createResource({
	url: 'mail.api.admin.get_tenant_members',
	makeParams: () => ({ tenant: user.data?.tenant }),
	auto: true,
	cache: ['mailTenantMembers', user.data?.tenant],
})
</script>
