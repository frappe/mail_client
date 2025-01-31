<template>
	<div class="h-full flex flex-col">
		<header
			class="sticky top-0 z-10 flex items-center justify-between border-b bg-white px-3 py-2.5 sm:px-5"
		>
			<Breadcrumbs :items="[{ label: 'Domains' }]" />
			<Button :label="__('Add Domain')" iconLeft="plus" @click="showAddDomain = true" />
		</header>
		<div class="m-6 flex-1 flex flex-col">
			<ListView
				class="flex-1"
				:columns="LIST_COLUMNS"
				:rows="domains?.data || []"
				:options="LIST_OPTIONS"
				row-key="name"
			>
				<ListHeader />
				<ListRows>
					<ListRow
						v-for="row in domains?.data || []"
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
								v-if="column.key == 'is_verified'"
								:name="item ? 'check' : 'x'"
								class="h-4 w-4"
							/>
						</ListRowItem>
					</ListRow>
				</ListRows>
			</ListView>
		</div>
	</div>
	<AddDomain v-model="showAddDomain" @reloadDomains="domains.reload()" />
</template>
<script setup>
import { ref, inject } from 'vue'
import { useRouter } from 'vue-router'
import {
	Button,
	Breadcrumbs,
	ListView,
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
const router = useRouter()

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
	onRowClick: (row) => router.push({ name: 'Domain', params: { domainName: row.name } }),
}

const domains = createListResource({
	doctype: 'Mail Domain',
	fields: ['name', 'enabled', 'is_verified'],
	filters: { tenant: user.data?.tenant },
	auto: true,
	pageLength: 50,
	cache: ['mailDomains', user.data?.tenant],
	transform(data) {
		return data.map((domain) => ({
			...domain,
			status: domain.enabled ? 'Enabled' : 'Disabled',
		}))
	},
})
</script>
