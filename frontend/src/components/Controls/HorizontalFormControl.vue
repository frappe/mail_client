<template>
	<div class="grid grid-cols-1 sm:grid-cols-2" :class="{ 'text-ink-gray-4': disabled }">
		<label class="font-medium leading-normal my-auto">
			{{ label }}
		</label>
		<slot />
	</div>
</template>

<script setup>
const props = defineProps({
	label: {
		type: String,
		required: true,
	},
	disabled: {
		type: Boolean,
		default: false,
	},
})
</script>
