<template>
	<div class="block pt-2 text-sm">
		<span class="mb-2 block leading-4 text-gray-700">{{ props.label }}</span>
		<button
			class="flex w-full items-center rounded-lg border-2 bg-gray-100 p-2"
			@click="copyToClipBoard(props.value)"
		>
			<span class="scrollbar-none mr-1.5 overflow-x-scroll text-nowrap text-gray-800">
				{{ props.value }}
			</span>
			<span class="ml-auto rounded border bg-white p-1 text-xs text-gray-600">
				{{ message }}
			</span>
		</button>
	</div>
</template>
<script setup>
import { ref } from 'vue'

const message = ref('Copy')

const props = defineProps({
	label: {
		type: String,
		required: true,
	},
	value: {
		type: String,
		required: true,
	},
})

const copyToClipBoard = async (text) => {
	try {
		await navigator.clipboard.writeText(text)
		message.value = 'Copied!'
		setTimeout(() => {
			message.value = 'Copy'
		}, 2000)
	} catch (e) {
		alert('Failed to copy text. Please copy from here: ' + text)
	}
}
</script>

<style>
.scrollbar-none::-webkit-scrollbar {
	display: none;
}

.scrollbar-none {
	-ms-overflow-style: none;
	scrollbar-width: none;
}
</style>
