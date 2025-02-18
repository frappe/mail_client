<template>
	<div class="mx-auto my-8 space-y-8 sm:w-[75rem]">
		<div class="flex items-center justify-between">
			<h1 class="text-xl font-medium">{{ __('MIME Message') }}</h1>
			<Button
				:label="__('Copy to Clipboard')"
				size="md"
				@click="copyToClipBoard(mime.data.message)"
			/>
		</div>
		<div v-if="mime.data" class="rounded border p-8">
			<pre style="font-size: 0.875rem">{{ mime.data.message }}</pre>
		</div>
	</div>
</template>

<script lang="ts" setup>
import { useRoute } from 'vue-router'
import { Button, createResource } from 'frappe-ui'

import { kebabToTitleCase, raiseToast } from '@/utils'

const route = useRoute()

const mime = createResource({
	url: 'mail.api.mail.get_mime_message',
	auto: true,
	makeParams: () => ({
		mail_type: kebabToTitleCase(route.fullPath.split('/')[2]),
		name: route.params.id,
	}),
})

const copyToClipBoard = async (text: string) => {
	try {
		await navigator.clipboard.writeText(text)
		raiseToast(__('Message copied successfully!'))
	} catch {
		raiseToast(__('Failed to copy text.'), 'error')
	}
}
</script>
