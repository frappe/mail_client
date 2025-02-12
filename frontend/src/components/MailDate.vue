<template>
	<Tooltip :text="tooltipText" :disabled="inList">
		<div class="cursor-pointer text-xs text-gray-600">
			{{ formattedDate }}
		</div>
	</Tooltip>
</template>
<script setup lang="ts">
import { computed, inject } from 'vue'
import { Tooltip } from 'frappe-ui'

import { timeAgo } from '@/utils'

const dayjs = inject('$dayjs')

const props = defineProps({
	datetime: {
		type: String,
		required: true,
	},
	inList: {
		type: Boolean,
		default: false,
	},
})

const formattedDate = computed(() => {
	if (props.inList) {
		if (dayjs(props.datetime).isToday()) {
			return dayjs(props.datetime).format('h:mm A')
		} else if (dayjs(props.datetime).isYesterday()) {
			return `Yesterday`
		} else {
			return dayjs(props.datetime).format('DD MMM YYYY')
		}
	}
	return __(timeAgo(props.datetime))
})

const tooltipText = computed(() => {
	return __(
		`${dayjs(props.datetime).format('DD MMM YYYY')} at ${dayjs(props.datetime).format(
			'h:mm A',
		)}`,
	)
})
</script>
