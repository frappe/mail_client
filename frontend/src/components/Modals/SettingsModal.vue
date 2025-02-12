<template>
	<Dialog v-model="show" :options="{ title: __('Settings'), size: '5xl' }">
		<template #body>
			<div class="flex" :style="{ height: 'calc(100vh - 9rem)' }">
				<div class="flex w-52 shrink-0 flex-col border-r bg-gray-50 p-4 py-3">
					<h1 class="px-2 text-xl font-semibold leading-6 text-gray-900">Settings</h1>
					<div class="mt-3 space-y-1">
						<button
							v-for="tab in tabs"
							:key="tab.label"
							class="flex h-7 w-full items-center gap-2 rounded px-2 py-1"
							:class="[
								activeTab.label == tab.label ? 'bg-gray-200' : 'hover:bg-gray-100',
							]"
							@click="activeTab = tab"
						>
							<component :is="tab.icon" class="h-4 w-4 stroke-[1.5] text-gray-700" />
							<span class="text-base text-gray-800">
								{{ tab.label }}
							</span>
						</button>
					</div>
				</div>
				<div class="flex flex-1 flex-col overflow-y-auto p-12">
					<component :is="activeTab.component" v-if="activeTab" />
				</div>
				<Button
					class="absolute right-0 my-3 mr-4"
					variant="ghost"
					icon="x"
					@click="show = false"
				/>
			</div>
		</template>
	</Dialog>
</template>
<script setup lang="ts">
import { markRaw, ref } from 'vue'
import { Mailbox, User } from 'lucide-vue-next'
import { Button, Dialog } from 'frappe-ui'

import MailAccountSettings from '@/components/Settings/MailAccountSettings.vue'
import UserSettings from '@/components/Settings/UserSettings.vue'

const show = defineModel()

const tabs = [
	{
		label: 'User',
		icon: User,
		component: markRaw(UserSettings),
	},
	{
		label: 'Mail Account',
		icon: Mailbox,
		component: markRaw(MailAccountSettings),
	},
]
const activeTab = ref(tabs[0])
</script>
