<template>
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
		<ErrorMessage :message="errorMessage" />
		<Button
			variant="solid"
			:loading="signUp.loading || verifyOtp.loading || createAccount.loading"
		>
			{{ buttonLabel }}
		</Button>
		<Button
			v-if="isVerificationStep"
			type="button"
			:loading="resendOtp.loading"
			@click="resendOtp.submit()"
		>
			Resend OTP
		</Button>
	</form>
	<div class="mt-6 text-center">
		<router-link class="text-center text-base font-medium hover:underline" to="/login">
			Already have an account? Log in.
		</router-link>
	</div>
</template>
<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { FormControl, Button, createResource, ErrorMessage } from 'frappe-ui'
import { sessionStore } from '@/stores/session'
import { raiseToast } from '@/utils'

const router = useRouter()
const { login } = sessionStore()

const props = defineProps({
	requestKey: {
		type: String,
		required: false,
	},
})

const isVerificationStep = ref(false)
const email = ref('')
const otp = ref('')
const firstName = ref('')
const lastName = ref('')
const password = ref('')
const accountRequest = ref('')
const errorMessage = ref('')

const buttonLabel = computed(() => {
	if (props.requestKey) return 'Create Account'
	return isVerificationStep.value ? 'Verify' : 'Sign Up'
})

const signUp = createResource({
	url: 'mail.api.account.signup',
	makeParams() {
		return { email: email.value }
	},
	onSuccess(data) {
		errorMessage.value = ''
		accountRequest.value = data.name
		isVerificationStep.value = true
		raiseToast('A verification code has been sent to your registered email address.')
	},
	onError(error) {
		errorMessage.value = error.messages[0]
	},
})

const resendOtp = createResource({
	url: 'mail.api.account.resend_otp',
	makeParams() {
		return { account_request: accountRequest.value }
	},
	onSuccess() {
		raiseToast('A verification code has been sent to your registered email address.')
	},
	onError(error) {
		raiseToast(error.messages[0], 'error')
	},
})

const verifyOtp = createResource({
	url: 'mail.api.account.verify_otp',
	makeParams() {
		return {
			account_request: accountRequest.value,
			otp: otp.value,
		}
	},
	onSuccess(requestKey) {
		errorMessage.value = ''
		router.push({ name: 'AccountSetup', params: { requestKey } })
	},
	onError(error) {
		errorMessage.value = error.messages[0]
	},
})

const getAccountRequest = createResource({
	url: 'mail.api.account.get_account_request',
	makeParams() {
		return { request_key: props.requestKey }
	},
	onSuccess(data) {
		if (data?.email && !data?.is_verified && !data?.is_expired) email.value = data.email
		else router.replace({ name: 'SignUp' })
	},
})

const createAccount = createResource({
	url: 'mail.api.account.create_account',
	makeParams() {
		return {
			request_key: props.requestKey,
			first_name: firstName.value,
			last_name: lastName.value,
			password: password.value,
		}
	},
	onSuccess() {
		errorMessage.value = ''
		login.submit({ usr: email.value, pwd: password.value })
	},
	onError(error) {
		errorMessage.value = error.messages[0]
	},
})

watch(
	() => props.requestKey,
	(val) => {
		isVerificationStep.value = false
		if (!val) return
		if (val.length === 32) getAccountRequest.submit()
		else router.replace({ name: 'SignUp' })
	},
	{ immediate: true }
)

const submit = () => {
	if (props.requestKey) createAccount.submit()
	else if (isVerificationStep.value) verifyOtp.submit()
	else signUp.submit()
}
</script>
