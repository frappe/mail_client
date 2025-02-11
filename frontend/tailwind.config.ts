import config from 'frappe-ui/src/utils/tailwind.config'

export default {
	presets: [config],
	content: [
		'./index.html',
		'./src/**/*.{vue,js,ts,jsx,tsx}',
		'./node_modules/frappe-ui/src/components/**/*.{vue,js,ts,jsx,tsx}',
	],
	theme: {
		extend: {
			strokeWidth: {
				1.5: '1.5',
			},
		},
	},
	plugins: [],
}
