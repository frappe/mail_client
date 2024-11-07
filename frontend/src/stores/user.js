import router from '@/router'
import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'

export const userStore = defineStore('mail-users', () => {
	let userResource = createResource({
		url: 'mail.api.mail.get_user_info',
		onError(error) {
			if (error && error.exc_type === 'AuthenticationError') {
				router.push('/login')
			}
		},
		auto: true,
	})

	return {
		userResource,
	}
})
