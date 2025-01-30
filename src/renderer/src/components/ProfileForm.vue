<script setup>
import { ref, watch } from 'vue'
import { LANGUAGES } from '../composables/languages'

const props = defineProps({
	modelValue: {
		type: Object,
		required: true
	}
})

const emit = defineEmits(['update:modelValue', 'save', 'cancel'])

// Create local state
const localProfile = ref({ ...props.modelValue })

// Watch for external changes
watch(
	() => props.modelValue,
	(newValue) => {
		localProfile.value = { ...newValue }
	},
	{ deep: true }
)

// Update handler
const updateProfile = (field, value) => {
	localProfile.value[field] = value
	emit('update:modelValue', { ...localProfile.value })
}
</script>

<template>
	<div class="space-y-4">
		<div>
			<input
				:value="localProfile.name"
				type="text"
				required
				placeholder="Profile Name"
				class="w-full px-3 py-2 bg-[#f5f5f7] rounded-lg focus:outline-none focus:bg-white focus:ring-2 focus:ring-[#1d1d1f]"
				@input="updateProfile('name', $event.target.value)"
			/>
		</div>
		<div>
			<textarea
				required
				placeholder="Enter prompt"
				rows="2"
				class="w-full px-3 py-2 bg-[#f5f5f7] rounded-lg focus:outline-none focus:bg-white focus:ring-2 focus:ring-[#1d1d1f]"
				:value="localProfile.prompt"
				@input="updateProfile('prompt', $event.target.value)"
			></textarea>
		</div>
		<div>
			<select
				:value="localProfile.language"
				class="w-full px-3 py-2 bg-[#f5f5f7] rounded-lg focus:outline-none focus:bg-white focus:ring-2 focus:ring-[#1d1d1f]"
				@change="updateProfile('language', $event.target.value)"
			>
				<option v-for="(name, code) in LANGUAGES" :key="code" :value="code">
					{{ name }}
				</option>
			</select>
		</div>
		<div class="flex gap-4">
			<label class="flex items-center">
				<input
					:checked="localProfile.useAI"
					type="checkbox"
					class="form-checkbox h-4 w-4 text-[#1d1d1f]"
					@change="updateProfile('useAI', $event.target.checked)"
				/>
				<span class="ml-2 text-sm">Use AI</span>
			</label>
			<label class="flex items-center">
				<input
					:checked="localProfile.copyToClipboard"
					type="checkbox"
					class="form-checkbox h-4 w-4 text-[#1d1d1f]"
					@change="updateProfile('copyToClipboard', $event.target.checked)"
				/>
				<span class="ml-2 text-sm">Copy to Clipboard</span>
			</label>
		</div>
		<div class="flex justify-end gap-2">
			<button
				class="px-3 py-1.5 text-sm font-medium text-[#86868b] hover:text-[#1d1d1f]"
				type="button"
				@click="$emit('cancel')"
			>
				Cancel
			</button>
			<button
				class="px-3 py-1.5 text-sm font-medium bg-[#1d1d1f] text-white rounded-lg hover:bg-[#2d2d2f]"
				type="button"
				@click="$emit('save')"
			>
				Save
			</button>
		</div>
	</div>
</template>
