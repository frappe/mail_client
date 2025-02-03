<template>
	<div class="h-full flex flex-col">
		<header
			class="sticky top-0 z-10 flex items-center justify-between border-b bg-white px-3 py-2.5 sm:px-5"
		>
			<Breadcrumbs :items="[{ label: __('Members') }]" />
			<Button
				:label="__('Invite User')"
				iconLeft="user-plus"
				@click="showInviteUser = true"
			/>
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
	<InviteUser v-model="showInviteUser" />
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
import InviteUser from '@/components/Modals/InviteUser.vue'

const user = inject('$user')

const showInviteUser = ref(false)

const members = createResource({
	url: 'mail.api.admin.get_tenant_members',
	makeParams: () => ({ tenant: user.data?.tenant }),
	auto: true,
	cache: ['mailTenantMembers', user.data?.tenant],
})
</script>
