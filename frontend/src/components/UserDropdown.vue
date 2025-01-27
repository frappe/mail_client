<template>
	<div>
		<Dropdown :options="userDropdownOptions">
			<template v-slot="{ open }">
				<button
					class="flex h-12 py-2 items-center rounded-md duration-300 ease-in-out"
					:class="
						isCollapsed
							? 'px-0 w-auto'
							: open
							? 'bg-white shadow-sm px-2 w-52'
							: 'hover:bg-gray-200 px-2 w-52'
					"
				>
					<span
						v-if="branding.data?.brand_html"
						v-html="branding.data?.brand_html"
						class="w-8 h-8 rounded flex-shrink-0"
					></span>
					<MailLogo v-else class="w-8 h-8 rounded flex-shrink-0" />
					<div
						class="flex flex-1 flex-col text-left duration-300 ease-in-out"
						:class="
							isCollapsed
								? 'opacity-0 ml-0 w-0 overflow-hidden'
								: 'opacity-100 ml-2 w-auto'
						"
					>
						<div class="text-base font-medium text-gray-900 leading-none">
							<span
								v-if="
									branding.data?.brand_name &&
									branding.data?.brand_name != 'Frappe'
								"
							>
								{{ branding.data?.brand_name }}
							</span>
							<span v-else> Mail </span>
						</div>
						<div v-if="userResource" class="mt-1 text-sm text-gray-700 leading-none">
							{{ convertToTitleCase(userResource.data?.full_name) }}
						</div>
					</div>
					<div
						class="duration-300 ease-in-out"
						:class="
							isCollapsed
								? 'opacity-0 ml-0 w-0 overflow-hidden'
								: 'opacity-100 ml-2 w-auto'
						"
					>
						<ChevronDown class="h-4 w-4 text-gray-700" />
					</div>
				</button>
			</template>
		</Dropdown>
		<Settings v-model="showSettings" />
	</div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import MailLogo from '@/components/Icons/MailLogo.vue'
import Settings from '@/components/Modals/Settings.vue'
import { sessionStore } from '@/stores/session'
import { Dropdown } from 'frappe-ui'
import {
	Home,
	LayoutDashboard,
	ChevronDown,
	LogIn,
	LogOut,
	ArrowRightLeft,
	Settings as SettingsIcon,
} from 'lucide-vue-next'
import { convertToTitleCase } from '../utils'
import { userStore } from '@/stores/user'

const { isLoggedIn, logout, branding } = sessionStore()
const { userResource } = userStore()
const router = useRouter()

const showSettings = ref(false)

const props = defineProps({
	isCollapsed: {
		type: Boolean,
		default: false,
	},
})

const userDropdownOptions = [
	{
		icon: Home,
		label: 'Home',
		onClick: () => {
			router.push('/')
		},
		condition: () => userResource.data.roles.includes('Mail Admin'),
	},
	{
		icon: LayoutDashboard,
		label: 'Admin Dashboard',
		onClick: () => {
			router.push('/dashboard/domains')
		},
		condition: () => userResource.data.roles.includes('Mail Admin'),
	},
	{
		icon: ArrowRightLeft,
		label: 'Switch to Desk',
		onClick: () => {
			window.location.href = '/app'
		},
		condition: () => {
			const cookies = new URLSearchParams(document.cookie.split('; ').join('&'))
			const system_user = cookies.get('system_user')
			return system_user === 'yes'
		},
	},
	{
		icon: SettingsIcon,
		label: 'Settings',
		onClick: () => {
			showSettings.value = true
		},
	},
	{
		icon: LogOut,
		label: 'Log Out',
		onClick: logout.submit,
	},
]
</script>
