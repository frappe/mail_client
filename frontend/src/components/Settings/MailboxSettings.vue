<template>
	<h1 class="font-semibold mb-8">Mailbox</h1>
	<div class="flex items-center mb-2">
		<span class="font-medium leading-normal text-gray-800 text-base">Email Address</span>
		<Link
			v-model="mailbox"
			doctype="Mailbox"
			:filters="{ user: userResource.data?.name }"
			class="ml-auto"
		/>
	</div>
	<IndividiualMailboxSettings v-if="mailbox" :mailbox="mailbox" />
</template>
<script setup>
import { ref } from 'vue'
import Link from '@/components/Controls/Link.vue'
import IndividiualMailboxSettings from '@/components/Settings/IndividualMailboxSettings.vue'
import { userStore } from '@/stores/user'

const { userResource, defaultOutgoing } = userStore()
const mailbox = ref(defaultOutgoing.data)
</script>
