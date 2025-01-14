<template>
	<div class="h-screen sm:bg-gray-50">
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
				<slot />
			</div>
		</div>
		<div class="absolute bottom-4 z-[1] flex w-full justify-center">
			<FrappeLogo class="h-4" />
		</div>
	</div>
</template>

<script setup>
import MailLogo from '@/components/Icons/MailLogo.vue'
import FrappeLogo from '@/components/Icons/FrappeLogo.vue'
</script>
