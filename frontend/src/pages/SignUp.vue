<template>
	<div>
		<div class="mb-6 text-center">
			<span class="text-center text-lg font-medium leading-5 tracking-tight text-gray-900">
				Create a new account
			</span>
		</div>
		<form class="flex flex-col space-y-4" @submit.prevent="submit">
			<FormControl
				label="Email"
				type="email"
				placeholder="johndoe@mail.com"
				autocomplete="email"
				v-model="email"
				:disabled="!!props.requestKey || isVerificationStep"
				required
			/>
			<FormControl
				v-if="isVerificationStep"
				label="Verification Code"
				type="text"
				placeholder="5 digit verification code"
				maxlength="5"
				autocomplete="email"
				v-model="otp"
				required
			/>
			<template v-if="props.requestKey">
				<FormControl
					label="First Name"
					type="text"
					placeholder="John"
					autocomplete="given-name"
					v-model="firstName"
					required
				/>
				<FormControl
					label="Last Name"
					type="text"
					placeholder="Doe"
					autocomplete="family-name"
					v-model="lastName"
					required
				/>
				<FormControl
					label="Password"
					type="password"
					placeholder="••••••••"
					name="password"
					autocomplete="current-password"
					v-model="password"
					required
				/>
			</template>
			<Button variant="solid">{{ buttonLabel }}</Button>
			<Button v-if="isVerificationStep">Resend OTP</Button>
		</form>
		<div class="mt-6 text-center">
			<router-link class="text-center text-base font-medium hover:underline" to="/login">
				Already have an account? Log in.
			</router-link>
		</div>
	</div>
</template>
<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { FormControl, Button, createResource } from 'frappe-ui'

const router = useRouter()

const props = defineProps({
	requestKey: {
		type: String,
		required: false,
	},
})

const isVerificationStep = ref(false)
const email = ref('')
const otp = ref('')
const accountRequest = ref('')

const buttonLabel = computed(() => {
	if (props.requestKey) return 'Create Account'
	return isVerificationStep.value ? 'Verify' : 'Sign Up'
})

const signUp = createResource({
	url: 'mail.api.account.signup',
	onSuccess(data) {
		accountRequest.value = data.name
		isVerificationStep.value = true
	},
})

const verifyOtp = createResource({
	url: 'mail.api.account.verify_otp',
	onSuccess(requestKey) {
		router.push({
			name: 'AccountSetup',
			params: { requestKey },
		})
	},
})

const verifiedEmail = createResource({
	url: 'mail.api.account.get_verified_email',
	onSuccess(data) {
		if (data) email.value = data
		else router.replace({ name: 'SignUp' })
	},
})

const createAccount = createResource({
	url: 'mail.api.account.create_account',
	onSuccess(data) {
		console.log(data)
	},
})

watch(
	() => props.requestKey,
	(val) => {
		isVerificationStep.value = false
		if (val) verifiedEmail.submit({ request_key: val })
	},
	{ immediate: true }
)

const submit = () => {
	if (props.requestKey) createAccount.submit()
	else if (isVerificationStep.value)
		verifyOtp.submit({ account_request: accountRequest.value, otp: otp.value })
	else signUp.submit({ email: email.value })
}
</script>
