<template>
	<Popover transition="default">
		<template #target="{ togglePopover, isOpen }">
			<slot v-bind="{ isOpen, togglePopover }">
				<span class="text-base"> {{ modelValue || '' }} </span>
			</slot>
		</template>
		<template #body="{ togglePopover }">
			<div
				v-if="reaction"
				class="flex items-center justify-center gap-2 rounded-full bg-white px-2 py-1 shadow-sm"
			>
				<div
					v-for="r in reactionEmojis"
					:key="r"
					class="size-5 cursor-pointer rounded-full bg-white text-xl"
					@click="() => (emoji = r) && togglePopover()"
				>
					<button>
						{{ r }}
					</button>
				</div>
				<Button class="rounded-full" icon="plus" @click.stop="() => (reaction = false)" />
			</div>
			<div v-else class="my-3 max-w-max transform rounded-lg bg-white px-4 sm:px-0">
				<div
					class="relative max-h-96 overflow-y-auto rounded-lg pb-3 shadow-2xl ring-1 ring-black ring-opacity-5"
				>
					<div class="flex gap-2 px-3 pb-1 pt-3">
						<div class="flex-1">
							<FormControl
								v-model="search"
								type="text"
								placeholder="Search by keyword"
								:debounce="300"
							/>
						</div>
						<Button @click="setRandom">Random</Button>
					</div>
					<div class="w-96"></div>
					<div v-for="(emojis, group) in emojiGroups" :key="group" class="px-3">
						<div class="sticky top-0 bg-white pb-2 pt-3 text-sm text-gray-700">
							{{ group }}
						</div>
						<div class="grid w-96 grid-cols-12 place-items-center">
							<button
								v-for="_emoji in emojis"
								:key="_emoji.description"
								class="h-8 w-8 rounded-md p-1 text-2xl hover:bg-gray-100 focus:outline-none focus:ring focus:ring-blue-200"
								:title="_emoji.description"
								@click="() => (emoji = _emoji.emoji) && togglePopover()"
							>
								{{ _emoji.emoji }}
							</button>
						</div>
					</div>
				</div>
			</div>
		</template>
	</Popover>
</template>
<script setup lang="ts">
import { computed, ref } from 'vue'
import { gemoji } from 'gemoji'
import { Button, FormControl, Popover } from 'frappe-ui'

const search = ref('')
const emoji = defineModel()
const reaction = defineModel('reaction')

const reactionEmojis = ref(['👍', '❤️', '😂', '😮', '😢', '🙏'])

const emojiGroups = computed(() => {
	const groups = {}
	for (const _emoji of gemoji) {
		if (search.value) {
			const keywords = [_emoji.description, ..._emoji.names, ..._emoji.tags]
				.join(' ')
				.toLowerCase()
			if (!keywords.includes(search.value.toLowerCase())) {
				continue
			}
		}

		let group = groups[_emoji.category]
		if (!group) {
			groups[_emoji.category] = []
			group = groups[_emoji.category]
		}
		group.push(_emoji)
	}
	if (!Object.keys(groups).length) {
		groups['No results'] = []
	}
	return groups
})

function setRandom() {
	const total = gemoji.length
	const index = randomInt(0, total - 1)
	emoji.value = gemoji[index].emoji
}

function randomInt(min, max) {
	return Math.floor(Math.random() * (max - min + 1) + min)
}

defineExpose({ setRandom })
</script>
