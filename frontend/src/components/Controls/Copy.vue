<template>
	<label class="block pt-2 text-sm">
		<span class="mb-2 block leading-4 text-gray-700">{{ props.label }}</span>
		<button
			class="border-2 rounded-lg bg-gray-100 p-2 w-full flex items-center"
			@click="copyToClipBoard(props.value)"
		>
			<span class="text-gray-800">{{ props.value }}</span>
			<span class="border rounded bg-white p-1 text-gray-600 text-xs ml-auto">
				{{ message }}
			</span>
		</button>
	</label>
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
	await navigator.clipboard.writeText(text)
	message.value = 'Copied!'
	setTimeout(() => {
		message.value = 'Copy'
	}, 2000)
}
</script>
