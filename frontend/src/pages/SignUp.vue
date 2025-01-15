<template>
	<div>
		<div class="mb-6 text-center">
			<span class="text-center text-lg font-medium leading-5 tracking-tight text-gray-900">
				Create a new account
			</span>
		</div>
		<form class="flex flex-col space-y-4">
			<FormControl
				label="Email"
				type="email"
				placeholder="johndoe@mail.com"
				autocomplete="email"
				v-model="email"
				required
			/>
			<Button variant="solid"> Sign Up </Button>
		</form>
		<div class="mt-6 text-center">
			<router-link class="text-center text-base font-medium hover:underline" to="login">
				Already have an account? Log in.
			</router-link>
		</div>
	</div>
</template>
<script setup>
import { FormControl, Button } from 'frappe-ui'
</script>
