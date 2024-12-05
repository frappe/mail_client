<template>
	<Dialog v-model="show" :options="{ title: __('Settings'), size: '5xl' }">
		<template #body>
			<div class="flex" :style="{ height: 'calc(100vh - 9rem)' }">
				<div class="flex w-52 shrink-0 flex-col bg-gray-50 py-3 p-4 border-r">
					<h1 class="text-xl font-semibold leading-6 text-gray-900 px-2">Settings</h1>
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
							<component :is="tab.icon" class="h-4 w-4 text-gray-700 stroke-[1.5]" />
							<span class="text-base text-gray-800">
								{{ tab.label }}
							</span>
						</button>
					</div>
				</div>
				<div class="flex flex-1 flex-col p-12 overflow-y-auto">
					<component :is="activeTab.component" v-if="activeTab" />
				</div>
				<Button
					class="my-3 mr-4 absolute right-0"
					variant="ghost"
					icon="x"
					@click="show = false"
				/>
			</div>
		</template>
	</Dialog>
</template>
<script setup>
import { markRaw, ref } from 'vue'
import UserSettings from '@/components/Settings/UserSettings.vue'
import { Dialog, Button } from 'frappe-ui'
import { User, Mailbox } from 'lucide-vue-next'

const show = defineModel()
const tabs = [
	{
		label: 'User',
		icon: User,
		component: markRaw(UserSettings),
	},
	{
		label: 'Mailbox',
		icon: Mailbox,
	},
]
const activeTab = ref(tabs[0])
</script>
