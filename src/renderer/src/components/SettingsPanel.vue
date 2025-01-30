<script setup>
defineProps({
	currentShortcut: {
		type: String,
		required: true
	},
	shortcutIsRecording: {
		type: Boolean,
		required: true
	}
})

defineEmits(['startRecording', 'stopRecording'])
</script>

<template>
	<div class="w-full">
		<div class="bg-white rounded-2xl p-6 shadow-sm space-y-6">
			<h3 class="text-2xl font-medium text-[#1d1d1f]">Settings</h3>

			<div class="space-y-4">
				<h4 class="text-sm font-medium text-[#86868b]">Keyboard Shortcuts</h4>
				<div class="flex items-center justify-between">
					<div class="text-sm text-[#1d1d1f]">
						Recording shortcut:
						<kbd
							class="px-2 py-1 text-xs font-medium bg-[#f5f5f7] rounded-lg shadow-sm text-[#1d1d1f] ml-1"
						>
							{{ currentShortcut }}
						</kbd>
					</div>
					<button
						:class="{
							'px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-200 focus:outline-none': true,
							'bg-[#f5f5f7] hover:bg-[#e5e5e7] text-[#1d1d1f]': !shortcutIsRecording,
							'bg-red-50 text-red-600 animate-pulse': shortcutIsRecording
						}"
						@click="
							shortcutIsRecording ? $emit('stopRecording') : $emit('startRecording')
						"
					>
						{{ shortcutIsRecording ? 'Press desired keys...' : 'Change Shortcut' }}
					</button>
				</div>
			</div>
		</div>
	</div>
</template>
