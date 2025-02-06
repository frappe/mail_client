<template>
	<form class="flex flex-col space-y-4" @submit.prevent="login.submit({ usr, pwd })">
		<FormControl
			label="Email"
			type="text"
			placeholder="johndoe@mail.com"
			autocomplete="email"
			v-model="usr"
			required
		/>
		<FormControl
			label="Password"
			type="password"
			placeholder="••••••••"
			name="password"
			autocomplete="current-password"
			v-model="pwd"
			required
		/>
		<ErrorMessage :message="login.error" />
		<Button variant="solid" :loading="login.loading"> Log In </Button>
	</form>
	<div class="mt-6 text-center">
		<router-link class="text-center text-base font-medium hover:underline" to="signup">
			New member? Create an account.
		</router-link>
	</div>
</template>
<script setup>
import { ref } from 'vue'
import { Button, FormControl, ErrorMessage } from 'frappe-ui'
import { sessionStore } from '@/stores/session'

const { login } = sessionStore()

const usr = ref('')
const pwd = ref('')
</script>
