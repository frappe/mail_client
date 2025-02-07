<template>
	<div class="h-full flex flex-col">
		<header
			class="sticky top-0 z-10 flex items-center justify-between border-b bg-white px-3 py-2.5 sm:px-5"
		>
			<Breadcrumbs :items="[{ label: __('Domains') }]" />
			<Button :label="__('Add Domain')" iconLeft="plus" @click="showAddDomain = true" />
		</header>
		<div class="m-6 flex-1 flex flex-col">
			<ListView
				v-if="domains?.data"
				class="flex-1"
				:columns="LIST_COLUMNS"
				:rows="domains.data"
				:options="LIST_OPTIONS"
				row-key="name"
			>
				<ListHeader />
				<ListRows>
					<template v-if="domains.data.length">
						<ListRow
							v-for="row in domains.data"
							:key="row.name"
							v-slot="{ column, item }"
							:row="row"
						>
							<ListRowItem :item="item">
								<Badge
									v-if="column.key == 'status'"
									:theme="item === 'Enabled' ? 'green' : 'red'"
									:label="item"
								/>
								<FeatherIcon
									v-else-if="column.key == 'is_verified'"
									:name="item ? 'check' : 'x'"
									class="h-4 w-4"
								/>
							</ListRowItem>
						</ListRow>
					</template>
					<ListEmptyState v-else />
				</ListRows>
			</ListView>
		</div>
	</div>
	<AddDomain v-model="showAddDomain" @reloadDomains="domains.reload()" />
</template>
<script setup>
import { ref, inject } from 'vue'
import {
	Button,
	Breadcrumbs,
	ListView,
	ListEmptyState,
	ListHeader,
	ListRows,
	ListRow,
	ListRowItem,
	Badge,
	FeatherIcon,
	createListResource,
} from 'frappe-ui'
import AddDomain from '@/components/Modals/AddDomain.vue'

const user = inject('$user')

const showAddDomain = ref(false)

const LIST_COLUMNS = [
	{
		label: 'Domain',
		key: 'name',
	},
	{
		label: 'Status',
		key: 'status',
	},
	{
		label: 'Verified',
		key: 'is_verified',
	},
]

const LIST_OPTIONS = {
	selectable: false,
	showTooltip: false,
	emptyState: {
		title: __('No Domains Configured'),
		description: __('Please add a domain to proceed with sending and receiving emails.'),
		button: {
			label: __('Add Domain'),
			variant: 'solid',
			iconLeft: 'plus',
			onClick: () => {
				showAddDomain.value = true
			},
		},
	},
	getRowRoute: (row) => ({ name: 'Domain', params: { domainName: row.name } }),
}

const domains = createListResource({
	doctype: 'Mail Domain',
	fields: ['name', 'enabled', 'is_verified'],
	filters: { tenant: user.data?.tenant },
	auto: true,
	pageLength: 50,
	cache: ['mailTenantDomains', user.data?.tenant],
	transform(data) {
		return data.map((domain) => ({
			...domain,
			status: domain.enabled ? 'Enabled' : 'Disabled',
		}))
	},
})
</script>
