import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'

import router from '@/router'
import { userStore } from '@/stores/user'

export const sessionStore = defineStore('mail-session', () => {
	const { userResource } = userStore()

	const sessionUser = () => {
		const cookies = new URLSearchParams(document.cookie.split('; ').join('&'))
		let _sessionUser = cookies.get('user_id')
		if (_sessionUser === 'Guest') {
			_sessionUser = null
		}
		return _sessionUser
	}

	const user = ref(sessionUser())
	const isLoggedIn = computed(() => !!user.value)

	const login = createResource({
		url: 'login',
		onError: () => {
			throw new Error('Invalid email or password')
		},
		onSuccess: () => {
			userResource.reload()
			user.value = sessionUser()
			login.reset()

			if (user.value === 'Administrator') window.location.replace('/app')
			else router.replace({ name: 'Inbox' })
		},
	})

	const logout = createResource({
		url: 'logout',
		onSuccess() {
			sessionStorage.removeItem('currentInboxMail')
			sessionStorage.removeItem('currentSentMail')
			sessionStorage.removeItem('currentDraftsMail')
			userResource.reset()
			user.value = null
			window.location.reload()
		},
	})

	const branding = createResource({
		url: 'mail.api.mail.get_branding',
		cache: 'brand',
		auto: true,
		onSuccess(data) {
			document.querySelector("link[rel='icon']").href = data.favicon
		},
	})

	return {
		user,
		isLoggedIn,
		login,
		logout,
		branding,
	}
})
