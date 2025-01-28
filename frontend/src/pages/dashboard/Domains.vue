<template>
	<div class="h-full">
		<header
			class="sticky top-0 z-10 flex items-center justify-between border-b bg-white px-3 py-2.5 sm:px-5"
		>
			<Breadcrumbs :items="[{ label: 'Domains' }]" />
			<Button :label="__('Add Domain')" iconLeft="plus" @click="showAddDomain = true" />
		</header>
	</div>
	<AddDomain v-model="showAddDomain" />
</template>
<script setup>
import { ref } from 'vue'
import { Button, Breadcrumbs } from 'frappe-ui'
import AddDomain from '@/components/Modals/AddDomain.vue'

const showAddDomain = ref(false)
</script>
