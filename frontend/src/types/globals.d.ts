export {}

type TranslateFunction = (message: string, variables?: string[]) => string
declare global {
	const __: TranslateFunction
}
declare module 'vue' {
	interface ComponentCustomProperties {
		__: TranslateFunction
	}
}
