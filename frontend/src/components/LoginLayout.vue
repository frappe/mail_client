<template>
	<div class="min-h-screen sm:bg-gray-50">
		<div class="relative z-10 mx-auto py-8 sm:w-max sm:py-32">
			<div class="flex">
				<slot name="logo">
					<div class="mx-auto flex items-center space-x-2">
						<MailLogo class="inline-block h-7 w-7" />
						<span
							class="select-none text-xl font-semibold tracking-tight text-gray-900"
						>
							Frappe Mail
						</span>
					</div>
				</slot>
			</div>
			<div
				class="mx-auto w-full bg-white px-4 py-8 sm:mt-6 sm:w-96 sm:rounded-lg sm:px-8 sm:shadow-xl"
			>
				<div class="mb-6 text-center">
					<span
						class="text-center text-lg font-medium leading-5 tracking-tight text-gray-900"
					>
						{{ title }}
					</span>
				</div>
				<slot />
			</div>
		</div>
		<div class="absolute bottom-4 z-[1] flex w-full justify-center">
			<FrappeLogo class="h-4" />
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import MailLogo from '@/components/Icons/MailLogo.vue'
import FrappeLogo from '@/components/Icons/FrappeLogo.vue'

const route = useRoute()

const title = computed(() => {
	switch (route.name) {
		case 'Login':
			return __('Sign in to your account')
		case 'Setup':
			return __('Set up organization')
		default:
			return __('Create a new account')
	}
})
</script>
