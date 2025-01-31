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
				:columns="LIST_COLUMNS"
				:rows="members.data"
				:options="{ selectable: false, showTooltip: false }"
				row-key="name"
			>
				<ListHeader />
				<ListRows>
					<ListRow
						v-for="row in members.data"
						:key="row.name"
						v-slot="{ column, item }"
						:row="row"
					>
						<ListRowItem :item="item"> </ListRowItem>
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
	Button,
	Breadcrumbs,
	ListView,
	ListHeader,
	ListRows,
	ListRow,
	ListRowItem,
	createListResource,
} from 'frappe-ui'
import InviteUser from '@/components/Modals/InviteUser.vue'

const user = inject('$user')

const showInviteUser = ref(false)

const LIST_COLUMNS = [
	{
		label: 'User',
		key: 'name',
	},
]

const members = createListResource({
	doctype: 'Mail Tenant Member',
	fields: ['name', 'is_admin'],
	filters: { tenant: user.data?.tenant },
	auto: true,
	pageLength: 9999,
	cache: ['mailTenantMembers', user.data?.tenant],
})
</script>
