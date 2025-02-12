<template>
	<form class="flex flex-col space-y-4" @submit.prevent="login.submit({ usr, pwd })">
		<FormControl
			v-model="usr"
			:label="__('Username')"
			type="text"
			placeholder="johndoe@mail.com"
			autocomplete="email"
			required
		/>
		<FormControl
			v-model="pwd"
			:label="__('Password')"
			type="password"
			placeholder="••••••••"
			name="password"
			autocomplete="current-password"
			required
		/>
		<ErrorMessage :message="login.error" />
		<Button variant="solid" :loading="login.loading">{{ __('Log In ') }} </Button>
	</form>
	<div class="mt-6 text-center">
		<router-link class="text-center text-base font-medium hover:underline" to="/signup">
			{{ __('New member? Create an account.') }}
		</router-link>
	</div>
</template>
<script setup lang="ts">
import { ref } from 'vue'
import { Button, ErrorMessage, FormControl } from 'frappe-ui'

import { sessionStore } from '@/stores/session'

const { login } = sessionStore()

const usr = ref('')
const pwd = ref('')
</script>
