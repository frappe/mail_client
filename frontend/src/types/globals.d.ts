export {}

declare global {
	const __: (message: string, variables?: string[]) => string
}
declare module 'vue' {
	interface ComponentCustomProperties {
		__: (message: string, variables?: string[]) => string
	}
}
