<template>
	<div class="relative flex h-full flex-col">
		<div class="h-full flex-1">
			<div class="flex h-screen text-base">
				<div
					class="relative block min-h-0 flex-shrink-0 overflow-hidden hover:overflow-auto"
				>
					<AppSidebar />
				</div>
				<div id="scrollContainer" class="w-full overflow-auto">
					<slot />
				</div>
			</div>
		</div>
	</div>
</template>
<script setup>
import AppSidebar from './AppSidebar.vue'
</script>
