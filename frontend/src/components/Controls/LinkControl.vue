<template>
	<div class="space-y-1.5">
		<label v-if="attrs.label" class="block" :class="labelClasses">
			{{ attrs.label }}
		</label>
		<AutocompleteControl
			ref="autocomplete"
			v-model="value"
			:options="options.data"
			:size="attrs.size || 'sm'"
			:variant="attrs.variant"
			:placeholder="attrs.placeholder"
			:filterable="false"
		>
			<template #target="{ open, togglePopover }">
				<slot name="target" v-bind="{ open, togglePopover }" />
			</template>

			<template #prefix>
				<slot name="prefix" />
			</template>

			<template #item-prefix="{ active, selected, option }">
				<slot name="item-prefix" v-bind="{ active, selected, option }" />
			</template>

			<template #item-label="{ active, selected, option }">
				<slot name="item-label" v-bind="{ active, selected, option }" />
			</template>

			<template v-if="attrs.onCreate" #footer="{ value, close }">
				<div>
					<Button
						variant="ghost"
						class="w-full !justify-start"
						label="Create New"
						@click="attrs.onCreate(value, close)"
					>
						<template #prefix>
							<Plus class="stroke-1.5 h-4 w-4" />
						</template>
					</Button>
				</div>
			</template>
		</AutocompleteControl>
	</div>
</template>

<script setup lang="ts">
import { computed, ref, useAttrs } from 'vue'
import { watchDebounced } from '@vueuse/core'
import { Plus } from 'lucide-vue-next'
import { Button, createResource } from 'frappe-ui'

import AutocompleteControl from '@/components/Controls/AutocompleteControl.vue'

const props = defineProps({
	doctype: {
		type: String,
		required: true,
	},
	filters: {
		type: Object,
		default: () => ({}),
	},
	modelValue: {
		type: String,
		default: '',
	},
})

const emit = defineEmits(['update:modelValue', 'change'])

const attrs = useAttrs()

const valuePropPassed = computed(() => 'value' in attrs)

const value = computed({
	get: () => (valuePropPassed.value ? attrs.value : props.modelValue),
	set: (val) => {
		return (
			val?.value && emit(valuePropPassed.value ? 'change' : 'update:modelValue', val?.value)
		)
	},
})

const autocomplete = ref(null)
const text = ref('')

watchDebounced(
	() => autocomplete.value?.query,
	(val) => {
		val = val || ''
		if (text.value === val) return
		text.value = val
		reload(val)
	},
	{ debounce: 300, immediate: true },
)

watchDebounced(
	() => props.doctype,
	() => reload(''),
	{ debounce: 300, immediate: true },
)

const options = createResource({
	url: 'frappe.desk.search.search_link',
	cache: [props.doctype, text.value],
	method: 'POST',
	params: {
		txt: text.value,
		doctype: props.doctype,
		filters: props.filters,
	},
	transform: (data) => {
		return data.map((option) => {
			return {
				label: option.value,
				value: option.value,
				description: option.description,
			}
		})
	},
})

function reload(val) {
	options.update({
		params: {
			txt: val,
			doctype: props.doctype,
			filters: props.filters,
		},
	})
	options.reload()
}

const labelClasses = computed(() => {
	return [
		{
			sm: 'text-xs',
			md: 'text-base',
		}[attrs.size || 'sm'],
		'text-gray-600',
	]
})
</script>
