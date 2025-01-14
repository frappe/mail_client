<template>
	<div>
		<div class="mb-6 text-center">
			<span class="text-center text-lg font-medium leading-5 tracking-tight text-gray-900">
				Sign in to your account
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
			<FormControl
				label="Password"
				type="password"
				placeholder="••••••••"
				v-model="password"
				name="password"
				autocomplete="current-password"
				required
			/>
			<Button variant="solid"> Log In </Button>
		</form>
		<div class="mt-6 text-center hover:underline">
			<router-link class="text-center text-base font-medium" to="signup">
				New member? Create an account.
			</router-link>
		</div>
	</div>
</template>
<script setup>
import { FormControl, Button } from 'frappe-ui'
</script>
