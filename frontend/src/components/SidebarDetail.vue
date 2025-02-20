<template>
	<div class="space-y-0.5 p-2">
		<div class="flex items-center justify-between">
			<div class="mr-1 truncate font-semibold">
				{{ mail.subject || __('(No Subject)') }}
			</div>
			<MailDate :datetime="mail.creation" :in-list="true" />
		</div>
		<div class="snippet line-clamp-1 text-xs">
			{{ mail.display_name ? mail.display_name : mail.sender }}
		</div>
		<div class="snippet line-clamp-2 h-9 text-xs text-gray-600">
			{{ mail.snippet }}
		</div>
	</div>
</template>
<script setup lang="ts">
import MailDate from './MailDate.vue'

defineProps({
	mail: {
		type: Object,
		required: true,
	},
})
</script>
<style>
.snippet {
	display: -webkit-box;
	-webkit-box-orient: vertical;
	text-overflow: ellipsis;
	width: 100%;
	overflow: hidden;
	line-height: 1.5;
}
</style>
