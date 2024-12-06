<template>
	<h1 class="font-semibold mb-8">Profile</h1>
	<div class="flex justify-start w-full items-center gap-x-4">
		<Avatar
			:image="userResource.data?.user_image"
			:label="userResource.data?.full_name"
			size="3xl"
			class="w-20 h-20"
		/>
		<div class="flex flex-col">
			<span class="text-xl font-semibold">{{ userResource.data?.full_name }}</span>
			<span class="text-base text-gray-700">{{ userResource.data?.email }}</span>
		</div>
	</div>

	<div class="mt-12 mb-4 flex items-center">
		<h1 class="font-semibold">API Access</h1>
		<Button
			:label="userResource.data?.api_key ? 'Regenerate Secret' : 'Generate Keys'"
			class="ml-auto"
			@click="generateKeys.submit()"
		/>
	</div>

	<Copy v-if="userResource.data?.api_key" label="API Key" :value="userResource.data?.api_key" />

	<div v-else class="mt-2">
		<p class="text-base">You don't have an API key yet. Generate one to access the API.</p>
	</div>

	<Dialog v-model="showSecret" :options="{ title: __('API Access') }">
		<template #body-content>
			<p class="text-base">
				Please copy the API secret now. You won’t be able to see it again!
			</p>
			<Copy label="API Key" :value="userResource.data?.api_key" />
			<Copy label="API Secret" :value="apiSecret" />
		</template>
	</Dialog>
</template>
<script setup>
import { ref } from 'vue'
import Copy from '@/components/Controls/Copy.vue'
import { Avatar, Button, Dialog, createResource } from 'frappe-ui'
import { userStore } from '@/stores/user'

const { userResource } = userStore()
const showSecret = ref(false)
const apiSecret = ref('')

const generateKeys = createResource({
	url: 'frappe.core.doctype.user.user.generate_keys',
	makeParams() {
		return {
			user: userResource.data?.name,
		}
	},
	onSuccess(data) {
		if (!userResource.data?.api_key) userResource.reload()
		apiSecret.value = data.api_secret
		showSecret.value = true
	},
})
</script>
