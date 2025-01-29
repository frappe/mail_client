<template>
	<div class="h-full flex flex-col">
		<header
			class="sticky top-0 z-10 flex items-center justify-between border-b bg-white px-3 py-2.5 sm:px-5"
		>
			<Breadcrumbs :items="[{ label: 'Domains' }]" />
			<Button :label="__('Add Domain')" iconLeft="plus" @click="showAddDomain = true" />
		</header>
		<div class="m-8 flex-1 flex flex-col"></div>
	</div>
</template>
<script setup>
import { ref, inject } from 'vue'
import { Button, Breadcrumbs, ListView, createListResource } from 'frappe-ui'
import AddDomain from '@/components/Modals/AddDomain.vue'

const user = inject('$user')

const showAddDomain = ref(false)

const props = defineProps({
	domainName: {
		type: String,
		required: true,
	},
})
</script>
