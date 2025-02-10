<template>
	<div class="p-2">
		<div class="flex items-center justify-between">
			<div class="font-semibold">
				{{ mail.display_name ? mail.display_name : mail.sender }}
			</div>
			<MailDate :datetime="mail.creation" :in-list="true" />
		</div>
		<div class="subject text-xs">
			{{ mail.subject }}
		</div>
		<div class="snippet text-xs text-gray-600">
			{{ mail.snippet }}
		</div>
	</div>
</template>
<script setup>
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
	line-clamp: 2;
	-webkit-line-clamp: 2;
	-webkit-box-orient: vertical;
	text-overflow: ellipsis;
	width: 100%;
	overflow: hidden;
	line-height: 1.5;
}

.subject {
	display: -webkit-box;
	line-clamp: 1;
	-webkit-line-clamp: 1;
	-webkit-box-orient: vertical;
	text-overflow: ellipsis;
	width: 100%;
	overflow: hidden;
	line-height: 1.5;
}
</style>
