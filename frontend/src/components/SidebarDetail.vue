<template>
	<div class="space-y-1 p-2.5">
		<div class="flex items-center justify-between">
			<h2 class="mr-1 truncate font-semibold" :class="{ italic: !mail.subject }">
				{{ mail.subject || __('[No subject]') }}
			</h2>
			<MailDate :datetime="mail.creation" :in-list="true" />
		</div>
		<h3 class="snippet line-clamp-1 text-xs">
			{{ mail.display_name ? mail.display_name : mail.sender }}
		</h3>
		<h4
			class="snippet line-clamp-2 h-9 text-xs text-gray-600"
			:class="{ italic: !mail.snippet }"
		>
			{{ mail.snippet || __('— No message body —') }}
		</h4>
		<div class="flex items-center">
			<!-- <div class="flex rounded bg-gray-100 p-1 text-gray-700">
				<Paperclip class="mr-1 h-3.5 w-3.5" />
				<span class="text-xs">{{ 20 }}</span>
			</div> -->
			<Badge
				class="ml-auto"
				v-if="Object.keys(STATUS).includes(badgeField)"
				:label="badge.label"
				:theme="badge.theme"
			/>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Paperclip } from 'lucide-vue-next'
import { Badge } from 'frappe-ui'

import MailDate from '@/components/MailDate.vue'

const props = defineProps<{
	mail: object
}>()

interface BadgeType {
	label: string
	theme: 'gray' | 'blue' | 'green' | 'orange' | 'red'
}

const STATUS = {
	Draft: { label: __('Draft'), theme: 'gray' },
	Queued: { label: __('Queued'), theme: 'orange' },
	Blocked: { label: __('Blocked'), theme: 'red' },
	Failed: { label: __('Failed'), theme: 'red' },
	'DSN Report': { label: __('DSN Report'), theme: 'blue' },
	'DMARC Report': { label: __('DMARC Report'), theme: 'blue' },
}

const badgeField = computed(() =>
	props.mail.mail_type === 'Outgoing Mail' ? props.mail.status : props.mail.type,
)

const badge = computed<BadgeType>(() => STATUS[badgeField.value])
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
