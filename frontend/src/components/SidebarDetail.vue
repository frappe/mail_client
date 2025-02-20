<template>
	<div class="space-y-1 p-2.5">
		<div class="flex items-center justify-between">
			<div class="mr-2 flex items-center space-x-2 truncate">
				<h2 class="truncate font-semibold">{{ mail.subject || __('(No Subject)') }}</h2>
				<Badge
					v-if="Object.keys(STATUS).includes(badgeField)"
					:label="badge.label"
					:theme="badge.theme"
					size="sm"
					class="!text-[11px]"
				/>
			</div>
			<MailDate :datetime="mail.creation" :in-list="true" />
		</div>

		<h3 class="snippet line-clamp-1 text-xs">
			{{ mail.display_name ? mail.display_name : mail.sender }}
		</h3>
		<h4 class="snippet line-clamp-2 h-9 text-xs text-gray-600">
			{{ mail.snippet }}
		</h4>
	</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
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
