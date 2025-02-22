import { createResource } from 'frappe-ui'

export default function translationPlugin(app) {
	app.config.globalProperties.__ = translate
	window.__ = translate
	if (!window.translatedMessages) fetchTranslations()
}

function translate(message: string, variables?: string[]) {
	const translatedMessages = window.translatedMessages || {}
	const translatedMessage = translatedMessages[message] || message

	const hasPlaceholders = /{\d+}/.test(message) && variables
	if (!hasPlaceholders) return translatedMessage

	return translatedMessage.replace(/{(\d+)}/g, (match: string, number: number) => {
		return typeof variables[number] !== 'undefined' ? variables[number] : match
	})
}

function fetchTranslations() {
	createResource({
		url: 'mail.api.mail.get_translations',
		cache: 'translations',
		auto: true,
		transform: (data) => {
			window.translatedMessages = data
		},
	})
}
